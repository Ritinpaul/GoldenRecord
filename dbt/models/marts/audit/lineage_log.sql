{{
  config(
    materialized='table',
    indexes=[
      {'columns': ['golden_record_id']},
      {'columns': ['event_type']}
    ]
  )
}}

SELECT
    id,
    event_id,
    golden_record_id,
    event_type,
    source_record_ids,
    event_details,
    confidence_at_merge,
    created_at
FROM audit.lineage_events
ORDER BY created_at DESC
