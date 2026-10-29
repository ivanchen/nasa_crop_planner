import type { Job, Location, Priorities } from '../types'

const API_URL = import.meta.env.VITE_API_URL ?? ''

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    throw new Error(body?.detail ?? `Request failed with status ${response.status}`)
  }
  return response.json()
}

export function analyze(location: Location, priorities: Priorities): Promise<Job> {
  return request<Job>('/api/analyze', {
    method: 'POST',
    body: JSON.stringify({ ...location, priorities }),
  })
}

export function getTask(jobId: string): Promise<Job> {
  return request<Job>(`/api/tasks/${jobId}`)
}
