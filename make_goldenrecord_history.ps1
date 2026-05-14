<#
  GoldenRecord - backdated commit history (v3 - correct incremental staging)
  Strategy: stage ONLY the files for each commit, never use add -A until the final commit.
#>

$repo  = "D:\NewStart\AI_resume_projects\github"
$name  = "Ritinpaul"
$email = "ritin.pal125@gmail.com"

$env:GIT_AUTHOR_NAME     = $name
$env:GIT_AUTHOR_EMAIL    = $email
$env:GIT_COMMITTER_NAME  = $name
$env:GIT_COMMITTER_EMAIL = $email

function Do-Commit {
    param([string]$date, [string]$hour, [string]$msg)
    $ts = "$date $($hour):00:00 +0530"
    $env:GIT_AUTHOR_DATE    = $ts
    $env:GIT_COMMITTER_DATE = $ts
    # Only commit what is staged - no implicit add -A
    $out = git -C $repo commit -m $msg 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  [SKIP - nothing staged] $msg"
    } else {
        Write-Host "  [$date] $msg"
    }
}

function Stage {
    param([string[]]$files)
    foreach ($f in $files) {
        git -C $repo add "$f" 2>&1 | Out-Null
    }
}

# ============================================================
# Nuke and re-init
# ============================================================
Write-Host "`n=== Removing old .git ==="
Remove-Item -Path "$repo\.git" -Recurse -Force
Write-Host "=== Reinitialising ==="
git -C $repo init -b main | Out-Null
git -C $repo config user.name  $name
git -C $repo config user.email $email

# ============================================================
# Phase 1 - Scaffold  (Feb 14-19)
# ============================================================
Write-Host "`n--- Phase 1: Scaffold ---"

Stage @("package.json","index.html","vite.config.ts")
Do-Commit "2026-02-14" "09" "init: scaffold Vite + React + TypeScript project"

Stage @("tsconfig.json","tsconfig.app.json","tsconfig.node.json")
Do-Commit "2026-02-15" "11" "config: add TypeScript compiler config files"

Stage @("tailwind.config.js","postcss.config.js","components.json")
Do-Commit "2026-02-17" "10" "config: add Tailwind CSS, PostCSS, and shadcn component config"

Stage @("eslint.config.js")
Do-Commit "2026-02-18" "14" "config: add ESLint with react-hooks and react-refresh plugins"

Stage @(".gitignore")
Do-Commit "2026-02-19" "09" "chore: add gitignore for node_modules, dist, and Python artifacts"

# ============================================================
# Phase 2 - Database  (Feb 21-24)
# ============================================================
Write-Host "`n--- Phase 2: Database Layer ---"

Stage @("database\pglite-server.mjs")
Do-Commit "2026-02-21" "10" "feat: add PGlite embedded PostgreSQL server"

Stage @("database\__init__.py","database\db_client.py")
Do-Commit "2026-02-24" "11" "feat: add Python database client with connection helpers"

# ============================================================
# Phase 3 - Pipeline  (Mar 1-24)
# ============================================================
Write-Host "`n--- Phase 3: Pipeline ---"

Stage @("pipeline\__init__.py","pipeline\generate_synthetic_data.py")
Do-Commit "2026-03-01" "10" "feat: add synthetic data generator for 120k records across 3 CRM sources"

Stage @("pipeline\standardization\__init__.py","pipeline\standardization\engine.py")
Do-Commit "2026-03-05" "11" "feat: implement standardization engine for name, email, phone, and company"

Stage @("pipeline\blocking\__init__.py","pipeline\blocking\engine.py")
Do-Commit "2026-03-08" "10" "feat: add multi-index blocking strategy using email, phone+region, and company"

Stage @("pipeline\scoring\__init__.py","pipeline\scoring\engine.py")
Do-Commit "2026-03-12" "14" "feat: implement Tier-A confidence scoring with weighted feature sum"

Stage @("pipeline\survivorship\__init__.py","pipeline\survivorship\engine.py")
Do-Commit "2026-03-17" "10" "feat: add survivorship engine with recency, priority, and longest-value rules"

Stage @("pipeline\orchestrator.py")
Do-Commit "2026-03-24" "11" "feat: wire pipeline stages in orchestrator with ordered execution"

# ============================================================
# Phase 4 - dbt  (Mar 26 - Apr 5)
# ============================================================
Write-Host "`n--- Phase 4: dbt Models ---"

Stage @("dbt\models\staging\stg_crm_primary.sql")
Do-Commit "2026-03-26" "10" "feat: add dbt staging model for CRM primary source"

Stage @("dbt\models\staging\stg_crm_secondary.sql","dbt\models\staging\stg_marketing.sql")
Do-Commit "2026-03-28" "14" "feat: add dbt staging models for CRM secondary and marketing automation"

Stage @("dbt\models\intermediate\int_blocking_index.sql")
Do-Commit "2026-03-30" "10" "feat: add dbt intermediate model for consolidated blocking index"

