{{
  config(
    materialized='table',
    indexes=[
      {'columns': ['golden_record_id']},
      {'columns': ['is_current']}
    ]
  )
}}

SELECT
    id,
    golden_record_id,
    source_record_ids,
    canonical_email,
    canonical_phone,
    canonical_first_name,
    canonical_last_name,
    canonical_company,
    canonical_title,
    canonical_region,
    survivorship_metadata,
    lineage_graph,
    valid_from,
    valid_to,
    is_current,
    version,
    created_at
FROM marts.golden_records
WHERE is_current = TRUE
