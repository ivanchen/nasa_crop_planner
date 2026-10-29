import type { Lang } from '../../i18n/messages'

export function LanguageToggle({ lang, onChange }: { lang: Lang; onChange: (l: Lang) => void }) {
  return (
    <div className="flex rounded-lg border border-green-700/30 bg-green-900/40 p-0.5 text-xs font-semibold">
      {(['id', 'en'] as const).map((l) => (
        <button
          key={l}
          type="button"
          onClick={() => onChange(l)}
          className={`rounded-md px-2.5 py-1 uppercase transition ${
            lang === l ? 'bg-white text-green-800' : 'text-green-100 hover:text-white'
          }`}
        >
          {l}
        </button>
      ))}
    </div>
  )
}
