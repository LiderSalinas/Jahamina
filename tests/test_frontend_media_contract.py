from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MEDIA = ROOT / "frontend" / "lib" / "media.ts"
AVATAR = ROOT / "frontend" / "components" / "ui" / "UserAvatar.tsx"
VEHICLE = ROOT / "frontend" / "components" / "trip-roadmap" / "VehicleImage.tsx"
UPLOAD = ROOT / "frontend" / "components" / "media" / "ImageUploadControl.tsx"
API = ROOT / "frontend" / "lib" / "api.ts"


def test_image_urls_only_accept_http_and_https() -> None:
    source = MEDIA.read_text(encoding="utf-8")
    assert '["http:", "https:"].includes(url.protocol)' in source
    assert "url.username || url.password" in source
    assert "return null" in source


def test_user_avatar_supports_photo_and_initials_fallback() -> None:
    source = AVATAR.read_text(encoding="utf-8")
    assert "safeRemoteImageUrl(imageUrl)" in source
    assert 'loading="lazy"' in source
    assert "onError={() => setFailedUrl(safeUrl)}" in source
    assert "initialsFor(name)" in source


def test_vehicle_image_supports_photo_failure_and_optional_metadata() -> None:
    source = VEHICLE.read_text(encoding="utf-8")
    assert "safeRemoteImageUrl(imageUrl)" in source
    assert "onError={() => setFailedUrl(resolvedImageUrl)}" in source
    assert 'className="vehicle-image-photo"' in source
    assert 'className="vehicle-image-meta"' in source
    assert "color &&" in source
    assert "registration &&" in source
    assert '<svg viewBox="0 0 460 220"' in source


def test_authenticated_frontend_upload_contract() -> None:
    api = API.read_text(encoding="utf-8")
    upload = UPLOAD.read_text(encoding="utf-8")
    assert '!(options.body instanceof FormData)' in api
    assert '"/usuarios/me/imagen"' in api
    assert '`/vehiculos/${id}/imagen`' in api
    assert 'type="file"' in upload
    assert 'accept="image/jpeg,image/png,image/webp"' in upload
    assert "MAX_BYTES = 5 * 1024 * 1024" in upload
    assert "URL.revokeObjectURL(previewRef.current)" in upload
