import re
import logging
from typing import List
from urllib.parse import urljoin, urlparse, parse_qs

from collectors.html_collector import HtmlCollector
from models.event import Event
from urllib.parse import urljoin
import re

class VisitOitaEventsCollector(HtmlCollector):
    def __init__(self, source_config: dict):
        super().__init__(source_config)
        self.logger = logging.getLogger(self.__class__.__name__)

    def collect(self) -> List[Event]:
        base_url = self.source_config["url"]
        area = self.source_config.get("area", "")

        page_urls = self._collect_pagination_urls(base_url)
        self.logger.info("一覧ページ候補: %d件", len(page_urls))

        detail_urls = []
        seen_detail = set()

        for page_url in page_urls:
            try:
                soup = self.fetch_html(page_url)
                urls = self._extract_detail_urls(soup, base_url)
                self.logger.info("詳細URL抽出: %s -> %d件", page_url, len(urls))

                for url in urls:
                    if url not in seen_detail:
                        seen_detail.add(url)
                        detail_urls.append(url)

            except Exception as e:
                self.logger.warning("一覧ページ取得失敗: %s (%s)", page_url, e)

        self.logger.info("詳細URL候補（重複除去後）: %d件", len(detail_urls))

        events: List[Event] = []

        for detail_url in detail_urls:
            try:
                detail_soup = self.fetch_html(detail_url)
                event = self._parse_detail_page(detail_soup, detail_url, area)
                if event:
                    events.append(event)
            except Exception as e:
                self.logger.warning("詳細ページ取得失敗: %s (%s)", detail_url, e)

        return events



    def _collect_pagination_urls(self, base_url: str) -> List[str]:
        """
        最初の一覧ページからページネーションリンクを拾って、一覧ページURLを集める。
        visit-oita は /events/index/page:2 のような形式。
        """
        soup = self.fetch_html(base_url)

        urls = [base_url]
        seen = {base_url}

        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            full_url = urljoin(base_url, href)

            # 詳細ページは除外
            if "/events/detail/" in full_url:
                continue

            # /events/ 自体
            if full_url.rstrip("/") == base_url.rstrip("/"):
                if full_url not in seen:
                    seen.add(full_url)
                    urls.append(full_url)
                continue

            # /events/index/page:2 または /events/index/page%3A2 を拾う
            if re.search(r"/events/index/page(?::|%3A)\d+", full_url):
                if full_url not in seen:
                    seen.add(full_url)
                    urls.append(full_url)

        urls.sort(key=self._page_sort_key)
        return urls


    def _page_sort_key(self, url: str) -> int:
        if url.rstrip("/") == self.source_config["url"].rstrip("/"):
            return 1

        m = re.search(r"/events/index/page(?::|%3A)(\d+)", url)
        if m:
            return int(m.group(1))

        return 999999

    def _extract_detail_urls(self, soup, base_url: str) -> List[str]:
        """
        一覧ページから /events/detail/ を含むURLを拾う。
        """
        urls = []
        seen = set()

        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if "/events/detail/" not in href:
                continue

            full_url = urljoin(base_url, href)

            if full_url in seen:
                continue

            seen.add(full_url)
            urls.append(full_url)

        return urls

    def _parse_detail_page(self, soup, detail_url: str, area: str) -> Event | None:
        title = self._extract_title(soup)
        date_text = self._extract_labeled_value(soup, "開催期間")
        location = self._extract_labeled_value(soup, "開催地")
        official_url = self._extract_homepage_url(soup)

        if not title:
            self.logger.warning("タイトル未取得のためスキップ: %s", detail_url)
            return None

        return Event(
            title=title,
            date_text=date_text,
            location=location,
            area=area,
            price="",
            source_name=self.name,
            source_url=detail_url,
        )

    def _extract_title(self, soup) -> str:
        candidates = []

        for tag_name in ["h1", "h2", "title"]:
            for tag in soup.find_all(tag_name):
                text = tag.get_text(" ", strip=True)
                if text:
                    candidates.append(text)

        if not candidates:
            return ""

        for text in candidates:
            if text not in {"イベント", "イベント情報"} and len(text) >= 4:
                return text

        return candidates[0]

    def _extract_labeled_value(self, soup, label: str) -> str:
        label_node = soup.find(string=lambda s: s and label in s)
        if not label_node:
            return ""

        parent = label_node.parent
        texts = []

        if parent:
            for elem in parent.next_elements:
                if getattr(elem, "name", None) in {"script", "style"}:
                    continue

                text = ""
                if hasattr(elem, "get_text"):
                    text = elem.get_text(" ", strip=True)
                elif isinstance(elem, str):
                    text = elem.strip()

                if not text:
                    continue
                if text == label:
                    continue

                texts.append(text)

                if len(texts) >= 1:
                    break

        return texts[0] if texts else ""

    def _extract_homepage_url(self, soup) -> str:
        homepage_label = soup.find(string=lambda s: s and "ホームページ" in s)
        if not homepage_label:
            return ""

        url_pattern = re.compile(r"^https?://")

        for elem in homepage_label.parent.next_elements if homepage_label.parent else []:
            if hasattr(elem, "get_text"):
                text = elem.get_text(" ", strip=True)
            elif isinstance(elem, str):
                text = elem.strip()
            else:
                text = ""

            if text and url_pattern.match(text):
                return text

            if getattr(elem, "name", None) == "a":
                href = elem.get("href", "").strip()
                if href and url_pattern.match(href):
                    return href

        return ""