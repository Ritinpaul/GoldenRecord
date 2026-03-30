{{
  config(
    materialized='table',
    indexes=[
      {'columns': ['block_key', 'block_type']},
      {'columns': ['standardized_record_id']}
    ]
  )
}}

SELECT
    id,
    standardized_record_id,
    block_key,
    block_type,
    created_at
FROM intermediate.blocking_index
