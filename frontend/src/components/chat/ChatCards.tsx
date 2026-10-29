import { messages, type Lang } from '../../i18n/messages'
import type { ChatCard } from '../../types/chat'
import type { ClimateSummary, MoistureSummary, Recommendation, SoilSummary, VegetationSummary } from '../../types'
import { ProvenanceFooter } from './ProvenanceFooter'

function LocationCard({ data }: { data: { lat: number; lon: number; label?: string } }) {
  const url = `https://www.openstreetmap.org/?mlat=${data.lat}&mlon=${data.lon}#map=12/${data.lat}/${data.lon}`
  return (
    <div className="rounded-lg bg-stone-50 p-3 text-sm">
      <p className="font-medium text-stone-800">
        {data.lat}, {data.lon}
        {data.label ? ` ${data.label}` : ''}
      </p>
      <a href={url} target="_blank" rel="noreferrer" className="text-xs text-green-700 underline">
        OpenStreetMap
      </a>
    </div>
  )
}

function ClimateCard({ data, lang, provenance }: { data: ClimateSummary; lang: Lang; provenance?: ChatCard['provenance'] }) {
  return (
    <div className="rounded-lg bg-sky-50 p-3 text-sm text-stone-700">
      <p>
        {data.mean_temp_c}°C · {data.annual_rainfall_mm} mm/yr · {data.dry_months} dry mo.
      </p>
      {provenance && <ProvenanceFooter meta={provenance} lang={lang} />}
    </div>
  )
}

function SoilCard({ data, lang, provenance }: { data: SoilSummary; lang: Lang; provenance?: ChatCard['provenance'] }) {
  return (
    <div className="rounded-lg bg-amber-50 p-3 text-sm text-stone-700">
      <p>
        pH {data.ph} · {data.texture} · SOC {data.soc_g_kg} g/kg
      </p>
      {provenance && <ProvenanceFooter meta={provenance} lang={lang} />}
    </div>
  )
}

function VegetationCard({ data, lang, provenance }: { data: VegetationSummary; lang: Lang; provenance?: ChatCard['provenance'] }) {
  return (
    <div className="rounded-lg bg-green-50 p-3 text-sm text-stone-700">
      <p>
        NDVI {data.mean_ndvi} · {messages.trend[data.trend][lang]}
      </p>
      {provenance && <ProvenanceFooter meta={provenance} lang={lang} />}
    </div>
  )
}

function MoistureCard({ data, lang, provenance }: { data: MoistureSummary; lang: Lang; provenance?: ChatCard['provenance'] }) {
  return (
    <div className="rounded-lg bg-cyan-50 p-3 text-sm text-stone-700">
      <p>
        {Math.round(data.mean_volumetric * 100)}% · {messages.variability[data.variability][lang]}
      </p>
      {provenance && <ProvenanceFooter meta={provenance} lang={lang} />}
    </div>
  )
}

function RotationCard({ data, lang }: { data: Recommendation; lang: Lang }) {
  return (
    <div className="rounded-lg border border-green-200 bg-white p-3 text-sm">
      <div className="flex justify-between">
        <p className="font-semibold text-stone-900">#{data.rank} {data.rotation.join(' → ')}</p>
        <span className="rounded bg-green-100 px-2 py-0.5 text-xs font-bold text-green-800">
          {Math.round(data.score)}
        </span>
      </div>
      <div className="mt-2 grid grid-cols-3 gap-1 text-[10px] text-stone-500">
        <span>{messages.water[lang]}: {Math.round(data.scores.water)}</span>
        <span>{messages.drought[lang]}: {Math.round(data.scores.drought)}</span>
        <span>{messages.soilHealth[lang]}: {Math.round(data.scores.soil_health)}</span>
      </div>
    </div>
  )
}

export function ChatCardView({ card, lang }: { card: ChatCard; lang: Lang }) {
  switch (card.type) {
    case 'location':
      return <LocationCard data={card.data as { lat: number; lon: number; label?: string }} />
    case 'climate':
      return <ClimateCard data={card.data as unknown as ClimateSummary} lang={lang} provenance={card.provenance} />
    case 'soil':
      return <SoilCard data={card.data as unknown as SoilSummary} lang={lang} provenance={card.provenance} />
    case 'vegetation':
      return <VegetationCard data={card.data as unknown as VegetationSummary} lang={lang} provenance={card.provenance} />
    case 'moisture':
      return <MoistureCard data={card.data as unknown as MoistureSummary} lang={lang} provenance={card.provenance} />
    case 'rotation':
      return <RotationCard data={card.data as unknown as Recommendation} lang={lang} />
    case 'warning':
      return (
        <div className="rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-900">
          {(card.data as { text: string }).text}
        </div>
      )
    default:
      return null
  }
}
