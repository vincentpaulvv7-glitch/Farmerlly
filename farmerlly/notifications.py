"""Build dashboard notifications from saved farm records and live forecasts."""

from datetime import date
import hashlib

import streamlit as st

from farmerlly.crop_catalog import crop_label, growth_stages
from farmerlly.i18n import translate, translate_mapping
from farmerlly.database import (
    get_alert_read_status,
    get_crop_records,
    get_roadmap_task_status,
    set_alert_read_status,
)
from farmerlly.roadmap import ACTIVITY_KEYS, _words as roadmap_words
from modules.weather import get_weather_alerts


COPY = {
    "English": {
        "title": "Notifications",
        "unread": "{count} unread",
        "none": "You’re all caught up. No active alerts.",
        "read": "Mark as read",
        "hidden": "{count} read notification(s) hidden.",
        "weather": "Weather update",
        "thunderstorm": "Thunderstorms are forecast for {day}. Check official local alerts and avoid exposed field work during lightning.",
        "heavy_rain": "Heavy rainfall is forecast for {day}: {value:g} mm. Check field drainage and local advisories.",
        "high_temperature": "High temperature is forecast for {day}: {value:g} °C. Monitor crop stress and follow local guidance.",
        "strong_wind": "Strong winds are forecast for {day}: {value:g} km/h. Check local conditions before exposed or spray work.",
        "task": "Farming task due today",
        "stage_task": "{crop}: check the field against its recorded growth stage and update the crop record if it has changed.",
        "weekly_task": "{crop}: complete this week’s field scouting for crop condition, pests, disease symptoms, weeds, and soil moisture.",
        "activity": "Important crop growth activity",
        "activity_body": "{crop} is recorded at the {stage} stage. Review this stage-specific guidance in the Smart Farming Roadmap.",
        "not_official": "Forecast-based planning cue, not an official warning.",
    },
    "\u0ba4\u0bae\u0bbf\u0bb4\u0bcd": {
        "title": "\u0b85\u0bb1\u0bbf\u0bb5\u0bbf\u0baa\u0bcd\u0baa\u0bc1\u0b95\u0bb3\u0bcd",
        "unread": "\u0baa\u0b9f\u0bbf\u0b95\u0bcd\u0b95\u0bbe\u0ba4 {count}",
        "none": "\u0baa\u0bc1\u0ba4\u0bbf\u0baf \u0b85\u0bb1\u0bbf\u0bb5\u0bbf\u0baa\u0bcd\u0baa\u0bc1\u0b95\u0bb3\u0bcd \u0b87\u0bb2\u0bcd\u0bb2\u0bc8.",
        "read": "\u0baa\u0b9f\u0bbf\u0ba4\u0bcd\u0ba4\u0ba4\u0bbe\u0b95\u0b95\u0bcd \u0b95\u0bc1\u0bb1\u0bbf\u0b95\u0bcd\u0b95\u0bb5\u0bc1\u0bae\u0bcd",
        "hidden": "\u0baa\u0b9f\u0bbf\u0ba4\u0bcd\u0ba4 {count} \u0b85\u0bb1\u0bbf\u0bb5\u0bbf\u0baa\u0bcd\u0baa\u0bc1\u0b95\u0bb3\u0bcd \u0bae\u0bb1\u0bc8\u0b95\u0bcd\u0b95\u0baa\u0bcd\u0baa\u0b9f\u0bcd\u0b9f\u0ba9.",
        "weather": "\u0bb5\u0bbe\u0ba9\u0bbf\u0bb2\u0bc8 \u0bae\u0bc1\u0ba9\u0bcd\u0ba9\u0bb1\u0bbf\u0bb5\u0bbf\u0baa\u0bcd\u0baa\u0bc1",
        "thunderstorm": "{day} \u0b85\u0ba9\u0bcd\u0bb1\u0bc1 \u0b87\u0b9f\u0bbf\u0baf\u0bc1\u0b9f\u0ba9\u0bcd \u0b95\u0bc2\u0b9f\u0bbf\u0baf \u0bae\u0bb4\u0bc8 \u0bae\u0bc1\u0ba9\u0bcd\u0ba9\u0bb1\u0bbf\u0bb5\u0bbf\u0b95\u0bcd\u0b95\u0baa\u0bcd\u0baa\u0b9f\u0bcd\u0b9f\u0bc1\u0bb3\u0bcd\u0bb3\u0ba4\u0bc1. \u0b85\u0ba4\u0bbf\u0b95\u0bbe\u0bb0\u0baa\u0bcd\u0baa\u0bc2\u0bb0\u0bcd\u0bb5 \u0b89\u0bb3\u0bcd\u0bb3\u0bc2\u0bb0\u0bcd \u0b85\u0bb1\u0bbf\u0bb5\u0bbf\u0baa\u0bcd\u0baa\u0bc1\u0b95\u0bb3\u0bc8\u0baa\u0bcd \u0baa\u0bbe\u0bb0\u0bcd\u0b95\u0bcd\u0b95\u0bb5\u0bc1\u0bae\u0bcd.",
        "heavy_rain": "{day} \u0b85\u0ba9\u0bcd\u0bb1\u0bc1 \u0b95\u0ba9\u0bae\u0bb4\u0bc8 \u0bae\u0bc1\u0ba9\u0bcd\u0ba9\u0bb1\u0bbf\u0bb5\u0bc1: {value:g} mm. \u0bb5\u0baf\u0bb2\u0bcd \u0ba8\u0bc0\u0bb0\u0bcd\u0bb5\u0b9f\u0bbf\u0b95\u0bbe\u0bb2\u0bc8\u0baf\u0bc1\u0bae\u0bcd \u0b89\u0bb3\u0bcd\u0bb3\u0bc2\u0bb0\u0bcd \u0b85\u0bb1\u0bbf\u0bb5\u0bc1\u0bb0\u0bc8\u0b95\u0bb3\u0bc8\u0baf\u0bc1\u0bae\u0bcd \u0b9a\u0bb0\u0bbf\u0baa\u0bbe\u0bb0\u0bcd\u0b95\u0bcd\u0b95\u0bb5\u0bc1\u0bae\u0bcd.",
        "high_temperature": "{day} \u0b85\u0ba9\u0bcd\u0bb1\u0bc1 \u0b85\u0ba4\u0bbf\u0b95 \u0b89\u0bb7\u0bcd\u0ba3\u0bae\u0bcd: {value:g} \u00b0C. \u0baa\u0baf\u0bbf\u0bb0\u0bcd \u0baa\u0bbe\u0ba4\u0bbf\u0baa\u0bcd\u0baa\u0bc8\u0b95\u0bcd \u0b95\u0bb5\u0ba9\u0bbf\u0ba4\u0bcd\u0ba4\u0bc1, \u0b89\u0bb3\u0bcd\u0bb3\u0bc2\u0bb0\u0bcd \u0bb5\u0bb4\u0bbf\u0b95\u0bbe\u0b9f\u0bcd\u0b9f\u0bb2\u0bc8\u0baa\u0bcd \u0baa\u0bbf\u0ba9\u0bcd\u0baa\u0bb1\u0bcd\u0bb1\u0bb5\u0bc1\u0bae\u0bcd.",
        "strong_wind": "{day} \u0b85\u0ba9\u0bcd\u0bb1\u0bc1 \u0baa\u0bb2\u0ba4\u0bcd\u0ba4 \u0b95\u0bbe\u0bb1\u0bcd\u0bb1\u0bc1: {value:g} km/h. \u0bb5\u0bc6\u0bb3\u0bbf\u0baa\u0bcd\u0baa\u0bc1\u0bb1 \u0bb5\u0bc7\u0bb2\u0bc8 \u0b85\u0bb2\u0bcd\u0bb2\u0ba4\u0bc1 \u0ba4\u0bc6\u0bb3\u0bbf\u0baa\u0bcd\u0baa\u0bc1\u0ba4\u0bc8\u0b95\u0bcd\u0b95\u0bc1 \u0bae\u0bc1\u0ba9\u0bcd \u0b89\u0bb3\u0bcd\u0bb3\u0bc2\u0bb0\u0bcd \u0b9a\u0bc2\u0bb4\u0bb2\u0bc8\u0b9a\u0bcd \u0b9a\u0bb0\u0bbf\u0baa\u0bbe\u0bb0\u0bcd\u0b95\u0bcd\u0b95\u0bb5\u0bc1\u0bae\u0bcd.",
        "task": "\u0b87\u0ba9\u0bcd\u0bb1\u0bc8\u0baf \u0bb5\u0bbf\u0bb5\u0b9a\u0bbe\u0baf\u0baa\u0bcd \u0baa\u0ba3\u0bbf",
        "stage_task": "{crop}: \u0baa\u0ba4\u0bbf\u0bb5\u0bc1\u0b9a\u0bc6\u0baf\u0bcd\u0baf\u0baa\u0bcd\u0baa\u0b9f\u0bcd\u0b9f \u0bb5\u0bb3\u0bb0\u0bcd\u0b9a\u0bcd\u0b9a\u0bbf \u0ba8\u0bbf\u0bb2\u0bc8\u0baf\u0bc1\u0b9f\u0ba9\u0bcd \u0bb5\u0baf\u0bb2\u0bc8\u0baa\u0bcd \u0baa\u0bb0\u0bbf\u0b9a\u0bcb\u0ba4\u0bbf\u0ba4\u0bcd\u0ba4\u0bc1, \u0bae\u0bbe\u0bb1\u0bbf\u0baf\u0bbf\u0bb0\u0bc1\u0ba8\u0bcd\u0ba4\u0bbe\u0bb2\u0bcd \u0baa\u0baf\u0bbf\u0bb0\u0bcd \u0baa\u0ba4\u0bbf\u0bb5\u0bc8\u0baa\u0bcd \u0baa\u0bc1\u0ba4\u0bc1\u0baa\u0bcd\u0baa\u0bbf\u0b95\u0bcd\u0b95\u0bb5\u0bc1\u0bae\u0bcd.",
        "weekly_task": "{crop}: \u0baa\u0baf\u0bbf\u0bb0\u0bcd \u0ba8\u0bbf\u0bb2\u0bc8, \u0baa\u0bc2\u0b9a\u0bcd\u0b9a\u0bbf, \u0ba8\u0bcb\u0baf\u0bcd \u0b85\u0bb1\u0bbf\u0b95\u0bc1\u0bb1\u0bbf\u0b95\u0bb3\u0bcd, \u0b95\u0bb3\u0bc8, \u0bae\u0ba3\u0bcd \u0b88\u0bb0\u0baa\u0bcd\u0baa\u0ba4\u0bae\u0bcd \u0b86\u0b95\u0bbf\u0baf\u0bb5\u0bb1\u0bcd\u0bb1\u0bc8 \u0b87\u0ba8\u0bcd\u0ba4 \u0bb5\u0bbe\u0bb0\u0bae\u0bcd \u0b95\u0ba3\u0bcd\u0b95\u0bbe\u0ba3\u0bbf\u0b95\u0bcd\u0b95\u0bb5\u0bc1\u0bae\u0bcd.",
        "activity": "\u0bae\u0bc1\u0b95\u0bcd\u0b95\u0bbf\u0baf \u0baa\u0baf\u0bbf\u0bb0\u0bcd \u0bb5\u0bb3\u0bb0\u0bcd\u0b9a\u0bcd\u0b9a\u0bbf \u0ba8\u0b9f\u0bb5\u0b9f\u0bbf\u0b95\u0bcd\u0b95\u0bc8",
        "activity_body": "{crop} \u0ba4\u0bb1\u0bcd\u0baa\u0bcb\u0ba4\u0bc1 {stage} \u0ba8\u0bbf\u0bb2\u0bc8\u0baf\u0bbf\u0bb2\u0bcd \u0baa\u0ba4\u0bbf\u0bb5\u0bc1\u0b9a\u0bc6\u0baf\u0bcd\u0baf\u0baa\u0bcd\u0baa\u0b9f\u0bcd\u0b9f\u0bc1\u0bb3\u0bcd\u0bb3\u0ba4\u0bc1. Smart Farming Roadmap-\u0b87\u0bb2\u0bcd \u0b87\u0ba8\u0bcd\u0ba4 \u0ba8\u0bbf\u0bb2\u0bc8\u0b95\u0bcd\u0b95\u0bbe\u0ba9 \u0bb5\u0bb4\u0bbf\u0b95\u0bbe\u0b9f\u0bcd\u0b9f\u0bb2\u0bc8\u0baa\u0bcd \u0baa\u0bbe\u0bb0\u0bcd\u0b95\u0bcd\u0b95\u0bb5\u0bc1\u0bae\u0bcd.",
        "not_official": "\u0bae\u0bc1\u0ba9\u0bcd\u0ba9\u0bb1\u0bbf\u0bb5\u0bbf\u0baa\u0bcd\u0baa\u0bc1\u0b95\u0bb3\u0bc8\u0baa\u0bcd \u0baa\u0baf\u0ba9\u0bcd\u0baa\u0b9f\u0bc1\u0ba4\u0bcd\u0ba4\u0bbf\u0baf \u0ba4\u0bbf\u0b9f\u0bcd\u0b9f\u0bae\u0bbf\u0b9f\u0bc1\u0ba4\u0bb2\u0bcd \u0b95\u0bc1\u0bb1\u0bbf\u0baa\u0bcd\u0baa\u0bc1; \u0b85\u0ba4\u0bbf\u0b95\u0bbe\u0bb0\u0baa\u0bcd\u0baa\u0bc2\u0bb0\u0bcd\u0bb5 \u0b8e\u0b9a\u0bcd\u0b9a\u0bb0\u0bbf\u0b95\u0bcd\u0b95\u0bc8 \u0b85\u0bb2\u0bcd\u0bb2.",
    },
}

