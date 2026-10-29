from typing import Literal

Lang = Literal["id", "en"]

MESSAGES: dict[str, dict[Lang, str]] = {
    "welcome": {
        "id": (
            "Halo Pak/Bu! Saya TaniPilot, penasihat rotasi tanam berbasis data satelit NASA. "
            "Saya bantu pilih tanaman untuk musim berikutnya agar tanah tetap sehat dan tahan kekeringan."
        ),
        "en": (
            "Hello! I'm TaniPilot, a crop rotation advisor powered by NASA satellite data. "
            "I'll help you choose crops for the next season to keep your soil healthy and drought-resilient."
        ),
    },
    "ask_location": {
        "id": "Di mana lokasi lahan Anda? Pakai GPS, pilih wilayah, atau ketik koordinat (mis. -7.45, 110.40).",
        "en": "Where is your farm? Use GPS, pick a region, or type coordinates (e.g. -7.45, 110.40).",
    },
    "gps_denied": {
        "id": "Akses lokasi ditolak. Ketik koordinat di kotak pesan bawah (mis. -7.45, 110.40) atau pilih wilayah di bawah.",
        "en": "Location access denied. Type coordinates in the message box below (e.g. -7.45, 110.40) or pick a region.",
    },
    "location_format_hint": {
        "id": "Format koordinat: latitude, longitude — contoh: -7.45, 110.40 atau -7.45 110.40",
        "en": "Coordinate format: latitude, longitude — e.g. -7.45, 110.40 or -7.45 110.40",
    },
    "need_location_first": {
        "id": "Saya perlu lokasi lahan dulu. Ketik koordinat (mis. -7.45, 110.40) atau pilih tombol di bawah.",
        "en": "I need your farm location first. Type coordinates (e.g. -7.45, 110.40) or use a button below.",
    },
    "confirm_location": {
        "id": "Lahan Anda di {lat}, {lon}{label}. Apakah benar?",
        "en": "Your farm is at {lat}, {lon}{label}. Is this correct?",
    },
    "outside_indonesia": {
        "id": "Lokasi di luar Indonesia. Rekomendasi tetap ditampilkan, tapi kurang akurat untuk kondisi lokal.",
        "en": "Location is outside Indonesia. Results are shown but may be less accurate for local conditions.",
    },
    "ask_last_crop": {
        "id": "Tanaman terakhir yang Anda tanam di lahan ini? Pilih tombol di bawah atau ketik sendiri — satu tanaman, atau campuran (mis. 30% jagung, 50% padi, 20% kedelai).",
        "en": "What was the last crop you planted on this field? Pick a button below or type it — one crop, or a mix (e.g. 30% corn, 50% rice, 20% soybean).",
    },
    "crop_accepted": {
        "id": "Baik, tanaman terakhir: {crop}.",
        "en": "Got it, last crop: {crop}.",
    },
    "crop_format_hint": {
        "id": "Ketik nama tanaman (mis. padi, jagung) atau campuran persentase (mis. 30% jagung, 50% padi, 20% kedelai).",
        "en": "Type a crop name (e.g. rice, corn) or a percentage mix (e.g. 30% corn, 50% rice, 20% soybean).",
    },
    "ask_priorities": {
        "id": "Prioritas utama Anda untuk rotasi berikutnya?",
        "en": "What is your main priority for the next rotation?",
    },
    "analyzing_climate": {
        "id": "Sedang mengambil data cuaca dari NASA POWER…",
        "en": "Fetching climate data from NASA POWER…",
    },
    "analyzing_soil": {
        "id": "Sedang mengambil data tanah dari SoilGrids…",
        "en": "Fetching soil data from SoilGrids…",
    },
    "analyzing_satellite": {
        "id": "Menunggu data satelit (vegetasi & kelembapan tanah). Bisa 1–2 menit…",
        "en": "Waiting for satellite data (vegetation & soil moisture). This can take 1–2 minutes…",
    },
    "climate_summary": {
        "id": (
            "Cuaca lahan Anda: suhu rata-rata {temp}°C, curah hujan {rain} mm/tahun, "
            "{dry} bulan kering."
        ),
        "en": (
            "Your farm climate: average temperature {temp}°C, {rain} mm/year rainfall, "
            "{dry} dry months."
        ),
    },
    "soil_summary": {
        "id": "Tanah: pH {ph}, tekstur {texture}, karbon organik {soc} g/kg.",
        "en": "Soil: pH {ph}, texture {texture}, organic carbon {soc} g/kg.",
    },
    "vegetation_summary": {
        "id": "Vegetasi (NDVI): rata-rata {ndvi}, tren {trend}.",
        "en": "Vegetation (NDVI): mean {ndvi}, trend {trend}.",
    },
    "moisture_summary": {
        "id": "Kelembapan tanah permukaan: {pct}%, variabilitas {var}.",
        "en": "Surface soil moisture: {pct}%, {var} variability.",
    },
    "results_intro": {
        "id": "Berikut {n} rekomendasi rotasi terbaik untuk lahan Anda:",
        "en": "Here are the top {n} rotation recommendations for your farm:",
    },
    "free_chat_hint": {
        "id": "Ada pertanyaan lain? Ketik bebas, atau pilih opsi di bawah.",
        "en": "Any other questions? Type freely or pick an option below.",
    },
    "llm_disabled": {
        "id": "Fitur tanya bebas belum aktif. Gunakan tombol di bawah atau mulai analisis baru.",
        "en": "Free-form chat is not enabled. Use the buttons below or start a new analysis.",
    },
    "unknown_input": {
        "id": "Maaf, saya belum paham. Silakan pilih salah satu opsi di bawah.",
        "en": "Sorry, I didn't understand. Please pick one of the options below.",
    },
    "analysis_failed": {
        "id": "Gagal mengambil data: {error}. Coba lagi atau ubah lokasi.",
        "en": "Failed to fetch data: {error}. Try again or change location.",
    },
    "trend_declining": {"id": "menurun", "en": "declining"},
    "trend_stable": {"id": "stabil", "en": "stable"},
    "trend_improving": {"id": "membaik", "en": "improving"},
    "var_low": {"id": "rendah", "en": "low"},
    "var_moderate": {"id": "sedang", "en": "moderate"},
    "var_high": {"id": "tinggi", "en": "high"},
}

