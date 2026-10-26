"""Outgoing e-mail (verification and password reset codes).

Configure SMTP with SMTP_HOST, SMTP_PORT (587), SMTP_USERNAME,
SMTP_PASSWORD, SMTP_FROM and SMTP_STARTTLS (true). Without SMTP_HOST:
- development: messages are written as .eml files to DEV_OUTBOX_DIR
  (default backend/dev_outbox, git-ignored) so codes never reach the logs;
- production (APP_ENV=production): sending raises MailNotConfigured.
"""

import logging
import os
import smtplib
import ssl
import uuid
from email.message import EmailMessage
from pathlib import Path

logger = logging.getLogger("backend.mailer")

_BACKEND_DIR = Path(__file__).resolve().parent


class MailNotConfigured(RuntimeError):
    pass


def _is_production() -> bool:
    return os.environ.get("APP_ENV", "development").lower() == "production"


def is_configured() -> bool:
    return bool(os.environ.get("SMTP_HOST")) or not _is_production()


def send_email(to: str, subject: str, body: str) -> None:
    message = EmailMessage()
    message["From"] = os.environ.get("SMTP_FROM", "AIT <no-reply@localhost>")
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)

    host = os.environ.get("SMTP_HOST")
    if host:
        _send_smtp(host, message)
    elif not _is_production():
        _write_dev_outbox(message)
    else:
        raise MailNotConfigured("SMTP_HOST is not set")


def _send_smtp(host: str, message: EmailMessage) -> None:
    port = int(os.environ.get("SMTP_PORT", "587"))
    with smtplib.SMTP(host, port, timeout=15) as smtp:
        if os.environ.get("SMTP_STARTTLS", "true").lower() == "true":
            smtp.starttls(context=ssl.create_default_context())
        username = os.environ.get("SMTP_USERNAME")
        if username:
            smtp.login(username, os.environ.get("SMTP_PASSWORD", ""))
        smtp.send_message(message)
    logger.info("e-mail sent subject=%r", message["Subject"])


def _write_dev_outbox(message: EmailMessage) -> None:
    outbox = Path(os.environ.get("DEV_OUTBOX_DIR", _BACKEND_DIR / "dev_outbox"))
    outbox.mkdir(parents=True, exist_ok=True)
    path = outbox / f"{uuid.uuid4().hex}.eml"
    path.write_bytes(bytes(message))
    # Only the folder is logged, never the message (it contains the code).
    logger.info("SMTP not configured; e-mail written to %s", outbox)
