import pytest

from app.services.chat_flow import _parse_location, handle_message, start_session


@pytest.mark.parametrize(
    "text,lat,lon",
    [
        ("-7.45, 110.40", -7.45, 110.40),
        ("-7.45 110.40", -7.45, 110.40),
        ("lat: -7.45, lon: 110.40", -7.45, 110.40),
        ("latitude -6.2 longitude 106.8", -6.2, 106.8),
    ],
)
def test_parse_location_formats(text, lat, lon):
    loc = _parse_location(text)
    assert loc is not None
    assert loc.lat == lat
    assert loc.lon == lon


async def test_manual_coordinates_at_ask_location():
    session = start_session("id")
    await handle_message(session, text="-7.45, 110.40")
    assert session.step == "confirm_location"
    assert session.location.lat == -7.45


async def test_invalid_text_shows_format_hint_not_gemini():
    session = start_session("id")
    before = len(session.messages)
    await handle_message(session, text="Halo pak")
    reply = session.messages[-1].text
    assert session.step == "ask_location"
    assert "koordinat" in reply.lower() or "coordinate" in reply.lower()
    assert "belum punya data" not in reply.lower()
    assert len(session.messages) > before


async def test_confirm_location_with_ya_text():
    session = start_session("id")
    await handle_message(session, text="-7.45, 110.40")
    await handle_message(session, text="ya")
    assert session.step == "ask_last_crop"
