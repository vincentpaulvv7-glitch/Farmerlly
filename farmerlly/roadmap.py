"""Build and display a cautious, crop-aware farming roadmap."""

from datetime import date, timedelta

import streamlit as st

from farmerlly.i18n import translate_mapping
from farmerlly.crop_catalog import crop_label, growth_stages
from farmerlly.database import (
    get_crop_records,
    get_roadmap_task_status,
    set_roadmap_task_status,
)


COPY = {
    "English": {
        "title": "Smart Farming Roadmap",
        "intro": "A practical checklist based on your crop record, location, selected horizon, and live forecast when available.",
        "crop": "Choose a crop record",
        "duration": "Planning duration",
        "weeks": "weeks",
        "today": "Today's tasks",
        "weekly": "Weekly tasks",
        "activities": "Important crop growth activities",
        "upcoming": "Upcoming crop stages",
        "precautions": "Weather-related precautions",
        "completed": "Completed",
        "progress": "Roadmap progress",
        "no_crops": "Add a crop in My crops before creating a roadmap.",
        "stage": "Current stage",
        "planted": "Planting date",
        "crop_age": "{days} days since planting",
        "location": "Location",
        "stage_check": "Walk the field and compare the crop with the selected growth stage. Record any changes in My crops.",
        "weekly_check": "Scout a representative part of the field for crop condition, pests, disease symptoms, weeds, and soil moisture. Record observations; verify any treatment with a local agriculture officer or KVK.",
        "rain_task": "Forecast rain for {day} ({rain:g} mm). Check field drainage and avoid entering waterlogged soil; follow local advisories.",
        "storm_task": "Thunderstorm forecast for {day}. Check official local alerts and secure equipment; avoid exposed field work during lightning.",
        "wind_task": "Strong wind forecast for {day} (up to {wind:g} km/h). Check local alerts and postpone exposed or spray work if conditions are unsafe.",
        "heat_task": "High temperature forecast for {day} ({temp:g} °C). Check soil moisture and crop stress; follow locally recommended irrigation timing.",
        "stage_activity": "At this stage, check crop establishment and soil moisture; act according to local crop guidance.",
        "rice_tillering": "Rice: inspect tiller development and field water condition. Water needs vary by soil, variety, and local practice; verify irrigation depth and timing with local guidance.",
        "rice_panicle": "Rice: monitor crop development around panicle initiation. Nutrient decisions should follow soil tests and local recommendations; do not apply an unverified dose.",
        "tomato_flowering": "Tomato: inspect flowering plants and keep moisture conditions as even as practical. Check local guidance before changing irrigation or applying inputs.",
        "tomato_fruit_set": "Tomato: inspect fruit development and look for pest or disease symptoms. Verify any control measure with a local extension source before use.",
        "banana_vegetative": "Banana: check root-zone moisture and drainage. TNAU notes moisture and drainage matter through growth; irrigation amounts depend on system and local conditions.",
        "banana_flowering": "Banana: inspect the flowering/shooting stage and maintain field drainage. Confirm stage-specific water management with local guidance.",
        "verify": "Verify this recommendation with your local KVK/agriculture department. Crop stage timing and field actions vary by variety, soil, season, and location.",
        "no_specific": "No crop-specific activity is configured for this crop and stage yet. Use the weekly scouting task and seek local crop guidance.",
        "no_next": "No later growth stages are listed for this crop.",
        "weather_live": "Weather precautions use the live Open-Meteo forecast for {place} (retrieved {time}). They are planning cues, not official warnings.",
        "weather_missing": "A live forecast is not available for this location. Weather precautions are omitted; refresh weather or check an official local forecast.",
        "refresh": "Refresh live forecast",
        "duration_help": "The forecast covers up to 7 days; weekly crop checks continue for the selected planning duration.",
        "source_title": "Agricultural references",
        "no_recommendation": "No fertilizer, pesticide, or yield recommendation is generated. Verify uncertain actions locally.",
    },
    "\u0ba4\u0bae\u0bbf\u0bb4\u0bcd": {
        "title": "à®ªà®¯à®¿à®°à¯ à®µà®´à®¿à®•à®¾à®Ÿà¯à®Ÿà®¿",
        "intro": "à®ªà®¯à®¿à®°à¯ à®ªà®¤à®¿à®µà¯, à®‡à®Ÿà®®à¯, à®¤à¯‡à®°à¯à®¨à¯à®¤ à®•à®¾à®²à®®à¯, à®•à®¿à®Ÿà¯ˆà®•à¯à®•à¯à®®à¯ à®¨à¯‡à®°à®Ÿà®¿ à®µà®¾à®©à®¿à®²à¯ˆ à®…à®Ÿà®¿à®ªà¯à®ªà®Ÿà¯ˆà®¯à®¿à®²à¯ à®¤à®¿à®Ÿà¯à®Ÿà®®à¯.",
        "crop": "à®ªà®¯à®¿à®°à¯ˆà®¤à¯ à®¤à¯‡à®°à¯à®¨à¯à®¤à¯†à®Ÿà¯à®•à¯à®•à®µà¯à®®à¯",
        "duration": "à®¤à¯€à®Ÿà¯à®Ÿà®®à®¿à®Ÿà¯à®®à¯ à®•à®¾à®²à®®à¯",
        "weeks": "à®µà®¾à®°à®™à¯à®•à®³à¯",
        "today": "à®‡à®©à¯à®±à¯ˆà®¯ à®ªà®£à®¿à®•à®³à¯",
        "weekly": "à®µà®¾à®°à®¾à®¨à¯à®¤à®¿à®° à®ªà®£à®¿à®•à®³à¯",
        "activities": "à®®à¯à®•à¯à®•à®¿à®¯ à®µà®³à®°à¯à®šà¯à®šà®¿ à®¨à®Ÿà®µà®Ÿà®¿à®•à¯à®•à¯ˆà®•à®³à¯",
        "upcoming": "à®…à®Ÿà¯à®¤à¯à®¤ à®µà®³à®°à¯à®šà¯à®šà®¿ à®¨à®¿à®²à¯ˆà®•à®³à¯",
        "precautions": "à®µà®¾à®©à®¿à®²à¯ˆ à®®à¯à®©à¯à®©à¯†à®šà¯à®šà®°à®¿à®•à¯à®•à¯ˆà®•à®³à¯",
        "completed": "à®®à¯à®Ÿà®¿à®•à¯à®•à®ªà¯à®ªà®Ÿà¯à®Ÿà®¤à¯",
        "progress": "à®¤à¯€à®Ÿà¯à®Ÿ à®®à¯à®©à¯à®©à¯‡à®±à¯à®±à®®à¯",
        "no_crops": "à®¤à¯€à®Ÿà¯à®Ÿà®¤à¯ˆ à®‰à®°à¯à®µà®¾à®•à¯à®• My crops à®ªà®•à¯à®¤à®¿à®¯à®¿à®²à¯ à®ªà®¯à®¿à®°à¯ˆà®šà¯ à®šà¯‡à®°à¯à®•à¯à®•à®µà¯à®®à¯.",
        "stage": "à®¤à®±à¯à®ªà¯‹à®¤à¯ˆà®¯ à®¨à®¿à®²à¯ˆ",
        "planted": "à®¨à®Ÿà®µà¯ à®¨à®¾à®³à¯",
        "crop_age": "à®¨à®Ÿà®µà¯ à®šà¯†à®¯à¯à®¤à¯ {days} à®¨à®¾à®³à¯",
        "location": "à®‡à®Ÿà®®à¯",
        "stage_check": "à®µà®¯à®²à¯ˆà®ªà¯ à®ªà®¾à®°à¯à®¤à¯à®¤à¯, à®ªà®¯à®¿à®°à¯ˆ à®¤à¯‡à®°à¯à®¨à¯à®¤ à®µà®³à®°à¯à®šà¯à®šà®¿ à®¨à®¿à®²à¯ˆà®¯à¯à®Ÿà®©à¯ à®’à®ªà¯à®ªà®¿à®Ÿà¯à®™à¯à®•à®³à¯. à®®à®¾à®±à¯à®±à®™à¯à®•à®³à¯ˆ My crops à®‡à®²à¯ à®ªà®¤à®¿à®µà®¿à®Ÿà¯à®™à¯à®•à®³à¯.",
        "weekly_check": "à®ªà®¯à®¿à®°à¯ à®¨à®²à®®à¯, à®ªà¯‚à®šà¯à®šà®¿, à®¨à¯‹à®¯à¯ à®…à®±à®¿à®•à¯à®±à®¿, à®•à®³à¯ˆ, à®®à®£à¯ à®ˆà®°à®ªà¯à®ªà®¤à®¤à¯ˆ à®šà®¿à®² à®ªà®•à¯à®¤à®¿à®•à®³à®¿à®²à¯ à®ªà®¾à®°à¯à®¤à¯à®¤à¯à®ªà¯ à®ªà®¤à®¿à®µà¯ à®šà¯†à®¯à¯à®¯à®µà¯à®®à¯. à®šà®¿à®•à®¿à®šà¯à®šà¯ˆà®•à¯à®•à¯ à®®à¯à®©à¯ à®‰à®³à¯à®³à¯‚à®°à¯ à®µà®¿à®µà®šà®¾à®¯ à®…à®¤à®¿à®•à®¾à®°à®¿ / KVK à®‰à®Ÿà®©à¯ à®‰à®±à¯à®¤à®¿à®ªà¯à®ªà®Ÿà¯à®¤à¯à®¤à®µà¯à®®à¯.",
        "rain_task": "{day} à®®à®´à¯ˆ à®®à¯à®©à¯à®©à®±à®¿à®µà®¿à®ªà¯à®ªà¯ ({rain:g} mm). à®µà®¯à®²à¯ à®µà®¾à®¯à¯à®•à¯à®•à®¾à®²à¯ˆà®ªà¯ à®ªà®¾à®°à¯à®•à¯à®•à®µà¯à®®à¯; à®¨à¯€à®°à¯ à®¤à¯‡à®™à¯à®•à®¿à®¯ à®®à®£à¯à®£à®¿à®²à¯ à®¨à®Ÿà®•à¯à®•à®¾à®¤à¯€à®°à¯à®•à®³à¯. à®‰à®³à¯à®³à¯‚à®°à¯ à®†à®²à¯‹à®šà®©à¯ˆà®¯à¯ˆà®ªà¯ à®ªà®¿à®©à¯à®ªà®±à¯à®±à®µà¯à®®à¯.",
        "storm_task": "{day} à®‡à®Ÿà®¿à®®à®¿à®©à¯à®©à®²à¯ à®®à®´à¯ˆ à®®à¯à®©à¯à®©à®±à®¿à®µà®¿à®ªà¯à®ªà¯. à®…à®¤à®¿à®•à®¾à®°à®ªà¯à®ªà¯‚à®°à¯à®µ à®‰à®³à¯à®³à¯‚à®°à¯ à®Žà®šà¯à®šà®°à®¿à®•à¯à®•à¯ˆà®•à®³à¯ˆà®ªà¯ à®ªà®¾à®°à¯à®•à¯à®•à®µà¯à®®à¯; à®®à®¿à®©à¯à®©à®²à¯ à®‡à®°à¯à®•à¯à®•à¯à®®à¯à®ªà¯‹à®¤à¯ à®µà¯†à®³à®¿à®¯à®¿à®²à¯ à®µà¯‡à®²à¯ˆ à®šà¯†à®¯à¯à®¯à®¾à®¤à¯€à®°à¯à®•à®³à¯.",
        "wind_task": "{day} à®ªà®²à®®à®¾à®© à®•à®¾à®±à¯à®±à¯ à®®à¯à®©à¯à®©à®±à®¿à®µà®¿à®ªà¯à®ªà¯ ({wind:g} km/h). à®‰à®³à¯à®³à¯‚à®°à¯ à®Žà®šà¯à®šà®°à®¿à®•à¯à®•à¯ˆà®•à®³à¯ˆà®ªà¯ à®ªà®¾à®°à¯à®•à¯à®•à®µà¯à®®à¯; à®ªà®¾à®¤à¯à®•à®¾à®ªà¯à®ªà®¿à®²à¯à®²à®¾à®¤ à®µà¯‡à®²à¯ˆ / à®¤à¯†à®³à®¿à®ªà¯à®ªà¯ˆ à®¤à®³à¯à®³à®¿à®µà¯ˆà®•à¯à®•à®µà¯à®®à¯.",
        "heat_task": "{day} à®…à®¤à®¿à®• à®µà¯†à®ªà¯à®ªà®®à¯ ({temp:g} °C). à®®à®£à¯ à®ˆà®°à®ªà¯à®ªà®¤à®®à¯, à®ªà®¯à®¿à®°à¯ à®µà®¾à®Ÿà®²à¯ˆà®ªà¯ à®ªà®¾à®°à¯à®•à¯à®•à®µà¯à®®à¯; à®‰à®³à¯à®³à¯‚à®°à¯ à®¨à¯€à®°à¯à®ªà¯à®ªà®¾à®šà®© à®¨à¯‡à®°à®¤à¯à®¤à¯ˆà®ªà¯ à®ªà®¿à®©à¯à®ªà®±à¯à®±à®µà¯à®®à¯.",
        "stage_activity": "à®‡à®¨à¯à®¤ à®¨à®¿à®²à¯ˆà®¯à®¿à®²à¯ à®ªà®¯à®¿à®°à¯ à®¨à®¿à®²à¯ˆà®ªà¯à®ªà®¾à®Ÿà¯, à®®à®£à¯ à®ˆà®°à®ªà¯à®ªà®¤à®¤à¯ˆ à®ªà®¾à®°à¯à®•à¯à®•à®µà¯à®®à¯; à®‰à®³à¯à®³à¯‚à®°à¯ à®ªà®¯à®¿à®°à¯ à®µà®´à®¿à®•à®¾à®Ÿà¯à®Ÿà®²à¯à®ªà®Ÿà®¿ à®šà¯†à®¯à®²à¯à®ªà®Ÿà®µà¯à®®à¯.",
        "rice_tillering": "à®¨à¯†à®²à¯: à®¤à¯‚à®°à¯ à®µà®³à®°à¯à®šà¯à®šà®¿, à®µà®¯à®²à¯ à®¨à¯€à®°à¯ à®¨à®¿à®²à¯ˆà®¯à¯ˆ à®ªà®¾à®°à¯à®•à¯à®•à®µà¯à®®à¯. à®®à®£à¯, à®°à®•à®®à¯, à®‰à®³à¯à®³à¯‚à®°à¯ à®®à¯à®±à¯ˆ à®ªà®Ÿà®¿ à®¨à¯€à®°à¯ à®®à®¾à®±à¯à®®à¯; à®‰à®³à¯à®³à¯‚à®°à¯ à®†à®²à¯‹à®šà®©à¯ˆà®¯à¯ˆ à®‰à®±à¯à®¤à®¿à®šà¯†à®¯à¯à®¯à®µà¯à®®à¯.",
        "rice_panicle": "à®¨à¯†à®²à¯: à®•à®¤à®¿à®°à¯ à®‰à®°à¯à®µà®¾à®•à¯à®®à¯ à®¨à®¿à®²à¯ˆà®¯à®¿à®²à¯ à®ªà®¯à®¿à®°à¯ˆ à®•à®£à¯à®•à®¾à®£à®¿à®•à¯à®•à®µà¯à®®à¯. à®®à®£à¯ à®ªà®°à®¿à®šà¯‹à®¤à®©à¯ˆ, à®‰à®³à¯à®³à¯‚à®°à¯ à®ªà®°à®¿à®¨à¯à®¤à¯à®°à¯ˆ à®‡à®²à¯à®²à®¾à®®à®²à¯ à®‰à®°à®®à¯ à®‡à®Ÿ à®µà¯‡à®£à¯à®Ÿà®¾à®®à¯.",
        "tomato_flowering": "à®¤à®•à¯à®•à®¾à®³à®¿: à®ªà¯‚à®•à¯à®•à¯à®®à¯ à®ªà®¯à®¿à®°à¯ˆ à®ªà®¾à®°à¯à®•à¯à®•à®µà¯à®®à¯; à®®à®£à¯ à®ˆà®°à®ªà¯à®ªà®¤à®¤à¯ˆ à®®à¯à®Ÿà®¿à®¨à¯à®¤à®µà®°à¯ˆ à®šà®®à®®à®¾à®• à®µà¯ˆà®•à¯à®•à®µà¯à®®à¯. à®¨à¯€à®°à¯ / à®‡à®Ÿà¯à®ªà¯Šà®°à¯à®³à¯ à®®à®¾à®±à¯à®±à®¤à¯à®¤à®¿à®±à¯à®•à¯ à®‰à®³à¯à®³à¯‚à®°à¯ à®†à®²à¯‹à®šà®©à¯ˆà®¯à¯ˆ à®ªà®¾à®°à¯à®•à¯à®•à®µà¯à®®à¯.",
        "tomato_fruit_set": "à®¤à®•à¯à®•à®¾à®³à®¿: à®•à®¾à®¯à¯ à®µà®³à®°à¯à®šà¯à®šà®¿, à®ªà¯‚à®šà¯à®šà®¿ / à®¨à¯‹à®¯à¯ à®…à®±à®¿à®•à¯à®±à®¿à®•à®³à¯ˆ à®ªà®¾à®°à¯à®•à¯à®•à®µà¯à®®à¯. à®•à®Ÿà¯à®Ÿà¯à®ªà¯à®ªà®¾à®Ÿà¯ à®®à¯à®±à¯ˆà®¯à¯ˆ à®‰à®³à¯à®³à¯‚à®°à¯ à®†à®¤à®¾à®°à®¤à¯à®¤à®¿à®²à¯ à®‰à®±à¯à®¤à®¿à®ªà¯à®ªà®Ÿà¯à®¤à¯à®¤à®µà¯à®®à¯.",
        "banana_vegetative": "à®µà®¾à®´à¯ˆ: à®µà¯‡à®°à¯ à®ªà®•à¯à®¤à®¿ à®®à®£à¯ à®ˆà®°à®ªà¯à®ªà®¤à®®à¯, à®µà®¾à®¯à¯à®•à¯à®•à®¾à®²à¯ˆ à®ªà®¾à®°à¯à®•à¯à®•à®µà¯à®®à¯. à®µà®³à®°à¯à®šà¯à®šà®¿à®¯à®¿à®²à¯ à®ˆà®°à®ªà¯à®ªà®®à¯, à®µà®Ÿà®¿à®•à®¾à®²à¯ à®®à¯à®•à¯à®•à®¿à®¯à®®à¯; à®¨à¯€à®°à®³à®µà¯ à®®à¯à®±à¯ˆ / à®‡à®Ÿà®¤à¯à®¤à¯ˆà®ªà¯ à®ªà¯Šà®±à¯à®¤à¯à®¤à¯ à®®à®¾à®±à¯à®®à¯.",
        "banana_flowering": "à®µà®¾à®´à¯ˆ: à®ªà¯‚à®•à¯à®•à¯à®®à¯ / à®¤à®£à¯à®Ÿà¯ à®µà¯†à®³à®¿à®µà®°à¯à®®à¯ à®¨à®¿à®²à¯ˆà®¯à¯ˆ à®ªà®¾à®°à¯à®•à¯à®•à®µà¯à®®à¯; à®µà®¯à®²à¯ à®µà®Ÿà®¿à®•à®¾à®²à¯ˆ à®ªà®°à®¾à®®à®°à®¿à®•à¯à®•à®µà¯à®®à¯. à®¨à®¿à®²à¯ˆà®•à¯à®•à¯‡à®±à¯à®ª à®¨à¯€à®°à¯ à®®à¯à®±à¯ˆà®¯à¯ˆ à®‰à®±à¯à®¤à®¿à®ªà¯à®ªà®Ÿà¯à®¤à¯à®¤à®µà¯à®®à¯.",
        "verify": "à®‡à®¨à¯à®¤ à®ªà®°à®¿à®¨à¯à®¤à¯à®°à¯ˆà®¯à¯ˆ à®‰à®³à¯à®³à¯‚à®°à¯ KVK / à®µà®¿à®µà®šà®¾à®¯à®¤à¯ à®¤à¯à®±à¯ˆà®¯à®¿à®²à¯ à®‰à®±à¯à®¤à®¿à®ªà¯à®ªà®Ÿà¯à®¤à¯à®¤à®µà¯à®®à¯. à®°à®•à®®à¯, à®®à®£à¯, à®ªà®°à¯à®µà®®à¯, à®‡à®Ÿà®¤à¯à®¤à®¾à®²à¯ à®¨à®¿à®²à¯ˆ à®¨à®¾à®³à¯ à®®à®±à¯à®±à¯à®®à¯ à®µà®¯à®²à¯ à®šà¯†à®¯à®²à¯à®•à®³à¯ à®®à®¾à®±à¯à®®à¯.",
        "no_specific": "à®‡à®¨à¯à®¤ à®ªà®¯à®¿à®°à¯ / à®¨à®¿à®²à¯ˆà®•à¯à®•à¯ à®¤à®©à®¿à®ªà¯à®ªà®Ÿà¯à®Ÿ à®¨à®Ÿà®µà®Ÿà®¿à®•à¯à®•à¯ˆ à®‡à®©à¯à®©à¯à®®à¯ à®‡à®²à¯à®²à¯ˆ. à®µà®¾à®°à®¾à®¨à¯à®¤à®¿à®° à®•à®£à¯à®•à®¾à®£à®¿à®ªà¯à®ªà¯ˆà®ªà¯ à®ªà®¯à®©à¯à®ªà®Ÿà¯à®¤à¯à®¤à®¿ à®‰à®³à¯à®³à¯‚à®°à¯ à®†à®²à¯‹à®šà®©à¯ˆ à®ªà¯†à®±à®µà¯à®®à¯.",
        "no_next": "à®‡à®¨à¯à®¤ à®ªà®¯à®¿à®°à¯à®•à¯à®•à¯ à®ªà®¿à®©à¯à®µà®°à¯à®®à¯ à®µà®³à®°à¯à®šà¯à®šà®¿ à®¨à®¿à®²à¯ˆ à®ªà®¤à®¿à®µà¯ à®šà¯†à®¯à¯à®¯à®ªà¯à®ªà®Ÿà®µà®¿à®²à¯à®²à¯ˆ.",
        "weather_live": "{place} à®‡à®Ÿà®¤à¯à®¤à®¿à®±à¯à®•à®¾à®© Open-Meteo à®¨à¯‡à®°à®Ÿà®¿ à®®à¯à®©à¯à®©à®±à®¿à®µà®¿à®ªà¯à®ªà¯ ({time}). à®‡à®µà¯ˆ à®¤à®¿à®Ÿà¯à®Ÿ à®‰à®¤à®µà®¿à®•à®³à¯; à®…à®¤à®¿à®•à®¾à®°à®ªà¯à®ªà¯‚à®°à¯à®µ à®Žà®šà¯à®šà®°à®¿à®•à¯à®•à¯ˆ à®…à®²à¯à®².",
        "weather_missing": "à®‡à®¨à¯à®¤ à®‡à®Ÿà®¤à¯à®¤à®¿à®±à¯à®•à®¾à®© à®¨à¯‡à®°à®Ÿà®¿ à®µà®¾à®©à®¿à®²à¯ˆ à®‡à®²à¯à®²à¯ˆ. à®®à¯à®©à¯à®©à¯†à®šà¯à®šà®°à®¿à®•à¯à®•à¯ˆ à®šà¯‡à®°à¯à®•à¯à®•à®ªà¯à®ªà®Ÿà®µà®¿à®²à¯à®²à¯ˆ; à®ªà¯à®¤à¯à®ªà¯à®ªà®¿à®•à¯à®•à®µà¯à®®à¯ à®…à®²à¯à®²à®¤à¯ à®…à®¤à®¿à®•à®¾à®°à®ªà¯à®ªà¯‚à®°à¯à®µ à®‰à®³à¯à®³à¯‚à®°à¯ à®µà®¾à®©à®¿à®²à¯ˆà®¯à¯ˆà®ªà¯ à®ªà®¾à®°à¯à®•à¯à®•à®µà¯à®®à¯.",
        "refresh": "à®¨à¯‡à®°à®Ÿà®¿ à®µà®¾à®©à®¿à®²à¯ˆà®¯à¯ˆ à®ªà¯à®¤à¯à®ªà¯à®ªà®¿",
        "duration_help": "à®®à¯à®©à¯à®©à®±à®¿à®µà®¿à®ªà¯à®ªà¯ 7 à®¨à®¾à®³à¯ à®µà®°à¯ˆ; à®¤à¯‡à®°à¯à®¨à¯à®¤ à®•à®¾à®²à®®à¯ à®®à¯à®´à¯à®¤à¯à®®à¯ à®µà®¾à®°à®¾à®¨à¯à®¤à®¿à®° à®•à®£à¯à®•à®¾à®£à®¿à®ªà¯à®ªà¯ à®¤à¯Šà®Ÿà®°à¯à®®à¯.",
        "source_title": "à®µà®¿à®µà®šà®¾à®¯ à®†à®¤à®¾à®°à®™à¯à®•à®³à¯",
        "no_recommendation": "à®‰à®°à®®à¯, à®ªà¯‚à®šà¯à®šà®¿à®•à¯à®•à¯Šà®²à¯à®²à®¿, à®µà®¿à®³à¯ˆà®šà¯à®šà®²à¯ à®ªà®°à®¿à®¨à¯à®¤à¯à®°à¯ˆ à®‰à®°à¯à®µà®¾à®•à¯à®•à®ªà¯à®ªà®Ÿà®µà®¿à®²à¯à®²à¯ˆ. à®‰à®±à¯à®¤à®¿à®¯à®¿à®²à¯à®²à®¾à®¤ à®šà¯†à®¯à®²à¯ˆ à®‰à®³à¯à®³à¯‚à®°à®¿à®²à¯ à®šà®°à®¿à®ªà®¾à®°à¯à®•à¯à®•à®µà¯à®®à¯.",
    },
}


