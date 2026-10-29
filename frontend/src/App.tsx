import { useState } from 'react'
import { ChatWindow } from './components/chat/ChatWindow'
import { InstallBanner } from './components/chat/InstallBanner'
import { LanguageToggle } from './components/chat/LanguageToggle'
import { messages } from './i18n/messages'
import { useChat } from './hooks/useChat'

export default function App() {
  const { session, loading, processing, error, lang, send, handleQuickReply, setLang } = useChat()
  const [text, setText] = useState('')

  const placeholder = (() => {
    switch (session?.step) {
      case 'ask_location':
      case 'confirm_location':
        return messages.inputPlaceholderLocation[lang]
      case 'ask_last_crop':
        return messages.inputPlaceholderCrop[lang]
      case 'free_chat':
        return messages.inputPlaceholderFree[lang]
      default:
        return messages.inputPlaceholder[lang]
    }
  })()

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!text.trim() || processing) return
    const msg = text.trim()
    setText('')
    await send({ text: msg })
  }

  if (loading) {
    return (
      <div className="flex min-h-dvh items-center justify-center bg-stone-100 text-stone-600">
        TaniPilot…
      </div>
    )
  }

  return (
    <div className="mx-auto flex h-dvh max-w-lg flex-col bg-stone-100">
      <header className="shrink-0 bg-green-800 text-white">
        <InstallBanner lang={lang} />
        <div className="flex items-center justify-between px-4 py-3">
          <div>
            <h1 className="text-lg font-bold">{messages.appTitle[lang]}</h1>
            <p className="text-xs text-green-100">{messages.appSubtitle[lang]}</p>
          </div>
          <LanguageToggle lang={lang} onChange={setLang} />
        </div>
      </header>

      {error && (
        <div className="shrink-0 bg-red-50 px-4 py-2 text-xs text-red-800">{error}</div>
      )}

      <ChatWindow
        messages={session?.messages ?? []}
        lang={lang}
        processing={processing}
        onQuickReply={handleQuickReply}
      />

      <form onSubmit={onSubmit} className="shrink-0 border-t border-stone-200 bg-white p-3">
        <div className="flex gap-2">
          <input
            type="text"
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder={placeholder}
            disabled={processing}
            className="min-w-0 flex-1 rounded-xl border border-stone-300 px-4 py-2.5 text-sm focus:border-green-600 focus:outline-none focus:ring-2 focus:ring-green-200 disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={processing || !text.trim()}
            className="rounded-xl bg-green-700 px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-50"
          >
            {messages.send[lang]}
          </button>
        </div>
      </form>
    </div>
  )
}
