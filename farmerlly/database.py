"""Small SQLite helpers for the farmer's local farm profile."""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATABASE_PATH = Path(__file__).resolve().parent.parent / "farmerlly.db"


def initialize_database() -> None:
    """Create the profile table the first time the app needs it."""
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS farmer_profile (
                profile_id INTEGER PRIMARY KEY CHECK (profile_id = 1),
                farmer_name TEXT NOT NULL,
                preferred_language TEXT NOT NULL,
                state TEXT NOT NULL,
                district TEXT NOT NULL,
                village_or_city TEXT NOT NULL,
                farm_size_acres REAL NOT NULL CHECK (farm_size_acres > 0),
                soil_type TEXT NOT NULL,
                water_sources TEXT NOT NULL,
                crops TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS crop_records (
                crop_id INTEGER PRIMARY KEY AUTOINCREMENT,
                crop_code TEXT NOT NULL,
                crop_name TEXT NOT NULL,
                variety TEXT NOT NULL DEFAULT '',
                planting_date TEXT NOT NULL,
                growth_stage TEXT NOT NULL,
                progress INTEGER NOT NULL CHECK (progress >= 0 AND progress <= 100),
                irrigation_method TEXT NOT NULL DEFAULT 'Unknown',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS roadmap_task_status (
                task_key TEXT PRIMARY KEY,
                is_complete INTEGER NOT NULL DEFAULT 0 CHECK (is_complete IN (0, 1)),
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS farm_alert_status (
                alert_id TEXT PRIMARY KEY,
                is_read INTEGER NOT NULL DEFAULT 0 CHECK (is_read IN (0, 1)),
                updated_at TEXT NOT NULL
            )
            """
        )
        crop_columns = {
            row[1] for row in connection.execute("PRAGMA table_info(crop_records)")
        }
        if "irrigation_method" not in crop_columns:
            connection.execute(
                "ALTER TABLE crop_records ADD COLUMN irrigation_method TEXT NOT NULL DEFAULT 'Unknown'"
            )


def get_farmer_profile() -> dict[str, Any] | None:
    """Return the saved profile, or None when this installation is new."""
    initialize_database()
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            "SELECT * FROM farmer_profile WHERE profile_id = 1"
        ).fetchone()

    if row is None:
        return None

    profile = dict(row)
    profile["water_sources"] = json.loads(profile["water_sources"])
    profile["crops"] = json.loads(profile["crops"])
    return profile


def save_farmer_profile(profile: dict[str, Any]) -> None:
    """Insert or update this installation's farmer profile."""
    initialize_database()
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    water_sources = json.dumps(profile["water_sources"], ensure_ascii=False)
    crops = json.dumps(profile["crops"], ensure_ascii=False)

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            """
            INSERT INTO farmer_profile (
                profile_id, farmer_name, preferred_language, state, district,
                village_or_city, farm_size_acres, soil_type, water_sources,
                crops, created_at, updated_at
            )
            VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(profile_id) DO UPDATE SET
                farmer_name = excluded.farmer_name,
                preferred_language = excluded.preferred_language,
                state = excluded.state,
                district = excluded.district,
                village_or_city = excluded.village_or_city,
                farm_size_acres = excluded.farm_size_acres,
                soil_type = excluded.soil_type,
                water_sources = excluded.water_sources,
                crops = excluded.crops,
                updated_at = excluded.updated_at
            """,
            (
                profile["farmer_name"],
                profile["preferred_language"],
                profile["state"],
                profile["district"],
                profile["village_or_city"],
                profile["farm_size_acres"],
                profile["soil_type"],
                water_sources,
                crops,
                now,
                now,
            ),
        )


def get_crop_records() -> list[dict[str, Any]]:
    """Return all saved crop records, newest planting date first."""
    initialize_database()
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            "SELECT * FROM crop_records ORDER BY planting_date DESC, crop_id DESC"
        ).fetchall()
    return [dict(row) for row in rows]


def add_crop_record(crop: dict[str, Any]) -> int:
    """Add a new crop record and return its database ID."""
    initialize_database()
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with sqlite3.connect(DATABASE_PATH) as connection:
        cursor = connection.execute(
            """
            INSERT INTO crop_records (
                crop_code, crop_name, variety, planting_date, growth_stage,
                progress, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                crop["crop_code"], crop["crop_name"], crop.get("variety", ""),
                crop["planting_date"], crop["growth_stage"], int(crop["progress"]),
                now, now,
            ),
        )
        return int(cursor.lastrowid)


def update_crop_record(crop_id: int, crop: dict[str, Any]) -> bool:
    """Update planting details, stage, variety, or progress for one crop."""
    initialize_database()
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with sqlite3.connect(DATABASE_PATH) as connection:
        cursor = connection.execute(
            """
            UPDATE crop_records
            SET variety = ?, planting_date = ?, growth_stage = ?, progress = ?, updated_at = ?
            WHERE crop_id = ?
            """,
            (
                crop.get("variety", ""), crop["planting_date"], crop["growth_stage"],
                int(crop["progress"]), now, int(crop_id),
            ),
        )
        return cursor.rowcount == 1


def get_roadmap_task_status(task_key: str) -> bool:
    """Return whether a generated roadmap task has been completed."""
    initialize_database()
    with sqlite3.connect(DATABASE_PATH) as connection:
        row = connection.execute(
            "SELECT is_complete FROM roadmap_task_status WHERE task_key = ?",
            (task_key,),
        ).fetchone()
    return bool(row and row[0])


def set_roadmap_task_status(task_key: str, is_complete: bool) -> None:
    """Persist completion for a roadmap task across Streamlit reruns."""
    initialize_database()
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            """
            INSERT INTO roadmap_task_status (task_key, is_complete, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(task_key) DO UPDATE SET
                is_complete = excluded.is_complete,
                updated_at = excluded.updated_at
            """,
            (task_key, int(is_complete), now),
        )


def get_alert_read_status(alert_ids: list[str]) -> dict[str, bool]:
    """Return saved read states for the requested active alerts."""
    if not alert_ids:
        return {}
    initialize_database()
    placeholders = ",".join("?" for _ in alert_ids)
    with sqlite3.connect(DATABASE_PATH) as connection:
        rows = connection.execute(
            f"SELECT alert_id, is_read FROM farm_alert_status WHERE alert_id IN ({placeholders})",
            alert_ids,
        ).fetchall()
    return {alert_id: bool(is_read) for alert_id, is_read in rows}


def set_alert_read_status(alert_id: str, is_read: bool) -> None:
    """Persist a farmer's read state for one alert."""
    initialize_database()
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            """
            INSERT INTO farm_alert_status (alert_id, is_read, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(alert_id) DO UPDATE SET
                is_read = excluded.is_read,
                updated_at = excluded.updated_at
            """,
            (alert_id, int(is_read), now),
        )


def update_crop_irrigation_method(crop_id: int, irrigation_method: str) -> bool:
    """Save the selected irrigation method with a crop record."""
    initialize_database()
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with sqlite3.connect(DATABASE_PATH) as connection:
        cursor = connection.execute(
            "UPDATE crop_records SET irrigation_method = ?, updated_at = ? WHERE crop_id = ?",
            (irrigation_method, now, int(crop_id)),
        )
        return cursor.rowcount == 1
