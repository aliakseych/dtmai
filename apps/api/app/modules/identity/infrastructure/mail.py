import asyncio
import smtplib
from email.message import EmailMessage

import structlog

from app.settings import Settings

log = structlog.get_logger()


class ConsoleMailer:
    """Dev adapter: logs the message instead of sending it."""

    async def send(self, to: str, subject: str, body: str) -> None:
        log.info("mail.console", to=to, subject=subject, body=body)


class SmtpMailer:
    def __init__(self, settings: Settings) -> None:
        self._s = settings

    async def send(self, to: str, subject: str, body: str) -> None:
        await asyncio.to_thread(self._send_sync, to, subject, body)

    def _send_sync(self, to: str, subject: str, body: str) -> None:
        msg = EmailMessage()
        msg["From"], msg["To"], msg["Subject"] = self._s.mail_from, to, subject
        msg.set_content(body)
        with smtplib.SMTP(self._s.smtp_host, self._s.smtp_port, timeout=15) as smtp:
            if self._s.smtp_starttls:
                smtp.starttls()
            if self._s.smtp_user:
                smtp.login(self._s.smtp_user, self._s.smtp_password)
            smtp.send_message(msg)


def build_mailer(settings: Settings) -> ConsoleMailer | SmtpMailer:
    return SmtpMailer(settings) if settings.mail_backend == "smtp" else ConsoleMailer()
