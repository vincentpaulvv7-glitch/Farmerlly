"""Open-Meteo geocoding and forecast requests for Farmerlly."""

from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import requests

from farmerlly.i18n import language_name, translate


GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
REQUEST_TIMEOUT = (4, 15)


class WeatherAPIError(Exception):
    """A clear, user-safe error from location lookup or weather retrieval."""


WEATHER_DESCRIPTIONS = {
    0: ("Clear sky", "தெளிவான வானம்"),
    1: ("Mainly clear", "பெரும்பாலும் தெளிவு"),
    2: ("Partly cloudy", "ஓரளவு மேகமூட்டம்"),
    3: ("Overcast", "முழு மேகமூட்டம்"),
    45: ("Fog", "மூடுபனி"),
    48: ("Depositing rime fog", "உறைபனி மூடுபனி"),
    51: ("Light drizzle", "லேசான தூறல்"),
    53: ("Moderate drizzle", "மிதமான தூறல்"),
    55: ("Dense drizzle", "அடர்ந்த தூறல்"),
    56: ("Light freezing drizzle", "லேசான உறைபனி தூறல்"),
    57: ("Dense freezing drizzle", "அடர்ந்த உறைபனி தூறல்"),
    61: ("Light rain", "லேசான மழை"),
    63: ("Moderate rain", "மிதமான மழை"),
    65: ("Heavy rain", "கனமழை"),
    66: ("Light freezing rain", "லேசான உறைபனி மழை"),
    67: ("Heavy freezing rain", "கனமான உறைபனி மழை"),
    71: ("Light snow", "லேசான பனிப்பொழிவு"),
    73: ("Moderate snow", "மிதமான பனிப்பொழிவு"),
    75: ("Heavy snow", "கனமான பனிப்பொழிவு"),
    77: ("Snow grains", "பனித்துகள்கள்"),
    80: ("Light rain showers", "லேசான மழைத் தூறல்"),
    81: ("Moderate rain showers", "மிதமான மழைத் தூறல்"),
    82: ("Violent rain showers", "தீவிர மழைத் தூறல்"),
    85: ("Light snow showers", "லேசான பனித்தூறல்"),
    86: ("Heavy snow showers", "கனமான பனித்தூறல்"),
    95: ("Thunderstorm", "இடியுடன் கூடிய மழை"),
    96: ("Thunderstorm with hail", "ஆலங்கட்டியுடன் இடியுடன் கூடிய மழை"),
    99: ("Thunderstorm with heavy hail", "பெரிய ஆலங்கட்டியுடன் இடியுடன் கூடிய மழை"),
}


def _get_json(url: str, params: dict) -> dict:
    """Make one bounded HTTP request and turn common failures into clear errors."""
    try:
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        payload = response.json()
    except requests.Timeout as error:
        raise WeatherAPIError("The weather service took too long to respond. Please try again.") from error
    except requests.ConnectionError as error:
        raise WeatherAPIError("The weather service could not be reached. Check your internet connection and retry.") from error
    except requests.HTTPError as error:
        raise WeatherAPIError("The weather service is temporarily unavailable. Please try again shortly.") from error
    except requests.RequestException as error:
        raise WeatherAPIError("Weather data could not be loaded. Please try again.") from error
    except ValueError as error:
        raise WeatherAPIError("The weather service returned an unreadable response. Please try again.") from error

    if not isinstance(payload, dict):
        raise WeatherAPIError("The weather service returned an unreadable response. Please try again.")
    if payload.get("error"):
        raise WeatherAPIError(payload.get("reason", "The weather service rejected this request."))
    return payload


def _valid_location(result: dict) -> bool:
    return (
        result.get("country_code") == "IN"
        and isinstance(result.get("latitude"), (int, float))
        and isinstance(result.get("longitude"), (int, float))
        and -90 <= result["latitude"] <= 90
        and -180 <= result["longitude"] <= 180
    )


