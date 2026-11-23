from __future__ import annotations

import smtplib
from email.message import EmailMessage
from app.core.config import settings
from app.core.logging import logger
from app.models.user import EmailOutbox


class EmailAdapter:
    def __init__(self) -> None:
        self.host = settings.SMTP_HOST
        self.port = settings.SMTP_PORT
        self.user = settings.SMTP_USER
        self.password = settings.SMTP_PASSWORD
        self.from_email = settings.SMTP_FROM_EMAIL
        self.use_tls = settings.SMTP_TLS

    def send_email_sync(self, recipient: str, subject: str, body: str) -> bool:
        """Synchronously send an email via SMTP. Falls back to mock logging if unconfigured."""
        if not self.host or self.host in ("localhost", "127.0.0.1") and not self.user:
            logger.info(
                "mock_email_dispatch",
                recipient=recipient,
                subject=subject,
                body_snippet=body[:100],
            )
            return True

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = self.from_email
        msg["To"] = recipient
        msg.set_content(body)

        try:
            with smtplib.SMTP(self.host, self.port, timeout=10) as server:
                if self.use_tls:
                    server.starttls()
                if self.user and self.password:
                    server.login(self.user, self.password)
                server.send_message(msg)
            logger.info("email_sent_successfully", recipient=recipient, subject=subject)
            return True
        except Exception as exc:
            logger.error("smtp_send_failed", recipient=recipient, error=str(exc))
            raise


email_adapter = EmailAdapter()
