from collections.abc import Callable
from typing import Any

from fastapi.testclient import TestClient


def test_registro_correcto(client: TestClient) -> None:
    response = client.post(
        "/auth/registro",
        json={
            "nombre": "Ana",
            "email": "ANA@EXAMPLE.COM",
            "password": "Password123",
        },
    )
    assert response.status_code == 201
    assert response.json()["email"] == "ana@example.com"
    assert "hashed_password" not in response.json()
    assert "password" not in response.json()


def test_registro_rechaza_email_invalido(client: TestClient) -> None:
    response = client.post(
        "/auth/registro",
        json={"nombre": "Ana", "email": "invalido", "password": "Password123"},
    )
    assert response.status_code == 422


def test_registro_rechaza_password_corta(client: TestClient) -> None:
    response = client.post(
        "/auth/registro",
        json={"nombre": "Ana", "email": "ana@example.com", "password": "123"},
    )
    assert response.status_code == 422


def test_registro_rechaza_password_superior_a_72_bytes(
    client: TestClient,
) -> None:
    response = client.post(
        "/auth/registro",
        json={
            "nombre": "Ana",
            "email": "ana@example.com",
            "password": "á" * 37,
        },
    )
    assert response.status_code == 422


def test_registro_duplicado_es_conflicto(
    client: TestClient,
    register_user: Callable[..., dict[str, Any]],
) -> None:
    register_user(email="ana@example.com")
    response = client.post(
        "/auth/registro",
        json={
            "nombre": "Otra Ana",
            "email": "ana@example.com",
            "password": "Password123",
        },
    )
    assert response.status_code == 409


def test_registro_duplicado_normaliza_mayusculas(
    client: TestClient,
    register_user: Callable[..., dict[str, Any]],
) -> None:
    register_user(email="ana@example.com")
    response = client.post(
        "/auth/registro",
        json={
            "nombre": "Otra Ana",
            "email": "ANA@EXAMPLE.COM",
            "password": "Password123",
        },
    )
    assert response.status_code == 409


def test_login_correcto(
    client: TestClient,
    register_user: Callable[..., dict[str, Any]],
) -> None:
    user = register_user(email="ana@example.com")
    response = client.post(
        "/auth/login",
        data={"username": "ANA@EXAMPLE.COM", "password": user["password"]},
    )
    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]


def test_login_incorrecto(
    client: TestClient,
    register_user: Callable[..., dict[str, Any]],
) -> None:
    register_user(email="ana@example.com")
    response = client.post(
        "/auth/login",
        data={"username": "ana@example.com", "password": "incorrecta"},
    )
    assert response.status_code == 401


def test_auth_me_con_token(
    client: TestClient,
    auth_headers: Callable[..., dict[str, str]],
) -> None:
    headers = auth_headers(email="ana@example.com")
    response = client.get("/auth/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["email"] == "ana@example.com"
    assert "hashed_password" not in response.json()


def test_auth_me_sin_token(client: TestClient) -> None:
    response = client.get("/auth/me")
    assert response.status_code == 401