TAMIL_LANGUAGE_KEY = "\u0ba4\u0bae\u0bbf\u0bb4\u0bcd"


def _copy_for(language: str) -> dict[str, str]:
    """Use Tamil copy for the app's non-English language option."""
    return COPY.get(language) or translate_mapping(COPY["English"], language)


def build_alerts(profile: dict | None, weather: dict | None, language: str) -> list[dict]:
    """Create only currently relevant alerts from live or saved app data."""
    text = _copy_for(language)
    alerts = []
    if weather:
        location = weather.get("location", {})
        location_key = "-".join(
            str(location.get(part, "")) for part in ("name", "admin1", "admin2")
        ).lower().replace(" ", "-")
        for item in get_weather_alerts(weather.get("daily", {})):
            kind = item["type"]
            template = text.get(kind)
            if not template:
                continue
            alert_id = f"weather:{location_key}:{kind}:{item['day']}"
            alerts.append({
                "id": alert_id,
                "title": text["weather"],
                "message": template.format(
                    day=item["day"], value=item.get("value", 0)
                ),
                "kind": "weather",
                "level": "warning" if item["level"] == "warning" else "caution",
                "note": text["not_official"],
            })

    words = roadmap_words(language)
    today = date.today()
    today_key = today.isoformat()
    week = today.isocalendar()
    for crop in get_crop_records():
        if crop["growth_stage"] == "harvested" or date.fromisoformat(crop["planting_date"]) > today:
            continue
        crop_name = crop["crop_name"] if crop["crop_code"] == "other" else crop_label(crop["crop_code"], language)
        crop_id = int(crop["crop_id"])

        stage_task_id = f"crop-{crop_id}-stage-check-{today_key}"
        if not get_roadmap_task_status(stage_task_id):
            alerts.append({
                "id": f"task:{stage_task_id}",
                "title": text["task"],
                "message": text["stage_task"].format(crop=crop_name),
                "kind": "task",
                "level": "task",
                "task_id": stage_task_id,
            })

        weekly_task_id = f"crop-{crop_id}-weekly-{week.year}-{week.week}"
        if not get_roadmap_task_status(weekly_task_id):
            alerts.append({
                "id": f"task:{weekly_task_id}",
                "title": text["task"],
                "message": text["weekly_task"].format(crop=crop_name),
                "kind": "task",
                "level": "task",
                "task_id": weekly_task_id,
            })

        activity_key = ACTIVITY_KEYS.get((crop["crop_code"], crop["growth_stage"]))
        if activity_key:
            stage_label = next(
                (translate(stage[1], language)
                 for stage in growth_stages(crop["crop_code"])
                 if stage[0] == crop["growth_stage"]), crop["growth_stage"]
            )
            alerts.append({
                "id": f"growth:{crop_id}:{crop['growth_stage']}",
                "title": text["activity"],
                "message": text["activity_body"].format(crop=crop_name, stage=stage_label),
                "kind": "growth",
                "level": "activity",
                "guidance": words[activity_key],
            })

    return alerts


