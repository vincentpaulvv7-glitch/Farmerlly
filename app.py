"""Farmerlly's beginner-friendly, bilingual Streamlit dashboard."""

from datetime import date, datetime, timedelta

import pandas as pd
import streamlit as st
from farmerlly.crop_ui import render_crop_management
from farmerlly.database import get_farmer_profile
from farmerlly.i18n import LANGUAGES, language_code, translate
from farmerlly.notifications import render_notification_center
from farmerlly.profile_ui import render_profile_page
from farmerlly.roadmap import render_roadmap
from farmerlly.water_advisor import render_water_advisor
from modules.weather import (
    WeatherAPIError,
    describe_weather_code,
    get_weather_alerts,
    get_weather_for_farmer,
    get_weather_for_coordinates,
    search_farmer_locations,
    search_locations,
)


st.set_page_config(
    page_title="Farmerlly | Farming dashboard",
    page_icon="🌱",
    layout="wide",
)


# All displayed copy is kept in one place so adding another language is simple.
TEXT = {
    "English": {
        "tagline": "Your fields, one clear view.",
        "language": "Language / மொழி",
        "navigation": "YOUR FARM",
        "overview": "Overview",
        "crops_nav": "My crops",
        "tasks_nav": "Smart Farming Roadmap",
        "water_nav": "Water advisory",
        "demo_note": "Weather and the water advisor use live Open-Meteo data when available.",
        "date_label": "A simple view of your farm for",
        "weather": "Weather overview",
        "demo": "DEMO DATA",
        "location": "Farm location",
        "temperature": "Temperature",
        "humidity": "Humidity",
        "rain_chance": "Rain chance",
        "wind": "Wind",
        "next_days": "Coming days",
        "day": "Day",
        "conditions": "Conditions",
        "crops": "My crops",
        "view_all": "Your crop plan at a glance",
        "tasks": "Today's farming tasks",
        "tasks_help": "Tick a task when it is done. Your progress updates here.",
        "done": "done",
        "crop": "Crop",
        "water": "Water advisory",
        "water_help": "Sample soil readings and general guidance only. No field sensors or weather service are connected.",
        "soil_moisture": "Sample soil moisture",
        "water_status": "Sample advisory",
        "water_message": "Demo guidance: inspect the soil near the roots before irrigating. Water early in the morning when the crop needs it.",
        "tomorrow": "Tomorrow",
        "day_after": "Day after",
        "today": "Today",
        "sunny": "Mostly sunny",
        "cloudy": "Partly cloudy",
        "showers": "Light showers",
        "rice": "Rice",
        "tomato": "Tomato",
        "banana": "Banana",
        "crop_stage": "Growth stage",
        "crop_area": "Area",
        "tillering": "Tillering",
        "flowering": "Flowering",
        "vegetative": "Vegetative",
        "acre": "acres",
        "task_1": "Check rice field water level",
        "task_2": "Inspect tomato leaves for pests",
        "task_3": "Prepare compost for banana plants",
        "task_4": "Record this week's rainfall",
        "soil_good": "Moisture looks adequate (demo)",
        "active_crops": "Active crops",
        "tasks_left": "Tasks left",
        "water_tip": "Tip: Check the top few centimetres of soil by hand before watering.",
        "profile_nav": "Farmer profile",
        "live_weather": "LIVE WEATHER · Open-Meteo",
        "weather_unavailable": "Live weather is unavailable. No sample weather is shown.",
        "weather_profile_needed": "Add your state and village or city in Farmer profile to see local weather.",
        "weather_current": "Current conditions",
        "rainfall": "Recent rainfall",
        "weather_forecast": "7-day forecast",
        "forecast_min": "Low °C",
        "forecast_max": "High °C",
        "forecast_rain": "Rain mm",
        "forecast_rain_chance": "Rain chance %",
        "forecast_wind": "Max wind km/h",
        "weather_alerts": "Farm weather alerts",
        "weather_alert_note": "Forecast-based guidance, not official emergency warnings.",
        "weather_no_alerts": "No alert thresholds were reached in the next 3 days. Keep checking local conditions.",
        "alert_title": "Forecast advisory",
        "alert_thunderstorm": "Thunderstorm forecast for {day}.",
        "alert_heavy_rain": "Heavy rain forecast for {day}: {value} mm.",
        "alert_high_temperature": "High temperature forecast for {day}: {value} °C.",
        "alert_strong_wind": "Strong wind forecast for {day}: {value} km/h.",
        "location_district": "The village could not be matched. Weather is shown for the district location instead.",
        "location_state": "The village and district could not be matched. Weather is shown for the state location instead.",
        "weather_updated": "Last updated",
        "weather_model_time": "Forecast observation time",
        "refresh_weather": "Refresh weather",
        "weather_chart_alt": "Daily minimum and maximum temperatures for the next seven days",
    },
    "தமிழ்": {
        "tagline": "உங்கள் வயல்கள் — ஒரே தெளிவான பார்வையில்.",
        "language": "மொழி / Language",
        "navigation": "உங்கள் பண்ணை",
        "overview": "முகப்புப் பார்வை",
        "crops_nav": "என் பயிர்கள்",
        "tasks_nav": "பயிர் வழிகாட்டி",
        "water_nav": "நீர் ஆலோசனை",
        "demo_note": "Weather and the water advisor use live Open-Meteo data when available.",
        "date_label": "உங்கள் பண்ணையின் இன்றைய பார்வை",
        "weather": "வானிலை பார்வை",
        "demo": "மாதிரி தரவு",
        "location": "பண்ணை இடம்",
        "temperature": "வெப்பநிலை",
        "humidity": "ஈரப்பதம்",
        "rain_chance": "மழை வாய்ப்பு",
        "wind": "காற்று",
        "next_days": "வரும் நாட்கள்",
        "day": "நாள்",
        "conditions": "வானிலை",
        "crops": "என் பயிர்கள்",
        "view_all": "உங்கள் பயிர் திட்டத்தின் சுருக்கம்",
        "tasks": "இன்றைய விவசாயப் பணிகள்",
        "tasks_help": "முடிந்த பணியைத் தேர்வு செய்யுங்கள். உங்கள் முன்னேற்றம் இங்கே தெரியும்.",
        "done": "முடிந்தது",
        "crop": "பயிர்",
        "water": "நீர் ஆலோசனை",
        "water_help": "மாதிரி மண் அளவீடுகள் மற்றும் பொதுவான வழிகாட்டல் மட்டும். வயல் உணரிகள் அல்லது வானிலை சேவை இணைக்கப்படவில்லை.",
        "soil_moisture": "மாதிரி மண் ஈரப்பதம்",
        "water_status": "மாதிரி ஆலோசனை",
        "water_message": "செயல்விளக்க வழிகாட்டல்: நீர் பாய்ச்சும் முன் வேரருகே மண்ணைச் சரிபார்க்கவும். பயிருக்கு தேவைப்பட்டால் அதிகாலையில் நீர் பாய்ச்சவும்.",
        "tomorrow": "நாளை",
        "day_after": "மறுநாள்",
        "today": "இன்று",
        "sunny": "பெரும்பாலும் வெயில்",
        "cloudy": "ஓரளவு மேகமூட்டம்",
        "showers": "லேசான மழை",
        "rice": "நெல்",
        "tomato": "தக்காளி",
        "banana": "வாழை",
        "crop_stage": "வளர்ச்சி நிலை",
        "crop_area": "பரப்பளவு",
        "tillering": "தூர் பிடித்தல்",
        "flowering": "பூக்கும் நிலை",
        "vegetative": "வளர்ச்சி நிலை",
        "acre": "ஏக்கர்",
        "task_1": "நெல் வயலின் நீர் அளவைச் சரிபார்க்கவும்",
        "task_2": "தக்காளி இலைகளில் பூச்சி உள்ளதா பார்க்கவும்",
        "task_3": "வாழைச் செடிகளுக்கு உரம் தயாரிக்கவும்",
        "task_4": "இந்த வார மழை அளவைப் பதிவு செய்யவும்",
        "soil_good": "மண் ஈரப்பதம் போதுமானது (மாதிரி)",
        "active_crops": "செயலில் உள்ள பயிர்கள்",
        "tasks_left": "மீதமுள்ள பணிகள்",
        "water_tip": "குறிப்பு: நீர் பாய்ச்சும் முன் மண்ணின் மேற்பகுதியை கையால் சரிபார்க்கவும்.",
        "profile_nav": "விவசாயி மற்றும் பண்ணை விவரம்",
        "live_weather": "நேரடி வானிலை · Open-Meteo",
        "weather_unavailable": "நேரடி வானிலை கிடைக்கவில்லை. மாதிரி வானிலை காட்டப்படாது.",
        "weather_profile_needed": "உள்ளூர் வானிலையைப் பார்க்க விவசாயி விவரத்தில் மாநிலம் மற்றும் கிராமம் அல்லது நகரத்தைச் சேர்க்கவும்.",
        "weather_current": "தற்போதைய வானிலை",
        "rainfall": "சமீபத்திய மழைப்பொழிவு",
        "weather_forecast": "7 நாள் வானிலை முன்னறிவிப்பு",
        "forecast_min": "குறைந்த வெப்பம் °C",
        "forecast_max": "அதிக வெப்பம் °C",
        "forecast_rain": "மழை mm",
        "forecast_rain_chance": "மழை வாய்ப்பு %",
        "forecast_wind": "அதிகபட்ச காற்று km/h",
        "weather_alerts": "வயல் வானிலை எச்சரிக்கைகள்",
        "weather_alert_note": "முன்னறிவிப்பை அடிப்படையாகக் கொண்ட வழிகாட்டல்; அதிகாரப்பூர்வ அவசர எச்சரிக்கை அல்ல.",
        "weather_no_alerts": "அடுத்த 3 நாட்களில் எச்சரிக்கை வரம்புகள் எதுவும் எட்டப்படவில்லை. உள்ளூர் நிலையை தொடர்ந்து கவனிக்கவும்.",
        "alert_title": "முன்னறிவிப்பு ஆலோசனை",
        "alert_thunderstorm": "{day} அன்று இடியுடன் கூடிய மழை முன்னறிவிக்கப்பட்டுள்ளது.",
        "alert_heavy_rain": "{day} அன்று கனமழை முன்னறிவிப்பு: {value} mm.",
        "alert_high_temperature": "{day} அன்று அதிக வெப்பநிலை முன்னறிவிப்பு: {value} °C.",
        "alert_strong_wind": "{day} அன்று பலத்த காற்று முன்னறிவிப்பு: {value} km/h.",
        "location_district": "கிராமத்தைப் பொருத்த முடியவில்லை. மாவட்ட இடத்திற்கான வானிலை காட்டப்படுகிறது.",
        "location_state": "கிராமம் மற்றும் மாவட்டத்தைப் பொருத்த முடியவில்லை. மாநில இடத்திற்கான வானிலை காட்டப்படுகிறது.",
        "weather_updated": "கடைசியாக புதுப்பிக்கப்பட்டது",
        "weather_model_time": "முன்னறிவிப்பு தரவு நேரம்",
        "refresh_weather": "வானிலையைப் புதுப்பிக்கவும்",
        "weather_chart_alt": "அடுத்த ஏழு நாட்களுக்கான தினசரி குறைந்த மற்றும் அதிக வெப்பநிலை",
    },
}


