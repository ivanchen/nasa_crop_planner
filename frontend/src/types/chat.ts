import type { DataSourceMeta, Recommendation } from './index'

export type Lang = 'id' | 'en'

export interface QuickReply {
  id: string
  label: string
  action: 'text' | 'gps'
}

export interface ChatCard {
  type: 'location' | 'climate' | 'soil' | 'vegetation' | 'moisture' | 'rotation' | 'warning'
  data: Record<string, unknown>
  provenance?: DataSourceMeta | null
}

export interface ChatMessage {
  id: string
  role: 'assistant' | 'user' | 'system'
  text: string
  quick_replies: QuickReply[]
  card?: ChatCard | null
}

export interface SessionState {
  session_id: string
  lang: Lang
  step: string
  messages: ChatMessage[]
  llm_enabled: boolean
  processing?: boolean
}

export type RotationCardData = Recommendation
