"""Water guidance using saved crop data and live forecast, without false precision."""

import json
from functools import lru_cache
from pathlib import Path

import pandas as pd
import streamlit as st

from farmerlly.i18n import translate, translate_mapping

from farmerlly.crop_catalog import crop_label, growth_stages
from farmerlly.database import get_crop_records, update_crop_irrigation_method


COPY = {
    "English": {
        "title": "Water requirement advisor",
        "intro": "Review crop water demand indicators, upcoming rain, soil, and your irrigation method before deciding whether to irrigate.",
        "crop": "Crop record",
        "irrigation": "Irrigation method",
        "save_method": "Save irrigation method",
        "saved": "Irrigation method saved.",
        "methods": {
            "Unknown": "Not set",
            "Drip": "Drip",
            "Sprinkler": "Sprinkler",
            "Furrow": "Furrow",
            "Basin/flood": "Basin / flood",
            "Manual": "Manual watering",
        },
        "soil": "Saved soil type",
        "stage": "Current growth stage",
        "weather_missing": "Live local weather is unavailable. The advisor will not estimate demand or rainfall from sample data.",
        "refresh": "Refresh live weather",
        "forecast": "7-day weather and rain outlook",
        "forecast_note": "Forecast rainfall is shown as forecast precipitation, not effective rainfall. Some rain may run off, drain below roots, or evaporate.",
        "rain_sum": "Forecast rainfall total",
        "rain_day": "First forecast rain",
        "temp_range": "Forecast temperature range",
        "wind_max": "Maximum forecast wind",
        "et0": "Reference evapotranspiration (ET₀)",
        "et0_note": "ET₀ is weather-based atmospheric demand for a reference grass surface, from Open-Meteo.",
        "etc": "Indicative crop evapotranspiration (ETc)",
        "etc_note": "Calculated as ETc = Kc × ET₀ over days with available data. This is potential crop use under standard conditions, not an irrigation dose or net irrigation requirement. Kc is not adjusted for your irrigation method, wetted area, or local climate.",
        "calculation_missing": "A crop ET estimate is unavailable because no verified coefficient is configured for this crop and stage, or daily ET₀ data is missing. No coefficient or quantity is inferred.",
        "coefficient": "FAO-56 planning coefficient (Kc)",
        "stage_note": "The coefficient range is mapped to your manually selected crop stage. Stage duration and local adjustment data are not available, so this is an indicative planning estimate.",
        "advice": "Water management guidance",
        "why": "Why this advice",
        "verify": "Verify field decisions with your local KVK/agriculture department. Soil labels are broad profile categories and do not replace a soil-moisture check or field assessment.",
        "rain_advice": "Rain is forecast during the next week. Check soil moisture and drainage before scheduling irrigation; do not count all forecast rain as water available to roots.",
        "dry_advice": "Little or no rain is forecast for the next week. Inspect moisture in the active root zone and follow a local crop schedule; the forecast alone cannot determine when to irrigate.",
        "soil_sandy": "Your profile labels this soil sandy. Sandy soils often drain quickly and store less plant-available water than finer soils, so check the root zone more often. This label alone cannot set an interval or quantity.",
        "soil_clay": "Your profile labels this soil clay. Clay soils generally infiltrate and drain more slowly; check for ponding and avoid applying water faster than the field can absorb it.",
        "soil_other": "Use the saved soil category as context only. Actual water storage depends on measured texture, structure, depth, organic matter, and field condition.",
        "method_drip": "Drip can place water near the root zone. Check emitters and soil moisture along the wetted strip; field efficiency and wetted area are unknown, so no volume is calculated.",
        "method_sprinkler": "Sprinklers wet a broader area and can lose water to wind and evaporation. Check uniformity and local wind before operation; no system efficiency is assumed.",
        "method_surface": "Furrow and basin/flood methods depend on field level, intake rate, and drainage. Check for runoff, uneven wetting, and prolonged ponding; no application depth is inferred.",
        "method_manual": "For manual watering, direct water to the root zone and check soil moisture before repeating. The app does not know the volume applied.",
        "method_unknown": "Select the irrigation method for this crop to tailor the management notes. No application efficiency is assumed.",
        "stage_generic": "Your selected stage is {stage}. Check the crop locally for moisture stress and follow crop-specific irrigation guidance; this stage does not have a configured coefficient here.",
        "stage_rice": "For rice, the selected stage is {stage}. Paddy water management depends on establishment, soil, rainfall, and the local production system; check field water and drainage against local rice guidance.",
        "stage_tomato": "For tomato, the selected stage is {stage}. Observe root-zone moisture and avoid abrupt irrigation changes; timing depends on soil, crop cover, and local practice.",
        "explain_weather": "Weather is incorporated in ET₀; forecast rain is displayed separately. The advisor does not subtract total rain from ETc because effective rainfall and stored soil water are unknown.",
        "sources": "Calculation and guidance sources",
        "last_updated": "Weather retrieved",
        "selected_crop": "Selected crop",
        "kc_source": "Kc source and conditions",
        "daily_estimates": "Daily ETc estimate",
        "estimate_date": "Date",
        "estimate_et0": "ET₀ (mm)",
        "estimate_kc": "Kc range",
        "estimate_etc": "ETc range (mm)",
        "seven_day_total": "Seven-day ETc estimate",
    },
    "\u0ba4\u0bae\u0bbf\u0bb4\u0bcd": {
        "title": "நீர் தேவை ஆலோசகர்",
        "intro": "நீர்ப்பாசனம் முடிவு செய்வதற்கு முன் பயிர், மழை முன்னறிவிப்பு, மண் மற்றும் பாசன முறையைப் பாருங்கள்.",
        "crop": "பயிர் பதிவு",
        "irrigation": "பாசன முறை",
        "save_method": "பாசன முறையைச் சேமிக்கவும்",
        "saved": "பாசன முறை சேமிக்கப்பட்டது.",
        "methods": {"Unknown": "தேர்வு செய்யவில்லை", "Drip": "சொட்டுநீர்", "Sprinkler": "தெளிப்பான்", "Furrow": "பார் பாசனம்", "Basin/flood": "பாத்தி / வெள்ளப்பாசனம்", "Manual": "கையால் நீர் ஊற்றுதல்"},
        "soil": "பதிவுசெய்த மண் வகை",
        "stage": "தற்போதைய வளர்ச்சி நிலை",
        "weather_missing": "இந்த இடத்திற்கான நேரடி வானிலை கிடைக்கவில்லை. மாதிரி தரவிலிருந்து மழை அல்லது நீர் தேவையை கணிக்கவில்லை.",
        "refresh": "நேரடி வானிலையைப் புதுப்பிக்கவும்",
        "forecast": "7 நாள் வானிலை மற்றும் மழை முன்னறிவிப்பு",
        "forecast_note": "முன்னறிவிப்பு மழை என்பது மொத்த மழை அளவு; வேருக்கு கிடைக்கும் பயனுள்ள மழை அல்ல. சில நீர் வழிந்தோடலாம், ஆழமாக ஊறலாம் அல்லது ஆவியாகலாம்.",
        "rain_sum": "முன்னறிவிப்பு மொத்த மழை",
        "rain_day": "முதல் மழை நாள்",
        "temp_range": "முன்னறிவிப்பு வெப்பநிலை வரம்பு",
        "wind_max": "அதிகபட்ச முன்னறிவிப்பு காற்று",
        "et0": "குறிப்பு ஆவியுயிர்ப்பு (ET₀)",
        "et0_note": "Open-Meteo வழங்கும், வானிலை சார்ந்த குறிப்பு புல்வெளி ஆவியுயிர்ப்பு அளவு.",
        "etc": "குறிப்பான பயிர் ஆவியுயிர்ப்பு (ETc)",
        "etc_note": "கிடைக்கும் நாட்களுக்கு ETc = Kc × ET₀. இது தரநிலை நிலைமைகளில் பயிரின் சாத்தியமான பயன்பாடு; பாசன அளவு அல்லது நிகர பாசனத் தேவை அல்ல. பாசன முறை, ஈரப்படுத்திய பரப்பு, உள்ளூர் காலநிலைக்காக Kc திருத்தப்படவில்லை.",
        "calculation_missing": "இந்தப் பயிர் மற்றும் நிலைக்கு சரிபார்க்கப்பட்ட Kc இல்லை அல்லது தினசரி ET₀ தரவு இல்லை. மதிப்பு அல்லது பாசன அளவை ஊகிக்கவில்லை.",
        "coefficient": "FAO-56 திட்டமிடல் குணகம் (Kc)",
        "stage_note": "குணக வரம்பு நீங்கள் தேர்ந்தெடுத்த நிலைக்கு இணைக்கப்பட்டுள்ளது. நிலை நீளமும் உள்ளூர் திருத்தத் தரவும் இல்லாததால் இது திட்டமிடலுக்கான தோராய மதிப்பீடு.",
        "advice": "நீர் மேலாண்மை வழிகாட்டல்",
        "why": "இந்த ஆலோசனைக்கான காரணம்",
        "verify": "வயல் முடிவுகளை உள்ளூர் KVK / வேளாண்துறையுடன் சரிபார்க்கவும். மண் வகை என்பது பொதுவான பதிவு மட்டுமே; மண் ஈரப்பதச் சோதனை அல்லது வயல் ஆய்வுக்கு மாற்றல்ல.",
        "rain_advice": "அடுத்த வாரத்தில் மழை முன்னறிவிப்பு உள்ளது. பாசனத்தைத் திட்டமிடும் முன் மண் ஈரப்பதம், வடிகாலைப் பாருங்கள்; முன்னறிவிப்பு மழை அனைத்தும் வேருக்கு கிடைக்கும் எனக் கருத வேண்டாம்.",
        "dry_advice": "அடுத்த வாரத்தில் மழை குறைவாகவோ இல்லாமலோ இருக்கலாம். செயலில் உள்ள வேர் பகுதியில் ஈரத்தைச் சரிபார்த்து உள்ளூர் பயிர் அட்டவணையைப் பின்பற்றவும்; முன்னறிவிப்பு மட்டும் பாசன நேரத்தை முடிவு செய்யாது.",
        "soil_sandy": "பதிவில் மணற்பாங்கான மண் என உள்ளது. இம்மண் விரைவாக நீரை வெளியேற்றி குறைவாகச் சேமிக்கலாம்; வேர் பகுதியில் அடிக்கடி ஈரத்தைச் சரிபார்க்கவும். இதனால் மட்டும் இடைவெளி அல்லது அளவை முடிவு செய்ய முடியாது.",
        "soil_clay": "பதிவில் களிமண் என உள்ளது. நீர் ஊடுருவலும் வடிகாலும் மெதுவாக இருக்கலாம்; நீர் தேங்குகிறதா எனப் பார்த்து, மண் உறிஞ்சும் வேகத்தை விட வேகமாக நீர் விட வேண்டாம்.",
        "soil_other": "பதிவிலுள்ள மண் வகையைச் சூழல் தகவலாக மட்டும் பயன்படுத்தவும். உண்மையான நீர் சேமிப்பு மண் அமைப்பு, ஆழம், கரிமப் பொருள் மற்றும் வயல் நிலையைப் பொறுத்தது.",
        "method_drip": "சொட்டுநீர் வேரருகே நீரை வழங்கலாம். சொட்டிகள் மற்றும் ஈரமான பகுதியில் மண் ஈரத்தைச் சரிபார்க்கவும்; செயல்திறன் தெரியாததால் அளவு கணக்கிடப்படவில்லை.",
        "method_sprinkler": "தெளிப்பான் பெரிய பரப்பை நனைக்கும்; காற்று, ஆவியால் இழப்பு ஏற்படலாம். ஒரே சீரான தெளிப்பு, உள்ளூர் காற்றைச் சரிபார்க்கவும்; செயல்திறன் ஊகிக்கப்படவில்லை.",
        "method_surface": "பார் / பாத்தி பாசனம் வயல் சமநிலை, மண் உறிஞ்சல், வடிகாலைப் பொறுத்தது. வழிதல், சீரற்ற ஈரம், நீர் தேக்கம் உள்ளதா பாருங்கள்; நீர் ஆழம் ஊகிக்கப்படவில்லை.",
        "method_manual": "கையால் நீர் ஊற்றும்போது வேர்ப் பகுதிக்கு நீர் விடவும்; மீண்டும் நீர் விடும் முன் மண் ஈரத்தைப் பாருங்கள். பயன்படுத்திய அளவு இத்திட்டத்திற்கு தெரியாது.",
        "method_unknown": "இந்தப் பயிருக்கான பாசன முறையைத் தேர்ந்தெடுத்தால் மேலாண்மை குறிப்புகள் பொருந்தும். செயல்திறன் ஊகிக்கப்படாது.",
        "stage_generic": "தேர்ந்தெடுத்த நிலை: {stage}. பயிரில் நீர் அழுத்த அறிகுறிகளைப் பார்த்து, பயிர் சார்ந்த உள்ளூர் வழிகாட்டலைப் பின்பற்றவும்; இந்நிலைக்கு இங்கு குணகம் அமைக்கப்படவில்லை.",
        "stage_rice": "நெல், தேர்ந்தெடுத்த நிலை: {stage}. பயிர் நிறுவல், மண், மழை மற்றும் உள்ளூர் முறையைப் பொறுத்து நீர் மேலாண்மை மாறும்; உள்ளூர் நெல் வழிகாட்டலுடன் வயல் நீர், வடிகாலைச் சரிபார்க்கவும்.",
        "stage_tomato": "தக்காளி, தேர்ந்தெடுத்த நிலை: {stage}. வேர் பகுதியில் ஈரத்தைப் பார்த்து, திடீர் பாசன மாற்றங்களைத் தவிர்க்கவும்; நேரம் மண், பயிர் மூடல், உள்ளூர் முறையைப் பொறுத்தது.",
        "explain_weather": "வானிலை ET₀-வில் சேர்க்கப்பட்டுள்ளது; மழை தனியாகக் காட்டப்படுகிறது. பயனுள்ள மழையும் மண்ணில் சேமித்த நீரும் தெரியாததால் மொத்த மழையை ETc-யிலிருந்து கழிக்கவில்லை.",
        "sources": "கணக்கீடு மற்றும் வழிகாட்டல் ஆதாரங்கள்",
        "last_updated": "வானிலை பெறப்பட்ட நேரம்",
        "selected_crop": "தேர்ந்தெடுத்த பயிர்",
        "kc_source": "Kc ஆதாரம் மற்றும் நிலைமைகள்",
        "daily_estimates": "தினசரி ETc மதிப்பீடு",
        "estimate_date": "தேதி",
        "estimate_et0": "ET₀ (மிமீ)",
        "estimate_kc": "Kc வரம்பு",
        "estimate_etc": "ETc வரம்பு (மிமீ)",
        "seven_day_total": "ஏழு நாள் ETc மதிப்பீடு",
    },
}


