from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "frontend" / "lib" / "client-id.ts"
PANEL = ROOT / "frontend" / "components" / "chat" / "ChatPanel.tsx"
COMPOSER = ROOT / "frontend" / "components" / "chat" / "MessageComposer.tsx"


def test_client_id_prefers_uuid_and_has_secure_and_monotonic_fallbacks():
    source = HELPER.read_text(encoding="utf-8")

    assert 'typeof cryptoApi?.randomUUID === "function"' in source
    assert "return cryptoApi.randomUUID()" in source
    assert 'typeof cryptoApi?.getRandomValues === "function"' in source
    assert "cryptoApi.getRandomValues(bytes)" in source
    assert "bytes[6] = (bytes[6] & 0x0f) | 0x40" in source
    assert "bytes[8] = (bytes[8] & 0x3f) | 0x80" in source
    assert "fallbackCounter += 1" in source
    assert "Math.random" not in source


def test_client_id_uuid_v4_shape_and_non_empty_fallback_contract():
    source = HELPER.read_text(encoding="utf-8")

    assert 'hex.slice(0, 4).join("")' in source
    assert 'hex.slice(10, 16).join("")' in source
    assert re.search(r"return `client-\$\{timeOrigin\}-\$\{timestamp", source)


def test_chat_reuses_client_id_and_has_no_unsafe_random_uuid_call():
    panel = PANEL.read_text(encoding="utf-8")

    assert "const clientId = previousId || createClientMessageId()" in panel
    assert "crypto.randomUUID()" not in panel
    assert "client_message_id: clientId" in panel
    assert "item.client_message_id === message.client_message_id" in panel


def test_composer_awaits_send_restores_content_and_blocks_double_submit():
    source = COMPOSER.read_text(encoding="utf-8")

    assert "await onSend(clean)" in source
    assert "if (!clean || disabled || sending) return" in source
    assert "setContent((current) => current || clean)" in source
    assert "catch" in source
    assert 'role="alert"' in source
    assert "void submit()" in source
