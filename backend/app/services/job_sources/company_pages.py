from __future__ import annotations

from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from app.services.job_sources.base import JobListing
from app.services.text import compact_whitespace


class CompanyCareerPageSource:
    name = "company_pages"

    def __init__(self, urls: list[str]):
        self.urls = urls

    def fetch(self, query: str, location: str, limit: int = 50) -> list[JobListing]:
        listings: list[JobListing] = []
        for url in self.urls:
            try:
                response = httpx.get(url, timeout=15, follow_redirects=True)
                response.raise_for_status()
            except httpx.HTTPError:
                continue
            soup = BeautifulSoup(response.text, "html.parser")
            candidates = soup.select("[data-job-id], .job, .opening, .posting, li, article")
            for idx, node in enumerate(candidates):
                text = compact_whitespace(node.get_text(" "))
                if not text or not _matches(text, query, location):
                    continue
                link = node.find("a", href=True)
                title = compact_whitespace(link.get_text(" ")) if link else text[:80]
                href = urljoin(url, link["href"]) if link else url
                listings.append(
                    JobListing(
                        source=self.name,
                        external_id=f"{url}#{idx}",
                        url=href,
                        title=title,
                        company=_company_from_url(url),
                        location=location,
                        remote="remote" in text.lower(),
                        description=text,
                        raw={"source_url": url},
                    ).normalized()
                )
                if len(listings) >= limit:
                    return listings
        return listings


def _matches(text: str, query: str, location: str) -> bool:
    haystack = text.lower()
    query_terms = [term for term in query.lower().replace("-", " ").split() if len(term) > 2]
    query_ok = any(term in haystack for term in query_terms) if query_terms else True
    location_ok = location.lower() in haystack or "remote" in haystack or not location
    return query_ok and location_ok


def _company_from_url(url: str) -> str:
    domain = url.split("//", 1)[-1].split("/", 1)[0]
    return domain.replace("www.", "").split(".")[0].title()

