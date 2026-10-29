from datetime import datetime, timezone

from app.services.satellite_summary import parse_results_csvs, summarize_moisture, summarize_vegetation

NDVI_CSV = "Date,Latitude,Longitude,MOD13A1_061__500m_16_days_NDVI\n" + "\n".join(
    f"{2020 + m // 12}-{m % 12 + 1:02d}-15,-6.5,107.4,{0.7 - 0.01 * m}" for m in range(36)
) + "\n2023-06-01,-6.5,107.4,-3000\n"

SMAP_CSV = (
    "Date,Latitude,Longitude,SPL3SMP_009_Soil_Moisture_Retrieval_Data_AM_soil_moisture,"
    "SPL3SMP_009_Soil_Moisture_Retrieval_Data_PM_soil_moisture_pm\n"
    + "\n".join(f"{2020 + m // 12}-{m % 12 + 1:02d}-10,-6.5,107.4,0.3,0.28" for m in range(24))
    + "\n2022-03-01,-6.5,107.4,-9999,-9999\n"
)


def test_parse_drops_fill_values_and_separates_layers():
    data = parse_results_csvs([NDVI_CSV, SMAP_CSV])
    assert len(data.ndvi) == 36
    assert len(data.moisture) == 48


def test_declining_ndvi_is_detected():
    data = parse_results_csvs([NDVI_CSV])
    summary = summarize_vegetation(data.ndvi, data.fetched_at)
    assert summary is not None
    assert summary.trend == "declining"


def test_vegetation_provenance_reports_observed_period_and_fetch_time():
    data = parse_results_csvs([NDVI_CSV])
    summary = summarize_vegetation(data.ndvi, data.fetched_at, cached=True)
    assert summary.meta.period_start == "2020-01-15"
    assert summary.meta.period_end == "2022-12-15"
    assert summary.meta.fetched_at == data.fetched_at
    assert summary.meta.cached is True


def test_steady_moisture_has_low_variability():
    data = parse_results_csvs([SMAP_CSV])
    summary = summarize_moisture(data.moisture, data.fetched_at)
    assert summary is not None
    assert summary.variability == "low"
    assert 0.27 < summary.mean_volumetric < 0.31


def test_too_few_observations_returns_none():
    assert summarize_vegetation([("2024-01-01", 0.5)], datetime.now(timezone.utc)) is None
