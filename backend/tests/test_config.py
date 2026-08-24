"""
Prueba de las reglas que derivan hosts/origins permitidos a partir de
ALLOWED_ORIGINS. Esta lógica protege CORS y TrustedHostMiddleware en
producción (ver app/core/config.py, app/main.py) — un error aquí abre
o cierra de más el acceso a la API.
"""
from app.core.config import Settings


def _settings(**overrides):
    base = {
        "DATABASE_URL": "postgresql+asyncpg://test:test@localhost:5432/test",
        "SECRET_KEY": "test-secret-key",
    }
    base.update(overrides)
    return Settings(**base)


def test_allowed_origins_list_splits_on_comma():
    s = _settings(ALLOWED_ORIGINS="http://localhost:5173,https://app.daco-group.com")
    assert s.allowed_origins_list == ["http://localhost:5173", "https://app.daco-group.com"]


def test_allowed_hosts_derived_from_origins_when_not_set_explicitly():
    s = _settings(ALLOWED_ORIGINS="http://localhost:5173,https://app.daco-group.com")
    assert set(s.allowed_hosts_list) == {"localhost", "app.daco-group.com"}


def test_allowed_hosts_uses_explicit_value_when_set():
    s = _settings(
        ALLOWED_ORIGINS="https://app.daco-group.com",
        ALLOWED_HOSTS="api.daco-group.com,app.daco-group.com",
    )
    assert s.allowed_hosts_list == ["api.daco-group.com", "app.daco-group.com"]


def test_allowed_hosts_never_wildcards():
    s = _settings(ALLOWED_ORIGINS="https://app.daco-group.com")
    assert "*" not in s.allowed_hosts_list