IRRIGATION_METHODS = ["Unknown", "Drip", "Sprinkler", "Furrow", "Basin/flood", "Manual"]

FAO_SOURCE = "https://www.fao.org/4/X0490E/x0490e0b.htm"
OPEN_METEO_SOURCE = "https://open-meteo.com/en/docs"
SOIL_SOURCE = "https://www.fao.org/soils-portal/soil-survey/proprietes-du-sol/proprietes-physiques/en/"
CROP_SOURCES = {
    "rice": ("TNAU rice water management", "https://agritech.tnau.ac.in/expert_system/paddy/cultivationpractices3.html"),
    "tomato": ("TNAU tomato irrigation", "https://www.agritech.tnau.ac.in/horticulture/horti_vegetables_tomato_irrigation.html"),
    "banana": ("TNAU banana irrigation", "https://www.agritech.tnau.ac.in/expert_system/banana/irrigationmanagement.html"),
    "cotton": ("TNAU cotton irrigation", "https://agritech.tnau.ac.in/agriculture/agri_cotton_irri_irrigation%20management.html"),
}


@lru_cache(maxsize=1)
def _load_crop_coefficients() -> dict:
    """Load source-linked crop-stage coefficients from the editable JSON file."""
    path = Path(__file__).with_name("crop_coefficients.json")
    with path.open(encoding="utf-8") as coefficient_file:
        return json.load(coefficient_file)


