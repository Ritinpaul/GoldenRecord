/**
 * PGlite TCP Server Wrapper
 * Exposes PGlite (WASM PostgreSQL) over TCP so Python/psycopg2 can connect
 */
import { PGlite } from '@electric-sql/pglite';
import { net } from 'net';
import { performance } from 'perf_hooks';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const DATA_DIR = join(__dirname, '.pgdata');
const PORT = 5432;
const HOST = '127.0.0.1';

console.log('[PGlite] Starting embedded PostgreSQL server...');
console.log(`[PGlite] Data directory: ${DATA_DIR}`);

const db = new PGlite(DATA_DIR, {
  debug: process.env.DEBUG === '1' ? 1 : 0,
});

await db.waitReady;
console.log('[PGlite] Database ready!');

// Execute schema initialization
const schemaSQL = `
-- Raw Layer: Source-agnostic staging schemas
CREATE SCHEMA IF NOT EXISTS raw_crm;
CREATE SCHEMA IF NOT EXISTS raw_marketing;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS intermediate;
CREATE SCHEMA IF NOT EXISTS marts;
CREATE SCHEMA IF NOT EXISTS audit;

-- Raw CRM Primary Leads
CREATE TABLE IF NOT EXISTS raw_crm.primary_leads (
    id SERIAL PRIMARY KEY,
    source_record_id VARCHAR(50) NOT NULL,
    source_system VARCHAR(50) DEFAULT 'crm_primary',
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    email VARCHAR(255),
    phone VARCHAR(50),
    company_name VARCHAR(255),
    lead_source VARCHAR(100),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    title VARCHAR(100),
    region VARCHAR(100),
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    raw_data JSONB,
    UNIQUE(source_record_id, source_system)
);

-- Raw CRM Secondary Leads
CREATE TABLE IF NOT EXISTS raw_crm.secondary_leads (
    id SERIAL PRIMARY KEY,
    source_record_id VARCHAR(50) NOT NULL,
    source_system VARCHAR(50) DEFAULT 'crm_secondary',
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    email VARCHAR(255),
    mobile VARCHAR(50),
    org_name VARCHAR(255),
    region VARCHAR(100),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    job_title VARCHAR(100),
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    raw_data JSONB,
    UNIQUE(source_record_id, source_system)
);

-- Raw Marketing Contacts
CREATE TABLE IF NOT EXISTS raw_marketing.contacts (
    id SERIAL PRIMARY KEY,
    source_record_id VARCHAR(50) NOT NULL,
    source_system VARCHAR(50) DEFAULT 'marketing_automation',
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    email VARCHAR(255),
    domain VARCHAR(255),
    job_title VARCHAR(100),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    company_name VARCHAR(255),
    region VARCHAR(100),
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    raw_data JSONB,
    UNIQUE(source_record_id, source_system)
);

-- Staging: Standardized entity records
CREATE TABLE IF NOT EXISTS staging.standardized_records (
    id SERIAL PRIMARY KEY,
    source_record_id VARCHAR(50) NOT NULL,
    source_system VARCHAR(50) NOT NULL,
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    canonical_email VARCHAR(255),
    canonical_phone VARCHAR(50),
    canonical_name JSONB,
    canonical_company VARCHAR(255),
    normalized_region VARCHAR(100),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    title VARCHAR(100),
    company_name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    region VARCHAR(100),
    lead_source VARCHAR(100),
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    standardization_metadata JSONB,
    UNIQUE(source_record_id, source_system)
);

-- Intermediate: Blocking index
CREATE TABLE IF NOT EXISTS intermediate.blocking_index (
    id SERIAL PRIMARY KEY,
    standardized_record_id INTEGER NOT NULL,
    block_key VARCHAR(255) NOT NULL,
    block_type VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_blocking_key ON intermediate.blocking_index(block_key, block_type);

-- Intermediate: Candidate pairs
CREATE TABLE IF NOT EXISTS intermediate.candidate_pairs (
    id SERIAL PRIMARY KEY,
    record_a_id INTEGER NOT NULL,
    record_b_id INTEGER NOT NULL,
    block_type VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(record_a_id, record_b_id)
);

-- Intermediate: Comparison features
CREATE TABLE IF NOT EXISTS intermediate.comparison_features (
    id SERIAL PRIMARY KEY,
    pair_id INTEGER NOT NULL,
    feature_name VARCHAR(100) NOT NULL,
    feature_value DECIMAL(10,8) NOT NULL,
    feature_weight DECIMAL(5,4) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Marts: Match results
CREATE TABLE IF NOT EXISTS marts.match_results (
    id SERIAL PRIMARY KEY,
    record_a_id INTEGER NOT NULL,
    record_b_id INTEGER NOT NULL,
    email_exact DECIMAL(3,2),
    email_domain DECIMAL(3,2),
    name_jaro_winkler DECIMAL(10,8),
    phone_exact DECIMAL(3,2),
    company_token_jaccard DECIMAL(10,8),
    confidence_score DECIMAL(10,8) NOT NULL,
    match_status VARCHAR(50) NOT NULL, -- 'auto_merge', 'review', 'distinct'
    match_tier VARCHAR(20) NOT NULL, -- 'tier_a', 'tier_b'
    merged_at TIMESTAMP,
    merge_decision JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_match_status ON marts.match_results(match_status);
CREATE INDEX IF NOT EXISTS idx_confidence ON marts.match_results(confidence_score);

-- Marts: Golden Records (SCD Type 2)
CREATE TABLE IF NOT EXISTS marts.golden_records (
    id SERIAL PRIMARY KEY,
    golden_record_id VARCHAR(50) NOT NULL,
    source_record_ids JSONB NOT NULL,
    canonical_email VARCHAR(255),
    canonical_phone VARCHAR(50),
    canonical_first_name VARCHAR(100),
    canonical_last_name VARCHAR(100),
    canonical_company VARCHAR(255),
    canonical_title VARCHAR(100),
    canonical_region VARCHAR(100),
    survivorship_metadata JSONB,
    lineage_graph JSONB,
    valid_from TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    valid_to TIMESTAMP,
    is_current BOOLEAN NOT NULL DEFAULT TRUE,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_golden_id ON marts.golden_records(golden_record_id);
CREATE INDEX IF NOT EXISTS idx_golden_current ON marts.golden_records(is_current) WHERE is_current = TRUE;

-- Marts: Survivorship Log
CREATE TABLE IF NOT EXISTS marts.survivorship_log (
    id SERIAL PRIMARY KEY,
    golden_record_id VARCHAR(50) NOT NULL,
    attribute VARCHAR(100) NOT NULL,
    selected_source VARCHAR(50) NOT NULL,
    selected_value TEXT,
    rule_applied VARCHAR(100) NOT NULL,
    rule_rationale VARCHAR(255),
    rejected_sources JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Audit: Reconciliation Log
CREATE TABLE IF NOT EXISTS audit.reconciliation_log (
    id SERIAL PRIMARY KEY,
    run_id VARCHAR(50) NOT NULL,
    source_system VARCHAR(50) NOT NULL,
    records_in INTEGER NOT NULL,
    records_merged INTEGER NOT NULL DEFAULT 0,
    records_flagged_review INTEGER NOT NULL DEFAULT 0,
    avg_confidence DECIMAL(10,8),
    run_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    run_duration_ms INTEGER,
    status VARCHAR(50) NOT NULL DEFAULT 'running'
);
CREATE INDEX IF NOT EXISTS idx_recon_run_date ON audit.reconciliation_log(run_timestamp);

-- Audit: Quality Metrics
CREATE TABLE IF NOT EXISTS audit.quality_metrics (
    id SERIAL PRIMARY KEY,
    run_id VARCHAR(50),
    source_system VARCHAR(50),
    snapshot_date DATE NOT NULL,
    completeness_pct DECIMAL(5,2),
    consistency_violations INTEGER,
    duplicate_rate DECIMAL(5,2),
    freshness_hours INTEGER,
    schema_drift_detected BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_quality_date ON audit.quality_metrics(snapshot_date);

-- Audit: Lineage Events
CREATE TABLE IF NOT EXISTS audit.lineage_events (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(50) NOT NULL,
    golden_record_id VARCHAR(50) NOT NULL,
    event_type VARCHAR(50) NOT NULL, -- 'merge', 'split', 'update', 'manual_override'
    source_record_ids JSONB NOT NULL,
    event_details JSONB,
    confidence_at_merge DECIMAL(10,8),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_lineage_gr ON audit.lineage_events(golden_record_id);
`;

