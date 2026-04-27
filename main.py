from pathlib import Path
import logging
import yaml
from collectors.source_xxx import VisitOitaEventsCollector,CrossroadFukuokaCollector

from services.normalize import normalize_events
from services.dedup import deduplicate_events
from services.storage import (
    init_db,
    save_events_to_sqlite,
    save_events_to_csv,
    save_events_to_json,
)


def setup_logging() -> None:
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler("logs/app.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def load_config(config_path: str = "config/sources.yaml") -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_collectors(config: dict):
    collectors = []

    for source in config.get("sources", []):
        if not source.get("enabled", False):
            continue

        source_type = source.get("type")
        source_name = source.get("name", "")

        if source_type == "html" and source_name == "visit_oita_events":
            collectors.append(VisitOitaEventsCollector(source))

        elif source_type == "html" and source_name == "crossroad_fukuoka_events":
            collectors.append(CrossroadFukuokaCollector(source))

        else:
            logging.warning("未対応のsourceです: type=%s name=%s", source_type, source_name)

    return collectors


def main() -> None:
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("event-collector 開始")

    config = load_config()
    collectors = build_collectors(config)

    all_events = []
    for collector in collectors:
        try:
            events = collector.collect()
            logger.info("%s: %d 件取得", collector.name, len(events))
            all_events.extend(events)
        except Exception as e:
            logger.exception("collector 実行中にエラー: %s", e)

    normalized = normalize_events(all_events)
    deduped = deduplicate_events(normalized)

    init_db("db/events.db")
    save_events_to_sqlite("db/events.db", deduped)
    save_events_to_csv("outputs/events.csv", deduped)
    save_events_to_json("outputs/events.json", deduped)

    logger.info(
        "完了: raw=%d normalized=%d deduped=%d",
        len(all_events),
        len(normalized),
        len(deduped),
    )


if __name__ == "__main__":
    main()