ACTIVITY_KEYS = {
    ("rice", "tillering"): "rice_tillering",
    ("rice", "panicle"): "rice_panicle",
    ("tomato", "flowering"): "tomato_flowering",
    ("tomato", "fruit_set"): "tomato_fruit_set",
    ("banana", "vegetative"): "banana_vegetative",
    ("banana", "flowering"): "banana_flowering",
}

SOURCE_LINKS = {
    "rice": [
        ("TNAU rice irrigation", "https://agritech.tnau.ac.in/agriculture/agri_irrigationmgt_cereals_rice.html"),
        ("TNAU rice nutrient management", "https://agritech.tnau.ac.in/expert_system/paddy/nutrientmanagement.html"),
    ],
    "tomato": [
        ("TNAU tomato cultivation", "https://agritech.tnau.ac.in/horticulture/agri_seasonandvarieties_tomato.html"),
        ("TNAU tomato water management", "https://agritech.tnau.ac.in/org_farm/orgfarm_tomato_water.html"),
    ],
    "banana": [
        ("TNAU banana cultivation", "https://agritech.tnau.ac.in/horticulture/horti_fruits_banana.html"),
        ("TNAU banana irrigation management", "https://www.agritech.tnau.ac.in/expert_system/banana/irrigationmanagement.html"),
    ],
}


