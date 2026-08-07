import asyncio
from io import BytesIO
from pathlib import Path
from unittest.mock import AsyncMock

from fastapi import UploadFile
from starlette.datastructures import Headers

from app.core.settings import settings
from app.services import media_service


PNG = b"\x89PNG\r\n\x1a\n" + b"safe-image"


def test_media_migration_is_nullable_and_reversible() -> None:
    source = Path("alembic/versions/20260807_0008_media_images.py").read_text(encoding="utf-8")
    assert 'op.add_column("usuarios"' in source
    assert 'op.add_column("vehiculos"' in source
    assert source.count("nullable=True") == 2
    assert 'op.drop_column("vehiculos", "imagen_url")' in source
    assert 'op.drop_column("usuarios", "imagen_url")' in source
    public_id_migration = Path("alembic/versions/20260807_0009_media_public_ids.py").read_text(encoding="utf-8")
    assert public_id_migration.count("imagen_public_id") == 4


def test_profile_image_requires_authentication(client) -> None:
    response = client.post("/usuarios/me/imagen", files={"file": ("photo.png", PNG, "image/png")})
    assert response.status_code == 401


def test_profile_upload_and_delete_are_persisted(client, auth_headers, monkeypatch) -> None:
    headers = auth_headers(email="media-profile@example.com")
    upload = AsyncMock(return_value=media_service.MediaAsset("https://res.cloudinary.com/test/image/upload/profile.png", "jahamina/users/1/image-aaaaaaaaaaaaaaaaaaaaaaaa"))
    destroy = AsyncMock()
    monkeypatch.setattr(media_service, "upload_image", upload)
    monkeypatch.setattr(media_service, "delete_image", destroy)

    uploaded = client.post("/usuarios/me/imagen", headers=headers, files={"file": ("photo.png", PNG, "image/png")})
    assert uploaded.status_code == 200
    assert uploaded.json()["imagen_url"].startswith("https://res.cloudinary.com/")
    assert client.get("/auth/me", headers=headers).json()["imagen_url"] == uploaded.json()["imagen_url"]
    assert upload.await_args.kwargs["owner"] == "users"

    deleted = client.delete("/usuarios/me/imagen", headers=headers)
    assert deleted.status_code == 200
    assert deleted.json()["imagen_url"] is None
    destroy.assert_awaited_once()
    assert destroy.await_args.kwargs["public_id"].startswith("jahamina/users/")


def test_vehicle_upload_requires_owner(client, auth_headers, create_vehicle, monkeypatch) -> None:
    owner = auth_headers(email="media-vehicle-owner@example.com")
    outsider = auth_headers(email="media-vehicle-outsider@example.com")
    vehicle = create_vehicle(owner)
    upload = AsyncMock(return_value=media_service.MediaAsset("https://res.cloudinary.com/test/image/upload/vehicle.png", "jahamina/vehicles/1/image-aaaaaaaaaaaaaaaaaaaaaaaa"))
    monkeypatch.setattr(media_service, "upload_image", upload)

    forbidden = client.post(f"/vehiculos/{vehicle['id']}/imagen", headers=outsider, files={"file": ("car.png", PNG, "image/png")})
    assert forbidden.status_code == 403
    upload.assert_not_awaited()

    uploaded = client.post(f"/vehiculos/{vehicle['id']}/imagen", headers=owner, files={"file": ("car.png", PNG, "image/png")})
    assert uploaded.status_code == 200
    assert uploaded.json()["imagen_url"].endswith("vehicle.png")
    assert upload.await_args.kwargs == {"owner": "vehicles", "owner_id": vehicle["id"]}


def test_vehicle_image_delete_is_persisted(client, auth_headers, create_vehicle, monkeypatch) -> None:
    owner = auth_headers(email="media-vehicle-delete@example.com")
    vehicle = create_vehicle(owner)
    monkeypatch.setattr(media_service, "upload_image", AsyncMock(return_value=media_service.MediaAsset("https://res.cloudinary.com/test/image/upload/vehicle.png", "jahamina/vehicles/1/image-aaaaaaaaaaaaaaaaaaaaaaaa")))
    destroy = AsyncMock()
    monkeypatch.setattr(media_service, "delete_image", destroy)
    client.post(f"/vehiculos/{vehicle['id']}/imagen", headers=owner, files={"file": ("car.png", PNG, "image/png")})
    deleted = client.delete(f"/vehiculos/{vehicle['id']}/imagen", headers=owner)
    assert deleted.status_code == 200
    assert deleted.json()["imagen_url"] is None
    destroy.assert_awaited_once()
    assert destroy.await_args.kwargs["public_id"].startswith("jahamina/vehicles/")


def _upload(data: bytes, content_type: str) -> UploadFile:
    return UploadFile(file=BytesIO(data), filename="image", headers=Headers({"content-type": content_type}))


def test_media_rejects_invalid_mime_and_signature() -> None:
    try:
        asyncio.run(media_service._read_validated(_upload(PNG, "application/pdf")))
    except media_service.MediaValidationError:
        pass
    else:
        raise AssertionError("An invalid MIME type was accepted")
    try:
        asyncio.run(media_service._read_validated(_upload(b"not-a-png", "image/png")))
    except media_service.MediaValidationError:
        pass
    else:
        raise AssertionError("A forged MIME type was accepted")


def test_media_rejects_oversized_files(monkeypatch) -> None:
    monkeypatch.setattr(settings, "media_max_upload_bytes", 8)
    try:
        asyncio.run(media_service._read_validated(_upload(PNG, "image/png")))
    except media_service.MediaValidationError as error:
        assert "5 MB" in str(error)
    else:
        raise AssertionError("An oversized image was accepted")


def test_cloudinary_upload_is_signed_and_uses_controlled_public_id(monkeypatch) -> None:
    captured = {}

    class Response:
        def raise_for_status(self) -> None: pass
        def json(self) -> dict[str, str]: return {"secure_url": "https://res.cloudinary.com/test/image/upload/safe.png"}

    class Client:
        def __init__(self, **kwargs): captured["client"] = kwargs
        async def __aenter__(self): return self
        async def __aexit__(self, *args): return None
        async def post(self, url, **kwargs): captured.update(url=url, **kwargs); return Response()

    monkeypatch.setattr(settings, "cloudinary_cloud_name", "test-cloud")
    monkeypatch.setattr(settings, "cloudinary_api_key", "test-key")
    monkeypatch.setattr(settings, "cloudinary_api_secret", "test-secret")
    monkeypatch.setattr(media_service.httpx, "AsyncClient", Client)
    result = asyncio.run(media_service.upload_image(_upload(PNG, "image/png"), owner="vehicles", owner_id=42))
    assert result.secure_url.startswith("https://res.cloudinary.com/")
    assert result.public_id.startswith("jahamina/vehicles/42/image-")
    assert captured["data"]["public_id"] == result.public_id
    assert captured["data"]["api_key"] == "test-key"
    assert captured["data"]["signature"]
    assert "test-secret" not in str(captured)


def test_new_users_and_vehicles_keep_null_images(client, auth_headers, create_vehicle) -> None:
    headers = auth_headers(email="media-null@example.com")
    assert client.get("/auth/me", headers=headers).json()["imagen_url"] is None
    assert create_vehicle(headers)["imagen_url"] is None
