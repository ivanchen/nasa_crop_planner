import asyncio
import json
import re
import uuid
from functools import lru_cache
from pathlib import Path
from typing import Literal

from app.i18n.messages import PRESETS, qr, t
from app.models.schemas import (
    AnalyzeRequest,
    ChatCard,
    ChatMessage,
    Location,
    Priorities,
    QuickReply,
)
from app.services import chat_sessions, jobs
from app.services.chat_agent import reply_freeform
from app.services.chat_sessions import ChatSession
from app.services.power_client import ClimateUnavailableError, fetch_climate
from app.services.soilgrids_client import fetch_soil

Lang = Literal["id", "en"]

COORD_RE = re.compile(r"(-?\d+\.?\d*)\s*[,;\s]\s*(-?\d+\.?\d*)")
COORD_LABELED_RE = re.compile(
    r"lat(?:itude)?[:\s=]+(-?\d+\.?\d*).*?lon(?:g(?:itude)?)?[:\s=]+(-?\d+\.?\d*)", re.IGNORECASE
)
YES_WORDS = {"ya", "yes", "benar", "ok", "oke", "betul", "correct", "y"}
INDONESIA = {"lat_min": -11.5, "lat_max": 6.5, "lon_min": 94.5, "lon_max": 141.5}

ACTION_MAP = {
    "use_gps": None,
    "confirm_yes": "confirm_yes",
    "confirm_change": "confirm_change",
    "crop_rice": "rice",
    "crop_corn": "corn",
    "crop_soybean": "soybean",
    "crop_peanut": "peanut",
    "crop_cassava": "cassava",
    "crop_none": "fallow",
    "prio_water": Priorities(water=1, drought=0, soil_health=0),
    "prio_drought": Priorities(water=0, drought=1, soil_health=0),
    "prio_soil": Priorities(water=0, drought=0, soil_health=1),
    "prio_balanced": Priorities(water=1, drought=1, soil_health=1),
    "new_analysis": "new_analysis",
    "change_priorities": "change_priorities",
}


def _msg(
    role: Literal["assistant", "user", "system"],
    text: str,
    quick_replies: list[QuickReply] | None = None,
    card: ChatCard | None = None,
) -> ChatMessage:
    return ChatMessage(
        id=uuid.uuid4().hex,
        role=role,
        text=text,
        quick_replies=quick_replies or [],
        card=card,
    )


def _qrs(session: ChatSession, *keys: str) -> list[QuickReply]:
    return [QuickReply(id=k, label=qr(session.lang, k), action="gps" if k == "use_gps" else "text") for k in keys]


def _in_indonesia(loc: Location) -> bool:
    return (
        INDONESIA["lat_min"] <= loc.lat <= INDONESIA["lat_max"]
        and INDONESIA["lon_min"] <= loc.lon <= INDONESIA["lon_max"]
    )


def _parse_location(text: str) -> Location | None:
    cleaned = text.strip()
    for pattern in (COORD_LABELED_RE, COORD_RE):
        m = pattern.search(cleaned)
        if m:
            lat, lon = float(m.group(1)), float(m.group(2))
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                return Location(lat=round(lat, 3), lon=round(lon, 3))
    return None


def _is_yes(text: str) -> bool:
    return text.strip().lower() in YES_WORDS


CROPS_PATH = Path(__file__).resolve().parent.parent / "data" / "crops.json"
CROP_ALIASES: dict[str, str] = {
    "bera": "fallow",
    "garing": "fallow",
    "kosong": "fallow",
    "belum tanam": "fallow",
    "ubi kayu": "cassava",
    "cabe": "chili",
    "cabai rawit": "chili",
    "maize": "corn",
    "kacang": "peanut",
}


@lru_cache
def _crops_data() -> tuple[dict, ...]:
    return tuple(json.loads(CROPS_PATH.read_text()))


def _crop_display(crop_id: str) -> str:
    for crop in _crops_data():
        if crop["id"] == crop_id:
            return crop["local_name"]
    return crop_id


@lru_cache
def _crop_lookup() -> dict[str, str]:
    lookup: dict[str, str] = dict(CROP_ALIASES)
    for crop in _crops_data():
        crop_id = crop["id"]
        for label in (crop["id"], crop["name"], crop["local_name"]):
            lookup[label.lower()] = crop_id
        for part in crop["local_name"].lower().split("/"):
            lookup[part.strip()] = crop_id
    return lookup


MIX_PART_RE = re.compile(r"(\d+)\s*%\s*([^,]+)")


