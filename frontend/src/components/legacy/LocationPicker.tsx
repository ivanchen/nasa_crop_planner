import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png'
import markerIcon from 'leaflet/dist/images/marker-icon.png'
import markerShadow from 'leaflet/dist/images/marker-shadow.png'
import { MapContainer, Marker, TileLayer, useMap, useMapEvents } from 'react-leaflet'
import { useEffect } from 'react'
import { PRESETS } from '../constants'
import type { Location } from '../types'

const pin = L.icon({
  iconUrl: markerIcon,
  iconRetinaUrl: markerIcon2x,
  shadowUrl: markerShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
})

const INDONESIA = { latMin: -11.5, latMax: 6.5, lonMin: 94.5, lonMax: 141.5 }

function isInIndonesia({ lat, lon }: Location) {
  return lat >= INDONESIA.latMin && lat <= INDONESIA.latMax && lon >= INDONESIA.lonMin && lon <= INDONESIA.lonMax
}

function ClickHandler({ onChange }: { onChange: (l: Location) => void }) {
  useMapEvents({
    click(e) {
      onChange({ lat: round(e.latlng.lat), lon: round(e.latlng.lng) })
    },
  })
  return null
}

function Recenter({ location }: { location: Location }) {
  const map = useMap()
  useEffect(() => {
    map.panTo([location.lat, location.lon])
  }, [map, location.lat, location.lon])
  return null
}

const round = (n: number) => Math.round(n * 1000) / 1000

interface Props {
  location: Location
  onChange: (location: Location) => void
}

export function LocationPicker({ location, onChange }: Props) {
  const setCoordinate = (key: keyof Location, raw: string) => {
    const value = parseFloat(raw)
    if (Number.isNaN(value)) return
    const limit = key === 'lat' ? 90 : 180
    onChange({ ...location, [key]: Math.max(-limit, Math.min(limit, value)) })
  }

  return (
    <section className="rounded-2xl border border-stone-200 bg-white p-5 shadow-sm">
      <h2 className="text-lg font-semibold text-stone-900">1. Choose your farm location</h2>
      <p className="mt-1 text-sm text-stone-500">Click the map or enter coordinates.</p>

      <div className="mt-4 h-64 overflow-hidden rounded-xl">
        <MapContainer center={[location.lat, location.lon]} zoom={6} scrollWheelZoom className="h-full">
          <TileLayer
            attribution="&copy; OpenStreetMap contributors"
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <Marker position={[location.lat, location.lon]} icon={pin} />
          <ClickHandler onChange={onChange} />
          <Recenter location={location} />
        </MapContainer>
      </div>

      <div className="mt-4 grid grid-cols-2 gap-3">
        {(['lat', 'lon'] as const).map((key) => (
          <label key={key} className="text-sm font-medium text-stone-600">
            {key === 'lat' ? 'Latitude' : 'Longitude'}
            <input
              type="number"
              step="0.001"
              value={location[key]}
              onChange={(e) => setCoordinate(key, e.target.value)}
              className="mt-1 w-full rounded-lg border border-stone-300 px-3 py-2 text-stone-900 focus:border-green-600 focus:outline-none focus:ring-2 focus:ring-green-200"
            />
          </label>
        ))}
      </div>

      <div className="mt-3 flex flex-wrap gap-2">
        {PRESETS.map((p) => (
          <button
            key={p.name}
            type="button"
            onClick={() => onChange(p.location)}
            className="rounded-full border border-green-200 bg-green-50 px-3 py-1 text-xs font-medium text-green-800 transition hover:bg-green-100"
          >
            {p.name}
          </button>
        ))}
      </div>

      {!isInIndonesia(location) && (
        <p className="mt-3 rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-800">
          This location is outside Indonesia. The crop list is tuned for Indonesian conditions, so results may be less
          relevant.
        </p>
      )}
    </section>
  )
}
