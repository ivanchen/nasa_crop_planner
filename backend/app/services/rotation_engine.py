import itertools
import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel

from app.models.schemas import (
    ClimateSummary,
    MoistureSummary,
    Priorities,
    Recommendation,
    RotationScores,
    RotationStep,
    SoilSummary,
    VegetationSummary,
)

CROPS_PATH = Path(__file__).resolve().parent.parent / "data" / "crops.json"

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
SEASONS_PER_YEAR = 3
MONTHS_PER_SEASON = 12 // SEASONS_PER_YEAR

MIN_CROP_FIT = 0.15
MAX_ROTATIONS_PER_CROP_SET = 2

# Fraction of rainfall that actually reaches the root zone, by soil type.
EFFECTIVE_RAIN_DEFAULT = 0.7
EFFECTIVE_RAIN_SANDY = 0.6
SANDY_THRESHOLD_PCT = 60

IRRIGATION_SCALE_MM = 1000
DEMAND_FLOOR_MM = 900
DEMAND_CEILING_MM = 2400
IRRIGATION_WEIGHT = 0.6

WET_MONTH_MM = 200
MODERATE_MONTH_MM = 100

MOISTURE_VARIABILITY_PENALTY = {"low": 0, "moderate": 8, "high": 16}
LOW_MOISTURE_THRESHOLD = 0.15
LOW_MOISTURE_PENALTY = 6

LOW_SOC_G_KG = 12
SOIL_NEED_BOOST = 1.5
SOIL_DIVERSITY_BONUS = {1: -6, 2: 2, 3: 6}
SAME_FAMILY_PENALTY = 8
NITROGEN_AFTER_HEAVY_FEEDER_BONUS = 6
RESTORATION_NEED_BONUS = 4


class TempRange(BaseModel):
    min: float
    opt_min: float
    opt_max: float
    max: float


class Crop(BaseModel):
    id: str
    name: str
    local_name: str
    family: str
    role: str
    temp_c: TempRange
    ph: TempRange
    water_mm: float
    drought_tolerance: float
    soil_improvement: float
    nitrogen_fixing: bool
    heavy_feeder: bool
    season: str
    cycle_days: int


@dataclass
class Season:
    index: int
    window: str
    label: str
    rainfall_mm: float
    wetness: str


@lru_cache
def load_crops() -> tuple[Crop, ...]:
    with CROPS_PATH.open() as f:
        return tuple(Crop(**c) for c in json.load(f))


def build_seasons(climate: ClimateSummary) -> list[Season]:
    rainfall = [m.rainfall_mm for m in sorted(climate.monthly, key=lambda m: m.month)]
    span = SEASONS_PER_YEAR * MONTHS_PER_SEASON

    def window_total(start: int) -> float:
        return sum(rainfall[(start + i) % span] for i in range(MONTHS_PER_SEASON))

    first_start = max(range(span), key=window_total)
    seasons = []
    for k in range(SEASONS_PER_YEAR):
        start = (first_start + k * MONTHS_PER_SEASON) % span
        end = (start + MONTHS_PER_SEASON - 1) % span
        total = window_total(start)
        monthly_avg = total / MONTHS_PER_SEASON
        wetness = "wet" if monthly_avg >= WET_MONTH_MM else "moderate" if monthly_avg >= MODERATE_MONTH_MM else "dry"
        seasons.append(
            Season(
                index=k,
                window=f"{MONTH_NAMES[start]}–{MONTH_NAMES[end]}",
                label=f"Season {k + 1} ({wetness})",
                rainfall_mm=total,
                wetness=wetness,
            )
        )
    return seasons


def _trapezoid_fit(value: float, r: TempRange) -> float:
    if value <= r.min or value >= r.max:
        return 0.0
    if value < r.opt_min:
        return (value - r.min) / (r.opt_min - r.min)
    if value > r.opt_max:
        return (r.max - value) / (r.max - r.opt_max)
    return 1.0


