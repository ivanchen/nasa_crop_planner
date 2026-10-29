import type { Priorities } from '../types'

const FIELDS: { key: keyof Priorities; label: string; hint: string }[] = [
  { key: 'water', label: 'Save water', hint: 'Prefer crops that need little irrigation' },
  { key: 'drought', label: 'Withstand drought', hint: 'Prefer crops that tolerate dry spells' },
  { key: 'soil_health', label: 'Improve soil', hint: 'Prefer legumes, cover crops and diverse rotations' },
]

function rebalance(current: Priorities, key: keyof Priorities, value: number): Priorities {
  const clamped = Math.max(0, Math.min(1, value))
  const others = FIELDS.map((f) => f.key).filter((k) => k !== key)
  const othersTotal = others.reduce((sum, k) => sum + current[k], 0)
  const remaining = 1 - clamped

  const next = { ...current, [key]: clamped }
  for (const k of others) {
    next[k] = othersTotal === 0 ? remaining / others.length : (current[k] / othersTotal) * remaining
  }
  return next
}

interface Props {
  priorities: Priorities
  onChange: (priorities: Priorities) => void
}

export function PriorityPanel({ priorities, onChange }: Props) {
  return (
    <section className="rounded-2xl border border-stone-200 bg-white p-5 shadow-sm">
      <h2 className="text-lg font-semibold text-stone-900">2. Set your priorities</h2>
      <p className="mt-1 text-sm text-stone-500">Moving one slider rebalances the others so they always total 100%.</p>

      <div className="mt-4 space-y-5">
        {FIELDS.map(({ key, label, hint }) => (
          <div key={key}>
            <div className="flex items-baseline justify-between">
              <label htmlFor={key} className="text-sm font-medium text-stone-700">
                {label}
              </label>
              <span className="text-sm font-semibold tabular-nums text-green-700">
                {Math.round(priorities[key] * 100)}%
              </span>
            </div>
            <input
              id={key}
              type="range"
              min={0}
              max={100}
              value={Math.round(priorities[key] * 100)}
              onChange={(e) => onChange(rebalance(priorities, key, Number(e.target.value) / 100))}
              className="mt-2 w-full accent-green-600"
            />
            <p className="text-xs text-stone-400">{hint}</p>
          </div>
        ))}
      </div>
    </section>
  )
}