def tr(key: str) -> str:
    """Return text in the language selected in the sidebar."""
    language = st.session_state.language
    if language in TEXT:
        return TEXT[language][key]
    return translate(TEXT["English"][key], language)


def greeting_period(now: datetime | None = None) -> str:
    """Return the translated greeting key for the computer's local clock time."""
    local_now = now if now is not None else datetime.now().astimezone()
    hour = local_now.hour
    if 5 <= hour < 12:
        return "Good Morning"
    if 12 <= hour < 17:
        return "Good Afternoon"
    if 17 <= hour < 21:
        return "Good Evening"
    return "Good Night"


@st.fragment(run_every=timedelta(seconds=30))
def render_greeting(profile: dict | None, language: str) -> None:
    """Refresh only the greeting periodically so it follows the local time."""
    greeting = translate(greeting_period(), language)
    farmer_name = profile.get("farmer_name", "").strip() if profile else ""
    if farmer_name:
        st.title(f"{greeting}, {farmer_name}! 🌱")
    else:
        st.title(f"{greeting}! 🌱")
    st.caption(translate("Welcome back to Farmerlly", language))


TASKS = ["task_1", "task_2", "task_3", "task_4"]
NAV_ITEMS = ["profile_nav", "overview", "crops_nav", "tasks_nav", "water_nav"]


