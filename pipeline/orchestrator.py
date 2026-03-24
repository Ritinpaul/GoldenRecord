"""
GoldenRecord Pipeline Orchestrator
Runs the complete entity resolution pipeline end-to-end
"""
import os
import sys
import json
import uuid
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from collections import defaultdict

# Add parent to path
sys.path.insert(0, str(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database.db_client import Database
from pipeline.standardization.engine import StandardizationEngine
from pipeline.blocking.engine import BlockingEngine
from pipeline.scoring.engine import ConfidenceScorer
from pipeline.survivorship.engine import SurvivorshipEngine


class PipelineOrchestrator:
    """Orchestrates the full entity resolution pipeline"""

    def __init__(self):
        self.standardizer = StandardizationEngine()
        self.blocker = BlockingEngine()
        self.scorer = ConfidenceScorer()
        self.survivorship = SurvivorshipEngine()
        self.run_id = None

    def start_run(self, source_system: str) -> str:
        """Start a new reconciliation run"""
        self.run_id = f"RUN-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"

        Database.execute("""
            INSERT INTO audit.reconciliation_log
            (run_id, source_system, records_in, run_timestamp, status)
            VALUES (%s, %s, 0, NOW(), 'running')
        """, (self.run_id, source_system))

        print(f"Started reconciliation run: {self.run_id}")
        return self.run_id

    def finish_run(self, records_in: int, records_merged: int,
                   records_flagged: int, avg_confidence: float,
                   duration_ms: int, status: str = 'completed'):
        """Finish the reconciliation run"""
        Database.execute("""
            UPDATE audit.reconciliation_log
            SET records_in = %s,
                records_merged = %s,
                records_flagged_review = %s,
                avg_confidence = %s,
                run_duration_ms = %s,
                status = %s
            WHERE run_id = %s
        """, (records_in, records_merged, records_flagged,
              avg_confidence, duration_ms, status, self.run_id))

        print(f"Finished run {self.run_id}: {records_merged} merged, {records_flagged} flagged for review")

    def standardize_raw_data(self, source_system: str) -> int:
        """Step 1: Standardize raw data"""
        print(f"\n{'='*60}")
        print(f"STEP 1: Standardizing {source_system}")
        print(f"{'='*60}")

        # Fetch raw records
        if source_system == 'crm_primary':
            raw_records = Database.execute(
                "SELECT * FROM raw_crm.primary_leads WHERE loaded_at > NOW() - INTERVAL '1 day'"
            )
        elif source_system == 'crm_secondary':
            raw_records = Database.execute(
                "SELECT * FROM raw_crm.secondary_leads WHERE loaded_at > NOW() - INTERVAL '1 day'"
            )
        elif source_system == 'marketing_automation':
            raw_records = Database.execute(
                "SELECT * FROM raw_marketing.contacts WHERE loaded_at > NOW() - INTERVAL '1 day'"
            )
        else:
            raise ValueError(f"Unknown source system: {source_system}")

        if not raw_records:
            print(f"  No new records for {source_system}")
            return 0

        print(f"  Fetched {len(raw_records)} raw records")

        # Standardize in batches
        batch_size = 1000
        standardized_count = 0

        for i in range(0, len(raw_records), batch_size):
            batch = raw_records[i:i+batch_size]
            standardized = self.standardizer.standardize_batch(batch, source_system)

            # Insert into staging
            values = [
                (r['source_record_id'], r['source_system'], r['loaded_at'],
                 r['canonical_email'], r['canonical_phone'], r['canonical_name'],
                 r['canonical_company'], r['normalized_region'],
                 r['first_name'], r['last_name'], r['title'], r['company_name'],
                 r['email'], r['phone'], r['region'], r['lead_source'],
                 r['created_at'], r['updated_at'], r['standardization_metadata'])
                for r in standardized
            ]

            from psycopg2.extras import execute_values
            with Database.get_connection() as conn:
                execute_values(conn.cur, """
                    INSERT INTO staging.standardized_records
                    (source_record_id, source_system, loaded_at,
                     canonical_email, canonical_phone, canonical_name,
                     canonical_company, normalized_region,
                     first_name, last_name, title, company_name,
                     email, phone, region, lead_source,
                     created_at, updated_at, standardization_metadata)
                    VALUES %s
                    ON CONFLICT (source_record_id, source_system) DO UPDATE SET
                        canonical_email = EXCLUDED.canonical_email,
                        canonical_phone = EXCLUDED.canonical_phone,
                        canonical_name = EXCLUDED.canonical_name,
                        canonical_company = EXCLUDED.canonical_company,
                        normalized_region = EXCLUDED.normalized_region,
                        updated_at = NOW()
                """, values)
                conn.commit()

            standardized_count += len(standardized)
            if (i + batch_size) % 10000 == 0:
                print(f"  Standardized {standardized_count} records...")

        print(f"  Standardized {standardized_count} total records")
        return standardized_count

    def create_blocking_index(self) -> int:
        """Step 2: Create blocking index"""
        print(f"\n{'='*60}")
        print(f"STEP 2: Creating Blocking Index")
        print(f"{'='*60}")

        # Get all standardized records not yet blocked
        records = Database.execute("""
            SELECT * FROM staging.standardized_records
            WHERE id NOT IN (
                SELECT DISTINCT standardized_record_id
                FROM intermediate.blocking_index
            )
        """)

        if not records:
            print("  No new records to block")
            # Still return total count
            result = Database.execute("SELECT COUNT(*) as cnt FROM intermediate.blocking_index")
            return result[0]['cnt'] if result else 0

        print(f"  Blocking {len(records)} new standardized records...")

        # Create blocking keys
        blocks = []
        for record in records:
            record_blocks = self.blocker.create_blocking_keys(record)
            blocks.extend(record_blocks)

        # Insert blocks
        if blocks:
            from psycopg2.extras import execute_values
            with Database.get_connection() as conn:
                values = [(b['record_id'], b['block_key'], b['block_type']) for b in blocks]
                execute_values(conn.cur, """
                    INSERT INTO intermediate.blocking_index
                    (standardized_record_id, block_key, block_type)
                    VALUES %s ON CONFLICT DO NOTHING
                """, values)
                conn.commit()

        print(f"  Created {len(blocks)} blocking index entries")

        # Return total blocking index count
        result = Database.execute("SELECT COUNT(*) as cnt FROM intermediate.blocking_index")
        return result[0]['cnt'] if result else 0

    def generate_candidate_pairs(self) -> int:
        """Step 3: Generate candidate pairs from blocking"""
        print(f"\n{'='*60}")
        print(f"STEP 3: Generating Candidate Pairs")
        print(f"{'='*60}")

        # Get all blocks and generate pairs
        # For efficiency, process block by block
        blocks = Database.execute("""
            SELECT block_key, block_type, standardized_record_id as record_id
            FROM intermediate.blocking_index
            ORDER BY block_key, block_type
        """)

        if not blocks:
            print("  No blocks to process")
            return 0

        print(f"  Processing {len(blocks)} blocking entries...")

        # Group by block
        block_groups = defaultdict(list)
        for block in blocks:
            key = (block['block_key'], block['block_type'])
            block_groups[key].append(block['record_id'])

        # Generate pairs
        pairs_seen = set()
        pairs_inserted = 0
        batch_values = []

        from psycopg2.extras import execute_values

        for (block_key, block_type), record_ids in block_groups.items():
            if len(record_ids) > 1000:
                continue  # Skip oversized blocks

            for i in range(len(record_ids)):
                for j in range(i + 1, len(record_ids)):
                    a, b = record_ids[i], record_ids[j]
                    if a > b:
                        a, b = b, a

                    pair_key = (a, b)
                    if pair_key not in pairs_seen:
                        pairs_seen.add(pair_key)
                        batch_values.append((a, b, block_type))

                        if len(batch_values) >= 5000:
                            with Database.get_connection() as conn:
                                execute_values(conn.cur, """
                                    INSERT INTO intermediate.candidate_pairs
                                    (record_a_id, record_b_id, block_type)
                                    VALUES %s ON CONFLICT DO NOTHING
                                """, batch_values)
                                conn.commit()
                            pairs_inserted += len(batch_values)
                            batch_values = []

        # Insert remaining
        if batch_values:
            with Database.get_connection() as conn:
                execute_values(conn.cur, """
                    INSERT INTO intermediate.candidate_pairs
                    (record_a_id, record_b_id, block_type)
                    VALUES %s ON CONFLICT DO NOTHING
                """, batch_values)
                conn.commit()
            pairs_inserted += len(batch_values)

        print(f"  Generated {pairs_inserted:,} unique candidate pairs")
        return pairs_inserted

    def score_candidates(self) -> Dict[str, int]:
        """Step 4: Score candidate pairs"""
        print(f"\n{'='*60}")
        print(f"STEP 4: Scoring Candidate Pairs")
        print(f"{'='*60}")

        # Get unscored pairs
        pairs = Database.execute("""
            SELECT cp.*, a.canonical_email as a_email, a.first_name as a_first,
                   a.last_name as a_last, a.canonical_phone as a_phone,
                   a.canonical_company as a_company, a.normalized_region as a_region,
                   a.source_system as a_source,
                   b.canonical_email as b_email, b.first_name as b_first,
                   b.last_name as b_last, b.canonical_phone as b_phone,
                   b.canonical_company as b_company, b.normalized_region as b_region,
                   b.source_system as b_source
            FROM intermediate.candidate_pairs cp
            JOIN staging.standardized_records a ON cp.record_a_id = a.id
            JOIN staging.standardized_records b ON cp.record_b_id = b.id
            WHERE NOT EXISTS (
                SELECT 1 FROM marts.match_results mr
                WHERE mr.record_a_id = cp.record_a_id
                AND mr.record_b_id = cp.record_b_id
            )
            LIMIT 50000  -- Process in batches for demo
        """)

        if not pairs:
            print("  No new pairs to score")
            # Return existing counts
            counts = Database.execute("""
                SELECT match_status, COUNT(*) as cnt FROM marts.match_results GROUP BY match_status
            """)
            return {r['match_status']: r['cnt'] for r in counts}

        print(f"  Scoring {len(pairs)} candidate pairs...")

        # Score pairs
        scored = []
        for i, pair in enumerate(pairs):
            result = self.scorer.score_pair(
                {
                    'id': pair['record_a_id'],
                    'email': pair['a_email'],
                    'first_name': pair['a_first'],
                    'last_name': pair['a_last'],
                    'phone': pair['a_phone'],
                    'company_name': pair['a_company'],
                    'region': pair['a_region'],
                    'source_system': pair['a_source'],
                },
                {
                    'id': pair['record_b_id'],
                    'email': pair['b_email'],
                    'first_name': pair['b_first'],
                    'last_name': pair['b_last'],
                    'phone': pair['b_phone'],
                    'company_name': pair['b_company'],
                    'region': pair['b_region'],
                    'source_system': pair['b_source'],
                }
            )
            result['block_type'] = pair['block_type']
            scored.append(result)

            if (i + 1) % 10000 == 0:
                print(f"  Scored {i + 1} pairs...")

        # Insert results
        if scored:
            from psycopg2.extras import execute_values
            values = [
                (r['record_a_id'], r['record_b_id'], r['email_exact'],
                 r['email_domain'], r['name_jaro_winkler'], r['phone_exact'],
                 r['company_token_jaccard'], r['confidence_score'],
                 r['match_status'], r['match_tier'], r['block_type'])
                for r in scored
            ]

            with Database.get_connection() as conn:
                execute_values(conn.cur, """
                    INSERT INTO marts.match_results
                    (record_a_id, record_b_id, email_exact, email_domain,
                     name_jaro_winkler, phone_exact, company_token_jaccard,
                     confidence_score, match_status, match_tier, block_type)
                    VALUES %s ON CONFLICT DO NOTHING
                """, values)
                conn.commit()

        # Count results
        counts = Database.execute("""
            SELECT match_status, COUNT(*) as cnt FROM marts.match_results GROUP BY match_status
        """)
        status_counts = {r['match_status']: r['cnt'] for r in counts}

        print(f"  Scoring complete:")
        for status, cnt in status_counts.items():
            print(f"    {status}: {cnt:,}")

        return status_counts

    def create_golden_records(self) -> int:
        """Step 5: Create golden records from auto-merge matches"""
        print(f"\n{'='*60}")
        print(f"STEP 5: Creating Golden Records")
        print(f"{'='*60}")

        # Get auto-merge matches not yet processed
        matches = Database.execute("""
            SELECT mr.*,
                   a.*, a.id as a_id,
                   b.*, b.id as b_id
            FROM marts.match_results mr
            JOIN staging.standardized_records a ON mr.record_a_id = a.id
            JOIN staging.standardized_records b ON mr.record_b_id = b.id
            WHERE mr.match_status = 'auto_merge'
            AND mr.merged_at IS NULL
            LIMIT 10000
        """)

        if not matches:
            print("  No new auto-merge matches to process")
            result = Database.execute("SELECT COUNT(*) as cnt FROM marts.golden_records WHERE is_current = TRUE")
            return result[0]['cnt'] if result else 0

        print(f"  Processing {len(matches)} auto-merge matches...")

        golden_records_created = 0

        for match in matches:
            # Build record dicts
            record_a = {k.replace('a_', ''): v for k, v in match.items() if k.startswith('a_')}
            record_b = {k.replace('b_', ''): v for k, v in match.items() if k.startswith('b_')}

            # Add full data back
            for key in ['source_record_id', 'source_system', 'first_name', 'last_name',
                       'title', 'company_name', 'email', 'phone', 'region',
                       'canonical_email', 'canonical_phone', 'canonical_name',
                       'canonical_company', 'normalized_region',
                       'created_at', 'updated_at']:
                record_a[key] = match.get(key) or match.get(f'a_{key}', '')
                record_b[key] = match.get(f'b_{key}', '')

            # Create golden record
            golden = self.survivorship.merge_records([record_a, record_b], match)

            if golden:
                golden_id = f"GR-{uuid.uuid4().hex[:8].upper()}"

                # Insert golden record
                Database.execute("""
                    INSERT INTO marts.golden_records
                    (golden_record_id, source_record_ids, canonical_email, canonical_phone,
                     canonical_first_name, canonical_last_name, canonical_company,
                     canonical_title, canonical_region, survivorship_metadata, lineage_graph,
                     valid_from, is_current, version)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), TRUE, 1)
                """, (
                    golden_id, golden['source_record_ids'], golden['canonical_email'],
                    golden['canonical_phone'], golden['canonical_first_name'],
                    golden['canonical_last_name'], golden['canonical_company'],
                    golden['canonical_title'], golden['canonical_region'],
                    golden['survivorship_metadata'], golden['lineage_graph']
                ))

                # Update match result
                Database.execute("""
                    UPDATE marts.match_results
                    SET merged_at = NOW(),
                        merge_decision = %s
                    WHERE id = %s
                """, (json.dumps({'golden_record_id': golden_id}), match['id']))

                # Log survivorship decisions
                decisions = json.loads(golden['survivorship_metadata'])
                for attr, decision in decisions.items():
                    Database.execute("""
                        INSERT INTO marts.survivorship_log
                        (golden_record_id, attribute, selected_source, selected_value,
                         rule_applied, rule_rationale, rejected_sources)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        golden_id, attr,
                        decision.get('selected_source', ''),
                        str(decision)[:255],
                        decision.get('rule', ''),
                        decision.get('rationale', ''),
                        json.dumps(decision.get('rejected_sources', []))
                    ))

                # Log lineage event
                Database.execute("""
                    INSERT INTO audit.lineage_events
                    (event_id, golden_record_id, event_type, source_record_ids,
                     event_details, confidence_at_merge)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    f"EVT-{uuid.uuid4().hex[:8]}",
                    golden_id,
                    'merge',
                    golden['source_record_ids'],
                    json.dumps({'match_id': match['id'], 'confidence': match['confidence_score']}),
                    match['confidence_score']
                ))

                golden_records_created += 1

        print(f"  Created {golden_records_created} golden records")
        return golden_records_created

    def run_quality_checks(self) -> Dict[str, Any]:
        """Step 6: Run data quality checks"""
        print(f"\n{'='*60}")
        print(f"STEP 6: Quality Checks")
        print(f"{'='*60}")

        # Completeness check
        completeness = Database.execute("""
            SELECT
                source_system,
                COUNT(*) as total,
                SUM(CASE WHEN canonical_email IS NOT NULL AND canonical_email != '' THEN 1 ELSE 0 END) as has_email,
                SUM(CASE WHEN canonical_phone IS NOT NULL AND canonical_phone != '' THEN 1 ELSE 0 END) as has_phone,
                SUM(CASE WHEN canonical_name IS NOT NULL AND canonical_name != '' THEN 1 ELSE 0 END) as has_name
            FROM staging.standardized_records
            GROUP BY source_system
        """)

        # Duplicate rate
        dup_rate = Database.execute("""
            SELECT
                COUNT(*) as total_records,
                COUNT(DISTINCT canonical_email) as unique_emails
            FROM staging.standardized_records
        """)

        results = {
            'completeness_by_source': [dict(r) for r in completeness],
            'duplicate_rate': dict(dup_rate[0]) if dup_rate else {},
        }

        # Insert quality metrics
        for src in completeness:
            total = src['total'] or 1
            pct = round((src['has_email'] or 0) / total * 100, 2)
            Database.execute("""
                INSERT INTO audit.quality_metrics
                (run_id, source_system, snapshot_date, completeness_pct, duplicate_rate)
                VALUES (%s, %s, CURRENT_DATE, %s, %s)
            """, (self.run_id, src['source_system'], pct,
                  round((1 - (src['has_email'] or 0) / max(total, 1)) * 100, 2)))

        print(f"  Quality checks complete")
        for src in completeness:
            total = src['total'] or 1
            print(f"    {src['source_system']}: {src['has_email']}/{total} have email "
                  f"({round(src['has_email']/total*100, 1)}%)")

        return results

    def run_full_pipeline(self, source_system: str = 'all') -> Dict[str, Any]:
        """Run the complete pipeline"""
        start_time = time.time()

        print("\n" + "=" * 70)
        print("  GOLDENRECORD: Master Data Reconciliation Pipeline")
        print("=" * 70)

        run_id = self.start_run(source_system)

        try:
            # Step 1: Standardization
            if source_system in ('all', 'crm_primary'):
                self.standardize_raw_data('crm_primary')
            if source_system in ('all', 'crm_secondary'):
                self.standardize_raw_data('crm_secondary')
            if source_system in ('all', 'marketing_automation'):
                self.standardize_raw_data('marketing_automation')

            # Step 2: Blocking
            self.create_blocking_index()

            # Step 3: Candidate pairs
            pairs_count = self.generate_candidate_pairs()

            # Step 4: Scoring
            status_counts = self.score_candidates()

            # Step 5: Golden records
            golden_count = self.create_golden_records()

            # Step 6: Quality
            quality = self.run_quality_checks()

            # Finish
            duration_ms = int((time.time() - start_time) * 1000)
            records_in = sum(
                Database.execute("SELECT COUNT(*) as cnt FROM raw_crm.primary_leads")[0]['cnt'],
                Database.execute("SELECT COUNT(*) as cnt FROM raw_crm.secondary_leads")[0]['cnt'],
                Database.execute("SELECT COUNT(*) as cnt FROM raw_marketing.contacts")[0]['cnt'],
            )
            records_merged = status_counts.get('auto_merge', 0)
            records_flagged = status_counts.get('review', 0)

            avg_confidence = 0
            if records_merged > 0:
                result = Database.execute("""
                    SELECT AVG(confidence_score) as avg_conf FROM marts.match_results
                    WHERE match_status = 'auto_merge'
                """)
                avg_confidence = result[0]['avg_conf'] if result and result[0]['avg_conf'] else 0

            self.finish_run(records_in, records_merged, records_flagged,
                          avg_confidence, duration_ms, 'completed')

            return {
                'run_id': run_id,
                'status': 'completed',
                'duration_ms': duration_ms,
                'records_processed': records_in,
                'records_merged': records_merged,
                'records_flagged_review': records_flagged,
                'golden_records_created': golden_count,
                'avg_confidence': round(avg_confidence, 4),
                'match_status_distribution': status_counts,
                'quality_metrics': quality,
            }

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            self.finish_run(0, 0, 0, 0, duration_ms, f'failed: {str(e)}')
            raise


def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='GoldenRecord Pipeline')
    parser.add_argument('--source', default='all',
                       choices=['all', 'crm_primary', 'crm_secondary', 'marketing_automation'])
    parser.add_argument('--generate-data', action='store_true',
                       help='Generate synthetic data first')

    args = parser.parse_args()

    if args.generate_data:
        from pipeline.generate_synthetic_data import main as gen_main
        gen_main()

    orchestrator = PipelineOrchestrator()
    result = orchestrator.run_full_pipeline(args.source)

    print("\n" + "=" * 70)
    print("  PIPELINE COMPLETE")
    print("=" * 70)
    print(json.dumps(result, indent=2, default=str))


if __name__ == '__main__':
    main()
