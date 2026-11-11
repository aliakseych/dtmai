import asyncio

import httpx

from app.modules.lyceums.domain.models import SourceLanguage, SourceLyceum, SourceSpeciality

BASE_URL = "https://my-api.edu.uz/api/v1"
SERVICE_ID = 15  # lyceum admission service


class EduUzSource:
    """Adapter for the public edu.uz admission overview API (no auth, no year field)."""

    def __init__(
        self, client: httpx.AsyncClient | None = None, *, base_url: str = BASE_URL
    ) -> None:
        self._client = client or httpx.AsyncClient(
            base_url=base_url, timeout=httpx.Timeout(30.0), headers={"Accept": "application/json"}
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def _get(self, path: str, params: dict[str, str | int]) -> list[dict]:  # type: ignore[type-arg]
        last: Exception | None = None
        for attempt in range(6):
            try:
                resp = await self._client.get(path, params=params)
                if resp.status_code == 429:  # edu.uz rate-limits bursts; honour Retry-After or back off
                    retry_after = resp.headers.get("Retry-After", "")
                    await asyncio.sleep(float(retry_after) if retry_after.isdigit() else 2.0 * 2**attempt)
                    last = httpx.HTTPStatusError("429", request=resp.request, response=resp)
                    continue
                resp.raise_for_status()
                data = resp.json()
                return data["results"] if isinstance(data, dict) and "results" in data else data
            except (httpx.HTTPError, ValueError, KeyError) as e:
                last = e
        raise RuntimeError(f"edu.uz request failed: {path}") from last

    async def lyceums(self) -> list[SourceLyceum]:
        rows = await self._get("/admission/lyceum/overview/tm/", {"service_id": SERVICE_ID})
        return [
            SourceLyceum(int(r["id"]), str(r.get("code", "")), r.get("name_uz") or "",
                         r.get("name_en") or "", r.get("name_ru") or "")
            for r in rows
        ]

    async def languages(self) -> list[SourceLanguage]:
        rows = await self._get("/classifier/cached/", {"classifier": "education-language"})
        return [
            SourceLanguage(int(r["id"]), str(r.get("code", "")), r.get("name_uz") or "",
                           r.get("name_en") or "", r.get("name_ru") or "")
            for r in rows
        ]

    async def specialities(
        self, lyceum_external_id: int, language_external_id: int
    ) -> list[SourceSpeciality]:
        rows = await self._get(
            "/admission/lyceum/overview/speciality/",
            {
                "service_id": SERVICE_ID,
                "tm_id": lyceum_external_id,
                "education_language_id": language_external_id,
            },
        )
        return [
            SourceSpeciality(
                str(r["speciality_code"]), r.get("speciality_name") or "",
                int(r.get("total_quota") or 0), int(r.get("total_application") or 0),
            )
            for r in rows
        ]
