import re
from typing import List, Tuple

from models.event import Event


def normalize_text(value: str) -> str:
    return " ".join(value.strip().split())


def to_iso_date(text: str) -> str:
    """
    '2026年4月21日' -> '2026-04-21'
    """
    text = normalize_text(text)

    m = re.search(r"(\d{4})年\s*(\d{1,2})月\s*(\d{1,2})日", text)
    if not m:
        return ""

    year = int(m.group(1))
    month = int(m.group(2))
    day = int(m.group(3))

    return f"{year:04d}-{month:02d}-{day:02d}"


def split_date_range(date_text: str) -> Tuple[str, str]:
    """
    開催期間文字列から開始日・終了日をざっくり抜く。
    対応例:
      - 2026年4月21日
      - 2026年4月21日～2026年5月6日
      - 2026年4月21日 - 2026年5月6日
      - 2026年4月21日〜2026年5月6日
    """
    text = normalize_text(date_text)

    # 区切り記号を統一
    unified = (
        text.replace("〜", "～")
        .replace("—", "～")
        .replace("–", "～")
        .replace(" - ", "～")
        .replace("-", "～")
    )

    parts = [p.strip() for p in unified.split("～") if p.strip()]

    if len(parts) == 1:
        start = to_iso_date(parts[0])
        return start, start

    if len(parts) >= 2:
        start = to_iso_date(parts[0])
        end = to_iso_date(parts[1])
        return start, end

    return "", ""


def normalize_events(events: List[Event]) -> List[Event]:
    normalized = []

    for event in events:
        title = normalize_text(event.title)
        date_text = normalize_text(event.date_text)
        location = normalize_text(event.location)
        area = normalize_text(event.area)
        price = normalize_text(event.price)
        source_name = normalize_text(event.source_name)
        source_url = event.source_url.strip()

        date_start, date_end = split_date_range(date_text)

        normalized.append(
            Event(
                title=title,
                date_text=date_text,
                date_start=date_start,
                date_end=date_end,
                location=location,
                area=area,
                price=price,
                source_name=source_name,
                source_url=source_url,
                fetched_at=event.fetched_at,
            )
        )

    return normalized