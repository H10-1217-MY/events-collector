from bs4 import BeautifulSoup
import requests

from collectors.base import BaseCollector


class HtmlCollector(BaseCollector):
    def fetch_html(self, url: str, headers: dict | None = None, timeout: int = 10) -> BeautifulSoup:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")