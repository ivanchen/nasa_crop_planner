import { useEffect, useState } from 'react'
import { messages, type Lang } from '../../i18n/messages'

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>
}

export function InstallBanner({ lang }: { lang: Lang }) {
  const [deferred, setDeferred] = useState<BeforeInstallPromptEvent | null>(null)
  const [dismissed, setDismissed] = useState(() => sessionStorage.getItem('pwa_dismissed') === '1')

  useEffect(() => {
    const handler = (e: Event) => {
      e.preventDefault()
      setDeferred(e as BeforeInstallPromptEvent)
    }
    window.addEventListener('beforeinstallprompt', handler)
    return () => window.removeEventListener('beforeinstallprompt', handler)
  }, [])

  if (dismissed || !deferred) return null

  return (
    <div className="flex items-center justify-between gap-2 border-b border-green-700/20 bg-green-900/30 px-4 py-2 text-xs text-green-50">
      <span>{messages.installHint[lang]}</span>
      <div className="flex shrink-0 gap-2">
        <button
          type="button"
          className="rounded-md bg-white px-2 py-1 font-semibold text-green-800"
          onClick={async () => {
            await deferred.prompt()
            setDeferred(null)
          }}
        >
          {messages.install[lang]}
        </button>
        <button
          type="button"
          className="text-green-200"
          onClick={() => {
            sessionStorage.setItem('pwa_dismissed', '1')
            setDismissed(true)
          }}
        >
          ✕
        </button>
      </div>
    </div>
  )
}
