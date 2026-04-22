import csv
import json
import sqlite3
from pathlib import Path
from typing import List

from models.event import Event


def init_db(db_path: str) -> None:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            date_text TEXT,
            date_start TEXT,
            date_end TEXT,
            location TEXT,
            area TEXT,
            price TEXT,
            source_name TEXT,
            source_url TEXT,
            fetched_at TEXT
        )
        """
    )

    conn.commit()
    conn.close()


def save_events_to_sqlite(db_path: str, events: List[Event]) -> None:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("DELETE FROM events")

    cur.executemany(
        """
        INSERT INTO events (
            title, date_text, date_start, date_end,
            location, area, price,
            source_name, source_url, fetched_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                e.title,
                e.date_text,
                e.date_start,
                e.date_end,
                e.location,
                e.area,
                e.price,
                e.source_name,
                e.source_url,
                e.fetched_at,
            )
            for e in events
        ],
    )

    conn.commit()
    conn.close()


def save_events_to_csv(csv_path: str, events: List[Event]) -> None:
    Path(csv_path).parent.mkdir(parents=True, exist_ok=True)

    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "title",
                "date_text",
                "date_start",
                "date_end",
                "location",
                "area",
                "price",
                "source_name",
                "source_url",
                "fetched_at",
            ],
        )
        writer.writeheader()
        for event in events:
            writer.writerow(event.model_dump())


def save_events_to_json(json_path: str, events: List[Event]) -> None:
    Path(json_path).parent.mkdir(parents=True, exist_ok=True)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(
            [event.model_dump() for event in events],
            f,
            ensure_ascii=False,
            indent=2,
        )