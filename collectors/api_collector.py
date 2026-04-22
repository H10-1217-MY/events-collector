from typing import Any, Dict
import requests

from collectors.base import BaseCollector


class ApiCollector(BaseCollector):
    def fetch_json(self, url: str, headers: Dict[str, str] | None = None, timeout: int = 10) -> Any:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response.json()