def _match_crop_token(token: str) -> tuple[str, str] | None:
    cleaned = token.strip().lower()
    if not cleaned:
        return None

    lookup = _crop_lookup()
    if cleaned in lookup:
        crop_id = lookup[cleaned]
        return crop_id, _crop_display(crop_id)

    for alias, crop_id in sorted(lookup.items(), key=lambda item: len(item[0]), reverse=True):
        if len(alias) >= 3 and alias in cleaned:
            return crop_id, _crop_display(crop_id)

    return cleaned, token.strip()


def _find_crops_in_text(text: str) -> list[tuple[str, str]]:
    """Return unique crops mentioned in text, ordered by first appearance."""
    text_lower = text.lower()
    lookup = _crop_lookup()
    matches: list[tuple[int, str, str]] = []
    used_spans: list[tuple[int, int]] = []

    for alias, crop_id in sorted(lookup.items(), key=lambda item: len(item[0]), reverse=True):
        if len(alias) < 3:
            continue
        start = 0
        while True:
            idx = text_lower.find(alias, start)
            if idx == -1:
                break
            end = idx + len(alias)
            if not any(not (end <= span_start or idx >= span_end) for span_start, span_end in used_spans):
                matches.append((idx, crop_id, _crop_display(crop_id)))
                used_spans.append((idx, end))
            start = idx + 1

    matches.sort(key=lambda item: item[0])
    seen: set[str] = set()
    ordered: list[tuple[str, str]] = []
    for _, crop_id, display in matches:
        if crop_id in seen:
            continue
        seen.add(crop_id)
        ordered.append((crop_id, display))
    return ordered


def _parse_mixed_crop_input(text: str) -> tuple[str, str] | None:
    parts = MIX_PART_RE.findall(text)
    if len(parts) < 2:
        return None

    entries: list[tuple[int, str]] = []
    for pct_raw, name in parts:
        matched = _match_crop_token(name)
        if not matched:
            continue
        entries.append((int(pct_raw), matched[1]))

    if len(entries) < 2:
        return None

    display = ", ".join(f"{pct}% {name}" for pct, name in entries)
    return display, display


def _resolve_crop(action_id: str | None, text: str) -> tuple[str, str] | None:
    """Return (stored_value, display_name) or None if unresolved."""
    if action_id and action_id.startswith("crop_"):
        mapped = ACTION_MAP.get(action_id)
        if isinstance(mapped, str):
            return mapped, _crop_display(mapped)

    cleaned = text.strip()
    if not cleaned:
        return None

    mixed = _parse_mixed_crop_input(cleaned)
    if mixed:
        return mixed

    lookup = _crop_lookup()
    lowered = cleaned.lower()
    if lowered in lookup:
        crop_id = lookup[lowered]
        return crop_id, _crop_display(crop_id)

    crops_in_text = _find_crops_in_text(cleaned)
    if len(crops_in_text) >= 2:
        display = ", ".join(display for _, display in crops_in_text)
        return display, display
    if len(crops_in_text) == 1:
        crop_id, display = crops_in_text[0]
        return crop_id, display

    matched = _match_crop_token(cleaned)
    if matched:
        return matched

    return lowered, cleaned


def _trend_key(trend: str) -> str:
    return {"declining": "trend_declining", "stable": "trend_stable", "improving": "trend_improving"}[trend]


def _var_key(v: str) -> str:
    return {"low": "var_low", "moderate": "var_moderate", "high": "var_high"}[v]


def start_session(lang: Lang) -> ChatSession:
    session = chat_sessions.create(lang)
    chat_sessions.add_message(session, _msg("assistant", t(lang, "welcome")))
    chat_sessions.add_message(
        session,
        _msg("assistant", t(lang, "ask_location"), _qrs(session, "use_gps", "preset_klaten", "preset_karawang", "preset_kupang")),
    )
    return session


