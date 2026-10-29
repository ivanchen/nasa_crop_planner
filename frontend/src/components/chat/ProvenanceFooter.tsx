import { disclaimer, messages, type Lang } from '../../i18n/messages'
import type { DataSourceMeta } from '../../types'

function formatDate(iso: string, lang: Lang) {
  return new Intl.DateTimeFormat(lang === 'id' ? 'id-ID' : 'en-GB', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(iso))
}

export function ProvenanceFooter({ meta, lang }: { meta: DataSourceMeta; lang: Lang }) {
  const period =
    meta.period_start && meta.period_end ? `${meta.period_start} – ${meta.period_end}` : null

  return (
    <footer className="mt-2 border-t border-stone-100 pt-2 text-[10px] leading-relaxed text-stone-400">
      <p>
        {messages.source[lang]}: {meta.source}
        {' · '}
        {messages.fetched[lang]}: {formatDate(meta.fetched_at, lang)}
        {meta.cached ? ` (${messages.cached[lang]})` : ''}
      </p>
      {period && (
        <p>
          {messages.period[lang]}: {period}
        </p>
      )}
      {meta.resolution && (
        <p>
          {messages.resolution[lang]}: {meta.resolution}
        </p>
      )}
      {meta.disclaimer && <p className="italic">{disclaimer(lang, meta.disclaimer)}</p>}
    </footer>
  )
}
