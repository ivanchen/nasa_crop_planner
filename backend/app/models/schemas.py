from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class DataSourceMeta(BaseModel):
    source: str
    fetched_at: datetime
    period_start: str | None = None
    period_end: str | None = None
    resolution: str | None = None
    cached: bool = False
    # Translation key, resolved to text by the client (e.g. "coarse_resolution").
    disclaimer: str | None = None


class Location(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)


class Priorities(BaseModel):
    water: float = Field(default=1, ge=0)
    drought: float = Field(default=1, ge=0)
    soil_health: float = Field(default=1, ge=0)

    def normalized(self) -> "Priorities":
        total = self.water + self.drought + self.soil_health
        if total <= 0:
            return Priorities(water=1 / 3, drought=1 / 3, soil_health=1 / 3)
        return Priorities(
            water=self.water / total,
            drought=self.drought / total,
            soil_health=self.soil_health / total,
        )


class AnalyzeRequest(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    priorities: Priorities = Field(default_factory=Priorities)


class MonthlyClimate(BaseModel):
    month: int
    temp_c: float
    rainfall_mm: float


class ClimateSummary(BaseModel):
    mean_temp_c: float
    min_temp_c: float
    max_temp_c: float
    annual_rainfall_mm: float
    dry_months: int
    mean_solar_mj_m2_day: float
    monthly: list[MonthlyClimate]
    years: int
    meta: DataSourceMeta


class SoilSummary(BaseModel):
    ph: float
    soc_g_kg: float
    sand_pct: float
    clay_pct: float
    silt_pct: float
    texture: str
    source: Literal["soilgrids", "fallback"]
    meta: DataSourceMeta


class SeriesPoint(BaseModel):
    date: str
    value: float


class VegetationSummary(BaseModel):
    mean_ndvi: float
    trend: Literal["declining", "stable", "improving"]
    series: list[SeriesPoint]
    meta: DataSourceMeta


class MoistureSummary(BaseModel):
    mean_volumetric: float
    variability: Literal["low", "moderate", "high"]
    series: list[SeriesPoint]
    meta: DataSourceMeta


class RotationStep(BaseModel):
    season: str
    window: str
    crop_id: str
    crop: str
    crop_local_name: str
    note: str


class RotationScores(BaseModel):
    water: float
    drought: float
    soil_health: float


class Recommendation(BaseModel):
    rank: int
    rotation: list[str]
    score: float
    scores: RotationScores
    steps: list[RotationStep]
    rationale: str


class JobResponse(BaseModel):
    job_id: str
    status: Literal["processing", "done"]
    progress: str
    analyzed_at: datetime | None = None
    location: Location
    priorities: Priorities
    climate: ClimateSummary
    soil: SoilSummary
    vegetation: VegetationSummary | None = None
    moisture: MoistureSummary | None = None
    recommendations: list[Recommendation] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class QuickReply(BaseModel):
    id: str
    label: str
    action: Literal["text", "gps"] = "text"


class ChatCard(BaseModel):
    type: Literal["location", "climate", "soil", "vegetation", "moisture", "rotation", "warning"]
    data: dict
    provenance: DataSourceMeta | None = None


class ChatMessage(BaseModel):
    id: str
    role: Literal["assistant", "user", "system"]
    text: str
    quick_replies: list[QuickReply] = Field(default_factory=list)
    card: ChatCard | None = None


class CreateSessionRequest(BaseModel):
    lang: Literal["id", "en"] = "id"


class SessionResponse(BaseModel):
    session_id: str
    lang: Literal["id", "en"]
    step: str
    messages: list[ChatMessage]
    llm_enabled: bool = False


class SendMessageRequest(BaseModel):
    text: str = ""
    action_id: str | None = None
    location: Location | None = None


class MessageResponse(BaseModel):
    messages: list[ChatMessage]
    step: str
    processing: bool = False
