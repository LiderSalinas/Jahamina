from collections.abc import Callable, Generator
from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.db import engine, get_db
from app.main import app


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(
        bind=connection,
        join_transaction_mode="create_savepoint",
    )
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def register_user(client: TestClient) -> Callable[..., dict[str, Any]]:
    counter = 0

    def register(
        *,
        nombre: str = "Usuario Test",
        email: str | None = None,
        password: str = "Password123",
    ) -> dict[str, Any]:
        nonlocal counter
        counter += 1
        user_email = email or f"usuario{counter}@example.com"
        response = client.post(
            "/auth/registro",
            json={"nombre": nombre, "email": user_email, "password": password},
        )
        assert response.status_code == 201, response.text
        return {
            "nombre": nombre,
            "email": user_email.lower(),
            "password": password,
            "response": response.json(),
        }

    return register


@pytest.fixture
def auth_headers(
    client: TestClient,
    register_user: Callable[..., dict[str, Any]],
) -> Callable[..., dict[str, str]]:
    def authenticate(**user_data: Any) -> dict[str, str]:
        user = register_user(**user_data)
        response = client.post(
            "/auth/login",
            data={"username": user["email"], "password": user["password"]},
        )
        assert response.status_code == 200, response.text
        return {"Authorization": f"Bearer {response.json()['access_token']}"}

    return authenticate


@pytest.fixture
def create_vehicle(
    client: TestClient,
) -> Callable[..., dict[str, Any]]:
    def create(
        headers: dict[str, str],
        *,
        capacidad: int = 4,
        matricula: str | None = None,
    ) -> dict[str, Any]:
        response = client.post(
            "/vehiculos",
            headers=headers,
            json={
                "marca": "Toyota",
                "modelo": "Corolla",
                "color": "Blanco",
                "matricula": matricula or f"T{uuid4().hex[:7]}",
                "capacidad": capacidad,
            },
        )
        assert response.status_code == 201, response.text
        return response.json()

    return create


@pytest.fixture
def future_trip_payload() -> dict[str, Any]:
    return {
        "origen": "Asunción",
        "destino": "San Lorenzo",
        "fecha": (datetime.now() + timedelta(days=1)).isoformat(),
        "cupos_totales": 3,
        "punto_salida": "Centro de Asunción",
        "punto_llegada": "Centro de San Lorenzo",
    }
