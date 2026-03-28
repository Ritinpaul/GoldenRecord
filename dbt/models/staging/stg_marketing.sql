{{
  config(
    materialized='view',
    unique_key=['source_record_id', 'source_system']
  )
}}

SELECT
    id,
    source_record_id,
    source_system,
    loaded_at,
    email,
    domain,
    job_title as title,
    first_name,
    last_name,
    company_name,
    region,
    created_at,
    updated_at,
    raw_data
FROM raw_marketing.contacts
