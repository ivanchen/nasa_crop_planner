from datetime import datetime, timezone

from app.models.schemas import (
    ClimateSummary,
    DataSourceMeta,
    MonthlyClimate,
    MoistureSummary,
    Priorities,
    SoilSummary,
    VegetationSummary,
)
from app.services.rotation_engine import build_seasons, recommend

JAKARTA_RAIN = [330, 395, 282, 205, 157, 148, 112, 75, 107, 153, 220, 300]


def make_meta(source: str = "test") -> DataSourceMeta:
    return DataSourceMeta(source=source, fetched_at=datetime(2026, 10, 2, 7, 30, tzinfo=timezone.utc))


def make_climate(rain=JAKARTA_RAIN, temp=27.5) -> ClimateSummary:
    return ClimateSummary(
        mean_temp_c=temp,
        min_temp_c=temp - 2,
        max_temp_c=temp + 2,
        annual_rainfall_mm=sum(rain),
        dry_months=sum(1 for r in rain if r < 100),
        mean_solar_mj_m2_day=16.5,
        monthly=[MonthlyClimate(month=i + 1, temp_c=temp, rainfall_mm=r) for i, r in enumerate(rain)],
        years=5,
        meta=make_meta("NASA POWER"),
    )


def make_soil(ph=5.8, soc=18.0) -> SoilSummary:
    return SoilSummary(
        ph=ph,
        soc_g_kg=soc,
        sand_pct=28,
        clay_pct=38,
        silt_pct=34,
        texture="clay loam",
        source="soilgrids",
        meta=make_meta("ISRIC SoilGrids"),
    )


def test_seasons_start_at_wettest_window():
    seasons = build_seasons(make_climate())
    assert seasons[0].window == "Dec–Mar"
    assert seasons[0].rainfall_mm > seasons[1].rainfall_mm > seasons[2].rainfall_mm


def test_recommendations_are_ranked_distinct_rotations():
    results = recommend(make_climate(), make_soil(), None, None, Priorities())
    assert len(results) == 5
    assert [r.rank for r in results] == [1, 2, 3, 4, 5]
    assert results[0].score >= results[-1].score
    for r in results:
        assert len(r.rotation) == 3 and len(set(r.rotation)) == 3
        assert len(r.steps) == 3


def test_soil_health_priority_favours_nitrogen_fixers_over_water_priority():
    soil_first = recommend(make_climate(), make_soil(), None, None, Priorities(water=0, drought=0, soil_health=1))
    water_first = recommend(make_climate(), make_soil(), None, None, Priorities(water=1, drought=0, soil_health=0))
    assert soil_first[0].scores.soil_health >= water_first[0].scores.soil_health
    assert water_first[0].scores.water >= soil_first[0].scores.water


def test_drought_priority_avoids_water_hungry_crops_when_moisture_is_volatile():
    volatile = MoistureSummary(mean_volumetric=0.12, variability="high", series=[], meta=make_meta())
    results = recommend(make_climate(), make_soil(), None, volatile, Priorities(water=0, drought=1, soil_health=0))
    assert "Rice" not in results[0].rotation


def test_cool_climate_excludes_tropical_crops():
    results = recommend(make_climate(temp=13), make_soil(), None, None, Priorities())
    assert all("Rice" not in r.rotation and "Cassava" not in r.rotation for r in results)


def test_declining_vegetation_boosts_soil_health_scores():
    declining = VegetationSummary(mean_ndvi=0.5, trend="declining", series=[], meta=make_meta())
    stable = VegetationSummary(mean_ndvi=0.5, trend="stable", series=[], meta=make_meta())
    priorities = Priorities(water=0, drought=0, soil_health=1)
    with_decline = recommend(make_climate(), make_soil(), declining, None, priorities)
    without = recommend(make_climate(), make_soil(), stable, None, priorities)
    assert with_decline[0].scores.soil_health >= without[0].scores.soil_health