def _guidance(words: dict, crop: dict, profile: dict, method: str, rain_total: float, language: str) -> tuple[str, str, str]:
    stage_value = next((translate(item[1], language)
                        for item in growth_stages(crop["crop_code"])
                        if item[0] == crop["growth_stage"]), crop["growth_stage"])
    if crop["crop_code"] == "rice":
        stage_text = words["stage_rice"].format(stage=stage_value)
    elif crop["crop_code"] == "tomato":
        stage_text = words["stage_tomato"].format(stage=stage_value)
    else:
        stage_text = words["stage_generic"].format(stage=stage_value)

    soil = profile.get("soil_type", "") if profile else ""
    soil_key = "soil_sandy" if "sandy" in soil.casefold() else "soil_clay" if "clay" in soil.casefold() else "soil_other"
    method_key = {
        "Drip": "method_drip", "Sprinkler": "method_sprinkler",
        "Furrow": "method_surface", "Basin/flood": "method_surface",
        "Manual": "method_manual",
    }.get(method, "method_unknown")
    rain_text = words["rain_advice"] if rain_total > 0 else words["dry_advice"]
    explanation = f"{stage_text} {words[soil_key]} {words[method_key]} {words['explain_weather']}"
    return rain_text, explanation, words["verify"]


def _calculate_etc(crop: dict, weather: dict | None) -> dict | None:
    if not weather:
        return None
    crop_config = _load_crop_coefficients().get("crops", {}).get(crop["crop_code"], {})
    stage_config = crop_config.get("stages", {}).get(crop["growth_stage"])
    daily = weather.get("daily", {})
    et0_values = daily.get("et0_fao_evapotranspiration")
    dates = daily.get("time", [])
    if not stage_config or not et0_values or len(et0_values) != len(dates):
        return None
    try:
        kc_low, kc_high = (float(value) for value in stage_config["kc"])
    except (KeyError, TypeError, ValueError):
        return None
    if kc_low < 0 or kc_high < kc_low:
        return None
    usable = []
    for day, et0 in zip(dates, et0_values):
        if et0 is None:
            continue
        try:
            et0 = float(et0)
        except (TypeError, ValueError):
            continue
        if et0 < 0:
            continue
        usable.append({
            "date": day,
            "et0": et0,
            "kc_low": kc_low,
            "kc_high": kc_high,
            "etc_low": et0 * kc_low,
            "etc_high": et0 * kc_high,
        })
    if not usable:
        return None
    return {
        "kc": (kc_low, kc_high),
        "days": len(usable),
        "start": usable[0]["date"],
        "end": usable[-1]["date"],
        "et0": sum(item["et0"] for item in usable),
        "etc_low": sum(item["etc_low"] for item in usable),
        "etc_high": sum(item["etc_high"] for item in usable),
        "daily": usable,
        "source_name": crop_config.get("source_name", ""),
        "source_url": crop_config.get("source_url", FAO_SOURCE),
        "standard_conditions": crop_config.get("standard_conditions", ""),
        "stage_note": stage_config.get("note", ""),
    }


