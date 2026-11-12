import asyncio
import json
import time
from pathlib import Path
from typing import Any

import httpx
import structlog

from app.modules.notify.domain.messages import Message
from app.modules.notify.settings import NotifySettings

log = structlog.get_logger()

FCM_SCOPE = "https://www.googleapis.com/auth/firebase.messaging"


class TelegramBotApi:
    def __init__(self, token: str, settings: NotifySettings) -> None:
        self._url = f"{settings.telegram_api_base}/bot{token}"
        self._enabled = bool(token)

    async def send_telegram(self, chat_id: int, message: Message) -> bool:
        if not self._enabled:
            log.warning("notify.telegram_disabled")
            return False
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{self._url}/sendMessage",
                json={"chat_id": chat_id, "text": f"{message.title}\n{message.body}"},
            )
        if resp.status_code >= 400:
            log.warning("notify.telegram_failed", status=resp.status_code, chat_id=chat_id)
            return False
        return True


class FcmPush:
    """FCM HTTP v1 using a service-account JWT (RS256, needs `cryptography`)."""

    def __init__(self, settings: NotifySettings) -> None:
        self._project = settings.fcm_project_id
        self._raw = settings.fcm_service_account
        self._token: tuple[str, float] | None = None
        self._lock = asyncio.Lock()

    @property
    def enabled(self) -> bool:
        return bool(self._project and self._raw)

    def _account(self) -> dict[str, Any]:
        raw = self._raw.strip()
        data = raw if raw.startswith("{") else Path(raw).read_text()
        return json.loads(data)  # type: ignore[no-any-return]

    async def _access_token(self, client: httpx.AsyncClient) -> str:
        async with self._lock:
            if self._token and self._token[1] > time.time() + 60:
                return self._token[0]
            import jwt  # local: RS256 requires the optional `cryptography` backend

            acc = self._account()
            now = int(time.time())
            assertion = jwt.encode(
                {
                    "iss": acc["client_email"],
                    "scope": FCM_SCOPE,
                    "aud": acc["token_uri"],
                    "iat": now,
                    "exp": now + 3600,
                },
                acc["private_key"],
                algorithm="RS256",
            )
            resp = await client.post(
                acc["token_uri"],
                data={
                    "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                    "assertion": assertion,
                },
            )
            resp.raise_for_status()
            body = resp.json()
            self._token = (body["access_token"], time.time() + int(body.get("expires_in", 3600)))
            return self._token[0]

    async def send_push(self, token: str, message: Message) -> bool:
        if not self.enabled:
            log.warning("notify.fcm_disabled")
            return True  # not a dead token; keep it
        async with httpx.AsyncClient(timeout=15) as client:
            access = await self._access_token(client)
            resp = await client.post(
                f"https://fcm.googleapis.com/v1/projects/{self._project}/messages:send",
                headers={"Authorization": f"Bearer {access}"},
                json={
                    "message": {
                        "token": token,
                        "notification": {"title": message.title, "body": message.body},
                    }
                },
            )
        if resp.status_code == 404 or (resp.status_code == 400 and "UNREGISTERED" in resp.text):
            return False
        if resp.status_code >= 400:
            log.warning("notify.fcm_failed", status=resp.status_code)
        return True


class MailerEmail:
    """Adapts the identity mailer (an infrastructure-level shared transport)."""

    def __init__(self) -> None:
        # Cross-module use is deliberate: identity owns the SMTP transport; no ORM involved.
        from app.modules.identity.infrastructure.mail import build_mailer
        from app.settings import get_settings

        self._mailer = build_mailer(get_settings())

    async def send_email(self, to: str, message: Message) -> None:
        await self._mailer.send(to, message.title, message.body)