await db.exec(schemaSQL);
console.log('[PGlite] Schema initialized successfully!');

// Simple TCP server that proxies to PGlite
const server = net.createServer(async (socket) => {
  console.log(`[PGlite] Client connected from ${socket.remoteAddress}:${socket.remotePort}`);

  socket.on('data', async (data) => {
    try {
      const query = data.toString().trim();
      if (!query) {
        socket.write(JSON.stringify({ status: 'ok', rows: [] }) + '\n');
        return;
      }

      // Handle pgwire protocol or simple JSON queries
      if (query.startsWith('{')) {
        // JSON protocol for our Python client
        const req = JSON.parse(query);
        const result = await db.query(req.sql, req.params || []);
        socket.write(JSON.stringify({ status: 'ok', rows: result.rows || [], fields: result.fields || [] }) + '\n');
      } else {
        // Simple text protocol
        try {
          const result = await db.query(query);
          socket.write(JSON.stringify({ status: 'ok', rows: result.rows || [], fields: result.fields || [] }) + '\n');
        } catch (e) {
          socket.write(JSON.stringify({ status: 'error', message: e.message }) + '\n');
        }
      }
    } catch (err) {
      socket.write(JSON.stringify({ status: 'error', message: err.message }) + '\n');
    }
  });

  socket.on('error', (err) => {
    console.error(`[PGlite] Socket error: ${err.message}`);
  });

  socket.on('close', () => {
    console.log('[PGlite] Client disconnected');
  });
});

server.listen(PORT, HOST, () => {
  console.log(`[PGlite] Server listening on ${HOST}:${PORT}`);
  console.log(`[PGlite] Python can now connect via: psycopg2.connect(host='127.0.0.1', port=5432, dbname='postgres')`);
});

// Graceful shutdown
process.on('SIGINT', async () => {
  console.log('\n[PGlite] Shutting down...');
  server.close();
  await db.close();
  process.exit(0);
});

process.on('SIGTERM', async () => {
  console.log('\n[PGlite] Shutting down...');
  server.close();
  await db.close();
  process.exit(0);
});
