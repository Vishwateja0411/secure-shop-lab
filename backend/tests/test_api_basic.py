from backend.app.config import settings

def test_settings_loaded():
    assert settings.BACKEND_PORT == 8000
    assert isinstance(settings.SECURE_MODE, bool)
