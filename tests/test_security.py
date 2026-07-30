from datetime import timedelta

from fastapi.testclient import TestClient

from app.core.jwt import create_access_token, decode_access_token


def test_token_valido() -> None:
    token = create_access_token({"sub": "ana@example.com"})
    assert decode_access_token(token) == "ana@example.com"


def test_token_invalido() -> None:
    assert decode_access_token("token-invalido") is None


def test_token_expirado() -> None:
    token = create_access_token(
        {"sub": "ana@example.com"},
        expires_delta=timedelta(seconds=-1),
    )
    assert decode_access_token(token) is None


def test_openapi_declara_oauth2_en_rutas_protegidas(
    client: TestClient,
) -> None:
    schema = client.get("/openapi.json").json()
    assert "OAuth2PasswordBearer" in schema["components"]["securitySchemes"]
    for path, operations in schema["paths"].items():
        if path.startswith("/viajes") or path == "/auth/me":
            for operation in operations.values():
                assert operation["security"] == [{"OAuth2PasswordBearer": []}]


def test_health_comprueba_servicio_y_base(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_cors_permite_frontend_local(client: TestClient) -> None:
    response = client.options(
        "/auth/me",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert (
        response.headers["access-control-allow-origin"]
        == "http://localhost:3000"
    )
    assert response.headers["access-control-allow-credentials"] == "true"
