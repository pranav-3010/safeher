import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple
import requests
from sqlalchemy.orm import Session
from app.agents.base_agent import DataSourceAgent
from app.models.incidents import NewsArticle
from app.services.data_processing import generate_content_hash, clean_text_string, normalize_utc_timestamp
from app.core.logging import logger


class NewsDataAgent(DataSourceAgent):
    """
    Ingestion Agent for Real Public News RSS feeds and Media APIs.
    Deduplicates using SHA-256 content hashes without storing copyrighted full text unnecessarily.
    """

    def __init__(self, source_name: str = "Google News RSS - Women Safety India"):
        super().__init__(source_name=source_name, source_type="news")

    def fetch(self, rss_url: str = "https://news.google.com/rss/search?q=women+safety+india&hl=en-IN", timeout_sec: int = 10) -> List[Dict[str, Any]]:
        """
        Fetches public RSS XML items from target URL.
        """
        try:
            headers = {"User-Agent": "SafeHer-IngestionBot/1.0 (+https://github.com/pranav-3010/safeher)"}
            res = requests.get(rss_url, headers=headers, timeout=timeout_sec)
            if res.status_code != 200:
                logger.warning(f"News RSS fetch returned HTTP status {res.status_code}")
                return []

            root = ET.fromstring(res.content)
            items = []
            for item in root.findall(".//item"):
                title = item.findtext("title")
                link = item.findtext("link")
                pub_date = item.findtext("pubDate")
                description = item.findtext("description")
                source_elem = item.find("source")
                publisher = source_elem.text if source_elem is not None else "Google News"

                if title and link:
                    items.append({
                        "title": title,
                        "url": link,
                        "publisher": publisher,
                        "description": description,
                        "published_at": pub_date
                    })
            return items
        except Exception as e:
            logger.error(f"Failed to fetch RSS news items: {e}")
            return []

    def validate(self, raw_records: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
        """
        Validates news article title and publisher presence.
        """
        valid = []
        rejected = 0
        for r in raw_records:
            title = clean_text_string(r.get("title"))
            publisher = clean_text_string(r.get("publisher")) or "Unknown Publisher"
            url = clean_text_string(r.get("url"))

            if not title or not url:
                rejected += 1
                continue

            content_hash = generate_content_hash(publisher, title, url)
            valid.append({
                "title": title,
                "publisher": publisher,
                "url": url,
                "description": clean_text_string(r.get("description")),
                "published_at": r.get("published_at"),
                "content_hash": content_hash
            })

        return valid, rejected

    def normalize(self, validated_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalizes timestamps and content attributes.
        """
        normalized = []
        for r in validated_records:
            pub_raw = r["published_at"]
            pub_dt = None
            if pub_raw:
                try:
                    # Attempt email/RFC 822 pubDate parsing or ISO format
                    pub_dt = datetime.strptime(pub_raw[:25], "%a, %d %b %Y %H:%M:%S")
                except Exception:
                    pub_dt = datetime.now(timezone.utc)

            r["published_at"] = normalize_utc_timestamp(pub_dt)
            r["retrieved_at"] = datetime.now(timezone.utc)
            normalized.append(r)
        return normalized

    def deduplicate(self, db: Session, normalized_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Incremental deduplication using content_hash against database.
        """
        hashes = [r["content_hash"] for r in normalized_records]
        if not hashes:
            return []

        existing_hashes = set(
            row[0] for row in db.query(NewsArticle.content_hash).filter(NewsArticle.content_hash.in_(hashes)).all()
        )

        return [r for r in normalized_records if r["content_hash"] not in existing_hashes]

    def store(self, db: Session, data_source_id: Any, records: List[Dict[str, Any]]) -> int:
        """
        Stores non-duplicate news articles into news_articles table.
        """
        if not records:
            return 0

        inserted_count = 0
        for r in records:
            article = NewsArticle(
                data_source_id=data_source_id,
                title=r["title"],
                publisher=r["publisher"],
                url=r["url"],
                description=r["description"],
                published_at=r["published_at"],
                retrieved_at=r["retrieved_at"],
                content_hash=r["content_hash"],
                processing_status="PENDING",
                llm_processed=False
            )
            db.add(article)
            inserted_count += 1

        db.commit()
        return inserted_count
