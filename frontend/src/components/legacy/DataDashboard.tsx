import {
  Bar,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { ReactNode } from 'react'
import type { Job, SeriesPoint } from '../types'

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

function Card({ title, value, detail }: { title: string; value: string; detail: string }) {
  return (
    <div className="rounded-xl border border-stone-200 bg-white p-4 shadow-sm">
      <p className="text-xs font-medium uppercase tracking-wide text-stone-500">{title}</p>
      <p className="mt-1 text-xl font-semibold text-stone-900">{value}</p>
      <p className="mt-1 text-xs text-stone-500">{detail}</p>
    </div>
  )
}

function ChartPanel({ title, source, children }: { title: string; source: string; children: ReactNode }) {
  return (
    <div className="rounded-xl border border-stone-200 bg-white p-4 shadow-sm">
      <div className="flex items-baseline justify-between">
        <h3 className="text-sm font-semibold text-stone-800">{title}</h3>
        <span className="text-xs text-stone-400">{source}</span>
      </div>
      <div className="mt-3 h-52">{children}</div>
    </div>
  )
}

function Pending({ processing, label }: { processing: boolean; label: string }) {
  return (
    <div className="flex h-full items-center justify-center rounded-lg bg-stone-50 px-4 text-center text-sm text-stone-400">
      {processing ? `Waiting for ${label}…` : `${label} not available for this location.`}
    </div>
  )
}

function SeriesChart({ data, color, domain }: { data: SeriesPoint[]; color: string; domain: [number, number] }) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={data} margin={{ left: -10, right: 8, top: 4 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e7e5e4" />
        <XAxis dataKey="date" tick={{ fontSize: 11 }} minTickGap={32} />
        <YAxis domain={domain} tick={{ fontSize: 11 }} />
        <Tooltip />
        <Line type="monotone" dataKey="value" stroke={color} strokeWidth={2} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  )
}

const TREND_LABEL = { declining: 'Declining', stable: 'Stable', improving: 'Improving' }

export function DataDashboard({ job }: { job: Job }) {
  const { climate, soil, vegetation, moisture } = job
  const processing = job.status === 'processing'
  const monthly = climate.monthly.map((m) => ({ ...m, name: MONTHS[m.month - 1] }))

  return (
    <section className="space-y-4">
      <h2 className="text-lg font-semibold text-stone-900">Your land at a glance</h2>

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Card
          title="Climate"
          value={`${climate.mean_temp_c} °C`}
          detail={`${climate.annual_rainfall_mm} mm rain per year, ${climate.dry_months} dry months`}
        />
        <Card
          title="Soil"
          value={`pH ${soil.ph}`}
          detail={`${soil.texture}, ${soil.soc_g_kg} g/kg organic carbon${soil.source === 'fallback' ? ' (estimated)' : ''}`}
        />
        <Card
          title="Vegetation"
          value={vegetation ? TREND_LABEL[vegetation.trend] : processing ? 'Loading…' : 'No data'}
          detail={vegetation ? `Mean NDVI ${vegetation.mean_ndvi}` : 'MODIS NDVI'}
        />
        <Card
          title="Soil moisture"
          value={moisture ? `${Math.round(moisture.mean_volumetric * 100)}%` : processing ? 'Loading…' : 'No data'}
          detail={moisture ? `${moisture.variability} variability` : 'SMAP surface moisture'}
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <ChartPanel title="Monthly rainfall and temperature" source="NASA POWER">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={monthly} margin={{ left: -10, right: -10, top: 4 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e7e5e4" />
              <XAxis dataKey="name" tick={{ fontSize: 11 }} />
              <YAxis yAxisId="rain" tick={{ fontSize: 11 }} />
              <YAxis yAxisId="temp" orientation="right" domain={['auto', 'auto']} tick={{ fontSize: 11 }} />
              <Tooltip />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Bar yAxisId="rain" dataKey="rainfall_mm" name="Rainfall (mm)" fill="#60a5fa" radius={[3, 3, 0, 0]} />
              <Line yAxisId="temp" type="monotone" dataKey="temp_c" name="Temp (°C)" stroke="#f97316" strokeWidth={2} />
            </ComposedChart>
          </ResponsiveContainer>
        </ChartPanel>

        <ChartPanel title="Vegetation health (NDVI)" source="MODIS MOD13A1">
          {vegetation ? (
            <SeriesChart data={vegetation.series} color="#16a34a" domain={[0, 1]} />
          ) : (
            <Pending processing={processing} label="vegetation data" />
          )}
        </ChartPanel>

        <ChartPanel title="Surface soil moisture" source="NASA SMAP SPL3SMP">
          {moisture ? (
            <SeriesChart data={moisture.series} color="#0891b2" domain={[0, 0.6]} />
          ) : (
            <Pending processing={processing} label="soil moisture data" />
          )}
        </ChartPanel>

        <div className="rounded-xl border border-stone-200 bg-white p-4 shadow-sm">
          <h3 className="text-sm font-semibold text-stone-800">Soil composition</h3>
          <p className="text-xs text-stone-400">
            {soil.source === 'soilgrids' ? 'ISRIC SoilGrids, 0–30 cm' : 'Typical lowland profile (SoilGrids unavailable)'}
          </p>
          <div className="mt-4 space-y-3">
            {[
              ['Sand', soil.sand_pct, 'bg-amber-400'],
              ['Silt', soil.silt_pct, 'bg-stone-400'],
              ['Clay', soil.clay_pct, 'bg-orange-700'],
            ].map(([label, pct, color]) => (
              <div key={label as string}>
                <div className="flex justify-between text-xs text-stone-600">
                  <span>{label}</span>
                  <span className="tabular-nums">{pct}%</span>
                </div>
                <div className="mt-1 h-2 rounded-full bg-stone-100">
                  <div className={`h-2 rounded-full ${color}`} style={{ width: `${pct}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
