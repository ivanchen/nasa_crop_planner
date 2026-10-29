import { useCallback, useEffect, useRef, useState } from 'react'
import * as chatApi from '../api/chat'
import { getDeviceLocation } from '../lib/geolocation'
import type { ChatMessage, Lang, SessionState } from '../types/chat'

const SESSION_KEY = 'tanipilot_session_id'
const LANG_KEY = 'tanipilot_lang'
const POLL_MS = 2000

export function useChat() {
  const [session, setSession] = useState<SessionState | null>(null)
  const [loading, setLoading] = useState(true)
  const [processing, setProcessing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const lang = (localStorage.getItem(LANG_KEY) as Lang) || 'id'

  const refresh = useCallback(async (sessionId: string) => {
    const state = await chatApi.getSession(sessionId)
    setSession(state)
    setProcessing(state.step === 'analyzing')
    return state
  }, [])

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const saved = localStorage.getItem(SESSION_KEY)
        if (saved) {
          try {
            const state = await chatApi.getSession(saved)
            if (!cancelled) {
              setSession(state)
              setProcessing(state.step === 'analyzing')
              setLoading(false)
              return
            }
          } catch {
            localStorage.removeItem(SESSION_KEY)
          }
        }
        const state = await chatApi.createSession(lang)
        if (!cancelled) {
          localStorage.setItem(SESSION_KEY, state.session_id)
          setSession(state)
          setLoading(false)
        }
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : 'Failed to start chat')
        setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [lang])

  useEffect(() => {
    if (!session || session.step !== 'analyzing') {
      if (pollRef.current) clearInterval(pollRef.current)
      return
    }
    pollRef.current = setInterval(() => {
      refresh(session.session_id).then((s) => {
        if (s.step === 'free_chat') setProcessing(false)
      })
    }, POLL_MS)
    return () => {
      if (pollRef.current) clearInterval(pollRef.current)
    }
  }, [session?.session_id, session?.step, refresh])

  const send = useCallback(
    async (payload: { text?: string; action_id?: string; location?: { lat: number; lon: number } }) => {
      if (!session) return
      setError(null)
      try {
        const result = await chatApi.sendMessage(session.session_id, payload)
        setProcessing(result.processing)
        await refresh(session.session_id)
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Send failed')
      }
    },
    [session, refresh],
  )

  const handleQuickReply = useCallback(
    async (reply: ChatMessage['quick_replies'][0]) => {
      if (reply.action === 'gps') {
        try {
          const loc = await getDeviceLocation()
          await send({ action_id: reply.id, location: loc, text: reply.label })
        } catch {
          await send({ action_id: reply.id, text: reply.label })
        }
        return
      }
      await send({ action_id: reply.id, text: reply.label })
    },
    [send],
  )

  const setLang = useCallback(
    async (newLang: Lang) => {
      localStorage.setItem(LANG_KEY, newLang)
      if (session) {
        const state = await chatApi.setSessionLang(session.session_id, newLang)
        setSession(state)
      } else {
        window.location.reload()
      }
    },
    [session],
  )

  const newSession = useCallback(async () => {
    localStorage.removeItem(SESSION_KEY)
    const state = await chatApi.createSession(lang)
    localStorage.setItem(SESSION_KEY, state.session_id)
    setSession(state)
    setProcessing(false)
  }, [lang])

  return {
    session,
    loading,
    processing,
    error,
    lang: session?.lang ?? lang,
    send,
    handleQuickReply,
    setLang,
    newSession,
  }
}