def _words(language: str) -> dict[str, str]:
    """Get roadmap wording through the shared translation catalog."""
    return COPY.get(language) or translate_mapping(COPY["English"], language)


def _weather_tasks(weather: dict | None, crop_id: int, words: dict[str, str]) -> list[dict]:
    """Turn only returned forecast values into dated, cautious field checks."""
    if not weather:
        return []
    daily = weather["daily"]
    tasks = []
    for index, day in enumerate(daily["time"]):
        rain = daily["precipitation_sum"][index]
        rain_chance = daily["precipitation_probability_max"][index]
        wind = daily["wind_speed_10m_max"][index]
        temperature = daily["temperature_2m_max"][index]
        code = daily["weather_code"][index]
        if rain >= 20 or (rain >= 10 and rain_chance >= 70):
            tasks.append({
                "id": f"crop-{crop_id}-weather-rain-{day}", "section": "today" if day == date.today().isoformat() else "weather",
                "label": words["rain_task"].format(day=day, rain=rain),
            })
        if code in (95, 96, 99):
            tasks.append({
                "id": f"crop-{crop_id}-weather-storm-{day}", "section": "today" if day == date.today().isoformat() else "weather",
                "label": words["storm_task"].format(day=day),
            })
        if wind >= 40:
            tasks.append({
                "id": f"crop-{crop_id}-weather-wind-{day}", "section": "today" if day == date.today().isoformat() else "weather",
                "label": words["wind_task"].format(day=day, wind=wind),
            })
        if temperature >= 40:
            tasks.append({
                "id": f"crop-{crop_id}-weather-heat-{day}", "section": "today" if day == date.today().isoformat() else "weather",
                "label": words["heat_task"].format(day=day, temp=temperature),
            })
    return tasks


