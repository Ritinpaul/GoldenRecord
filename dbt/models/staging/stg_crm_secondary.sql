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
    mobile as phone,
    org_name as company_name,
    region,
    first_name,
    last_name,
    job_title as title,
    created_at,
    updated_at,
    raw_data
FROM raw_crm.secondary_leads
