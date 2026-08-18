import pytest
from app.core.config import Settings


def test_configuration_loads_default_settings():
    settings = Settings()
    assert settings.APP_NAME == "women-safety-backend"
    assert settings.API_V1_PREFIX == "/api/v1"
    assert settings.DEBUG is True
    assert "supabase.co" in settings.SUPABASE_URL
    assert len(settings.SUPABASE_ANON_KEY) > 0
    assert "http://localhost:3000" in settings.CORS_ORIGINS


def test_cors_origins_parsing():
    settings = Settings(CORS_ORIGINS="http://example.com,http://test.com")
    assert settings.CORS_ORIGINS == ["http://example.com", "http://test.com"]


def test_invalid_configuration_rejected():
    with pytest.raises(Exception):
        Settings(DEBUG="invalid_boolean_string_that_cannot_cast")
