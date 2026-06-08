from __future__ import annotations

from pathlib import Path
from urllib.parse import urljoin

from app.core.config import get_settings
from app.services.job_sources.base import JobListing
from app.services.text import compact_whitespace


class PlaywrightBoardSource:
    """Generic browser adapter for sites that need rendering or a logged-in session.

    This intentionally uses conservative selectors and dry-run-friendly browsing.
    Site-specific selectors can be tightened in production without changing the
    discovery pipeline.
    """

    name = "playwright"

    def __init__(self, board: str, search_url_template: str):
        self.board = board
        self.search_url_template = search_url_template
        self.settings = get_settings()

    def fetch(self, query: str, location: str, limit: int = 25) -> list[JobListing]:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise RuntimeError("Playwright is not installed. Run `playwright install chromium` for browser job boards.")

        url = self.search_url_template.format(query=query.replace(" ", "%20"), location=location.replace(" ", "%20"))
        listings: list[JobListing] = []
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.settings.playwright_headless)
            storage_state = _storage_state_path(self.board)
            context = browser.new_context(storage_state=storage_state) if storage_state else browser.new_context()
            page = context.new_page()
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(1500)
                cards = page.locator(_card_selector(self.board)).all()
                for idx, card in enumerate(cards[:limit]):
                    try:
                        text = compact_whitespace(card.inner_text(timeout=1200))
                    except Exception:
                        continue
                    href = _extract_href(card, url)
                    if not text:
                        continue
                    title = _extract_title(text)
                    listings.append(
                        JobListing(
                            source=f"{self.name}:{self.board}",
                            external_id=f"{self.board}-{idx}-{href}",
                            url=href if href.startswith("http") else url,
                            title=title,
                            company=self.board.title(),
                            location=location,
                            remote="remote" in text.lower(),
                            description=text,
                            raw={"search_url": url},
                        ).normalized()
                    )
            finally:
                context.close()
                browser.close()
        return listings


def _card_selector(board: str) -> str:
    board_selectors = {
        "linkedin": ".base-card, .job-search-card, li.jobs-search-results__list-item, a[href*='/jobs/view/']",
        "instahyre": ".job, .employer-row, div[class*='job'], a[href*='/job-']",
        "naukri": ".srp-jobtuple-wrapper, .jobTuple, article[class*='job'], a[href*='job-listings']",
        "indeed": ".job_seen_beacon, td.resultContent, .jobsearch-SerpJobCard, a[href*='/rc/clk'], a[href*='jk=']",
        "wellfound": "[data-test*='Job'], [data-test*='Startup'], div[class*='job'], a[href*='/jobs']",
    }
    generic = "a[href*='job'], a[href*='career'], [data-job-id], .job, .posting"
    return f"{board_selectors.get(board, generic)}, {generic}"


def _extract_href(card, base_url: str) -> str:
    try:
        href = card.get_attribute("href")
        if href:
            return urljoin(base_url, href)
    except Exception:
        pass
    try:
        link = card.locator("a[href]").first()
        href = link.get_attribute("href", timeout=1000)
        if href:
            return urljoin(base_url, href)
    except Exception:
        pass
    return base_url


def _extract_title(text: str) -> str:
    first_line = next((line.strip() for line in text.splitlines() if line.strip()), text)
    for separator in (" at ", "\n", " | "):
        if separator in first_line:
            first_line = first_line.split(separator, 1)[0]
    return first_line[:120]


def _storage_state_path(board: str) -> str | None:
    path = f"playwright/.auth/{board}.json"
    return path if Path(path).exists() else None