def render_water_advisor(profile: dict | None, weather: dict | None, language: str, clear_weather_cache) -> None:
    words = COPY.get(language) or translate_mapping(COPY["English"], language)
    st.subheader(words["title"])
    st.caption(words["intro"])
    records = get_crop_records()
    if not records:
        st.info("Add a crop record in My crops to get crop-specific water guidance." if language == "English" else "பயிர் சார்ந்த நீர் வழிகாட்டலுக்கு My crops பகுதியில் பயிர் பதிவைச் சேர்க்கவும்.")
        return

    crop_id = st.selectbox(
        words["crop"], [record["crop_id"] for record in records],
        format_func=lambda selected: next(
            f"{record['crop_name'] if record['crop_code'] == 'other' else crop_label(record['crop_code'], language)} · {record['planting_date']}"
            for record in records if record["crop_id"] == selected
        ), key="water_crop_record",
    )
    crop = next(record for record in records if record["crop_id"] == crop_id)
    stage = next((translate(stage[1], language)
                  for stage in growth_stages(crop["crop_code"])
                  if stage[0] == crop["growth_stage"]), crop["growth_stage"])
    crop_name = crop.get("crop_name") if crop["crop_code"] == "other" else crop_label(crop["crop_code"], language)
    cols = st.columns(4)
    cols[0].metric(words["selected_crop"], crop_name)
    cols[1].metric(words["stage"], stage)
    cols[2].metric(words["soil"], profile.get("soil_type", "—") if profile else "—")
    cols[3].metric("Location" if language == "English" else "இடம்",
                   ", ".join(part for part in (profile.get("village_or_city"), profile.get("district")) if part) if profile else "—")

    with st.form(f"water_method_form_{crop_id}"):
        method = st.selectbox(
            words["irrigation"], IRRIGATION_METHODS,
            index=IRRIGATION_METHODS.index(crop.get("irrigation_method", "Unknown"))
            if crop.get("irrigation_method", "Unknown") in IRRIGATION_METHODS else 0,
            format_func=words["methods"].get,
        )
        save_method = st.form_submit_button(words["save_method"])
    if save_method:
        update_crop_irrigation_method(crop_id, method)
        st.session_state["water_method_saved"] = True
        st.rerun()
    if st.session_state.pop("water_method_saved", False):
        st.success(words["saved"])

    if st.button(words["refresh"], icon=":material/refresh:", key="water_refresh_weather"):
        clear_weather_cache()
        st.rerun()
    if not weather:
        st.info(words["weather_missing"])
        return

    daily = weather["daily"]
    rainfall = [value for value in daily.get("precipitation_sum", []) if value is not None]
    rain_total = sum(rainfall)
    rain_days = [day for day, value in zip(daily.get("time", []), daily.get("precipitation_sum", [])) if value and value > 0]
    st.markdown(f"#### {words['forecast']}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(words["rain_sum"], f"{rain_total:.1f} mm")
    c2.metric(words["rain_day"], rain_days[0] if rain_days else ("None forecast" if language == "English" else "மழை இல்லை"))
    low_values = [value for value in daily.get("temperature_2m_min", []) if value is not None]
    high_values = [value for value in daily.get("temperature_2m_max", []) if value is not None]
    wind_values = [value for value in daily.get("wind_speed_10m_max", []) if value is not None]
    if low_values and high_values:
        c3.metric(words["temp_range"], f"{min(low_values):g}–{max(high_values):g} °C")
    if wind_values:
        c4.metric(words["wind_max"], f"{max(wind_values):g} km/h")
    st.caption(words["forecast_note"])

    et0_values = [value for value in daily.get("et0_fao_evapotranspiration", []) if value is not None]
    if et0_values:
        st.metric(words["et0"], f"{sum(et0_values):.1f} mm / {len(et0_values)} forecast days")
        st.caption(words["et0_note"])

    estimate = _calculate_etc(crop, weather)
    if estimate:
        st.markdown(f"#### {words['etc']}")
        if abs(estimate["etc_high"] - estimate["etc_low"]) < 0.05:
            etc_display = f"{estimate['etc_low']:.1f} mm"
        else:
            etc_display = f"{estimate['etc_low']:.1f}–{estimate['etc_high']:.1f} mm"
        st.metric(words["coefficient"], f"{estimate['kc'][0]:g}–{estimate['kc'][1]:g}" if estimate['kc'][0] != estimate['kc'][1] else f"{estimate['kc'][0]:g}")
        st.metric(words["seven_day_total"], etc_display)
        st.info(f"{etc_display} · {estimate['start']} to {estimate['end']}", title=words["etc"])
        st.caption(words["etc_note"])
        st.caption(words["stage_note"])
        st.caption(f"{words['kc_source']}: {estimate['source_name']}. {estimate['standard_conditions']} {estimate['stage_note']}")
        if crop["crop_code"] == "rice" and crop["growth_stage"] == "nursery":
            st.warning(estimate["stage_note"], title=words["coefficient"])
        st.markdown(f"[{estimate['source_name']}]({estimate['source_url']})")
        daily_rows = [
            {
                words["estimate_date"]: item["date"],
                words["estimate_et0"]: round(item["et0"], 2),
                words["estimate_kc"]: f"{item['kc_low']:g}–{item['kc_high']:g}" if item["kc_low"] != item["kc_high"] else f"{item['kc_low']:g}",
                words["estimate_etc"]: f"{item['etc_low']:.2f}–{item['etc_high']:.2f}" if item["etc_low"] != item["etc_high"] else f"{item['etc_low']:.2f}",
            }
            for item in estimate["daily"]
        ]
        st.markdown(f"#### {words['daily_estimates']}")
        st.dataframe(pd.DataFrame(daily_rows), hide_index=True, width="stretch", alt="Daily crop evapotranspiration estimates")
    else:
        st.info(words["calculation_missing"])

    rain_advice, explanation, verify = _guidance(
        words, crop, profile, crop.get("irrigation_method", "Unknown"), rain_total, language
    )
    st.markdown(f"#### {words['advice']}")
    st.write(rain_advice)
    st.markdown(f"#### {words['why']}")
    st.write(explanation)
    st.caption(verify)
    st.caption(f"{words['last_updated']}: {weather['fetched_at']}")
    links = [
        f"[FAO-56 crop coefficient method]({FAO_SOURCE})",
        f"[FAO soil physical properties]({SOIL_SOURCE})",
        f"[Open-Meteo daily ET₀]({OPEN_METEO_SOURCE})",
    ]
    crop_source = CROP_SOURCES.get(crop["crop_code"])
    if crop_source:
        links.append(f"[{crop_source[0]}]({crop_source[1]})")
    st.markdown(f"**{words['sources']}**: " + " · ".join(links))