def crop_fit(crop: Crop, climate: ClimateSummary, soil: SoilSummary) -> float:
    return _trapezoid_fit(climate.mean_temp_c, crop.temp_c) * _trapezoid_fit(soil.ph, crop.ph)


def _clamp(value: float, low: float = 0, high: float = 100) -> float:
    return max(low, min(high, value))


@dataclass
class Context:
    seasons: list[Season]
    effective_rain: float
    moisture_penalty: float
    restoration_needed: bool
    fits: dict[str, float]


def _build_context(
    crops: list[Crop],
    climate: ClimateSummary,
    soil: SoilSummary,
    vegetation: VegetationSummary | None,
    moisture: MoistureSummary | None,
) -> Context:
    moisture_penalty = 0.0
    if moisture is not None:
        moisture_penalty = MOISTURE_VARIABILITY_PENALTY[moisture.variability]
        if moisture.mean_volumetric < LOW_MOISTURE_THRESHOLD:
            moisture_penalty += LOW_MOISTURE_PENALTY

    return Context(
        seasons=build_seasons(climate),
        effective_rain=EFFECTIVE_RAIN_SANDY if soil.sand_pct >= SANDY_THRESHOLD_PCT else EFFECTIVE_RAIN_DEFAULT,
        moisture_penalty=moisture_penalty,
        restoration_needed=(vegetation is not None and vegetation.trend == "declining")
        or soil.soc_g_kg < LOW_SOC_G_KG,
        fits={c.id: crop_fit(c, climate, soil) for c in crops},
    )


def _irrigation_gap(crop: Crop, season: Season, ctx: Context) -> float:
    return max(0.0, crop.water_mm - season.rainfall_mm * ctx.effective_rain)


def _score_water(sequence: tuple[Crop, ...], ctx: Context) -> float:
    gap = sum(_irrigation_gap(c, s, ctx) for c, s in zip(sequence, ctx.seasons))
    demand = sum(c.water_mm for c in sequence)
    irrigation_score = _clamp(100 * (1 - gap / IRRIGATION_SCALE_MM))
    demand_score = _clamp(100 * (DEMAND_CEILING_MM - demand) / (DEMAND_CEILING_MM - DEMAND_FLOOR_MM))
    return IRRIGATION_WEIGHT * irrigation_score + (1 - IRRIGATION_WEIGHT) * demand_score


def _score_drought(sequence: tuple[Crop, ...], ctx: Context) -> float:
    max_rain = max(s.rainfall_mm for s in ctx.seasons) or 1
    weights = [1 + (1 - s.rainfall_mm / max_rain) for s in ctx.seasons]
    adjusted = [
        c.drought_tolerance - ctx.moisture_penalty * (1 - c.drought_tolerance / 100) for c in sequence
    ]
    return _clamp(sum(w * a for w, a in zip(weights, adjusted)) / sum(weights))


def _score_soil_health(sequence: tuple[Crop, ...], ctx: Context) -> float:
    base = sum(c.soil_improvement for c in sequence) / len(sequence)
    bonus = SOIL_DIVERSITY_BONUS[len({c.family for c in sequence})]

    n = len(sequence)
    for i, crop in enumerate(sequence):
        following = sequence[(i + 1) % n]
        if crop.family != "cover" and crop.family == following.family:
            bonus -= SAME_FAMILY_PENALTY
        if crop.heavy_feeder and following.nitrogen_fixing:
            bonus += NITROGEN_AFTER_HEAVY_FEEDER_BONUS
        if ctx.restoration_needed and crop.nitrogen_fixing:
            bonus += RESTORATION_NEED_BONUS

    if ctx.restoration_needed:
        bonus *= SOIL_NEED_BOOST
    return _clamp(base + bonus)


