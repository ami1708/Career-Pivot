from __future__ import annotations

from pathlib import Path

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
            return []

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
                cards = page.locator("a[href*='job'], a[href*='career'], [data-job-id], .job, .posting").all()
                for idx, card in enumerate(cards[:limit]):
                    text = compact_whitespace(card.inner_text(timeout=1000))
                    href = card.get_attribute("href") or url
                    if not text:
                        continue
                    title = text.split(" at ")[0][:120]
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


def _storage_state_path(board: str) -> str | None:
    path = f"playwright/.auth/{board}.json"
    return path if Path(path).exists() else None
