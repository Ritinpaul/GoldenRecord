import { useState, useEffect, useCallback } from 'react';
import type {
  HealthResponse,
  StatsResponse,
  GoldenRecord,
  MatchResult,
  LineageResponse,
  ResolveResponse,
  PipelineRun,
} from '@/types';

const API_BASE = import.meta.env.DEV ? '/api' : window.location.origin + '/api';

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    throw new ApiError(response.status, await response.text());
  }

  return response.json();
}

export function useHealth() {
  const [data, setData] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetch = useCallback(async () => {
    try {
      setLoading(true);
      const result = await fetchJson<HealthResponse>(`${API_BASE}/health`);
      setData(result);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetch();
    const interval = setInterval(fetch, 10000);
    return () => clearInterval(interval);
  }, [fetch]);

  return { data, loading, error, refetch: fetch };
}

export function useStats() {
  const [data, setData] = useState<StatsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetch = useCallback(async () => {
    try {
      setLoading(true);
      const result = await fetchJson<StatsResponse>(`${API_BASE}/stats`);
      setData(result);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetch();
    const interval = setInterval(fetch, 15000);
    return () => clearInterval(interval);
  }, [fetch]);

  return { data, loading, error, refetch: fetch };
}

export function useGoldenRecords(search?: string) {
  const [data, setData] = useState<{ records: GoldenRecord[]; count: number } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetch = useCallback(async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (search) params.set('search', search);
      params.set('limit', '50');
      const result = await fetchJson<{ records: GoldenRecord[]; count: number }>(
        `${API_BASE}/golden-records?${params}`
      );
      setData(result);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, [search]);

  useEffect(() => {
    fetch();
  }, [fetch]);

  return { data, loading, error, refetch: fetch };
}

export function useMatches(status?: string) {
  const [data, setData] = useState<{ matches: MatchResult[]; count: number } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetch = useCallback(async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (status) params.set('status', status);
      params.set('limit', '50');
      const result = await fetchJson<{ matches: MatchResult[]; count: number }>(
        `${API_BASE}/matches?${params}`
      );
      setData(result);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, [status]);

  useEffect(() => {
    fetch();
  }, [fetch]);

  return { data, loading, error, refetch: fetch };
}

export function useLineage(goldenId: string) {
  const [data, setData] = useState<LineageResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchJson<LineageResponse>(`${API_BASE}/golden-record/${goldenId}/lineage`)
      .then(setData)
      .catch((e) => setError(e instanceof Error ? e.message : 'Unknown error'))
      .finally(() => setLoading(false));
  }, [goldenId]);

  return { data, loading, error };
}

export async function resolveRecord(record: {
  email?: string;
  phone?: string;
  first_name?: string;
  last_name?: string;
  company_name?: string;
  region?: string;
}): Promise<ResolveResponse> {
  return fetchJson<ResolveResponse>(`${API_BASE}/resolve`, {
    method: 'POST',
    body: JSON.stringify(record),
  });
}

export async function runPipeline(source: string = 'all'): Promise<PipelineRun> {
  return fetchJson<PipelineRun>(`${API_BASE}/pipeline/run?source=${source}`, {
    method: 'POST',
  });
}
