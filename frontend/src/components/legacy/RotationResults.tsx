import type { Recommendation, RotationScores } from '../types'

const AXES: { key: keyof RotationScores; label: string; color: string }[] = [
  { key: 'water', label: 'Water efficiency', color: 'bg-sky-500' },
  { key: 'drought', label: 'Drought resilience', color: 'bg-amber-500' },
  { key: 'soil_health', label: 'Soil health', color: 'bg-green-600' },
]

function ScoreBar({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div>
      <div className="flex justify-between text-xs text-stone-600">
        <span>{label}</span>
        <span className="tabular-nums">{Math.round(value)}</span>
      </div>
      <div className="mt-1 h-2 rounded-full bg-stone-100">
        <div className={`h-2 rounded-full ${color}`} style={{ width: `${value}%` }} />
      </div>
    </div>
  )
}

function RotationCard({ rec }: { rec: Recommendation }) {
  return (
    <article className="rounded-2xl border border-stone-200 bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-green-700">Option {rec.rank}</p>
          <h3 className="mt-1 text-lg font-semibold text-stone-900">{rec.rotation.join('  →  ')}</h3>
        </div>
        <div className="shrink-0 rounded-xl bg-green-50 px-3 py-2 text-center">
          <p className="text-2xl font-bold tabular-nums text-green-700">{Math.round(rec.score)}</p>
          <p className="text-[10px] uppercase tracking-wide text-green-700">Score</p>
        </div>
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        {AXES.map((a) => (
          <ScoreBar key={a.key} label={a.label} value={rec.scores[a.key]} color={a.color} />
        ))}
      </div>

      <p className="mt-4 text-sm text-stone-600">{rec.rationale}</p>

      <details className="mt-3 group" open={rec.rank === 1}>
        <summary className="cursor-pointer text-sm font-medium text-green-700 hover:text-green-800">
          Season-by-season plan
        </summary>
        <ol className="mt-3 space-y-3 border-l-2 border-green-200 pl-4">
          {rec.steps.map((s) => (
            <li key={s.season}>
              <p className="text-xs text-stone-500">
                {s.season} · {s.window}
              </p>
              <p className="text-sm font-semibold text-stone-900">
                {s.crop} <span className="font-normal text-stone-400">({s.crop_local_name})</span>
              </p>
              <p className="text-sm text-stone-600">{s.note}</p>
            </li>
          ))}
        </ol>
      </details>
    </article>
  )
}

export function RotationResults({ recommendations, processing }: { recommendations: Recommendation[]; processing: boolean }) {
  return (
    <section className="space-y-4">
      <h2 className="text-lg font-semibold text-stone-900">Recommended rotations</h2>
      {recommendations.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-stone-300 bg-white p-8 text-center text-sm text-stone-500">
          {processing
            ? 'Recommendations will appear once satellite data has been retrieved.'
            : 'No suitable rotation was found for this location.'}
        </div>
      ) : (
        recommendations.map((rec) => <RotationCard key={rec.rank} rec={rec} />)
      )}
    </section>
  )
}
