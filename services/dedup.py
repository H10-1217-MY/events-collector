from typing import List

from models.event import Event


def make_dedup_key(event: Event) -> tuple:
    return (
        event.title,
        event.date_text,
        event.location,
        event.source_url,
    )


def deduplicate_events(events: List[Event]) -> List[Event]:
    seen = set()
    deduped = []

    for event in events:
        key = make_dedup_key(event)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(event)

    return deduped