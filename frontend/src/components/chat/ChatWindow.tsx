import { useEffect, useRef } from 'react'
import type { ChatMessage, QuickReply } from '../../types/chat'
import type { Lang } from '../../i18n/messages'
import { ChatCardView } from './ChatCards'
import { QuickReplies } from './QuickReplies'

interface Props {
  messages: ChatMessage[]
  lang: Lang
  processing: boolean
  onQuickReply: (reply: QuickReply) => void
}

export function ChatWindow({ messages, lang, processing, onQuickReply }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages.length, processing])

  const lastAssistant = [...messages].reverse().find((m) => m.role === 'assistant')

  return (
    <div className="flex-1 space-y-3 overflow-y-auto px-4 py-4">
      {messages.map((m) => (
        <div key={m.id} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
          <div
            className={`max-w-[88%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed shadow-sm ${
              m.role === 'user'
                ? 'rounded-br-md bg-green-700 text-white'
                : 'rounded-bl-md border border-stone-200 bg-white text-stone-800'
            }`}
          >
            <p className="whitespace-pre-wrap">{m.text}</p>
            {m.card && (
              <div className="mt-2">
                <ChatCardView card={m.card} lang={lang} />
              </div>
            )}
            {m.role === 'assistant' && m.id === lastAssistant?.id && m.quick_replies.length > 0 && (
              <QuickReplies replies={m.quick_replies} disabled={processing} onSelect={onQuickReply} />
            )}
          </div>
        </div>
      ))}
      {processing && (
        <div className="flex justify-start">
          <div className="rounded-2xl rounded-bl-md border border-stone-200 bg-white px-4 py-3 shadow-sm">
            <span className="inline-flex gap-1">
              <span className="h-2 w-2 animate-bounce rounded-full bg-green-600 [animation-delay:-0.3s]" />
              <span className="h-2 w-2 animate-bounce rounded-full bg-green-600 [animation-delay:-0.15s]" />
              <span className="h-2 w-2 animate-bounce rounded-full bg-green-600" />
            </span>
          </div>
        </div>
      )}
      <div ref={bottomRef} />
    </div>
  )
}
