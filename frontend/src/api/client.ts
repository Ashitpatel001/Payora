const API_BASE = "http://localhost:8000/api";

export async function checkHealth() {
  const res = await fetch(`${API_BASE}/health`);
  return res.json();
}

export async function getEvents() {
  const res = await fetch(`${API_BASE}/events?split=dev`);
  if (!res.ok) throw new Error("Failed to fetch events");
  return res.json();
}

export async function getDashboardStats() {
  const res = await fetch(`${API_BASE}/dashboard/stats`);
  if (!res.ok) throw new Error("Failed to fetch dashboard stats");
  return res.json();
}

export async function getCase(id: string) {
  const res = await fetch(`${API_BASE}/cases/${id}`);
  if (!res.ok) throw new Error("Failed to fetch case");
  return res.json();
}

export async function triggerCaseRun(id: string) {
  const res = await fetch(`${API_BASE}/cases/${id}/run`, { method: 'POST' });
  if (!res.ok) throw new Error("Failed to trigger case run");
  return res.json();
}

export async function getGuardrails() {
  const res = await fetch(`${API_BASE}/guardrails`);
  if (!res.ok) throw new Error("Failed to fetch guardrails");
  return res.json();
}

export async function resolvePTP(id: string, status: 'kept' | 'broken') {
  const res = await fetch(`${API_BASE}/cases/${id}/ptp/resolve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status })
  });
  if (!res.ok) throw new Error("Failed to resolve PTP");
  return res.json();
}

export async function startBatchRun() {
  const res = await fetch(`${API_BASE}/batch-run`, { method: 'POST' });
  if (!res.ok) throw new Error("Failed to start batch run");
  return res.json();
}

export async function getBatchResults() {
  const res = await fetch(`${API_BASE}/batch-results`);
  if (!res.ok) throw new Error("Failed to fetch batch results");
  return res.json();
}

export async function getBatchResult(id: string) {
  const res = await fetch(`${API_BASE}/batch-results/${id}`);
  if (!res.ok) throw new Error("Failed to fetch batch result");
  return res.json();
}

export async function simulatePayment(id: string) {
  const res = await fetch(`${API_BASE}/cases/${id}/simulate-payment`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to simulate payment');
  return res.json();
}
