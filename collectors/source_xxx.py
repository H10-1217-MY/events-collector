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
    

class CrossroadFukuokaCollector(HtmlCollector):
    def __init__(self, source_config: dict):
        super().__init__(source_config)
        self.logger = logging.getLogger(self.__class__.__name__)

    def collect(self) -> List[Event]:
        base_url = self.source_config["url"]
        area = self.source_config.get("area", "")

        soup = self.fetch_html(base_url)

        detail_urls = self._extract_detail_urls(soup, base_url)
        self.logger.info("詳細URL候補: %d件", len(detail_urls))

        events: List[Event] = []

        for detail_url in detail_urls:
            try:
                detail_soup = self.fetch_html(detail_url)
                event = self._parse_detail_page(detail_soup, detail_url, area)

                if event:
                    events.append(event)

            except Exception as e:
                self.logger.warning("詳細取得失敗: %s (%s)", detail_url, e)

        self.logger.info("取得イベント数: %d", len(events))
        return events

    def _extract_detail_urls(self, soup, base_url: str) -> List[str]:
        urls = []
        seen = set()

        for a in soup.find_all("a", href=True):
            href = a.get("href", "").strip()

            # /event/数字 の詳細ページだけ拾う
            if not re.search(r"/event/\d+/?$", href):
                continue

            full_url = urljoin(base_url, href)

            if full_url in seen:
                continue

            seen.add(full_url)
            urls.append(full_url)

        return urls

    def _parse_detail_page(self, soup, detail_url: str, area: str) -> Event | None:
        title = self._extract_title(soup)
        date_text = self._extract_labeled_value(soup, ["開催日", "開催期間"])
        location = self._extract_labeled_value(soup, ["住所", "開催地"])

        if not title:
            self.logger.warning("タイトル未取得のためスキップ: %s", detail_url)
            return None

        # 明らかにページ全体を巻き込んでいるタイトルは除外
        if len(title) > 80:
            self.logger.warning("タイトルが長すぎるためスキップ: %s / %s", title[:80], detail_url)
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
        """
        Crossroad Fukuoka は h1 にイベント名が入る想定。
        h2/h3 は PR・関連記事・基本情報などを拾いやすいので使わない。
        """
        h1 = soup.find("h1")
        if h1:
            text = h1.get_text(" ", strip=True)
            text = self._clean_text(text)

            if text and not self._is_bad_title(text):
                return text

        # fallback: titleタグ
        title_tag = soup.find("title")
        if title_tag:
            text = self._clean_text(title_tag.get_text(" ", strip=True))

            text = text.replace("| 福岡県観光情報 クロスロードふくおか", "").strip()
            text = text.replace("〖公式〗福岡県の観光/旅行情報サイト「クロスロードふくおか」", "").strip()
            text = text.replace(" | クロスロードふくおか", "").strip()

            if text and not self._is_bad_title(text):
                return text

        return ""

    def _extract_labeled_value(self, soup, labels: list[str]) -> str:

        for label in labels:
            node = soup.find(string=lambda s: s and label in s)
            if not node:
                continue

            parent = node.parent
            if not parent:
                continue

            # 同じ親要素内で dt/dd 構造がある場合
            next_sibling = parent.find_next_sibling()
            if next_sibling:
                text = self._clean_text(next_sibling.get_text(" ", strip=True))
                if text and text != label and len(text) < 300:
                    return text

            # fallback: 次の要素から短い値だけ拾う
            for elem in parent.next_elements:
                text = ""

                if hasattr(elem, "get_text"):
                    text = elem.get_text(" ", strip=True)
                elif isinstance(elem, str):
                    text = elem.strip()

                text = self._clean_text(text)

                if not text:
                    continue

                if text == label:
                    continue

                if len(text) >= 300:
                    continue

                return text

        return ""

    def _clean_text(self, text: str) -> str:
        return " ".join(text.strip().split())

    def _is_bad_title(self, text: str) -> bool:
        if not text:
            return True

        if len(text) > 80:
            return True

        # 完全一致で除外する見出し
        exact_bad_titles = {
            "PR",
            "基本情報",
            "SHARE",
            "周辺にあるスポット",
            "このスポットの関連記事",
            "いま読まれている特集記事",
            "関連記事",
        }

        if text in exact_bad_titles:
            return True

        bad_keywords = [
            "特集",
            "モデルコース",
            "観光スポット",
            "体験プラン",
            "宿泊",
            "アクセス",
            "お気に入り",
            "Main Menu",
            "メインメニュー",
            "Language",
            "HOME",
        ]

        # ナビ語が複数入っているタイトルは除外
        hit_count = sum(1 for word in bad_keywords if word in text)
        if hit_count >= 2:
            return True

        return False