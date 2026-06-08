from __future__ import annotations

import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from pathlib import Path

from app.core.config import get_settings


@dataclass
class EmailResult:
    sent: bool
    dry_run: bool
    message: str


class EmailConnector:
    def __init__(self) -> None:
        self.settings = get_settings()

    def send(self, to_email: str, subject: str, body: str, attachment_path: str | None = None) -> EmailResult:
        if self.settings.outreach_dry_run:
            return EmailResult(sent=False, dry_run=True, message=f"Dry run: email prepared for {to_email}.")
        if not (self.settings.smtp_username and self.settings.smtp_password):
            return EmailResult(sent=False, dry_run=False, message="SMTP credentials are not configured.")

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = self.settings.smtp_from or self.settings.smtp_username
        msg["To"] = to_email
        msg.set_content(body)

        if attachment_path:
            path = Path(attachment_path)
            if path.exists():
                msg.add_attachment(
                    path.read_bytes(),
                    maintype="application",
                    subtype="octet-stream",
                    filename=path.name,
                )

        with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port, timeout=30) as smtp:
            smtp.starttls()
            smtp.login(self.settings.smtp_username, self.settings.smtp_password)
            smtp.send_message(msg)

        return EmailResult(sent=True, dry_run=False, message=f"Email sent to {to_email}.")