def _render_checklist(task: dict, crop_id: int, words: dict[str, str]) -> None:
    key = f"roadmap_{crop_id}_{task['id']}"
    current = get_roadmap_task_status(task["id"])
    checked = st.checkbox(task["label"], value=current, key=key)
    if checked != current:
        set_roadmap_task_status(task["id"], checked)
        st.rerun()


def render_roadmap(profile: dict | None, weather: dict | None, language: str, clear_weather_cache) -> None:
    """Render a personalized checklist that updates from crop and forecast data."""
    words = _words(language)
    st.subheader(words["title"])
    st.caption(words["intro"])

    crops = get_crop_records()
    if not crops:
        st.info(words["no_crops"])
        return

    selected_id = st.selectbox(
        words["crop"],
        options=[record["crop_id"] for record in crops],
        format_func=lambda crop_id: next(
            f"{record['crop_name'] if record['crop_code'] == 'other' else crop_label(record['crop_code'], language)} · {record['planting_date']} · {record['growth_stage']}"
            for record in crops if record["crop_id"] == crop_id
        ),
    )
    crop = next(record for record in crops if record["crop_id"] == selected_id)
    duration = st.select_slider(words["duration"], options=[1, 2, 4, 8, 12], value=4,
                                format_func=lambda value: f"{value} {words['weeks']}",
                                help=words["duration_help"])

    place = ""
    if profile:
        place = ", ".join(part for part in (
            profile.get("village_or_city"), profile.get("district"), profile.get("state")
        ) if part)
    cols = st.columns(3)
    cols[0].metric(words["stage"], next(
        (stage[1]
         for stage in growth_stages(crop["crop_code"]) if stage[0] == crop["growth_stage"]),
        crop["growth_stage"],
    ))
    cols[1].metric(words["planted"], crop["planting_date"])
    cols[2].metric(words["location"], place or "—")

    if st.button(words["refresh"], icon=":material/refresh:", key="roadmap_refresh_weather"):
        clear_weather_cache()
        st.rerun()

    if weather:
        st.caption(words["weather_live"].format(place=weather["location"].get("name", place), time=weather["fetched_at"]))
    else:
        st.info(words["weather_missing"])

    crop_id = int(crop["crop_id"])
    today = date.today().isoformat()
    crop_age_days = (date.today() - date.fromisoformat(crop["planting_date"])).days
    tasks = [{
        "id": f"crop-{crop_id}-stage-check-{today}",
        "section": "today",
        "label": f"{words['stage_check']} ({words['crop_age'].format(days=crop_age_days)})",
    }]
    tasks.extend(_weather_tasks(weather, crop_id, words))
    for week in range(duration):
        week_day = date.today() + timedelta(days=week * 7)
        tasks.append({
            "id": f"crop-{crop_id}-weekly-{week_day.isocalendar().year}-{week_day.isocalendar().week}",
            "section": "weekly",
            "label": f"{week_day.strftime('%d %b')}: {words['weekly_check']}",
        })

    st.divider()
    stages = growth_stages(crop["crop_code"])
    stage_index = next((i for i, stage in enumerate(stages) if stage[0] == crop["growth_stage"]), -1)
    next_stages = stages[stage_index + 1:] if stage_index >= 0 else stages
    activity_key = ACTIVITY_KEYS.get((crop["crop_code"], crop["growth_stage"]))
    if activity_key:
        st.markdown(f"#### {words['activities']}")
        st.info(words[activity_key])
        st.caption(words["verify"])
        refs = SOURCE_LINKS.get(crop["crop_code"], [])
        if refs:
            st.caption(" · ".join(f"[{title}]({url})" for title, url in refs))
    else:
        st.markdown(f"#### {words['activities']}")
        st.info(words["no_specific"])

    st.markdown(f"#### {words['upcoming']}")
    if next_stages:
        st.caption(" → ".join(stage[1] for stage in next_stages))
        st.caption(words["verify"])
    else:
        st.caption(words["no_next"])

    st.markdown(f"#### {words['today']}")
    today_tasks = [task for task in tasks if task["section"] == "today"]
    for task in today_tasks:
        _render_checklist(task, crop_id, words)
    st.markdown(f"#### {words['weekly']}")
    for task in (task for task in tasks if task["section"] == "weekly"):
        _render_checklist(task, crop_id, words)
    st.markdown(f"#### {words['precautions']}")
    weather_tasks = [task for task in tasks if task["section"] == "weather"]
    if weather_tasks:
        for task in weather_tasks:
            _render_checklist(task, crop_id, words)
    elif weather:
        st.caption("No roadmap weather triggers were met in the available forecast. Continue to check the local forecast.")
    else:
        st.caption(words["weather_missing"])

    all_tasks = today_tasks + [task for task in tasks if task["section"] == "weekly"] + weather_tasks
    done_count = sum(get_roadmap_task_status(task["id"]) for task in all_tasks)
    st.progress(done_count / len(all_tasks) if all_tasks else 0, text=f"{words['progress']}: {done_count}/{len(all_tasks)} {words['completed']}")
    st.caption(words["no_recommendation"])
