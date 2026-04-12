"""
GoldenRecord FastAPI Backend
API layer for entity resolution operations
"""
import os
import sys
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Add parent to path
sys.path.insert(0, str(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database.db_client import Database
from pipeline.standardization.engine import StandardizationEngine
from pipeline.scoring.engine import ConfidenceScorer, ComparisonFeatures
from pipeline.orchestrator import PipelineOrchestrator


# Request/Response models
class ResolveRequest(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company_name: Optional[str] = None
    region: Optional[str] = None
    source_system: str = "api"


class MatchResult(BaseModel):
    golden_record_id: Optional[str] = None
    confidence: float
    status: str
    matched_fields: Dict[str, Any]


class HealthResponse(BaseModel):
    status: str
    database: str
    records: Dict[str, int]
    last_run: Optional[Dict[str, Any]] = None


class GoldenRecordResponse(BaseModel):
    golden_record_id: str
    source_records: List[str]
    canonical_data: Dict[str, Any]
    survivorship_decisions: Dict[str, Any]
    versions: List[Dict[str, Any]]


# Initialize engines
standardizer = StandardizationEngine()
scorer = ConfidenceScorer()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    try:
        result = Database.execute("SELECT 1 as test")
        print(f"[API] Database connected: {result}")
    except Exception as e:
        print(f"[API] Database connection warning: {e}")
    yield
    # Shutdown
    print("[API] Shutting down...")


app = FastAPI(
    title="GoldenRecord API",
    description="Confidence-scored entity resolution engine with full audit lineage",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "name": "GoldenRecord API",
        "version": "1.0.0",
        "endpoints": [
            "/health",
            "/resolve",
            "/golden-record/{id}/lineage",
            "/stats",
            "/pipeline/run",
            "/pipeline/status",
        ]
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Data quality snapshot"""
    try:
        stats = Database.get_stats()

        # Get last run
        last_run = Database.execute("""
            SELECT * FROM audit.reconciliation_log
            ORDER BY run_timestamp DESC LIMIT 1
        """)

        return HealthResponse(
            status="healthy",
            database="connected",
            records={
                "raw_crm_primary": stats.get('raw_crm.primary_leads', 0),
                "raw_crm_secondary": stats.get('raw_crm.secondary_leads', 0),
                "raw_marketing": stats.get('raw_marketing.contacts', 0),
                "standardized": Database.execute(
                    "SELECT COUNT(*) as cnt FROM staging.standardized_records"
                )[0]['cnt'] if True else 0,
                "golden_records": stats.get('golden_records', 0),
                "match_results": stats.get('match_results', 0),
            },
            last_run=dict(last_run[0]) if last_run else None
        )
    except Exception as e:
        return HealthResponse(
            status="degraded",
            database=f"error: {str(e)}",
            records={},
        )


@app.post("/resolve")
async def resolve_record(request: ResolveRequest):
    """
    Submit a new record and get potential matches.
    Returns the best matching golden record with confidence score.
    """
    try:
        # Standardize the incoming record
        raw = {
            'email': request.email,
            'phone': request.phone,
            'first_name': request.first_name,
            'last_name': request.last_name,
            'company_name': request.company_name,
            'region': request.region,
        }

        standardized = standardizer.standardize_record(raw, request.source_system)

        # Search for matches in standardized records
        matches = []

        # Search by email
        if standardized.get('canonical_email'):
            email_matches = Database.execute("""
                SELECT s.*, gr.golden_record_id
                FROM staging.standardized_records s
                LEFT JOIN marts.golden_records gr ON
                    gr.source_record_ids::jsonb ? s.source_record_id
                WHERE s.canonical_email = %s
                LIMIT 10
            """, (standardized['canonical_email'],))
            matches.extend([dict(r) for r in email_matches])

        # Search by phone
        if standardized.get('canonical_phone') and len(matches) < 10:
            phone_digits = standardized['canonical_phone'][-7:] if len(standardized['canonical_phone']) > 7 else standardized['canonical_phone']
            phone_matches = Database.execute("""
                SELECT s.*, gr.golden_record_id
                FROM staging.standardized_records s
                LEFT JOIN marts.golden_records gr ON
                    gr.source_record_ids::jsonb ? s.source_record_id
                WHERE s.canonical_phone LIKE %s
                LIMIT %s
            """, (f'%{phone_digits}%', 10 - len(matches)))
            matches.extend([dict(r) for r in phone_matches])

        # Score each match
        scored_matches = []
        seen_ids = set()

        for match in matches:
            if match['id'] in seen_ids:
                continue
            seen_ids.add(match['id'])

            score_result = scorer.score_pair(standardized, match)
            explanation = scorer.explain_decision(score_result)

            scored_matches.append({
                'record_id': match['id'],
                'source_system': match.get('source_system', ''),
                'source_record_id': match.get('source_record_id', ''),
                'golden_record_id': match.get('golden_record_id', ''),
                'confidence': round(score_result['confidence_score'], 4),
                'status': score_result['match_status'],
                'features': {
                    'email_exact': score_result['email_exact'],
                    'name_similarity': round(score_result['name_jaro_winkler'], 4),
                    'phone_exact': score_result['phone_exact'],
                    'company_similarity': round(score_result['company_token_jaccard'], 4),
                },
                'explanation': explanation,
                'matched_data': {
                    'email': match.get('canonical_email', ''),
                    'first_name': match.get('first_name', ''),
                    'last_name': match.get('last_name', ''),
                    'company': match.get('canonical_company', ''),
                    'phone': match.get('canonical_phone', ''),
                }
            })

        # Sort by confidence descending
        scored_matches.sort(key=lambda x: x['confidence'], reverse=True)

        # Get best match
        best_match = scored_matches[0] if scored_matches else None

        return {
            "input": {
                "email": request.email,
                "first_name": request.first_name,
                "last_name": request.last_name,
                "company": request.company_name,
            },
            "standardized": {
                "canonical_email": standardized.get('canonical_email'),
                "canonical_phone": standardized.get('canonical_phone'),
                "canonical_company": standardized.get('canonical_company'),
            },
            "best_match": best_match,
            "all_matches": scored_matches[:5],
            "total_matches_found": len(scored_matches),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/golden-record/{golden_id}/lineage")
async def get_lineage(golden_id: str):
    """
    Get full provenance tree for a golden record.
    Returns the complete lineage graph with all merge events.
    """
    try:
        # Get golden record
        golden = Database.execute("""
            SELECT * FROM marts.golden_records
            WHERE golden_record_id = %s
            ORDER BY version DESC
        """, (golden_id,))

        if not golden:
            raise HTTPException(status_code=404, detail=f"Golden record {golden_id} not found")

        current = dict(golden[0])

        # Get all versions
        versions = []
        for g in golden:
            versions.append({
                'version': g['version'],
                'valid_from': g['valid_from'],
                'valid_to': g['valid_to'],
                'is_current': g['is_current'],
                'canonical_email': g['canonical_email'],
                'canonical_company': g['canonical_company'],
            })

        # Get lineage events
        events = Database.execute("""
            SELECT * FROM audit.lineage_events
            WHERE golden_record_id = %s
            ORDER BY created_at DESC
        """, (golden_id,))

        # Get survivorship log
        survivorship = Database.execute("""
            SELECT * FROM marts.survivorship_log
            WHERE golden_record_id = %s
            ORDER BY created_at DESC
        """, (golden_id,))

        # Parse lineage graph
        lineage_graph = {}
        try:
            if current.get('lineage_graph'):
                lg = current['lineage_graph']
                lineage_graph = json.loads(lg) if isinstance(lg, str) else lg
        except:
            lineage_graph = {"parse_error": True}

        # Parse survivorship metadata
        survivorship_meta = {}
        try:
            if current.get('survivorship_metadata'):
                sm = current['survivorship_metadata']
                survivorship_meta = json.loads(sm) if isinstance(sm, str) else sm
        except:
            survivorship_meta = {"parse_error": True}

        # Build response
        response = {
            "golden_record_id": golden_id,
            "is_current": current.get('is_current', True),
            "valid_from": current.get('valid_from'),
            "version": current.get('version', 1),

            "canonical_data": {
                "email": current.get('canonical_email'),
                "phone": current.get('canonical_phone'),
                "first_name": current.get('canonical_first_name'),
                "last_name": current.get('canonical_last_name'),
                "company": current.get('canonical_company'),
                "title": current.get('canonical_title'),
                "region": current.get('canonical_region'),
            },

            "provenance": {
                "source_record_ids": json.loads(current['source_record_ids'])
                    if isinstance(current.get('source_record_ids'), str)
                    else current.get('source_record_ids', []),
                "survivorship_decisions": survivorship_meta,
            },

            "lineage_graph": lineage_graph,

            "history": {
                "versions": versions,
                "events": [dict(e) for e in events],
                "survivorship_log": [dict(s) for s in survivorship],
            },

            "audit_trail": {
                "created_at": current.get('created_at'),
                "version_count": len(versions),
                "event_count": len(events),
                "survivorship_decision_count": len(survivorship),
            }
        }

        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
async def get_stats():
    """Get comprehensive system statistics"""
    try:
        stats = Database.get_stats()

        # Match confidence distribution
        confidence_dist = Database.execute("""
            SELECT
                CASE
                    WHEN confidence_score >= 0.85 THEN 'high (>=0.85)'
                    WHEN confidence_score >= 0.60 THEN 'medium (0.60-0.85)'
                    ELSE 'low (<0.60)'
                END as confidence_band,
                COUNT(*) as count,
                AVG(confidence_score) as avg_confidence
            FROM marts.match_results
            GROUP BY 1
            ORDER BY 1
        """)

        # Top duplicate clusters
        top_clusters = Database.execute("""
            SELECT
                golden_record_id,
                COUNT(*) as source_count,
                AVG(match_confidence) as avg_confidence
            FROM (
                SELECT gr.golden_record_id, mr.confidence_score as match_confidence
                FROM marts.golden_records gr
                JOIN marts.match_results mr ON
                    (gr.source_record_ids::jsonb ? (
                        SELECT source_record_id FROM staging.standardized_records
                        WHERE id = mr.record_a_id
                    ) OR gr.source_record_ids::jsonb ? (
                        SELECT source_record_id FROM staging.standardized_records
                        WHERE id = mr.record_b_id
                    ))
                WHERE gr.is_current = TRUE
            ) sub
            GROUP BY golden_record_id
            HAVING COUNT(*) > 1
            ORDER BY source_count DESC
            LIMIT 10
        """)

        # Recent reconciliation runs
        recent_runs = Database.execute("""
            SELECT * FROM audit.reconciliation_log
            ORDER BY run_timestamp DESC
            LIMIT 5
        """)

        # Quality trends
        quality_trends = Database.execute("""
            SELECT
                snapshot_date,
                source_system,
                completeness_pct,
                duplicate_rate
            FROM audit.quality_metrics
            ORDER BY snapshot_date DESC
            LIMIT 20
        """)

        return {
            "record_counts": stats,
            "match_status_distribution": stats.get('match_status_dist', {}),
            "confidence_distribution": [dict(r) for r in confidence_dist],
            "top_duplicate_clusters": [dict(r) for r in top_clusters],
            "recent_runs": [dict(r) for r in recent_runs],
            "quality_trends": [dict(r) for r in quality_trends],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/pipeline/run")
async def run_pipeline(source: str = Query(default="all")):
    """Trigger a full pipeline run"""
    try:
        orchestrator = PipelineOrchestrator()
        result = orchestrator.run_full_pipeline(source)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/pipeline/status")
async def pipeline_status():
    """Get current pipeline status"""
    try:
        runs = Database.execute("""
            SELECT * FROM audit.reconciliation_log
            ORDER BY run_timestamp DESC
            LIMIT 10
        """)

        return {
            "recent_runs": [dict(r) for r in runs],
            "pipeline_ready": True,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/golden-records")
async def list_golden_records(
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0),
    search: Optional[str] = None,
):
    """List golden records with optional search"""
    try:
        if search:
            records = Database.execute("""
                SELECT * FROM marts.golden_records
                WHERE is_current = TRUE
                AND (canonical_first_name ILIKE %s
                     OR canonical_last_name ILIKE %s
                     OR canonical_email ILIKE %s
                     OR canonical_company ILIKE %s
                     OR golden_record_id ILIKE %s)
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """, (f'%{search}%', f'%{search}%', f'%{search}%',
                  f'%{search}%', f'%{search}%', limit, offset))
        else:
            records = Database.execute("""
                SELECT * FROM marts.golden_records
                WHERE is_current = TRUE
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """, (limit, offset))

        return {
            "records": [dict(r) for r in records],
            "count": len(records),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/matches")
async def list_matches(
    status: Optional[str] = None,
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0),
):
    """List match results with optional status filter"""
    try:
        if status:
            matches = Database.execute("""
                SELECT mr.*,
                       a.canonical_email as a_email,
                       b.canonical_email as b_email
                FROM marts.match_results mr
                JOIN staging.standardized_records a ON mr.record_a_id = a.id
                JOIN staging.standardized_records b ON mr.record_b_id = b.id
                WHERE mr.match_status = %s
                ORDER BY mr.confidence_score DESC
                LIMIT %s OFFSET %s
            """, (status, limit, offset))
        else:
            matches = Database.execute("""
                SELECT mr.*,
                       a.canonical_email as a_email,
                       b.canonical_email as b_email
                FROM marts.match_results mr
                JOIN staging.standardized_records a ON mr.record_a_id = a.id
                JOIN staging.standardized_records b ON mr.record_b_id = b.id
                ORDER BY mr.confidence_score DESC
                LIMIT %s OFFSET %s
            """, (limit, offset))

        return {
            "matches": [dict(m) for m in matches],
            "count": len(matches),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