def _step_note(index: int, sequence: tuple[Crop, ...], ctx: Context) -> str:
    crop = sequence[index]
    previous = sequence[index - 1]
    season = ctx.seasons[index]
    gap = _irrigation_gap(crop, season, ctx)
    notes = []

    if crop.id == "fallow":
        notes.append("A resting cover crop rebuilds organic matter and soil structure.")
    elif crop.nitrogen_fixing and previous.heavy_feeder:
        notes.append(f"Fixes nitrogen to replenish what {previous.name.lower()} removed.")
    elif crop.nitrogen_fixing:
        notes.append("Fixes atmospheric nitrogen, reducing fertilizer needs.")

    if gap <= 0.1 * crop.water_mm:
        notes.append("Rainfall in this window covers its water need.")
    elif gap <= 0.5 * crop.water_mm:
        notes.append(f"Needs roughly {round(gap, -1):.0f} mm of supplementary irrigation.")
    else:
        notes.append(f"High irrigation need (about {round(gap, -1):.0f} mm); best kept to irrigated plots.")

    if crop.drought_tolerance >= 65 and season.wetness == "dry":
        notes.append("Tolerates the dry spell in this window.")
    return " ".join(notes)


def _rationale(
    sequence: tuple[Crop, ...], scores: RotationScores, ctx: Context
) -> str:
    gap = sum(_irrigation_gap(c, s, ctx) for c, s in zip(sequence, ctx.seasons))
    strongest = max(
        (("water efficiency", scores.water), ("drought resilience", scores.drought), ("soil health", scores.soil_health)),
        key=lambda item: item[1],
    )
    parts = [f"Strongest on {strongest[0]} ({strongest[1]:.0f}/100)."]
    if any(c.nitrogen_fixing and c.id != "fallow" for c in sequence):
        parts.append("Includes a nitrogen-fixing legume.")
    if gap < 50:
        parts.append("Largely rain-fed across the year.")
    else:
        parts.append(f"Needs about {round(gap, -1):.0f} mm of supplementary irrigation per year.")
    if ctx.restoration_needed:
        parts.append("Favoured because local soil or vegetation data show a need for restoration.")
    return " ".join(parts)


def recommend(
    climate: ClimateSummary,
    soil: SoilSummary,
    vegetation: VegetationSummary | None,
    moisture: MoistureSummary | None,
    priorities: Priorities,
    top_n: int = 5,
) -> list[Recommendation]:
    weights = priorities.normalized()
    crops = list(load_crops())
    ctx = _build_context(crops, climate, soil, vegetation, moisture)
    candidates = [c for c in crops if ctx.fits[c.id] >= MIN_CROP_FIT]

    scored = []
    for sequence in itertools.permutations(candidates, SEASONS_PER_YEAR):
        scores = RotationScores(
            water=round(_score_water(sequence, ctx), 1),
            drought=round(_score_drought(sequence, ctx), 1),
            soil_health=round(_score_soil_health(sequence, ctx), 1),
        )
        weighted = (
            weights.water * scores.water + weights.drought * scores.drought + weights.soil_health * scores.soil_health
        )
        fit = sum(ctx.fits[c.id] for c in sequence) / len(sequence)
        scored.append((weighted * (0.8 + 0.2 * fit), sequence, scores))

    scored.sort(key=lambda item: item[0], reverse=True)

    picked = []
    seen_sets: dict[frozenset[str], int] = {}
    for total, sequence, scores in scored:
        key = frozenset(c.id for c in sequence)
        if seen_sets.get(key, 0) >= MAX_ROTATIONS_PER_CROP_SET:
            continue
        seen_sets[key] = seen_sets.get(key, 0) + 1
        picked.append((total, sequence, scores))
        if len(picked) == top_n:
            break

    return [
        Recommendation(
            rank=rank,
            rotation=[c.name for c in sequence],
            score=round(total, 1),
            scores=scores,
            steps=[
                RotationStep(
                    season=ctx.seasons[i].label,
                    window=ctx.seasons[i].window,
                    crop_id=crop.id,
                    crop=crop.name,
                    crop_local_name=crop.local_name,
                    note=_step_note(i, sequence, ctx),
                )
                for i, crop in enumerate(sequence)
            ],
            rationale=_rationale(sequence, scores, ctx),
        )
        for rank, (total, sequence, scores) in enumerate(picked, start=1)
    ]
