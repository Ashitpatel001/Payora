const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8001/api";
const API_KEY = import.meta.env.VITE_API_KEY || "dev-secret-key"; // Basic auth for dev

async function fetchApi(endpoint: string, options: RequestInit = {}) {
  const headers = {
    ...options.headers,
    'x-api-key': API_KEY,
  };
  
  const res = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });
  if (!res.ok) {
    const errText = await res.text();
    throw new Error(`API Error: ${res.status} - ${errText}`);
  }
  return res.json();
}

// --------------------------------------------------------
// Interfaces
// --------------------------------------------------------

export interface RiskEvent {
  id: string;
  source: string;
  event_type: string;
  customer_id: string;
  amount: number;
  currency: string;
  created_at: string;
  split: string;
}

export interface DashboardStats {
  total_at_risk: number;
  recovered_amount: number;
  recovery_rate: number;
  total_cases: number;
  active_cases: number;
  guardrail_blocks: number;
  quadrant_distribution: Record<string, number>;
  root_cause_distribution: Record<string, number>;
  batch_trends: Array<{
    id: string;
    date: string;
    recovery_rate: number;
    amount_recovered: number;
    total_cases: number;
  }>;
}

export interface BatchRunResult {
  id: string;
  status: string;
  total_cases: number;
  cases_processed: number;
  amount_at_risk: number;
  amount_recovered: number;
  recovery_rate: number;
  false_escalation_rate: number;
  exception_list: Array<{case_id: string; reason: string; rule: string}>;
  recovered_list: Array<{case_id: string; amount: number; channel: string; short_url: string; status: string}>;
  started_at: string;
  completed_at: string | null;
}

// --------------------------------------------------------
// API Methods
// --------------------------------------------------------

export async function checkHealth() {
  const res = await fetch(`${API_BASE}/health`);
  return res.json();
}

export async function getEvents(): Promise<any[]> {
  return fetchApi('/events?split=dev');
}

export async function getDashboardStats(): Promise<DashboardStats> {
  return fetchApi('/dashboard/stats');
}

export async function getCase(id: string): Promise<any> {
  return fetchApi(`/cases/${id}`);
}

export async function triggerCaseRun(id: string): Promise<any> {
  return fetchApi(`/cases/${id}/run`, { method: 'POST' });
}

export async function getGuardrails(): Promise<any[]> {
  return fetchApi('/guardrails');
}

export async function resolvePTP(id: string, status: 'kept' | 'broken'): Promise<any> {
  return fetchApi(`/cases/${id}/ptp/resolve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status })
  });
}

export async function startBatchRun(): Promise<{run_id: string, status: string}> {
  return fetchApi('/batch-run', { method: 'POST' });
}

export async function getBatchResults(): Promise<BatchRunResult[]> {
  return fetchApi('/batch-results');
}

export async function getBatchResult(id: string): Promise<BatchRunResult> {
  return fetchApi(`/batch-results/${id}`);
}

export async function simulatePayment(id: string): Promise<any> {
  return fetchApi(`/cases/${id}/simulate-payment`, { method: 'POST' });
}

export async function simulatePtp(id: string): Promise<any> {
  return fetchApi(`/cases/${id}/simulate-ptp`, { method: 'POST' });
}
