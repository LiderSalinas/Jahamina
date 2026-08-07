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


def test_backend_push_config_is_authoritative_and_env_key_is_only_fallback():
    helper = (ROOT / "frontend/lib/push-notifications.ts").read_text(encoding="utf-8")
    card = (ROOT / "frontend/components/notifications/NotificationPermissionCard.tsx").read_text(encoding="utf-8")

    assert "const config = await api.pushConfig()" in helper
    assert 'if (!config.enabled) throw new PushSetupError("unconfigured"' in helper
    assert "config.public_key?.trim() || configuredVapidPublicKey()" in helper
    assert "const publicKey = await loadPushPublicKey()" in helper
    assert helper.index("const publicKey = await loadPushPublicKey()") < helper.index("Notification.requestPermission()")
    restore_guard = helper.split("export async function restorePushSubscription", 1)[1].split("const registration", 1)[0]
    assert "configuredVapidPublicKey" not in restore_guard
    assert 'useState<PermissionState>("checking")' in card
    assert "loadPushPublicKey()" in card
    assert 'else setState("available")' in card


def test_push_ui_distinguishes_disabled_unsupported_and_denied_states():
    helper = (ROOT / "frontend/lib/push-notifications.ts").read_text(encoding="utf-8")
    card = (ROOT / "frontend/components/notifications/NotificationPermissionCard.tsx").read_text(encoding="utf-8")

    assert 'PushSetupError("unsupported"' in helper
    assert 'PushSetupError("insecure"' in helper
    assert 'setState("denied")' in card
    assert "Este navegador no admite notificaciones Push." in card
    assert "El permiso fue rechazado." in card
    assert "Las notificaciones Push todavía no están configuradas." in card
    assert 'state === "unconfigured"' in card


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
