/**
 * API Client for Agent Orchestrator backend
 */

const BASE_URL = '/api'

async function request(endpoint, options = {}) {
  const url = `${BASE_URL}${endpoint}`
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  }

  if (config.body && typeof config.body === 'object') {
    config.body = JSON.stringify(config.body)
  }

  const response = await fetch(url, config)

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }

  if (response.status === 204) {
    return null
  }

  return response.json()
}

// Health
export const health = {
  check: () => request('/health'),
}

// Projects
export const projects = {
  list: () => request('/projects'),
  get: (id) => request(`/projects/${id}`),
  create: (data) => request('/projects', { method: 'POST', body: data }),
  update: (id, data) => request(`/projects/${id}`, { method: 'PATCH', body: data }),
  delete: (id) => request(`/projects/${id}`, { method: 'DELETE' }),
}

// Ideas
export const ideas = {
  list: (params = {}) => {
    const query = new URLSearchParams(params).toString()
    return request(`/ideas${query ? `?${query}` : ''}`)
  },
  get: (id) => request(`/ideas/${id}`),
  create: (data) => request('/ideas', { method: 'POST', body: data }),
  update: (id, data) => request(`/ideas/${id}`, { method: 'PATCH', body: data }),
  delete: (id) => request(`/ideas/${id}`, { method: 'DELETE' }),
  refine: (id) => request(`/ideas/${id}/refine`, { method: 'POST' }),
  approve: (id) => request(`/ideas/${id}/approve`, { method: 'POST' }),
  reject: (id, reason) => request(`/ideas/${id}/reject?reason=${encodeURIComponent(reason || '')}`, { method: 'POST' }),
  getQuestions: (id) => request(`/ideas/${id}/questions`),
}

// Questions
export const questions = {
  list: (params = {}) => {
    const query = new URLSearchParams(params).toString()
    return request(`/questions${query ? `?${query}` : ''}`)
  },
  pending: (projectId) => request(`/questions/pending${projectId ? `?project_id=${projectId}` : ''}`),
  get: (id) => request(`/questions/${id}`),
  answer: (id, answer) => request(`/questions/${id}/answer`, { method: 'POST', body: { answer } }),
  skip: (id) => request(`/questions/${id}/skip`, { method: 'POST' }),
}

// Tickets
export const tickets = {
  list: (params = {}) => {
    const query = new URLSearchParams(params).toString()
    return request(`/tickets${query ? `?${query}` : ''}`)
  },
  queue: (projectId) => request(`/tickets/queue${projectId ? `?project_id=${projectId}` : ''}`),
  get: (id) => request(`/tickets/${id}`),
  create: (data) => request('/tickets', { method: 'POST', body: data }),
  update: (id, data) => request(`/tickets/${id}`, { method: 'PATCH', body: data }),
  delete: (id) => request(`/tickets/${id}`, { method: 'DELETE' }),
  start: (id) => request(`/tickets/${id}/start`, { method: 'POST' }),
  submitForReview: (id) => request(`/tickets/${id}/review`, { method: 'POST' }),
  getReviewSummary: (id) => request(`/tickets/${id}/review`),
  approve: (id, comment) => request(`/tickets/${id}/approve${comment ? `?comment=${encodeURIComponent(comment)}` : ''}`, { method: 'POST' }),
  requestChanges: (id, feedback) => request(`/tickets/${id}/request-changes?feedback=${encodeURIComponent(feedback)}`, { method: 'POST' }),
  cancel: (id, reason) => request(`/tickets/${id}/cancel${reason ? `?reason=${encodeURIComponent(reason)}` : ''}`, { method: 'POST' }),
  // Subtasks
  listSubtasks: (ticketId) => request(`/tickets/${ticketId}/subtasks`),
  createSubtask: (ticketId, data) => request(`/tickets/${ticketId}/subtasks`, { method: 'POST', body: data }),
  updateSubtask: (ticketId, subtaskId, data) => request(`/tickets/${ticketId}/subtasks/${subtaskId}`, { method: 'PATCH', body: data }),
}

// Agents
export const agents = {
  list: (params = {}) => {
    const query = new URLSearchParams(params).toString()
    return request(`/agents${query ? `?${query}` : ''}`)
  },
  get: (id) => request(`/agents/${id}`),
  create: (data) => request('/agents', { method: 'POST', body: data }),
  update: (id, data) => request(`/agents/${id}`, { method: 'PATCH', body: data }),
  delete: (id) => request(`/agents/${id}`, { method: 'DELETE' }),
  getRuns: (id, limit = 50) => request(`/agents/${id}/runs?limit=${limit}`),
}

// Runs
export const runs = {
  create: (data) => request('/runs', { method: 'POST', body: data }),
  get: (id) => request(`/runs/${id}`),
}

export default {
  health,
  projects,
  ideas,
  questions,
  tickets,
  agents,
  runs,
}
