from app.core.config import get_settings


def connector_status() -> dict[str, dict[str, bool | str]]:
    settings = get_settings()
    return {
        "gmail": {
            "available": bool(settings.smtp_username and settings.smtp_password),
            "mode": "smtp_gmail",
        },
        "google_sheets": {
            "available": bool(settings.google_service_account_json and settings.google_sheets_spreadsheet_id),
            "mode": "service_account_export",
        },
        "linkedin": {
            "available": False,
            "mode": "playwright_browser_flow_only",
        },
        "browser_automation": {
            "available": True,
            "mode": "playwright",
        },
        "calendar": {
            "available": bool(settings.google_service_account_json),
            "mode": "google_calendar_adapter_placeholder",
        },
    }

