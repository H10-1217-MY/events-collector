from datetime import datetime
from pydantic import BaseModel, Field


class Event(BaseModel):
    title: str
    date_text: str = ""
    date_start: str = ""
    date_end: str = ""
    location: str = ""
    area: str = ""
    price: str = ""
    source_name: str
    source_url: str
    fetched_at: str = Field(default_factory=lambda: datetime.now().isoformat())