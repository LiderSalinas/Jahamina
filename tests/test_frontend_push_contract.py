from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_vapid_conversion_and_explicit_activation_contract():
    helper = (ROOT / "frontend/lib/push-notifications.ts").read_text(encoding="utf-8")
    card = (ROOT / "frontend/components/notifications/NotificationPermissionCard.tsx").read_text(encoding="utf-8")

    assert '"=".repeat((4 - normalized.length % 4) % 4)' in helper
    assert '.replace(/-/g, "+").replace(/_/g, "/")' in helper
    assert "bytes.length !== 65" in helper
    assert "NEXT_PUBLIC_VAPID_PUBLIC_KEY" in helper
    assert "Notification.requestPermission()" in helper
    assert "pushManager.getSubscription()" in helper
    assert "pushManager.subscribe" in helper
    assert "Activar notificaciones" in card
    assert "Desactivar en este dispositivo" in card


def test_service_worker_only_opens_known_internal_routes():
    worker = (ROOT / "frontend/public/sw.js").read_text(encoding="utf-8")

    assert 'self.addEventListener("push"' in worker
    assert 'self.addEventListener("notificationclick"' in worker
    assert "ALLOWED_ROUTES" in worker
    assert 'value.startsWith("//")' in worker
    assert "parsed.origin === self.location.origin" in worker
    assert "clients.openWindow(url)" in worker


def test_private_vapid_key_is_never_a_frontend_variable():
    source_roots = [ROOT / "frontend/app", ROOT / "frontend/components", ROOT / "frontend/lib"]
    frontend = "\n".join(path.read_text(encoding="utf-8") for source_root in source_roots for path in source_root.rglob("*.ts*"))
    frontend_example = (ROOT / "frontend/.env.example").read_text(encoding="utf-8")

    assert "NEXT_PUBLIC_VAPID_PUBLIC_KEY" in frontend_example
    assert "VAPID_PRIVATE" not in frontend
    assert "VAPID_PRIVATE" not in frontend_example
