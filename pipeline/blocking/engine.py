"""
GoldenRecord Blocking Engine
Multi-index blocking to reduce O(n²) comparisons to manageable candidate pairs
"""
from typing import List, Dict, Any, Set, Tuple
from collections import defaultdict
import json


class BlockingEngine:
    """
    Multi-index blocking strategy:
    - Block 1: Exact email match
    - Block 2: Phone last 3 digits + region
    - Block 3: Company token overlap + region
    """

    def __init__(self):
        self.block_stats = {}

    def create_blocking_keys(self, record: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate all blocking keys for a record"""
        blocks = []
        record_id = record.get('id')

        # Block 1: Exact email match
        email = record.get('canonical_email', '') or record.get('email', '')
        if email:
            blocks.append({
                'record_id': record_id,
                'block_key': email.lower().strip(),
                'block_type': 'email_exact'
            })

        # Block 2: Phone last 3 digits + region
        phone = record.get('canonical_phone', '') or record.get('phone', '')
        region = record.get('normalized_region', '') or record.get('region', '')
        if phone and len(phone) >= 3:
            last_digits = phone[-3:]
            region_clean = region.lower().strip() if region else ''
            blocks.append({
                'record_id': record_id,
                'block_key': f"{last_digits}:{region_clean}",
                'block_type': 'phone_region'
            })

        # Block 3: Company name token + region
        company = record.get('canonical_company', '') or record.get('company_name', '')
        if company:
            # Use first 2 significant tokens
            tokens = [t.strip().lower() for t in company.split()
                     if len(t.strip()) > 2]
            if tokens:
                # Use the first token as blocking key
                primary_token = tokens[0]
                region_clean = region.lower().strip() if region else ''
                blocks.append({
                    'record_id': record_id,
                    'block_key': f"{primary_token}:{region_clean}",
                    'block_type': 'company_region'
                })

        return blocks

    def generate_candidate_pairs(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate candidate pairs by blocking.
        Returns pairs that share at least one block key.
        """
        print(f"Blocking {len(records)} records...")

        # Index blocks
        block_index = defaultdict(list)  # block_key -> list of record_ids
        record_blocks = defaultdict(list)  # record_id -> list of block_types

        for record in records:
            blocks = self.create_blocking_keys(record)
            for block in blocks:
                block_index[(block['block_key'], block['block_type'])].append(block['record_id'])
                record_blocks[block['record_id']].append(block['block_type'])

        # Generate pairs from blocks
        pairs_seen = set()
        candidate_pairs = []
        block_stats = defaultdict(int)

        for (block_key, block_type), record_ids in block_index.items():
            block_stats[f'{block_type}_blocks'] += 1

            # Skip blocks that are too large (too many candidates)
            if len(record_ids) > 1000:
                print(f"  Skipping oversized block: {block_key} ({len(record_ids)} records)")
                continue

            # Generate all pairs within this block
            for i in range(len(record_ids)):
                for j in range(i + 1, len(record_ids)):
                    a, b = record_ids[i], record_ids[j]

                    # Ensure consistent ordering
                    if a > b:
                        a, b = b, a

                    pair_key = (a, b)
                    if pair_key not in pairs_seen:
                        pairs_seen.add(pair_key)
                        candidate_pairs.append({
                            'record_a_id': a,
                            'record_b_id': b,
                            'block_type': block_type,
                            'block_key': block_key
                        })

            block_stats[f'{block_type}_pairs'] += len(record_ids) * (len(record_ids) - 1) // 2

        self.block_stats = dict(block_stats)

        print(f"  Blocking complete:")
        for key, value in block_stats.items():
            print(f"    {key}: {value:,}")
        print(f"  Total candidate pairs: {len(candidate_pairs):,}")

        return candidate_pairs

    def get_stats(self) -> Dict[str, Any]:
        """Get blocking statistics"""
        return self.block_stats
