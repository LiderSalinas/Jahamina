from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_notification_navigation_uses_safe_contextual_fallbacks() -> None:
    source = (ROOT / "frontend/lib/notification-navigation.ts").read_text(encoding="utf-8")
    assert "new URL(value, window.location.origin)" in source
    assert 'value.startsWith("//")' in source
    assert "parsed.origin === window.location.origin" in source
    assert '"/reservas"' in source
    assert '"/mis-viajes"' in source
    assert "conversacion_id" in source
    assert "?chat=" in source


def test_bell_and_chat_use_contextual_target() -> None:
    bell = (ROOT / "frontend/components/notifications/NotificationBell.tsx").read_text(encoding="utf-8")
    chat = (ROOT / "frontend/components/chat/ChatPreview.tsx").read_text(encoding="utf-8")
    assert "safeNotificationTarget(item)" in bell
    assert 'get("chat")' in chat
    assert "setOpen(true)" in chat


def test_service_worker_keeps_internal_notification_navigation() -> None:
    worker = (ROOT / "frontend/public/sw.js").read_text(encoding="utf-8")
    assert "safeInternalUrl" in worker
    assert "payload.data?.url ?? payload.url" in worker
    assert "event.notification.data?.url" in worker
    assert 'clients.openWindow(url)' in worker