def _normalized_admin(value: str) -> str:
    """Normalize common administrative suffixes for conservative matching."""
    value = " ".join((value or "").casefold().split())
    for suffix in (" district", " dist.", " state"):
        if value.endswith(suffix):
            value = value[: -len(suffix)].strip()
    return value


def search_locations(query: str, state: str = "", district: str = "", language: str = "en") -> list[dict]:
    """Search Open-Meteo for selectable Indian locations, ranked by admin matches."""
    query = (query or "").strip()
    if len(query) < 2:
        return []
    payload = _get_json(GEOCODING_URL, {
        "name": query, "count": 10, "language": language, "format": "json", "countryCode": "IN",
    })
    results = [r for r in payload.get("results", []) if isinstance(r, dict) and _valid_location(r)]
    state_key, district_key = state.strip().casefold(), district.strip().casefold()
    if state_key:
        state_matches = [r for r in results if str(r.get("admin1", "")).casefold() == state_key]
        if state_matches:
            results = state_matches
    results.sort(key=lambda r: (
        0 if state_key and str(r.get("admin1", "")).casefold() == state_key else 1,
        0 if district_key and str(r.get("admin2", "")).casefold() == district_key else 1,
        0 if str(r.get("name", "")).casefold() == query.casefold() else 1,
    ))
    return [
        {"latitude": r["latitude"], "longitude": r["longitude"], "name": r["name"],
         "admin1": r.get("admin1", ""), "admin2": r.get("admin2", ""),
         "admin3": r.get("admin3", ""), "admin4": r.get("admin4", ""),
         "timezone": r.get("timezone", "Asia/Kolkata"), "precision": "selected",
         "feature_code": r.get("feature_code", "")}
        for r in results
    ]


def search_farmer_locations(
    village_or_city: str,
    district: str,
    state: str,
    language: str = "en",
) -> list[dict]:
    """Search the village by itself, then fall back to its district and state.

    Candidates must match India and the saved administrative fields. The caller
    should present every candidate for the farmer to choose from.
    """
    village = (village_or_city or "").strip()
    district = (district or "").strip()
    state = (state or "").strip()
    if len(village) >= 2:
        village_results = search_locations(village, state, district, language)
        exact_village = [
            result for result in village_results
            if _normalized_admin(result["name"]) == _normalized_admin(village)
            and _normalized_admin(result["admin1"]) == _normalized_admin(state)
            and _normalized_admin(result["admin2"]) == _normalized_admin(district)
        ]
        if exact_village:
            for result in exact_village:
                result["precision"] = "village"
            return exact_village

    if len(district) >= 2 and state:
        district_results = search_locations(f"{district}, {state}", state, district, language)
        exact_district = [
            result for result in district_results
            if _normalized_admin(result["admin1"]) == _normalized_admin(state)
            and (
                _normalized_admin(result["name"]) == _normalized_admin(district)
                or _normalized_admin(result["admin2"]) == _normalized_admin(district)
            )
        ]
        if exact_district:
            for result in exact_district:
                result["precision"] = "district"
            return exact_district

    raise WeatherAPIError(
        "Open-Meteo could not find this village or a matching location in its district and state. "
        "Check the spelling, search for another location, or enter coordinates."
    )


def geocode_farmer_location(
    village_or_city: str,
    district: str,
    state: str,
    language: str = "en",
) -> dict:
    """Resolve a verified profile match for non-interactive weather consumers."""
    locations = search_farmer_locations(village_or_city, district, state, language)
    return locations[0]


def _local_time(timezone_name: str) -> str:
    """Format the time this response was fetched in the farm's time zone."""
    try:
        timezone = ZoneInfo(timezone_name)
    except (ZoneInfoNotFoundError, ValueError, TypeError):
        timezone = ZoneInfo("Asia/Kolkata")
    return datetime.now(timezone).strftime("%d %b %Y, %I:%M %p %Z")


def get_weather_for_farmer(
    village_or_city: str,
    district: str,
    state: str,
    language: str = "en",
) -> dict:
    """Geocode a saved farm location and return current and seven-day weather."""
    location = geocode_farmer_location(village_or_city, district, state, language)
    return get_weather_for_coordinates(location["latitude"], location["longitude"], location, language)


