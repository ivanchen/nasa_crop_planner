export type Lang = 'id' | 'en'

export const messages = {
  appTitle: { id: 'TaniPilot', en: 'TaniPilot' },
  appSubtitle: { id: 'Wiweka — co-advisor rotasi tanam', en: 'Wiweka — crop rotation co-advisor' },
  inputPlaceholder: { id: 'Ketik pesan…', en: 'Type a message…' },
  inputPlaceholderLocation: {
    id: 'Ketik koordinat, mis. -7.45, 110.40',
    en: 'Type coordinates, e.g. -7.45, 110.40',
  },
  inputPlaceholderConfirm: {
    id: 'Ketik "ya" atau koordinat baru…',
    en: 'Type "yes" or new coordinates…',
  },
  inputPlaceholderCrop: {
    id: 'Mis. padi — atau 30% jagung, 50% padi, 20% kedelai…',
    en: 'E.g. rice — or 30% corn, 50% rice, 20% soybean…',
  },
  inputPlaceholderFree: {
    id: 'Tanya apapun tentang rotasi tanam…',
    en: 'Ask anything about crop rotation…',
  },
  send: { id: 'Kirim', en: 'Send' },
  processing: { id: 'Sedang menganalisis…', en: 'Analyzing…' },
  installHint: {
    id: 'Tambahkan ke layar utama untuk akses GPS lebih mudah.',
    en: 'Add to home screen for easier GPS access.',
  },
  install: { id: 'Pasang', en: 'Install' },
  source: { id: 'Sumber', en: 'Source' },
  fetched: { id: 'Diambil', en: 'Fetched' },
  period: { id: 'Periode', en: 'Period' },
  resolution: { id: 'Resolusi', en: 'Resolution' },
  cached: { id: 'dari cache', en: 'cached' },
  disclaimers: {
    coarse_resolution: {
      id: 'Data perkiraan tingkat wilayah, bukan pengukuran lapangan.',
      en: 'Regional estimate, not a field measurement.',
    },
    modelled_soil: {
      id: 'Model tanah global; verifikasi dengan pengamatan lapangan.',
      en: 'Global soil model; verify with field observations.',
    },
    fallback_soil: {
      id: 'Perkiraan tanah dataran rendah (SoilGrids tidak tersedia).',
      en: 'Typical lowland soil estimate (SoilGrids unavailable).',
    },
  },
  trend: {
    declining: { id: 'menurun', en: 'declining' },
    stable: { id: 'stabil', en: 'stable' },
    improving: { id: 'membaik', en: 'improving' },
  },
  variability: {
    low: { id: 'rendah', en: 'low' },
    moderate: { id: 'sedang', en: 'moderate' },
    high: { id: 'tinggi', en: 'high' },
  },
  rotationScore: { id: 'Skor', en: 'Score' },
  water: { id: 'Air', en: 'Water' },
  drought: { id: 'Kekeringan', en: 'Drought' },
  soilHealth: { id: 'Tanah', en: 'Soil' },
} as const

export function t(lang: Lang, key: keyof typeof messages): string {
  const entry = messages[key]
  if (typeof entry === 'object' && 'id' in entry) return entry[lang]
  return String(entry)
}

export function disclaimer(lang: Lang, key: string | null | undefined): string {
  if (!key) return ''
  const d = messages.disclaimers[key as keyof typeof messages.disclaimers]
  return d ? d[lang] : ''
}
