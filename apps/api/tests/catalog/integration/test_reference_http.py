"""HTTP-level: real routers, JWT auth and error handlers over an in-memory repository."""

from collections.abc import AsyncIterator
from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.interfaces.http.v1 import catalog as http
from app.modules.catalog import facade
from app.modules.catalog.application.service import CatalogService
from app.modules.catalog.wiring import get_catalog_service
from app.shared.db import get_session
from app.shared.errors import install_error_handlers
from app.shared.security import encode_access_token
from tests.catalog.unit.test_reference_sheet import make


@pytest.fixture
async def ctx(
    monkeypatch: pytest.MonkeyPatch,
) -> AsyncIterator[tuple[AsyncClient, CatalogService, str]]:
    svc, _repo, sid = make()
    app = FastAPI()
    install_error_handlers(app)
    app.include_router(http.router, prefix="/v1/catalog")
    app.include_router(http.admin_router, prefix="/v1/admin/catalog")

    async def no_session() -> AsyncIterator[None]:
        yield None

    app.dependency_overrides[get_session] = no_session
    app.dependency_overrides[get_catalog_service] = lambda: svc
    monkeypatch.setattr(facade, "service", lambda _session: svc)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        yield c, svc, str(sid)


def auth(role: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {encode_access_token(uuid4(), [role])}"}


async def test_public_404_until_published_then_locale_fallback(ctx):
    c, _, sid = ctx
    assert (await c.get(f"/v1/catalog/subjects/{sid}/reference")).status_code == 404

    body = {"contents": {"uz-Latn": "$a^2$", "ru": "$b^2$"}, "source": "PIIMA"}
    put = await c.put(
        f"/v1/admin/catalog/subjects/{sid}/reference", json=body, headers=auth("admin")
    )
    assert put.status_code == 200 and put.json()["active"] is True

    ru = (await c.get(f"/v1/catalog/subjects/{sid}/reference", params={"locale": "ru"})).json()
    assert ru["locale"] == "ru" and ru["content"] == "$b^2$" and ru["source"] == "PIIMA"
    cyr = (
        await c.get(f"/v1/catalog/subjects/{sid}/reference", params={"locale": "uz-Cyrl"})
    ).json()
    assert cyr["locale"] == "uz-Latn"


async def test_inactive_sheet_is_hidden_from_learners_but_not_admin(ctx):
    c, _, sid = ctx
    url = f"/v1/admin/catalog/subjects/{sid}/reference"
    await c.put(url, json={"contents": {"ru": "x"}, "active": False}, headers=auth("admin"))
    assert (await c.get(f"/v1/catalog/subjects/{sid}/reference")).status_code == 404
    assert (await c.get(url, headers=auth("admin"))).json()["active"] is False


async def test_admin_routes_require_admin_role(ctx):
    c, _, sid = ctx
    url = f"/v1/admin/catalog/subjects/{sid}/reference"
    assert (await c.put(url, json={"contents": {"ru": "x"}})).status_code == 401
    r = await c.put(url, json={"contents": {"ru": "x"}}, headers=auth("student"))
    assert r.status_code == 403


async def test_admin_validation_unknown_subject_and_delete(ctx):
    c, _, sid = ctx
    h = auth("admin")
    bad = await c.put(
        f"/v1/admin/catalog/subjects/{sid}/reference", json={"contents": {"xx": "a"}}, headers=h
    )
    assert bad.status_code == 422
    miss = await c.put(
        f"/v1/admin/catalog/subjects/{uuid4()}/reference", json={"contents": {"ru": "a"}}, headers=h
    )
    assert miss.status_code == 404
    await c.put(
        f"/v1/admin/catalog/subjects/{sid}/reference", json={"contents": {"ru": "a"}}, headers=h
    )
    assert (
        await c.delete(f"/v1/admin/catalog/subjects/{sid}/reference", headers=h)
    ).status_code == 204
    assert (
        await c.delete(f"/v1/admin/catalog/subjects/{sid}/reference", headers=h)
    ).status_code == 404
