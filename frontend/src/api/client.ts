const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    throw new Error(`API ${res.status}: ${res.statusText}`);
  }
  return res.json();
}

export const api = {
  getPersonas: () => request<any[]>('/personas'),
  getPersona: (id: string) => request<any>(`/personas/${id}`),
  score: (body: { persona_id: string; as_of_month?: number }) =>
    request<any>('/score', { method: 'POST', body: JSON.stringify(body) }),
  transaction: (body: { persona_id: string; category: string; amount_inr: number }) =>
    request<any>('/transaction', { method: 'POST', body: JSON.stringify(body) }),
  project: (body: any) =>
    request<any>('/project', { method: 'POST', body: JSON.stringify(body) }),
  reset: () => request<any>('/reset', { method: 'POST' }),
  health: () => request<any>('/health'),
};
