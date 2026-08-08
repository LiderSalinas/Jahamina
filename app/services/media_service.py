from __future__ import annotations

from hashlib import sha1
from dataclasses import dataclass
import logging
import re
import secrets
import time
from typing import Literal
from urllib.parse import urlparse

import httpx
from fastapi import UploadFile

from app.core.settings import settings


logger = logging.getLogger(__name__)


ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
READ_CHUNK_BYTES = 64 * 1024


class MediaError(Exception):
    pass


class MediaConfigurationError(MediaError):
    pass


class MediaValidationError(MediaError):
    pass


class MediaProviderError(MediaError):
    pass


@dataclass(frozen=True)
class MediaAsset:
    secure_url: str
    public_id: str


def _configuration() -> tuple[str, str, str]:
    cloud_name = settings.cloudinary_cloud_name
    api_key = settings.cloudinary_api_key
    api_secret = settings.cloudinary_api_secret
    if not cloud_name or not cloud_name.strip() or not api_key or not api_key.strip() or not api_secret or not api_secret.strip():
        raise MediaConfigurationError("El almacenamiento de imágenes no está configurado.")
    return cloud_name.strip(), api_key.strip(), api_secret.strip()


def _signature(params: dict[str, str], secret: str) -> str:
    serialized = "&".join(f"{key}={value}" for key, value in sorted(params.items()) if value)
    return sha1(f"{serialized}{secret}".encode("utf-8")).hexdigest()


def _matches_content(content_type: str, data: bytes) -> bool:
    if content_type == "image/jpeg":
        return data.startswith(b"\xff\xd8\xff")
    if content_type == "image/png":
        return data.startswith(b"\x89PNG\r\n\x1a\n")
    if content_type == "image/webp":
        return len(data) >= 12 and data.startswith(b"RIFF") and data[8:12] == b"WEBP"
    return False


async def _read_validated(file: UploadFile) -> tuple[bytes, str]:
    content_type = (file.content_type or "").lower()
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise MediaValidationError("Usá una imagen JPEG, PNG o WebP.")
    chunks: list[bytes] = []
    total = 0
    while chunk := await file.read(READ_CHUNK_BYTES):
        total += len(chunk)
        if total > settings.media_max_upload_bytes:
            raise MediaValidationError("La imagen no puede superar 5 MB.")
        chunks.append(chunk)
    data = b"".join(chunks)
    if not data or not _matches_content(content_type, data):
        raise MediaValidationError("El contenido del archivo no coincide con una imagen permitida.")
    return data, content_type


def _safe_cloudinary_url(value: object) -> str:
    if not isinstance(value, str):
        raise MediaProviderError("Cloudinary no devolvió una imagen válida.")
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
        raise MediaProviderError("Cloudinary devolvió una URL no permitida.")
    return value


def _sanitize_provider_message(value: object) -> str:
    if not isinstance(value, str):
        return "Cloudinary no devolvió un mensaje de error."
    message = " ".join(value.split())
    message = re.sub(
        r"(?i)(api[_ -]?secret|authorization|token|signature)\s*[:=]\s*\S+",
        r"\1=[redacted]",
        message,
    )
    return message[:300] or "Cloudinary devolvió un mensaje de error vacío."


def _provider_error_message(response: httpx.Response) -> str:
    try:
        body = response.json()
    except ValueError:
        return "Cloudinary devolvió una respuesta no JSON."
    if isinstance(body, dict):
        error = body.get("error")
        if isinstance(error, dict):
            return _sanitize_provider_message(error.get("message"))
        return _sanitize_provider_message(body.get("message"))
    return "Cloudinary devolvió un error con formato inesperado."


def _log_provider_failure(
    *,
    operation: str,
    endpoint: str,
    response: httpx.Response | None = None,
    error: Exception | None = None,
) -> None:
    status_code = response.status_code if response is not None else None
    message = _provider_error_message(response) if response is not None else "No hubo respuesta HTTP de Cloudinary."
    error_type = type(error).__name__ if error is not None else "HTTPStatusError"
    logger.warning(
        "cloudinary operation=%s endpoint=%s status=%s error_type=%s message=%s",
        operation,
        endpoint,
        status_code,
        error_type,
        message,
    )


def _new_public_id(owner: Literal["users", "vehicles"], owner_id: int) -> str:
    return f"jahamina/{owner}/{owner_id}/image-{secrets.token_hex(12)}"


def _validate_public_id(public_id: str) -> str:
    pattern = r"^jahamina/(users|vehicles)/[0-9]+/image-[a-f0-9]{24}$"
    if not isinstance(public_id, str) or not re.fullmatch(pattern, public_id):
        raise MediaValidationError("El identificador de imagen no es válido.")
    return public_id


async def upload_image(file: UploadFile, *, owner: Literal["users", "vehicles"], owner_id: int) -> MediaAsset:
    cloud_name, api_key, api_secret = _configuration()
    data, content_type = await _read_validated(file)
    public_id = _new_public_id(owner, owner_id)
    transformation = "c_fill,g_auto,h_512,q_auto:good,w_512" if owner == "users" else "c_limit,h_1200,q_auto:good,w_1600"
    signed = {"invalidate": "true", "overwrite": "true", "public_id": public_id, "timestamp": str(int(time.time())), "transformation": transformation}
    payload = {**signed, "api_key": api_key, "signature": _signature(signed, api_secret)}
    endpoint = f"/v1_1/{cloud_name}/image/upload"
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                f"https://api.cloudinary.com{endpoint}",
                data=payload,
                files={"file": ("image", data, content_type)},
            )
            response.raise_for_status()
            return MediaAsset(
                secure_url=_safe_cloudinary_url(response.json().get("secure_url")),
                public_id=public_id,
            )
    except httpx.HTTPStatusError as error:
        _log_provider_failure(operation="upload", endpoint=endpoint, response=error.response, error=error)
        raise MediaProviderError("No pudimos guardar la imagen.") from error
    except httpx.RequestError as error:
        _log_provider_failure(operation="upload", endpoint=endpoint, error=error)
        raise MediaProviderError("No pudimos guardar la imagen.") from error
    except MediaProviderError as error:
        _log_provider_failure(
            operation="upload",
            endpoint=endpoint,
            response=response,
            error=error,
        )
        raise
    except (ValueError, KeyError) as error:
        _log_provider_failure(operation="upload", endpoint=endpoint, response=response, error=error)
        raise MediaProviderError("No pudimos guardar la imagen. Intentá nuevamente.") from error


async def delete_image(*, public_id: str) -> None:
    cloud_name, api_key, api_secret = _configuration()
    public_id = _validate_public_id(public_id)
    signed = {"invalidate": "true", "public_id": public_id, "timestamp": str(int(time.time()))}
    payload = {**signed, "api_key": api_key, "signature": _signature(signed, api_secret)}
    endpoint = f"/v1_1/{cloud_name}/image/destroy"
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(f"https://api.cloudinary.com{endpoint}", data=payload)
            response.raise_for_status()
    except httpx.HTTPStatusError as error:
        _log_provider_failure(operation="destroy", endpoint=endpoint, response=error.response, error=error)
        raise MediaProviderError("No pudimos eliminar la imagen.") from error
    except httpx.RequestError as error:
        _log_provider_failure(operation="destroy", endpoint=endpoint, error=error)
        raise MediaProviderError("No pudimos eliminar la imagen.") from error
