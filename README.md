# GoldenRecord: Master Data Reconciliation Platform

**Confidence-scored entity resolution engine with full audit lineage.**

Replaces brittle deterministic matching with probabilistic confidence thresholds, applies survivorship rules to merge duplicates, and exposes operational health through dbt-native observability.

**Core value proposition: deduplicate without destroying provenance.**

---

## Quick Start

### Prerequisites
- Node.js 18+ (for frontend)
- Python 3.12+ (for backend pipeline)
- PostgreSQL client libraries (`libpq-dev` - pre-installed on most systems)

### Install Dependencies

```bash
# Frontend dependencies (already installed)
npm install

# Python dependencies
pip3 install --user psycopg2-binary sqlalchemy pandas numpy fuzzywuzzy \
    python-Levenshtein fastapi uvicorn pydantic jaro-winkler
```

### Option 1: Unified Startup (Recommended)

```bash
node start.mjs
```

This starts all services in order:
1. PGlite (embedded PostgreSQL on port 5432)
2. Generates 120K synthetic records
3. Runs entity resolution pipeline
4. FastAPI backend (port 8000)
5. React frontend (port 3000)

Access the dashboard at: http://localhost:3000

### Option 2: Manual Start

```bash
# Terminal 1: Start database
node database/pglite-server.mjs

# Terminal 2: Generate data
python3 pipeline/generate_synthetic_data.py

# Terminal 3: Run pipeline
python3 pipeline/orchestrator.py

# Terminal 4: Start API
python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 5: Start frontend
npm run dev
```

---

## Architecture

```
Source Systems (120K records, 18% duplicates)
    |-- CRM Primary (~80K)
    |-- CRM Secondary (~25K)
    |-- Marketing Automation (~15K)
           |
           v
   [Python Ingestion Pipeline]
           |
           v
   [Standardization Engine] -- Name, Email, Phone, Company normalization
           |
           v
   [Multi-Index Blocking] -- Email exact, Phone+Region, Company+Region
           |
           v
   [Confidence Scoring] -- Tier A: Weighted sum, Tier B: ML (TODO)
           |-- >= 0.85: Auto-merge
           |-- 0.60-0.85: Review queue
           |-- < 0.60: Distinct
           |
           v
   [Survivorship Engine] -- Recency, Priority, Longest, Minimum rules
           |
           v
   [Golden Records] -- SCD Type 2 with full lineage
           |
           v
   [FastAPI + React Dashboard] -- Operational visibility
```

---

## Project Structure

```
.
|-- database/              # PGlite server + DB client
|-- pipeline/              # Data pipeline modules
|   |-- generate_synthetic_data.py
|   |-- orchestrator.py
|   |-- standardization/
|   |   |-- engine.py
|   |-- blocking/
|   |   |-- engine.py
|   |-- scoring/
|   |   |-- engine.py
|   |-- survivorship/
|   |   |-- engine.py
|-- api/                   # FastAPI backend
|   |-- main.py
|-- dbt/                   # dbt models (SQL specs)
|   |-- models/
|   |   |-- staging/
|   |   |-- intermediate/
|   |   |-- marts/
|-- src/                   # React frontend
|   |-- pages/
|   |   |-- Dashboard.tsx
|   |-- components/
|   |   |-- dashboard/
|   |-- hooks/
|   |   |-- useApi.ts
|   |-- types/
|   |   |-- index.ts
|-- TODO.md                # Deferred tasks (ML, dbt, etc.)
|-- start.mjs              # Unified startup script
```

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Database connection & system status |
| `/resolve` | POST | Submit record, get potential matches |
| `/golden-record/{id}/lineage` | GET | Full provenance tree |
| `/stats` | GET | Comprehensive statistics |
| `/golden-records` | GET | List golden records |
| `/matches` | GET | List match results |
| `/pipeline/run` | POST | Trigger pipeline run |
| `/pipeline/status` | GET | Pipeline status |

---

## Confidence Scoring

### Tier A: Weighted Sum (Fast Path)

| Feature | Weight | Description |
|---------|--------|-------------|
| `email_exact` | 0.35 | Exact email match |
| `phone_exact` | 0.25 | Phone number match |
| `name_jaro_winkler` | 0.20 | Name similarity |
| `email_domain` | 0.10 | Same email domain |
| `company_token_jaccard` | 0.10 | Company name overlap |

### Decision Thresholds

- **Auto-merge**: Confidence >= 0.85
- **Review queue**: Confidence 0.60-0.85
- **Distinct**: Confidence < 0.60

### Tier B: ML Classifier (Deferred)
See `TODO.md` for full implementation plan.

---

## Dashboard Features

- **Schema Health**: Real-time record counts per source system
- **Match Confidence**: Distribution charts with status breakdowns
- **Data Quality Trends**: Completeness and duplicate rate over time
- **Reconciliation Runs**: Pipeline execution history with run controls
- **Golden Records**: Searchable table with pagination
- **Match Results**: Filterable by status (auto_merge, review, distinct)
- **Entity Resolution**: Interactive form to test resolution
- **Lineage View**: Full provenance tree with audit trail

---


## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19 + TypeScript + Vite + Tailwind CSS + shadcn/ui + Recharts |
| Backend API | FastAPI (Python) |
| Database | PGlite (WASM PostgreSQL in Node.js) |
| Data Pipeline | Python 3.12 + Pandas + FuzzyWuzzy |
| dbt | SQL models defined (full implementation in TODO) |