def section_heading(title: str, description: str | None = None) -> None:
    st.subheader(title)
    if description:
        st.caption(description)


@st.cache_data(ttl=900, show_spinner=False)
def load_weather(village_or_city: str, district: str, state: str, language: str) -> dict:
    """Cache live weather briefly so normal dashboard reruns do not repeat API calls."""
    geocoding_language = language_code(language)
    return get_weather_for_farmer(village_or_city, district, state, geocoding_language)


@st.cache_data(ttl=900, show_spinner=False)
def load_weather_coordinates(latitude: float, longitude: float, location: dict, language: str) -> dict:
    return get_weather_for_coordinates(latitude, longitude, location, language_code(language))


@st.cache_data(ttl=3600, show_spinner=False)
def load_farmer_location_candidates(village: str, district: str, state: str, language: str) -> list[dict]:
    return search_farmer_locations(village, district, state, language_code(language))


def load_profile_weather(profile: dict, language: str) -> dict:
    selected = st.session_state.get("weather_location_override")
    if selected:
        return load_weather_coordinates(selected["latitude"], selected["longitude"], selected, language)
    return load_weather(profile["village_or_city"], profile["district"], profile["state"], language)


def render_weather(
    profile: dict | None,
    weather_data: dict | None = None,
    weather_error: WeatherAPIError | None = None,
) -> None:
    if profile is None:
        section_heading(tr("weather"))
        st.info(tr("weather_profile_needed"))
        return

    location_input = (
        profile["village_or_city"],
        profile["district"],
        profile["state"],
    )
    override_location = st.session_state.get("weather_location_override")
    section_location = ", ".join(
        part for part in (
            override_location.get("name") if override_location else profile["village_or_city"],
            override_location.get("admin2") if override_location else profile["district"],
            override_location.get("admin1") if override_location else profile["state"],
        ) if part
    )
    section_heading(
        tr("weather"),
        section_location,
    )
    location_key = (profile.get("village_or_city", ""), profile.get("district", ""), profile.get("state", ""))
    if not override_location and (
        "weather_location_candidates" not in st.session_state
        or st.session_state.get("weather_candidates_profile_key") != location_key
    ):
        try:
            candidates = load_farmer_location_candidates(*location_key, st.session_state.language)
            st.session_state.weather_location_candidates = candidates
            st.session_state.weather_candidates_profile_key = location_key
            st.session_state.weather_location_search_error = None
        except WeatherAPIError as error:
            candidates = []
            st.session_state.weather_location_candidates = []
            st.session_state.weather_candidates_profile_key = location_key
            st.session_state.weather_location_search_error = str(error)
    with st.expander(translate("Choose or enter another weather location", st.session_state.language), expanded=not bool(override_location)):
        if st.session_state.get("weather_location_override") and st.button(
            translate("Use farm profile location", st.session_state.language), key="reset_weather_location"
        ):
            st.session_state.pop("weather_location_override", None)
            load_weather_coordinates.clear()
            st.rerun()
        query = st.text_input(translate("Search a village, district, or city", st.session_state.language), key="weather_location_query")
        if st.button(translate("Search locations", st.session_state.language), key="search_weather_locations"):
            try:
                st.session_state.weather_location_candidates = search_locations(
                    query, profile.get("state", ""), profile.get("district", ""),
                    language_code(st.session_state.language),
                )
                if not st.session_state.weather_location_candidates:
                    st.warning(translate("No matching locations found. Try a nearby district or city, or enter coordinates below.", st.session_state.language))
            except WeatherAPIError as error:
                st.error(str(error))
        candidates = st.session_state.get("weather_location_candidates", [])
        if not override_location and candidates:
            if candidates[0].get("precision") == "village":
                st.caption(translate("Matching farm locations were found. Choose the correct one to load live weather.", st.session_state.language))
            elif candidates[0].get("precision") == "district":
                st.info(translate("The village was not found in this district. Choose a matching district location to load live weather.", st.session_state.language))
        elif not override_location and st.session_state.get("weather_location_search_error"):
            st.warning(st.session_state.weather_location_search_error)
        if candidates:
            option_labels = [", ".join(filter(None, (item["name"], item.get("admin2"), item.get("admin1"), f"{item['latitude']:.4f}, {item['longitude']:.4f}"))) for item in candidates]
            chosen_index = st.selectbox(translate("Select a matching location", st.session_state.language), range(len(candidates)), format_func=lambda i: option_labels[i], key="weather_location_choice")
            if st.button(translate("Use selected location", st.session_state.language), key="use_weather_location"):
                st.session_state.weather_location_override = candidates[chosen_index]
                load_weather_coordinates.clear()
                st.rerun()
        with st.form("manual_weather_coordinates"):
            st.caption(translate("Optional fallback: enter coordinates from a trusted map source.", st.session_state.language))
            latitude_col, longitude_col = st.columns(2)
            latitude = latitude_col.number_input(translate("Latitude", st.session_state.language), min_value=-90.0, max_value=90.0, value=None, placeholder="e.g. 10.7905", format="%.6f")
            longitude = longitude_col.number_input(translate("Longitude", st.session_state.language), min_value=-180.0, max_value=180.0, value=None, placeholder="e.g. 78.7047", format="%.6f")
            coordinate_label = st.text_input(translate("Location label", st.session_state.language), value="Manually selected location")
            if st.form_submit_button(translate("Use these coordinates", st.session_state.language)):
                if latitude is None or longitude is None:
                    st.error(translate("Enter both latitude and longitude values.", st.session_state.language))
                else:
                    st.session_state.weather_location_override = {
                        "latitude": latitude, "longitude": longitude, "name": coordinate_label.strip() or "Selected coordinates",
                        "admin1": "", "admin2": "", "timezone": "Asia/Kolkata", "precision": "manual",
                    }
                    load_weather_coordinates.clear()
                    st.rerun()
    if st.button(tr("refresh_weather"), icon=":material/refresh:", key="refresh_weather"):
        load_weather.clear()
        load_weather_coordinates.clear()

    try:
        if weather_error and "weather_location_override" not in st.session_state:
            raise weather_error
        if "weather_location_override" in st.session_state:
            selected = st.session_state.weather_location_override
            weather_data = load_weather_coordinates(selected["latitude"], selected["longitude"], selected, st.session_state.language)
        elif weather_data is None:
            st.info(translate("Choose a matching location above to load live weather.", st.session_state.language))
            return
        weather = weather_data
    except WeatherAPIError as error:
        st.error(tr("weather_unavailable"), title=tr("weather"))
        st.caption(str(error))
        return

    weather_language_code = language_code(st.session_state.language)
    location = weather["location"]
    location_label = ", ".join(
        part for part in (location["name"], location.get("admin2"), location.get("admin1")) if part
    )
    st.caption(f":material/cloud: {tr('live_weather')} · {location_label} · [Open-Meteo](https://open-meteo.com/)")
    if location["precision"] == "district":
        st.warning(tr("location_district"), icon=":material/location_searching:")
    elif location["precision"] == "state":
        st.warning(tr("location_state"), icon=":material/location_searching:")

    current = weather["current"]
    with st.container(border=True):
        st.subheader(tr("weather_current"))
        with st.container(horizontal=True):
            st.metric(tr("temperature"), f"{current['temperature_2m']:.1f} °C")
            st.metric(tr("humidity"), f"{current['relative_humidity_2m']}%")
            st.metric(tr("rainfall"), f"{current['precipitation']:.1f} mm")
            st.metric(tr("wind"), f"{current['wind_speed_10m']:.1f} km/h")
        st.markdown(f"**{describe_weather_code(current.get('weather_code'), weather_language_code)}**")
        st.caption(f"{tr('weather_updated')}: {weather['fetched_at']} · {tr('weather_model_time')}: {weather['observation_time']}")

    daily = weather["daily"]
    forecast_rows = []
    for index, forecast_day in enumerate(daily["time"]):
        forecast_rows.append(
            {
                tr("day"): forecast_day,
                tr("conditions"): describe_weather_code(daily["weather_code"][index], weather_language_code),
                tr("forecast_min"): daily["temperature_2m_min"][index],
                tr("forecast_max"): daily["temperature_2m_max"][index],
                tr("forecast_rain"): daily["precipitation_sum"][index],
                tr("forecast_rain_chance"): daily["precipitation_probability_max"][index],
                tr("forecast_wind"): daily["wind_speed_10m_max"][index],
            }
        )
    forecast_frame = pd.DataFrame(forecast_rows)

    section_heading(tr("weather_forecast"))
    st.line_chart(
        forecast_frame,
        x=tr("day"),
        y=[tr("forecast_min"), tr("forecast_max")],
        alt=tr("weather_chart_alt"),
    )
    st.dataframe(forecast_frame, hide_index=True, width="stretch")

    section_heading(tr("weather_alerts"), tr("weather_alert_note"))
    alerts = get_weather_alerts(daily)
    if not alerts:
        st.success(tr("weather_no_alerts"), icon=":material/check_circle:")
    for alert in alerts:
        message = tr(f"alert_{alert['type']}").format(
            day=alert["day"], value=f"{alert.get('value', 0):g}"
        )
        if alert["level"] == "warning":
            st.warning(message, title=tr("alert_title"))
        else:
            st.info(message, title=tr("alert_title"))


