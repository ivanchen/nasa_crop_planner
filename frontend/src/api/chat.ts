import type { Lang, SessionState, ChatMessage } from '../types/chat'
import type { Location } from '../types'

const API_URL = import.meta.env.VITE_API_URL ?? ''

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    throw new Error(body?.detail ?? `Request failed (${response.status})`)
  }
  return response.json()
}

export function createSession(lang: Lang): Promise<SessionState> {
  return request('/api/chat/session', { method: 'POST', body: JSON.stringify({ lang }) })
}

export function getSession(sessionId: string): Promise<SessionState> {
  return request(`/api/chat/session/${sessionId}`)
}

export function sendMessage(
  sessionId: string,
  payload: { text?: string; action_id?: string; location?: Location },
): Promise<{ messages: ChatMessage[]; step: string; processing: boolean }> {
  return request(`/api/chat/session/${sessionId}/message`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function setSessionLang(sessionId: string, lang: Lang): Promise<SessionState> {
  return request(`/api/chat/session/${sessionId}/lang?lang=${lang}`, { method: 'PATCH' })
}
