from models.event import Event
from services.normalize import normalize_events, split_date_range


def test_split_date_range_single():
    start, end = split_date_range("2026年4月21日")
    assert start == "2026-04-21"
    assert end == "2026-04-21"


def test_split_date_range_range():
    start, end = split_date_range("2026年4月21日～2026年5月6日")
    assert start == "2026-04-21"
    assert end == "2026-05-06"


def test_normalize_events():
    events = [
        Event(
            title="  春 の   陶器市  ",
            date_text=" 2026年4月21日 ～ 2026年5月6日 ",
            location="  別府市  ",
            area=" 大分 ",
            price=" 無料 ",
            source_name=" visit_oita_events ",
            source_url=" https://example.com/event/1 ",
        )
    ]

    normalized = normalize_events(events)

    assert normalized[0].title == "春 の 陶器市"
    assert normalized[0].location == "別府市"
    assert normalized[0].area == "大分"
    assert normalized[0].price == "無料"
    assert normalized[0].source_name == "visit_oita_events"
    assert normalized[0].source_url == "https://example.com/event/1"
    assert normalized[0].date_start == "2026-04-21"
    assert normalized[0].date_end == "2026-05-06"