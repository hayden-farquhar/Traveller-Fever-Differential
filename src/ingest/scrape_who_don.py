"""WHO Disease Outbreak News (DON) scraper for live outbreak signals.

Uses the WHO Sitefinity OData API (primary) with RSS fallback.
Classifies entries by (region, diagnosis) and appends to monthly
JSONL archive files.

Output: data/raw/who_don_archive/YYYY-MM.jsonl (append-only)

Usage:
    python -m src.ingest.scrape_who_don
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError

import feedparser

from src.ingest.signal_classifier import ClassifiedSignal, classify_signal
from src.utils import RAW_DIR, ensure_dirs

logger = logging.getLogger(__name__)

# Primary: WHO Sitefinity OData API (reliable, structured JSON)
WHO_DON_API = (
    "https://www.who.int/api/news/diseaseoutbreaknews"
    "?sf_culture=en"
    "&$orderby=PublicationDateAndTime%20desc"
    "&$top=50"
)

# Fallback: RSS feeds
WHO_DON_RSS_FEEDS = [
    "https://www.who.int/feeds/entity/don/en/rss.xml",
    "https://www.who.int/emergencies/disease-outbreak-news/feed",
]

WHO_DON_BASE_URL = "https://www.who.int/emergencies/disease-outbreak-news/item"


def fetch_who_don_api(url: str = WHO_DON_API) -> list[dict]:
    """Fetch WHO DON entries via the Sitefinity OData API.

    Returns list of dicts with keys: title, summary, link, published.
    """
    logger.info("Fetching WHO DON via API: %s", url[:80] + "...")

    try:
        req = Request(url, headers={"Accept": "application/json", "User-Agent": "TravellerFeverDifferential/0.1"})
        with urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (URLError, json.JSONDecodeError, TimeoutError) as e:
        logger.warning("API request failed: %s", e)
        return []

    entries = []
    items = data.get("value", data) if isinstance(data, dict) else data
    if not isinstance(items, list):
        logger.warning("Unexpected API response format")
        return []

    for item in items:
        title = item.get("Title", "")
        summary = item.get("Summary", item.get("TrimmedSummary", ""))
        pub_date = item.get("PublicationDateAndTime", item.get("PublicationDate", ""))
        don_id = item.get("DonId", "")
        item_url = item.get("ItemDefaultUrl", "")

        # Build full URL
        if item_url and not item_url.startswith("http"):
            link = f"{WHO_DON_BASE_URL}{item_url}"
        elif item_url:
            link = item_url
        elif don_id:
            link = f"{WHO_DON_BASE_URL}/{don_id}"
        else:
            link = ""

        # Normalise date to ISO format
        published = ""
        if pub_date:
            try:
                dt = datetime.fromisoformat(pub_date.replace("Z", "+00:00"))
                published = dt.isoformat()
            except ValueError:
                published = pub_date

        entries.append({
            "title": title,
            "summary": summary,
            "link": link,
            "published": published,
        })

    logger.info("Fetched %d WHO DON entries via API", len(entries))
    return entries


def fetch_who_don_rss() -> list[dict]:
    """Fallback: fetch WHO DON entries via RSS feeds."""
    for url in WHO_DON_RSS_FEEDS:
        logger.info("Trying WHO DON RSS: %s", url)
        feed = feedparser.parse(url)
        if feed.entries:
            entries = []
            for entry in feed.entries:
                published = ""
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    published = datetime(*entry.published_parsed[:6],
                                         tzinfo=timezone.utc).isoformat()
                elif hasattr(entry, "published"):
                    published = entry.published
                entries.append({
                    "title": getattr(entry, "title", ""),
                    "summary": getattr(entry, "summary", ""),
                    "link": getattr(entry, "link", ""),
                    "published": published,
                })
            logger.info("Fetched %d entries via RSS", len(entries))
            return entries
    return []


def fetch_who_don_entries() -> list[dict]:
    """Fetch WHO DON entries, trying API first then RSS fallback."""
    entries = fetch_who_don_api()
    if entries:
        return entries

    logger.info("API failed, falling back to RSS")
    return fetch_who_don_rss()


def classify_entries(entries: list[dict]) -> list[ClassifiedSignal]:
    """Classify WHO DON entries into (region, diagnosis) pairs."""
    signals = []
    for entry in entries:
        signal = classify_signal(
            title=entry["title"],
            text=entry["summary"],
            source="who_don",
            date=entry["published"],
            url=entry["link"],
        )
        signals.append(signal)
    return signals


def save_signals(signals: list[ClassifiedSignal], archive_dir: Path) -> None:
    """Append classified signals to monthly JSONL archive.

    Each month gets its own file: YYYY-MM.jsonl
    Deduplicates by URL within the same file.
    """
    archive_dir.mkdir(parents=True, exist_ok=True)

    by_month: dict[str, list[ClassifiedSignal]] = {}
    for signal in signals:
        if signal.date:
            try:
                dt = datetime.fromisoformat(signal.date.replace("Z", "+00:00"))
                month_key = dt.strftime("%Y-%m")
            except ValueError:
                month_key = datetime.now(timezone.utc).strftime("%Y-%m")
        else:
            month_key = datetime.now(timezone.utc).strftime("%Y-%m")

        by_month.setdefault(month_key, []).append(signal)

    for month_key, month_signals in by_month.items():
        filepath = archive_dir / f"{month_key}.jsonl"

        existing_urls: set[str] = set()
        if filepath.exists():
            with open(filepath) as f:
                for line in f:
                    try:
                        existing = json.loads(line)
                        existing_urls.add(existing.get("url", ""))
                    except json.JSONDecodeError:
                        continue

        new_count = 0
        with open(filepath, "a") as f:
            for signal in month_signals:
                if signal.url and signal.url in existing_urls:
                    continue
                record = {
                    "source": signal.source,
                    "title": signal.title,
                    "date": signal.date,
                    "url": signal.url,
                    "diagnoses": signal.diagnoses,
                    "regions": signal.regions,
                    "classified": signal.classified,
                    "scraped_at": datetime.now(timezone.utc).isoformat(),
                }
                f.write(json.dumps(record) + "\n")
                new_count += 1

        logger.info("Wrote %d new signals to %s (%d duplicates skipped)",
                     new_count, filepath, len(month_signals) - new_count)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    ensure_dirs()

    archive_dir = RAW_DIR / "who_don_archive"

    entries = fetch_who_don_entries()
    if not entries:
        logger.warning("No entries fetched from WHO DON (API + RSS both failed).")
        return

    signals = classify_entries(entries)

    classified_count = sum(1 for s in signals if s.classified)
    logger.info("Classified %d/%d entries (%.0f%%)",
                classified_count, len(signals),
                100 * classified_count / max(len(signals), 1))

    save_signals(signals, archive_dir)

    print(f"\nWHO DON scrape complete:")
    print(f"  Entries fetched: {len(entries)}")
    print(f"  Classified: {classified_count}/{len(signals)}")
    print(f"  Archive dir: {archive_dir}")

    if classified_count > 0:
        print("\n  Classified signals:")
        for s in signals:
            if s.classified:
                print(f"    {s.date[:10] if s.date else '?'} | "
                      f"{', '.join(s.diagnoses)} | "
                      f"{', '.join(s.regions)} | "
                      f"{s.title[:80]}")

    unclassified = [s for s in signals if not s.classified]
    if unclassified:
        print(f"\n  Unclassified ({len(unclassified)} entries):")
        for s in unclassified[:5]:
            print(f"    {s.title[:100]}")
        if len(unclassified) > 5:
            print(f"    ... and {len(unclassified) - 5} more")


if __name__ == "__main__":
    main()
