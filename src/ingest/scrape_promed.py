"""ProMED-mail scraper for live outbreak signals.

Uses RSS feed (primary) with HTML scraping fallback via the ProMED
homepage "Weekly Pulse" section.

Classifies entries by (region, diagnosis) and appends to monthly
JSONL archive files.

Output: data/raw/promed_archive/YYYY-MM.jsonl (append-only)

Usage:
    python -m src.ingest.scrape_promed
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError

import feedparser

from src.ingest.signal_classifier import ClassifiedSignal, classify_signal
from src.utils import RAW_DIR, ensure_dirs

logger = logging.getLogger(__name__)

PROMED_RSS_URLS = [
    "https://promedmail.org/feed/",
    "https://promedmail.org/promed-posts/feed/",
]

PROMED_HOMEPAGE = "https://promedmail.org"


def fetch_promed_rss() -> list[dict]:
    """Try ProMED RSS feeds."""
    for url in PROMED_RSS_URLS:
        logger.info("Trying ProMED RSS: %s", url)
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


def fetch_promed_html() -> list[dict]:
    """Fallback: scrape ProMED homepage for recent alerts.

    Extracts titles from the "Weekly Pulse" section visible on the homepage.
    ProMED uses client-side rendering, so we extract what's available in the
    initial HTML payload.
    """
    logger.info("Trying ProMED HTML scrape: %s", PROMED_HOMEPAGE)

    try:
        req = Request(PROMED_HOMEPAGE, headers={
            "User-Agent": "TravellerFeverDifferential/0.1 (research tool)",
            "Accept": "text/html",
        })
        with urlopen(req, timeout=30) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except (URLError, TimeoutError) as e:
        logger.warning("HTML fetch failed: %s", e)
        return []

    # Extract alert titles from the HTML
    # ProMED titles follow pattern: "DISEASE - COUNTRY (NN): detail"
    # Look for these in the HTML text
    entries = []

    # Pattern: ProMED-style titles in the HTML
    # e.g., "AVIAN INFLUENZA - INDIA (18): (KARNATAKA) POULTRY, H5N1"
    title_pattern = re.compile(
        r'([A-Z][A-Z\s/]+(?:VIRUS|FEVER|INFLUENZA|DISEASE|POX|CHOLERA|MALARIA'
        r'|MEASLES|DENGUE|CHIKUNGUNYA|ZIKA|EBOLA|MARBURG|PLAGUE|RABIES'
        r'|TUBERCULOSIS|MENINGITIS|HEPATITIS|LEPTOSPIROSIS|ENCEPHALITIS'
        r'|MPOX|OROPOUCHE|YELLOW FEVER|TYPHOID|ANTHRAX|BRUCELLOSIS'
        r'|DIPHTHERIA|POLIO)'
        r'\s*-\s*[A-Z][A-Z\s,]+(?:\([^)]*\))?[^<"]{0,100})',
        re.IGNORECASE
    )

    matches = title_pattern.findall(html)
    seen_titles = set()
    today = datetime.now(timezone.utc).isoformat()

    for match in matches:
        title = match.strip()
        # Clean up
        title = re.sub(r'\s+', ' ', title)
        if len(title) < 15 or len(title) > 200:
            continue
        if title in seen_titles:
            continue
        seen_titles.add(title)

        entries.append({
            "title": title,
            "summary": "",
            "link": PROMED_HOMEPAGE,
            "published": today,
        })

    logger.info("Extracted %d ProMED titles via HTML scrape", len(entries))
    return entries


def fetch_promed_entries() -> list[dict]:
    """Fetch ProMED entries, trying RSS first then HTML fallback."""
    entries = fetch_promed_rss()
    if entries:
        return entries

    logger.info("RSS failed, falling back to HTML scrape")
    return fetch_promed_html()


def classify_entries(entries: list[dict]) -> list[ClassifiedSignal]:
    """Classify ProMED entries into (region, diagnosis) pairs."""
    signals = []
    for entry in entries:
        signal = classify_signal(
            title=entry["title"],
            text=entry["summary"],
            source="promed",
            date=entry["published"],
            url=entry["link"],
        )
        signals.append(signal)
    return signals


def save_signals(signals: list[ClassifiedSignal], archive_dir: Path) -> None:
    """Append classified signals to monthly JSONL archive.

    Each month gets its own file: YYYY-MM.jsonl
    Deduplicates by URL+title within the same file.
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

        # Load existing entries for deduplication (by URL+title)
        existing_keys: set[str] = set()
        if filepath.exists():
            with open(filepath) as f:
                for line in f:
                    try:
                        existing = json.loads(line)
                        key = f"{existing.get('url', '')}|{existing.get('title', '')}"
                        existing_keys.add(key)
                    except json.JSONDecodeError:
                        continue

        new_count = 0
        with open(filepath, "a") as f:
            for signal in month_signals:
                key = f"{signal.url}|{signal.title}"
                if key in existing_keys:
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
                existing_keys.add(key)

        logger.info("Wrote %d new signals to %s (%d duplicates skipped)",
                     new_count, filepath, len(month_signals) - new_count)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    ensure_dirs()

    archive_dir = RAW_DIR / "promed_archive"

    entries = fetch_promed_entries()
    if not entries:
        logger.warning("No entries fetched from ProMED (RSS + HTML both failed).")
        return

    signals = classify_entries(entries)

    classified_count = sum(1 for s in signals if s.classified)
    logger.info("Classified %d/%d entries (%.0f%%)",
                classified_count, len(signals),
                100 * classified_count / max(len(signals), 1))

    save_signals(signals, archive_dir)

    print(f"\nProMED scrape complete:")
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
