export interface DataSourceMeta {
  source: string
  fetched_at: string
  period_start?: string | null
  period_end?: string | null
  resolution?: string | null
  cached: boolean
  disclaimer?: string | null
}

export interface Location {
  lat: number
  lon: number
}

export interface Priorities {
  water: number
  drought: number
  soil_health: number
}

export interface MonthlyClimate {
  month: number
  temp_c: number
  rainfall_mm: number
}

export interface ClimateSummary {
  mean_temp_c: number
  min_temp_c: number
  max_temp_c: number
  annual_rainfall_mm: number
  dry_months: number
  mean_solar_mj_m2_day: number
  monthly: MonthlyClimate[]
  years: number
}

export interface SoilSummary {
  ph: number
  soc_g_kg: number
  sand_pct: number
  clay_pct: number
  silt_pct: number
  texture: string
  source: 'soilgrids' | 'fallback'
}

export interface SeriesPoint {
  date: string
  value: number
}

export interface VegetationSummary {
  mean_ndvi: number
  trend: 'declining' | 'stable' | 'improving'
  series: SeriesPoint[]
}

export interface MoistureSummary {
  mean_volumetric: number
  variability: 'low' | 'moderate' | 'high'
  series: SeriesPoint[]
}

export interface RotationStep {
  season: string
  window: string
  crop_id: string
  crop: string
  crop_local_name: string
  note: string
}

export interface RotationScores {
  water: number
  drought: number
  soil_health: number
}

export interface Recommendation {
  rank: number
  rotation: string[]
  score: number
  scores: RotationScores
  steps: RotationStep[]
  rationale: string
}

export interface Job {
  job_id: string
  status: 'processing' | 'done'
  progress: string
  location: Location
  priorities: Priorities
  climate: ClimateSummary
  soil: SoilSummary
  vegetation: VegetationSummary | null
  moisture: MoistureSummary | null
  recommendations: Recommendation[]
  warnings: string[]
}