def get_weather_for_coordinates(latitude: float, longitude: float, location: dict | None = None, language: str = "en") -> dict:
    """Fetch real Open-Meteo weather for validated coordinates."""
    try:
        latitude, longitude = float(latitude), float(longitude)
    except (TypeError, ValueError) as error:
        raise WeatherAPIError("Enter valid numeric latitude and longitude values.") from error
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        raise WeatherAPIError("Coordinates are outside the valid latitude/longitude range.")
    location = dict(location or {})
    location.update(latitude=latitude, longitude=longitude)
    location.setdefault("name", "Selected coordinates")
    location.setdefault("admin1", "")
    location.setdefault("admin2", "")
    location.setdefault("timezone", "Asia/Kolkata")
    location.setdefault("precision", "manual")
    forecast = _get_json(
        FORECAST_URL,
        {
            "latitude": location["latitude"],
            "longitude": location["longitude"],
            "current": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m,weather_code",
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,wind_speed_10m_max,et0_fao_evapotranspiration",
            "forecast_days": 7,
            "timezone": "auto",
            "temperature_unit": "celsius",
            "wind_speed_unit": "kmh",
            "precipitation_unit": "mm",
        },
    )

    current = forecast.get("current")
    daily = forecast.get("daily")
    if (
        not isinstance(current, dict)
        or not isinstance(daily, dict)
        or not isinstance(daily.get("time"), list)
        or not daily["time"]
    ):
        raise WeatherAPIError("The weather service did not return current conditions and a forecast for this location.")

    required_current = (
        "temperature_2m", "relative_humidity_2m", "precipitation", "wind_speed_10m", "weather_code"
    )
    required_daily = (
        "weather_code", "temperature_2m_max", "temperature_2m_min", "precipitation_sum",
        "precipitation_probability_max", "wind_speed_10m_max",
    )
    if any(current.get(key) is None for key in required_current):
        raise WeatherAPIError("Current weather values are unavailable for this location right now.")
    if any(
        key not in daily
        or len(daily[key]) != len(daily["time"])
        or any(value is None for value in daily[key])
        for key in required_daily
    ):
        raise WeatherAPIError("The weather service returned an incomplete forecast for this location.")

    return {
        "location": location,
        "current": current,
        "daily": daily,
        "fetched_at": _local_time(forecast.get("timezone", location["timezone"])),
        "observation_time": current.get("time"),
        "timezone": forecast.get("timezone", location["timezone"]),
    }


def describe_weather_code(code: int | None, language: str = "en") -> str:
    """Return a translated description for a common Open-Meteo weather code."""
    if code is None:
        return "?"
    description = WEATHER_DESCRIPTIONS.get(int(code))
    if description is None:
        return "Unknown conditions"
    return translate(description[0], language_name(language))


def get_weather_alerts(daily: dict) -> list[dict]:
    """Create simple farm alerts from forecast values, not official warnings."""
    alerts = []
    day_count = min(3, len(daily.get("time", [])))
    for index in range(day_count):
        day = daily["time"][index]
        code = daily.get("weather_code", [None] * day_count)[index]
        rain = daily.get("precipitation_sum", [0] * day_count)[index] or 0
        rain_chance = daily.get("precipitation_probability_max", [0] * day_count)[index] or 0
        high_temp = daily.get("temperature_2m_max", [0] * day_count)[index] or 0
        max_wind = daily.get("wind_speed_10m_max", [0] * day_count)[index] or 0

        if code in (95, 96, 99):
            alerts.append({"level": "warning", "type": "thunderstorm", "day": day})
        if rain >= 50 or (rain >= 20 and rain_chance >= 70):
            alerts.append({"level": "warning", "type": "heavy_rain", "day": day, "value": rain})
        if high_temp >= 40:
            alerts.append({"level": "caution", "type": "high_temperature", "day": day, "value": high_temp})
        if max_wind >= 40:
            alerts.append({"level": "caution", "type": "strong_wind", "day": day, "value": max_wind})

    return alerts
