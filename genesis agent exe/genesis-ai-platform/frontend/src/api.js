/**
 * GENESIS API Client
 * Calls the FastAPI backend. In dev, Vite proxies /api → localhost:8000.
 * In production (Docker), Nginx routes /api → backend service.
 */

const BASE = '/api/v1'

class GenesisAPIError extends Error {
  constructor(message, status) {
    super(message)
    this.status = status
    this.name = 'GenesisAPIError'
  }
}

async function req(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new GenesisAPIError(body.detail || `HTTP ${res.status}`, res.status)
  }
  return res.json()
}

export const AgentsAPI = {
  list:      (params = {}) => req(`/agents?${new URLSearchParams(params)}`),
  get:       (id)          => req(`/agents/${id}`),
  seed:      ()            => req('/agents/seed'),
  create:    (body)        => req('/agents', { method: 'POST', body: JSON.stringify(body) }),
  retire:    (id)          => req(`/agents/${id}`, { method: 'DELETE' }),
  updateDNA: (id, dna)     => req(`/agents/${id}/dna`, { method: 'PUT', body: JSON.stringify(dna) }),
}

export const TasksAPI = {
  execute: (body)        => req('/tasks', { method: 'POST', body: JSON.stringify(body) }),
  list:    (params = {}) => req(`/tasks?${new URLSearchParams(params)}`),
}

export const EvolutionAPI = {
  run:     (body)     => req('/evolution/run', { method: 'POST', body: JSON.stringify(body) }),
  mutate:  (id, body) => req(`/evolution/mutate/${id}`, { method: 'POST', body: JSON.stringify(body) }),
  history: (n = 20)   => req(`/evolution/history?limit=${n}`),
  events:  (n = 50)   => req(`/evolution/events?limit=${n}`),
}

export const MemoryAPI = {
  query: (query, params = {}) => req(`/memory?query=${encodeURIComponent(query)}&${new URLSearchParams(params)}`),
  store: (body)               => req('/memory', { method: 'POST', body: JSON.stringify(body) }),
  stats: ()                   => req('/memory/stats'),
}

export const SkillsAPI = {
  list:   (params = {}) => req(`/skills?${new URLSearchParams(params)}`),
  seed:   ()            => req('/skills/seed'),
  create: (body)        => req('/skills', { method: 'POST', body: JSON.stringify(body) }),
}

export const SystemAPI = {
  health: () => req('/system/health'),
  stats:  () => req('/system/stats'),
}

export { GenesisAPIError }