def render_tasks() -> None:
    section_heading(tr("tasks"), tr("tasks_help"))
    with st.container(border=True):
        st.caption(tr("demo"))
        for task in TASKS:
            st.checkbox(tr(task), key=f"done_{task}")
        completed = sum(bool(st.session_state.get(f"done_{task}", False)) for task in TASKS)
        st.progress(completed / len(TASKS), text=f"{completed}/{len(TASKS)} {tr('done')}")


profile = get_farmer_profile()
st.session_state.pop("assistant_messages", None)
st.session_state.pop("assistant_chat_input", None)
preferred_language = st.session_state.pop("_preferred_language_pending", None)
if preferred_language:
    st.session_state["language"] = preferred_language
st.session_state.setdefault("language", profile["preferred_language"] if profile else "English")
if st.session_state.language not in LANGUAGES:
    st.session_state.language = "English"

with st.sidebar:
    st.markdown("# 🌱 Farmerlly")
    st.caption(tr("tagline"))
    language = st.selectbox(
        translate("Language", st.session_state.language),
        options=LANGUAGES,
        key="language",
    )
    st.markdown(f"**{tr('navigation')}**")
    selected_section = st.radio(
        translate("Your farm", language),
        options=NAV_ITEMS,
        index=0 if profile is None else 1,
        format_func=lambda item: tr(item),
        label_visibility="collapsed",
        key="navigation",
    )
    st.divider()
    st.caption("🌿  Simple tools for healthier fields")


