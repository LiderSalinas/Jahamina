from pathlib import Path
from collections.abc import Callable
from typing import Any

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]


def test_login_form_prevents_credentials_in_url_and_blocks_duplicates():
    source = (ROOT / "frontend" / "app" / "login" / "page.tsx").read_text(
        encoding="utf-8"
    )

    assert 'method="post"' in source
    assert "onSubmit={submit}" in source
    assert "event.preventDefault()" in source
    assert "if (submitting.current) return" in source
    assert 'type="submit"' in source
    assert "console.log" not in source


def test_login_client_uses_oauth_form_contract_and_public_api_url():
    source = (ROOT / "frontend" / "lib" / "api.ts").read_text(encoding="utf-8")

    assert "process.env.NEXT_PUBLIC_API_URL" in source
    assert 'throw new ApiError(0, "NEXT_PUBLIC_API_URL no contiene una URL válida.")' in source
    assert '["localhost", "127.0.0.1"].includes(parsed.hostname)' in source
    assert 'new URLSearchParams({ username: email, password })' in source
    assert 'request<TokenResponse>("/auth/login", { method: "POST", body })' in source
    assert "const API_URL" not in source
    assert 'url.protocol = url.protocol === "https:" ? "wss:" : "ws:"' in source
    assert 'buildWebSocketUrl(`/ws/chat?ticket=${encodeURIComponent(response.ticket)}`)' in source
    assert 'buildWebSocketUrl(`/ws/ubicacion?ticket=${encodeURIComponent(response.ticket)}`)' in source
    assert 'process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"' not in source


def test_websocket_url_contract_preserves_host_port_path_and_ticket():
    cases = (
        ("http://localhost:8000", "ws://localhost:8000/ws/chat?ticket=single-use"),
        ("http://192.168.0.107:8000", "ws://192.168.0.107:8000/ws/chat?ticket=single-use"),
        ("https://api.example.com", "wss://api.example.com/ws/chat?ticket=single-use"),
    )
    for api_base, expected in cases:
        websocket_base = api_base.replace("https://", "wss://").replace("http://", "ws://")
        assert f"{websocket_base}/ws/chat?ticket=single-use" == expected


def test_login_succeeds_from_supported_frontend_origins(
    client: TestClient,
    register_user: Callable[..., dict[str, Any]],
):
    user = register_user(email="lan-login@example.com")

    for origin in (
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://192.168.0.107:3000",
        "http://192.168.1.20:3000",
    ):
        response = client.options(
            "/auth/login",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == origin
        assert response.headers["access-control-allow-credentials"] == "true"

        login = client.post(
            "/auth/login",
            headers={"Origin": origin},
            data={"username": user["email"], "password": user["password"]},
        )
        assert login.status_code == 200
        assert login.headers["access-control-allow-origin"] == origin
        assert login.json()["token_type"] == "bearer"
        assert login.json()["access_token"]


def test_cors_rejects_unknown_origin(client: TestClient):
    response = client.options(
        "/auth/login",
        headers={
            "Origin": "http://192.168.0.250:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


def test_login_rejects_invalid_oauth_payload(client: TestClient):
    response = client.post("/auth/login", data={"email": "invalid@example.com"})
    assert response.status_code == 422
