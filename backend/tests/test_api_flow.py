import httpx
import pytest
import respx

from app.config import get_settings
from app.main import app
from app.services import appeears_client, earthdata_auth
from tests.test_rotation_engine import make_climate, make_soil

BASE = "https://appeears.earthdatacloud.nasa.gov/api"

NDVI_CSV = "Date,Latitude,Longitude,MOD13A1_061__500m_16_days_NDVI\n" + "\n".join(
    f"{2021 + m // 12}-{m % 12 + 1:02d}-15,-7.4,110.4,{0.8 - 0.012 * m}" for m in range(36)
)
SMAP_CSV = "Date,Latitude,Longitude,SPL3SMP_009_Soil_Moisture_Retrieval_Data_AM_soil_moisture\n" + "\n".join(
    f"{2021 + m // 12}-{m % 12 + 1:02d}-10,-7.4,110.4,{0.2 + 0.3 * (m % 2)}" for m in range(36)
)


@pytest.fixture(autouse=True)
def stub_nasa_clients(monkeypatch):
    async def climate(lat, lon):
        return make_climate()

    async def soil(lat, lon):
        return make_soil()

    monkeypatch.setattr("app.routers.location.fetch_climate", climate)
    monkeypatch.setattr("app.routers.location.fetch_soil", soil)
    monkeypatch.setattr(appeears_client, "_satellite_cache", appeears_client.TTLCache())
    monkeypatch.setattr(appeears_client, "_layer_cache", appeears_client.TTLCache())
    monkeypatch.setattr(earthdata_auth, "_token", None)


@pytest.fixture
def client():
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")


def use_credentials(monkeypatch, configured: bool):
    monkeypatch.setenv("EARTHDATA_USERNAME", "user" if configured else "")
    monkeypatch.setenv("EARTHDATA_PASSWORD", "pass" if configured else "")
    get_settings.cache_clear()


def mock_appeears(mock: respx.MockRouter, statuses: list[str]):
    mock.get(f"{BASE}/product").respond(
        json=[
            {"Product": "MOD13A1", "Version": "061", "Available": True, "Deleted": False},
            {"Product": "SPL3SMP", "Version": "009", "Available": True, "Deleted": False},
        ]
    )
    mock.get(f"{BASE}/product/MOD13A1.061").respond(json={"_500m_16_days_NDVI": {}, "_500m_16_days_EVI": {}})
    mock.get(f"{BASE}/product/SPL3SMP.009").respond(json={"Soil_Moisture_Retrieval_Data_AM_soil_moisture": {}})
    mock.post(f"{BASE}/login").respond(json={"token": "t"})
    mock.post(f"{BASE}/task").respond(json={"task_id": "abc", "status": "pending"})
    mock.get(f"{BASE}/task/abc").side_effect = [httpx.Response(200, json={"status": s}) for s in statuses]
    mock.get(f"{BASE}/bundle/abc").respond(
        json={
            "files": [
                {"file_id": "f1", "file_name": "Point-MOD13A1-061-results.csv"},
                {"file_id": "f2", "file_name": "Point-SPL3SMP-009-results.csv"},
                {"file_id": "f3", "file_name": "README.md"},
            ]
        }
    )
    mock.get(f"{BASE}/bundle/abc/f1").respond(text=NDVI_CSV)
    mock.get(f"{BASE}/bundle/abc/f2").respond(text=SMAP_CSV)


async def test_without_credentials_returns_recommendations_immediately(client, monkeypatch):
    use_credentials(monkeypatch, configured=False)
    async with client:
        response = await client.post("/api/analyze", json={"lat": -7.4, "lon": 110.4})
    body = response.json()
    assert body["status"] == "done"
    assert len(body["recommendations"]) == 5
    assert any("credentials" in w for w in body["warnings"])


async def test_appeears_flow_polls_then_scores_with_satellite_data(client, monkeypatch):
    use_credentials(monkeypatch, configured=True)
    with respx.mock(assert_all_called=False) as mock:
        mock_appeears(mock, statuses=["processing", "done"])
        async with client:
            started = (await client.post("/api/analyze", json={"lat": -7.4, "lon": 110.4})).json()
            assert started["status"] == "processing"
            assert started["recommendations"] == []

            pending = (await client.get(f"/api/tasks/{started['job_id']}")).json()
            assert pending["status"] == "processing"

            finished = (await client.get(f"/api/tasks/{started['job_id']}")).json()

    assert finished["status"] == "done"
    assert finished["vegetation"]["trend"] == "declining"
    assert finished["moisture"]["variability"] == "high"
    assert len(finished["recommendations"]) == 5
    assert finished["analyzed_at"] is not None
    assert finished["vegetation"]["meta"]["cached"] is False
    assert finished["vegetation"]["meta"]["source"].startswith("NASA MODIS")


async def test_failed_appeears_task_degrades_to_climate_and_soil(client, monkeypatch):
    use_credentials(monkeypatch, configured=True)
    with respx.mock(assert_all_called=False) as mock:
        mock_appeears(mock, statuses=["error"])
        async with client:
            started = (await client.post("/api/analyze", json={"lat": -7.4, "lon": 110.4})).json()
            finished = (await client.get(f"/api/tasks/{started['job_id']}")).json()

    assert finished["status"] == "done"
    assert finished["vegetation"] is None
    assert any("failed" in w for w in finished["warnings"])


async def test_second_analysis_of_same_location_uses_cached_satellite_data(client, monkeypatch):
    use_credentials(monkeypatch, configured=True)
    with respx.mock(assert_all_called=False) as mock:
        mock_appeears(mock, statuses=["done"])
        async with client:
            first = (await client.post("/api/analyze", json={"lat": -7.4, "lon": 110.4})).json()
            await client.get(f"/api/tasks/{first['job_id']}")
            second = (await client.post("/api/analyze", json={"lat": -7.4, "lon": 110.4})).json()

    assert second["status"] == "done"
    assert second["vegetation"] is not None
    assert second["vegetation"]["meta"]["cached"] is True
    assert second["vegetation"]["meta"]["fetched_at"] is not None


async def test_unknown_job_returns_404(client):
    async with client:
        response = await client.get("/api/tasks/missing")
    assert response.status_code == 404
