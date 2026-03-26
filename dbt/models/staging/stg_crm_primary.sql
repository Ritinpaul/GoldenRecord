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
    phone,
    company_name,
    lead_source,
    first_name,
    last_name,
    title,
    region,
    created_at,
    updated_at,
    raw_data
FROM raw_crm.primary_leads