async def handle_message(
    session: ChatSession,
    text: str = "",
    action_id: str | None = None,
    gps_location: Location | None = None,
) -> list[ChatMessage]:
    if session.analyzing:
        return []

    outgoing: list[ChatMessage] = []
    lang = session.lang

    if text.strip():
        user = _msg("user", text.strip())
        chat_sessions.add_message(session, user)
        outgoing.append(user)

    if session.step == "free_chat":
        if not session.job_id:
            session.step = "ask_location"
            bot = _msg(
                "assistant",
                t(lang, "need_location_first"),
                _qrs(session, "use_gps", "preset_klaten", "preset_karawang", "preset_kupang"),
            )
            chat_sessions.add_message(session, bot)
            outgoing.append(bot)
            return outgoing
        if not text.strip() and not action_id:
            return outgoing
        reply = await reply_freeform(session, text)
        bot = _msg("assistant", reply, _qrs(session, "new_analysis", "change_priorities"))
        chat_sessions.add_message(session, bot)
        outgoing.append(bot)
        return outgoing

    if action_id == "new_analysis":
        session.step = "ask_location"
        session.location = None
        session.job_id = None
        bot = _msg("assistant", t(lang, "ask_location"), _qrs(session, "use_gps", "preset_klaten", "preset_karawang", "preset_kupang"))
        chat_sessions.add_message(session, bot)
        outgoing.append(bot)
        return outgoing

    if action_id == "change_priorities":
        session.step = "ask_priorities"
        bot = _msg("assistant", t(lang, "ask_priorities"), _qrs(session, "prio_water", "prio_drought", "prio_soil", "prio_balanced"))
        chat_sessions.add_message(session, bot)
        outgoing.append(bot)
        return outgoing

    if session.step == "ask_location":
        loc = gps_location
        label = ""
        if action_id and action_id in PRESETS:
            lat, lon = PRESETS[action_id]
            loc = Location(lat=lat, lon=lon)
            label = f" ({qr(lang, action_id)})"
        elif action_id == "use_gps" and gps_location is None:
            bot = _msg("assistant", t(lang, "gps_denied"), _qrs(session, "preset_klaten", "preset_karawang", "preset_kupang"))
            chat_sessions.add_message(session, bot)
            outgoing.append(bot)
            return outgoing
        elif not loc and text:
            loc = _parse_location(text)

        if loc is None:
            hint = t(lang, "location_format_hint") if text.strip() else t(lang, "ask_location")
            bot = _msg("assistant", hint, _qrs(session, "use_gps", "preset_klaten", "preset_karawang", "preset_kupang"))
            chat_sessions.add_message(session, bot)
            outgoing.append(bot)
            return outgoing

        session.location = loc
        session.location_label = label
        session.step = "confirm_location"
        confirm_text = t(lang, "confirm_location", lat=loc.lat, lon=loc.lon, label=label)
        card = ChatCard(type="location", data={"lat": loc.lat, "lon": loc.lon, "label": label.strip()})
        bot = _msg("assistant", confirm_text, _qrs(session, "confirm_yes", "confirm_change"), card)
        chat_sessions.add_message(session, bot)
        outgoing.append(bot)
        if not _in_indonesia(loc):
            warn = _msg("assistant", t(lang, "outside_indonesia"))
            chat_sessions.add_message(session, warn)
            outgoing.append(warn)
        return outgoing

    if session.step == "confirm_location":
        if text.strip():
            new_loc = _parse_location(text)
            if new_loc:
                session.location = new_loc
                session.location_label = ""
                confirm_text = t(lang, "confirm_location", lat=new_loc.lat, lon=new_loc.lon, label="")
                card = ChatCard(type="location", data={"lat": new_loc.lat, "lon": new_loc.lon, "label": ""})
                bot = _msg("assistant", confirm_text, _qrs(session, "confirm_yes", "confirm_change"), card)
                chat_sessions.add_message(session, bot)
                outgoing.append(bot)
                return outgoing
        if action_id != "confirm_yes" and not (text.strip() and _is_yes(text)):
            session.step = "ask_location"
            bot = _msg("assistant", t(lang, "ask_location"), _qrs(session, "use_gps", "preset_klaten", "preset_karawang", "preset_kupang"))
            chat_sessions.add_message(session, bot)
            outgoing.append(bot)
            return outgoing
        session.step = "ask_last_crop"
        bot = _msg(
            "assistant",
            t(lang, "ask_last_crop"),
            _qrs(session, "crop_rice", "crop_corn", "crop_soybean", "crop_peanut", "crop_cassava", "crop_none"),
        )
        chat_sessions.add_message(session, bot)
        outgoing.append(bot)
        return outgoing

    if session.step == "ask_last_crop":
        resolved = _resolve_crop(action_id, text)
        if resolved is None:
            bot = _msg(
                "assistant",
                t(lang, "crop_format_hint"),
                _qrs(session, "crop_rice", "crop_corn", "crop_soybean", "crop_peanut", "crop_cassava", "crop_none"),
            )
            chat_sessions.add_message(session, bot)
            outgoing.append(bot)
            return outgoing
        crop_id, display = resolved
        session.last_crop = crop_id
        session.step = "ask_priorities"
        if not (action_id and action_id.startswith("crop_")):
            ack = _msg("assistant", t(lang, "crop_accepted", crop=display))
            chat_sessions.add_message(session, ack)
            outgoing.append(ack)
        bot = _msg("assistant", t(lang, "ask_priorities"), _qrs(session, "prio_water", "prio_drought", "prio_soil", "prio_balanced"))
        chat_sessions.add_message(session, bot)
        outgoing.append(bot)
        return outgoing

    if session.step == "ask_priorities":
        prio = ACTION_MAP.get(action_id or "")
        if not isinstance(prio, Priorities):
            bot = _msg("assistant", t(lang, "unknown_input"), _qrs(session, "prio_water", "prio_drought", "prio_soil", "prio_balanced"))
            chat_sessions.add_message(session, bot)
            outgoing.append(bot)
            return outgoing
        session.priorities = prio.normalized()
        session.step = "analyzing"
        session.analyzing = True
        progress = _msg("assistant", t(lang, "analyzing_climate"))
        chat_sessions.add_message(session, progress)
        outgoing.append(progress)
        asyncio.create_task(_run_analysis(session.id))
        return outgoing

    bot = _msg("assistant", t(lang, "unknown_input"))
    chat_sessions.add_message(session, bot)
    outgoing.append(bot)
    return outgoing