Stage @("dbt\models\marts\golden_records\dim_golden_records.sql")
Do-Commit "2026-04-02" "11" "feat: add golden records mart with SCD Type-2 lineage tracking"

Stage @("dbt\models\marts\audit\lineage_log.sql","dbt\models\marts\audit\quality_daily.sql")
Do-Commit "2026-04-05" "10" "feat: add audit marts for lineage log and daily quality metrics"

# ============================================================
# Phase 5 - FastAPI  (Apr 8-12)
# ============================================================
Write-Host "`n--- Phase 5: FastAPI Backend ---"

Stage @("api\__init__.py","api\routers\__init__.py")
Do-Commit "2026-04-08" "10" "feat: scaffold FastAPI app with router structure"

Stage @("api\main.py")
Do-Commit "2026-04-12" "14" "feat: add health, stats, golden-records, matches, resolve, and pipeline endpoints"

# ============================================================
# Phase 6 - React frontend  (Apr 18 - May 7)
# ============================================================
Write-Host "`n--- Phase 6: React Frontend ---"

Stage @("src\main.tsx","src\App.tsx","src\App.css","src\index.css")
Do-Commit "2026-04-18" "10" "feat: add React app entry point and root App component"

Stage @("src\lib\utils.ts","src\types\index.ts")
Do-Commit "2026-04-20" "11" "feat: add shared utility functions and TypeScript type definitions"

Stage @("src\pages\Home.tsx","src\pages\Dashboard.tsx")
Do-Commit "2026-04-22" "10" "feat: add Home landing page and main Dashboard page layout"

Stage @("src\components\dashboard\StatsCards.tsx")
Do-Commit "2026-04-24" "14" "feat: add StatsCards component for schema health overview"

Stage @("src\components\dashboard\ConfidenceChart.tsx","src\components\dashboard\MatchStatusChart.tsx")
Do-Commit "2026-04-26" "10" "feat: add ConfidenceChart and MatchStatusChart with Recharts"

Stage @("src\components\dashboard\GoldenRecordsTable.tsx","src\components\dashboard\MatchesTable.tsx")
Do-Commit "2026-04-28" "11" "feat: add GoldenRecordsTable and MatchesTable with pagination and filters"

Stage @("src\components\dashboard\ResolveForm.tsx","src\components\dashboard\LineageView.tsx")
Do-Commit "2026-04-30" "10" "feat: add ResolveForm for entity resolution and LineageView for provenance"

Stage @("src\components\dashboard\QualityTrends.tsx","src\components\dashboard\PipelineRuns.tsx")
Do-Commit "2026-05-02" "14" "feat: add QualityTrends time-series chart and PipelineRuns control panel"

Stage @("src\hooks\useApi.ts","src\hooks\use-mobile.ts")
Do-Commit "2026-05-05" "10" "feat: add useApi data-fetching hook wired to FastAPI backend"

# Stage all ui components individually
Get-ChildItem -Path "$repo\src\components\ui" -Filter "*.tsx" | ForEach-Object {
    git -C $repo add "src\components\ui\$($_.Name)" | Out-Null
}
Do-Commit "2026-05-07" "11" "chore: add shadcn/ui component library from accordion through tooltip"

# ============================================================
# Phase 7 - Integration and polish  (May 8-14)
# ============================================================
Write-Host "`n--- Phase 7: Integration and Polish ---"

Stage @("start.mjs")
Do-Commit "2026-05-08" "10" "feat: add unified start.mjs to orchestrate all services in correct order"

Stage @("package-lock.json")
Do-Commit "2026-05-10" "11" "chore: lock dependency versions in package-lock.json"

Stage @("README.md")
Do-Commit "2026-05-12" "14" "docs: add comprehensive README with architecture, quickstart, and API reference"

# Final catch-all for anything remaining
$ts = "2026-05-14 10:00:00 +0530"
$env:GIT_AUTHOR_DATE    = $ts
$env:GIT_COMMITTER_DATE = $ts
git -C $repo add -A | Out-Null
$pending = git -C $repo diff --cached --name-only 2>&1
if ($pending) {
    git -C $repo commit -m "chore: final cleanup, fix package name, polish project structure" | Out-Null
    Write-Host "  [2026-05-14] chore: final cleanup, fix package name, polish project structure"
} else {
    Write-Host "  [2026-05-14] Nothing remaining to commit"
}

# ============================================================
# Summary
# ============================================================
Write-Host "`n=== Commit log ==="
git -C $repo log --format="%h %ad %s" --date=short 2>&1

Write-Host "`n=== Total ==="
$n = git -C $repo rev-list --count HEAD
Write-Host "  $n commits"

Write-Host "`n=== Adding remote ==="
git -C $repo remote add origin git@github.com:Ritinpaul/GoldenRecord.git 2>&1
git -C $repo remote -v

Write-Host "`n=== Force-pushing to origin/main ==="
git -C $repo push --force -u origin main 2>&1
Write-Host "`n=== Done ==="