QUICK_REPLY_LABELS: dict[str, dict[Lang, str]] = {
    "use_gps": {"id": "📍 Pakai lokasi saya", "en": "📍 Use my location"},
    "preset_klaten": {"id": "Klaten (Jawa Tengah)", "en": "Klaten (Central Java)"},
    "preset_karawang": {"id": "Karawang (Jawa Barat)", "en": "Karawang (West Java)"},
    "preset_kupang": {"id": "Kupang (NTT)", "en": "Kupang (East Nusa Tenggara)"},
    "confirm_yes": {"id": "Ya, benar", "en": "Yes, correct"},
    "confirm_change": {"id": "Ubah lokasi", "en": "Change location"},
    "crop_rice": {"id": "Padi", "en": "Rice"},
    "crop_corn": {"id": "Jagung", "en": "Corn"},
    "crop_soybean": {"id": "Kedelai", "en": "Soybean"},
    "crop_peanut": {"id": "Kacang tanah", "en": "Peanut"},
    "crop_cassava": {"id": "Singkong", "en": "Cassava"},
    "crop_none": {"id": "Belum tanam / bera", "en": "Fallow / none"},
    "prio_water": {"id": "💧 Hemat air", "en": "💧 Save water"},
    "prio_drought": {"id": "☀️ Tahan kekeringan", "en": "☀️ Drought tolerant"},
    "prio_soil": {"id": "🌱 Tanah sehat", "en": "🌱 Soil health"},
    "prio_balanced": {"id": "⚖️ Seimbang", "en": "⚖️ Balanced"},
    "new_analysis": {"id": "Analisis baru", "en": "New analysis"},
    "change_priorities": {"id": "Ubah prioritas", "en": "Change priorities"},
}

PRESETS = {
    "preset_klaten": (-7.45, 110.40),
    "preset_karawang": (-6.32, 107.34),
    "preset_kupang": (-10.18, 123.60),
}


def t(lang: Lang, key: str, **kwargs: str | int | float) -> str:
    template = MESSAGES[key][lang]
    return template.format(**kwargs) if kwargs else template


def qr(lang: Lang, key: str) -> str:
    return QUICK_REPLY_LABELS[key][lang]
