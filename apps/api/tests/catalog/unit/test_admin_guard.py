from app.interfaces.http.v1 import bank, catalog


def test_admin_routers_are_guarded():
    for r in (catalog.admin_router, bank.admin_router):
        assert r.dependencies, "admin router must carry the admin role dependency"
        assert r.routes