render_greeting(profile, language)
st.caption(f"{tr('date_label')} · {date.today().strftime('%d %b %Y')}")
st.caption(tr("demo_note"))

if selected_section == "profile_nav":
    render_profile_page(language, profile)
elif selected_section == "overview":
    overview_weather = None
    overview_weather_error = None
    if profile and st.session_state.get("weather_location_override"):
        try:
            overview_weather = load_profile_weather(profile, language)
        except WeatherAPIError as error:
            overview_weather_error = error
    render_notification_center(profile, overview_weather, language)
    render_weather(profile, overview_weather, overview_weather_error)
    st.divider()
    render_crop_management(language, profile, compact=True)
    st.divider()
    render_tasks()
elif selected_section == "crops_nav":
    render_crop_management(language, profile)
elif selected_section == "tasks_nav":
    roadmap_weather = None
    if profile:
        try:
            roadmap_weather = load_profile_weather(profile, language)
        except WeatherAPIError as error:
            st.warning(tr("weather_unavailable"), icon=":material/cloud_off:")
            st.caption(str(error))
    render_roadmap(profile, roadmap_weather, language, load_weather.clear)
elif selected_section == "water_nav":
    advisor_weather = None
    if profile:
        try:
            advisor_weather = load_profile_weather(profile, language)
        except WeatherAPIError as error:
            st.warning(tr("weather_unavailable"), icon=":material/cloud_off:")
            st.caption(str(error))
    render_water_advisor(profile, advisor_weather, language, load_weather.clear)
