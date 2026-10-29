import httpx
import pytest
import respx

from app.config import get_settings
from app.main import app
from tests.test_api_flow import mock_appeears, use_credentials
from tests.test_rotation_engine import make_climate, make_soil

BASE = "https://appeears.earthdatacloud.nasa.gov/api"


@pytest.fixture(autouse=True)
def stub_nasa(monkeypatch):
    async def climate(lat, lon):
        return make_climate()

    async def soil(lat, lon):
        return make_soil()

    monkeypatch.setattr("app.services.chat_flow.fetch_climate", climate)
    monkeypatch.setattr("app.services.chat_flow.fetch_soil", soil)


@pytest.fixture
def client():
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")


async def _through_priorities(client: httpx.AsyncClient, session_id: str):
    await client.post(
        f"/api/chat/session/{session_id}/message",
        json={"action_id": "preset_klaten"},
    )
    await client.post(
        f"/api/chat/session/{session_id}/message",
        json={"action_id": "confirm_yes"},
    )
    await client.post(
        f"/api/chat/session/{session_id}/message",
        json={"action_id": "crop_rice"},
    )
    return await client.post(
        f"/api/chat/session/{session_id}/message",
        json={"action_id": "prio_balanced"},
    )


async def test_create_session_returns_welcome_in_indonesian(client):
    async with client:
        r = await client.post("/api/chat/session", json={"lang": "id"})
    body = r.json()
    assert r.status_code == 200
    assert body["lang"] == "id"
    assert "TaniPilot" in body["messages"][0]["text"]
    assert any(q["id"] == "use_gps" for q in body["messages"][-1]["quick_replies"])


async def test_full_structured_flow_completes(client, monkeypatch):
    monkeypatch.setenv("EARTHDATA_USERNAME", "")
    monkeypatch.setenv("EARTHDATA_PASSWORD", "")
    get_settings.cache_clear()
    async with client:
        session = (await client.post("/api/chat/session", json={"lang": "id"})).json()
        sid = session["session_id"]
        await _through_priorities(client, sid)
        for _ in range(30):
            state = (await client.get(f"/api/chat/session/{sid}")).json()
            if state["step"] == "free_chat":
                break
            await asyncio.sleep(0.2)
        else:
            pytest.fail("analysis did not complete")

        cards = [m["card"]["type"] for m in state["messages"] if m.get("card")]
        assert "climate" in cards
        assert "soil" in cards
        assert "rotation" in cards
        climate_cards = [m["card"] for m in state["messages"] if m.get("card") and m["card"]["type"] == "climate"]
        assert climate_cards and climate_cards[0]["provenance"] is not None


async def test_gps_location_via_message_body(client):
    async with client:
        session = (await client.post("/api/chat/session", json={"lang": "en"})).json()
        r = await client.post(
            f"/api/chat/session/{session['session_id']}/message",
            json={"action_id": "use_gps", "location": {"lat": -7.45, "lon": 110.4}},
        )
    assert r.json()["messages"][-1]["card"]["type"] == "location"


async def test_unknown_session_returns_404(client):
    async with client:
        r = await client.get("/api/chat/session/missing")
    assert r.status_code == 404


import asyncio  # noqa: E402 — placed after test that needs it at module level for sleep