async def _run_analysis(session_id: str) -> None:
    session = chat_sessions.get(session_id)
    if not session or not session.location or not session.priorities:
        return
    lang = session.lang
    loc = session.location

    try:
        climate, soil = await asyncio.gather(fetch_climate(loc.lat, loc.lon), fetch_soil(loc.lat, loc.lon))
    except ClimateUnavailableError as exc:
        session.analyzing = False
        session.step = "ask_location"
        chat_sessions.add_message(
            session,
            _msg("assistant", t(lang, "analysis_failed", error=str(exc)), _qrs(session, "use_gps", "preset_klaten")),
        )
        return

    chat_sessions.add_message(
        session,
        _msg(
            "assistant",
            t(lang, "climate_summary", temp=climate.mean_temp_c, rain=climate.annual_rainfall_mm, dry=climate.dry_months),
            card=ChatCard(type="climate", data=climate.model_dump(mode="json"), provenance=climate.meta),
        ),
    )
    chat_sessions.add_message(
        session,
        _msg(
            "assistant",
            t(lang, "soil_summary", ph=soil.ph, texture=soil.texture, soc=soil.soc_g_kg),
            card=ChatCard(type="soil", data=soil.model_dump(mode="json"), provenance=soil.meta),
        ),
    )

    request = AnalyzeRequest(lat=loc.lat, lon=loc.lon, priorities=session.priorities)
    job = await jobs.start_job(request, climate, soil)
    session.job_id = job.id

    if not job.done:
        chat_sessions.add_message(session, _msg("assistant", t(lang, "analyzing_satellite")))
        while not job.done:
            await asyncio.sleep(5)
            job = await jobs.refresh_job(job)
            session = chat_sessions.get(session_id)
            if session is None:
                return

    job = jobs.get_job(job.id)
    if job is None:
        return

    if job.vegetation:
        chat_sessions.add_message(
            session,
            _msg(
                "assistant",
                t(
                    lang,
                    "vegetation_summary",
                    ndvi=job.vegetation.mean_ndvi,
                    trend=t(lang, _trend_key(job.vegetation.trend)),
                ),
                card=ChatCard(
                    type="vegetation",
                    data=job.vegetation.model_dump(mode="json"),
                    provenance=job.vegetation.meta,
                ),
            ),
        )
    if job.moisture:
        chat_sessions.add_message(
            session,
            _msg(
                "assistant",
                t(
                    lang,
                    "moisture_summary",
                    pct=round(job.moisture.mean_volumetric * 100),
                    var=t(lang, _var_key(job.moisture.variability)),
                ),
                card=ChatCard(
                    type="moisture",
                    data=job.moisture.model_dump(mode="json"),
                    provenance=job.moisture.meta,
                ),
            ),
        )

    for warning in job.warnings:
        chat_sessions.add_message(session, _msg("assistant", warning, card=ChatCard(type="warning", data={"text": warning})))

    chat_sessions.add_message(session, _msg("assistant", t(lang, "results_intro", n=len(job.recommendations))))
    for rec in job.recommendations[:3]:
        chat_sessions.add_message(
            session,
            _msg(
                "assistant",
                rec.rationale,
                card=ChatCard(type="rotation", data=rec.model_dump(mode="json")),
            ),
        )

    session.step = "free_chat"
    session.analyzing = False
    chat_sessions.add_message(
        session,
        _msg("assistant", t(lang, "free_chat_hint"), _qrs(session, "new_analysis", "change_priorities")),
    )
