{{
  config(
    materialized='table',
    indexes=[
      {'columns': ['snapshot_date']},
      {'columns': ['source_system']}
    ]
  )
}}

SELECT
    id,
    run_id,
    source_system,
    snapshot_date,
    completeness_pct,
    consistency_violations,
    duplicate_rate,
    freshness_hours,
    schema_drift_detected,
    created_at
FROM audit.quality_metrics
ORDER BY snapshot_date DESC, source_system
