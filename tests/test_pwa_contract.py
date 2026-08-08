from pathlib import Path
import struct


ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"


def png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    return struct.unpack(">II", data[16:24])


def test_pwa_manifest_declares_installable_android_assets() -> None:
    manifest = (FRONTEND / "app/manifest.ts").read_text(encoding="utf-8")
    assert 'name: "Jahamina"' in manifest
    assert 'short_name: "Jahamina"' in manifest
    assert 'start_url: "/"' in manifest
    assert 'scope: "/"' in manifest
    assert 'display: "standalone"' in manifest
    assert 'src: "/icons/icon-192.png"' in manifest
    assert 'src: "/icons/icon-512.png"' in manifest
    assert 'purpose: "maskable"' in manifest
    assert "prefer_related_applications" not in manifest
    assert png_size(FRONTEND / "public/icons/icon-192.png") == (192, 192)
    assert png_size(FRONTEND / "public/icons/icon-512.png") == (512, 512)


def test_pwa_install_prompt_is_deferred_and_ios_specific() -> None:
    prompt = (FRONTEND / "components/pwa/InstallPrompt.tsx").read_text(encoding="utf-8")
    assert "beforeinstallprompt" in prompt
    assert "event.preventDefault()" in prompt
    assert ".prompt()" in prompt
    assert "display-mode" in prompt
    assert "Añadir a pantalla de inicio" in prompt
    assert "standalone?: boolean" in prompt


def test_existing_service_worker_still_handles_push_and_click() -> None:
    worker = (FRONTEND / "public/sw.js").read_text(encoding="utf-8")
    assert 'self.addEventListener("push"' in worker
    assert 'self.addEventListener("notificationclick"' in worker
    assert "showNotification" in worker
    assert "openWindow" in worker
