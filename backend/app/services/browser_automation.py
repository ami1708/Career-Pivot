from __future__ import annotations

from dataclasses import dataclass

from app.core.config import get_settings


@dataclass
class PrefillResult:
    opened_url: str
    dry_run: bool
    submitted: bool
    message: str


COMMON_FIELD_MAP = {
    "name": "Amisha Negi",
    "full name": "Amisha Negi",
    "first name": "Amisha",
    "last name": "Negi",
    "experience": "4+ years",
    "current role": "SDE-2",
}


def prefill_application_form(url: str, answers: dict, resume_path: str | None = None) -> PrefillResult:
    settings = get_settings()
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return PrefillResult(url, True, False, "Playwright is not installed.")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=settings.playwright_headless)
        page = browser.new_page()
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            filled = 0
            for label, value in _field_candidates(answers):
                if value is None:
                    continue
                if _try_fill(page, label, str(value)):
                    filled += 1
            uploaded_resume = False
            if resume_path:
                inputs = page.locator("input[type='file']").all()
                for input_el in inputs[:1]:
                    try:
                        input_el.set_input_files(resume_path)
                        uploaded_resume = True
                    except Exception:
                        continue
            if settings.application_dry_run or settings.require_application_approval or not settings.auto_apply_enabled:
                return PrefillResult(
                    url,
                    True,
                    False,
                    f"Form prefilled where selectors matched ({filled} fields, resume uploaded: {uploaded_resume}). Final submit was not clicked.",
                )
            if filled == 0 and not uploaded_resume:
                return PrefillResult(url, False, False, "No matching application fields were found. Manual review needed.")
            submit = page.locator("button[type='submit'], input[type='submit']").first()
            submit.click(timeout=5000)
            return PrefillResult(url, False, True, "Form submitted.")
        except Exception as exc:
            return PrefillResult(url, settings.application_dry_run, False, f"Browser automation failed: {exc}")
        finally:
            browser.close()


def _field_candidates(answers: dict) -> list[tuple[str, str | None]]:
    candidates: list[tuple[str, str | None]] = list(COMMON_FIELD_MAP.items())
    label_aliases = {
        "why_this_role": ["why this role", "why are you interested", "why do you want to work"],
        "relevant_experience": ["relevant experience", "experience", "tell us about your experience"],
        "notice_period": ["notice period", "availability", "when can you start"],
        "work_authorization": ["work authorization", "authorized to work", "visa status"],
        "salary_expectation_note": ["salary expectation", "expected salary", "compensation expectation"],
    }
    for key, value in answers.items():
        if value is None:
            continue
        labels = label_aliases.get(key, [key.replace("_", " ")])
        candidates.extend((label, str(value)) for label in labels)
    return candidates


def _try_fill(page, label: str, value: str) -> bool:
    try:
        label_locator = page.get_by_label(label, exact=False).first()
        if label_locator.count() > 0:
            label_locator.fill(value, timeout=1000)
            return True
    except Exception:
        pass

    normalized_label = label.replace(" ", "_")
    selectors = [
        f"input[aria-label*='{label}' i]",
        f"textarea[aria-label*='{label}' i]",
        f"input[name*='{normalized_label}' i]",
        f"textarea[name*='{normalized_label}' i]",
        f"input[id*='{normalized_label}' i]",
        f"textarea[id*='{normalized_label}' i]",
        f"input[placeholder*='{label}' i]",
        f"textarea[placeholder*='{label}' i]",
    ]
    for selector in selectors:
        locator = page.locator(selector).first()
        try:
            if locator.count() > 0:
                locator.fill(value, timeout=1000)
                return True
        except Exception:
            continue
    return False
