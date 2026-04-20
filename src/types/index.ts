export interface HealthResponse {
  status: string;
  database: string;
  records: Record<string, number>;
  last_run: PipelineRun | null;
}

export interface PipelineRun {
  run_id: string;
  source_system: string;
  records_in: number;
  records_merged: number;
  records_flagged_review: number;
  avg_confidence: number;
  run_timestamp: string;
  run_duration_ms: number;
  status: string;
}

export interface StatsResponse {
  record_counts: Record<string, number>;
  match_status_distribution: Record<string, number>;
  confidence_distribution: ConfidenceBand[];
  top_duplicate_clusters: DuplicateCluster[];
  recent_runs: PipelineRun[];
  quality_trends: QualityMetric[];
}

export interface ConfidenceBand {
  confidence_band: string;
  count: number;
  avg_confidence: number;
}

export interface DuplicateCluster {
  golden_record_id: string;
  source_count: number;
  avg_confidence: number;
}

export interface QualityMetric {
  snapshot_date: string;
  source_system: string;
  completeness_pct: number;
  duplicate_rate: number;
}

export interface GoldenRecord {
  id: number;
  golden_record_id: string;
  canonical_email: string | null;
  canonical_phone: string | null;
  canonical_first_name: string | null;
  canonical_last_name: string | null;
  canonical_company: string | null;
  canonical_title: string | null;
  canonical_region: string | null;
  version: number;
  is_current: boolean;
  created_at: string;
  source_record_ids?: string | Record<string, unknown>;
  survivorship_metadata?: string | Record<string, unknown>;
  lineage_graph?: string | Record<string, unknown>;
}

export interface MatchResult {
  id: number;
  record_a_id: number;
  record_b_id: number;
  email_exact: number;
  email_domain: number;
  name_jaro_winkler: number;
  phone_exact: number;
  company_token_jaccard: number;
  confidence_score: number;
  match_status: string;
  match_tier: string;
  block_type: string;
  created_at: string;
  a_email?: string;
  b_email?: string;
}

export interface LineageResponse {
  golden_record_id: string;
  is_current: boolean;
  valid_from: string;
  version: number;
  canonical_data: Record<string, string | null>;
  provenance: {
    source_record_ids: string[];
    survivorship_decisions: Record<string, unknown>;
  };
  lineage_graph: Record<string, unknown>;
  history: {
    versions: Array<Record<string, unknown>>;
    events: Array<Record<string, unknown>>;
    survivorship_log: Array<Record<string, unknown>>;
  };
  audit_trail: {
    created_at: string;
    version_count: number;
    event_count: number;
    survivorship_decision_count: number;
  };
}

export interface ResolveResponse {
  input: Record<string, string | undefined>;
  standardized: Record<string, string | undefined>;
  best_match: MatchCandidate | null;
  all_matches: MatchCandidate[];
  total_matches_found: number;
}

export interface MatchCandidate {
  record_id: number;
  source_system: string;
  source_record_id: string;
  golden_record_id: string | null;
  confidence: number;
  status: string;
  features: Record<string, number>;
  explanation: Record<string, unknown>;
  matched_data: Record<string, string>;
}