def render_notification_center(profile: dict | None, weather: dict | None, language: str) -> None:
    """Show current dashboard alerts and save read state in SQLite."""
    text = _copy_for(language)
    alerts = build_alerts(profile, weather, language)
    saved = get_alert_read_status([alert["id"] for alert in alerts])
    unread = [alert for alert in alerts if not saved.get(alert["id"], False)]

    with st.expander(f"🔔 {text['title']} · {text['unread'].format(count=len(unread))}", expanded=False):
        if not alerts:
            st.caption(text["none"])
            return
        if not unread:
            st.success(text["none"], icon=":material/check_circle:")
        for alert in alerts:
            is_read = saved.get(alert["id"], False)
            if is_read:
                continue
            with st.container(border=True):
                st.markdown(f"**{alert['title']}**")
                if alert["level"] in ("warning", "caution"):
                    st.warning(alert["message"], icon=":material/notifications_active:")
                else:
                    st.info(alert["message"], icon=":material/task_alt:")
                if alert.get("guidance"):
                    st.caption(alert["guidance"])
                    st.caption(roadmap_words(language)["verify"])
                if alert.get("note"):
                    st.caption(alert["note"])
                widget_key = "alert_read_" + hashlib.sha1(alert["id"].encode()).hexdigest()[:12]
                checked = st.checkbox(text["read"], key=widget_key)
                if checked:
                    set_alert_read_status(alert["id"], True)
                    st.rerun()
        read_count = len(alerts) - len(unread)
        if read_count:
            st.caption(text["hidden"].format(count=read_count))
