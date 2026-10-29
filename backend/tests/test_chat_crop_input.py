import pytest

from app.services.chat_flow import _resolve_crop, handle_message, start_session


@pytest.mark.parametrize(
    "text,expected_id",
    [
        ("padi", "rice"),
        ("Padi", "rice"),
        ("jagung", "corn"),
        ("kedelai", "soybean"),
        ("kacang tanah", "peanut"),
        ("bera", "fallow"),
        ("belum tanam", "fallow"),
        ("cabai", "chili"),
    ],
)
def test_resolve_crop_from_text(text, expected_id):
    resolved = _resolve_crop(None, text)
    assert resolved is not None
    assert resolved[0] == expected_id


def test_resolve_crop_from_button():
    resolved = _resolve_crop("crop_rice", "")
    assert resolved == ("rice", "Padi")


async def test_manual_crop_at_ask_last_crop():
    session = start_session("id")
    await handle_message(session, text="-7.45, 110.40")
    await handle_message(session, text="ya")
    assert session.step == "ask_last_crop"
    await handle_message(session, text="jagung")
    assert session.last_crop == "corn"
    assert session.step == "ask_priorities"
    assert "Jagung" in session.messages[-2].text


async def test_custom_crop_accepted():
    session = start_session("id")
    await handle_message(session, text="-7.45, 110.40")
    await handle_message(session, text="ya")
    await handle_message(session, text="Timun")
    assert session.last_crop == "timun"
    assert session.step == "ask_priorities"
    assert "Timun" in session.messages[-2].text


def test_resolve_mixed_crop_percentages():
    resolved = _resolve_crop(None, "30% jagung, 50% padi, 20% kedelai")
    assert resolved is not None
    assert resolved[1] == "30% Jagung, 50% Padi, 20% Kedelai"
    assert resolved[0] == resolved[1]


async def test_mixed_crop_at_ask_last_crop():
    session = start_session("id")
    await handle_message(session, text="-7.45, 110.40")
    await handle_message(session, text="ya")
    await handle_message(session, text="30% jagung, 50% padi, 20% kedelai")
    assert session.last_crop == "30% Jagung, 50% Padi, 20% Kedelai"
    assert session.step == "ask_priorities"
    assert "30% Jagung" in session.messages[-2].text
    assert "20% Kedelai" in session.messages[-2].text


def test_resolve_multiple_crops_without_percentages():
    resolved = _resolve_crop(None, "padi dan jagung")
    assert resolved is not None
    assert resolved[1] == "Padi, Jagung"
