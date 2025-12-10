from app.core.settings.auth_settings import AuthSettings


def test_auth_settings_defaults(monkeypatch):
    """
    We don't rely on the real environment (which may contain actual secrets).
    Instead we override env vars and check that AuthSettings reads them correctly.
    """
    # AuthSettings is nested under the top-level Settings model and uses
    # the `AUTH__` environment prefix; tests should set the prefixed vars.
    monkeypatch.setenv("AUTH__GOOGLE_CLIENT_ID", "dummy-google-client-id")
    monkeypatch.setenv("AUTH__GOOGLE_CLIENT_SECRET", "dummy-google-client-secret")
    monkeypatch.setenv("AUTH__JWT_SECRET_KEY", "super-secret")
    monkeypatch.setenv("AUTH__JWT_ALGORITHM", "HS256")
    monkeypatch.setenv("AUTH__ACCESS_TOKEN_EXPIRE_MINUTES", "1440")  # 24h
    monkeypatch.setenv("AUTH__FRONTEND_ORIGIN", "http://localhost:5173")

    settings = AuthSettings()

    assert settings.GOOGLE_CLIENT_ID == "dummy-google-client-id"
    assert settings.GOOGLE_CLIENT_SECRET == "dummy-google-client-secret"
    assert settings.JWT_SECRET_KEY == "super-secret"
    assert settings.JWT_ALGORITHM == "HS256"
    assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 1440
    assert settings.FRONTEND_ORIGIN == "http://localhost:5173"

    