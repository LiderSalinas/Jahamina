from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_navbar_keeps_authenticated_public_and_nested_route_navigation() -> None:
    source = (ROOT / "frontend/components/Navbar.tsx").read_text(encoding="utf-8")
    assert '["Viajes", "/viajes"' in source
    assert '["Reservas", "/reservas"' in source
    assert '["Mis viajes", "/mis-viajes"' in source
    assert '["Perfil", "/perfil"' in source
    assert 'href="/login"' in source
    assert 'href="/registro"' in source
    assert 'pathname.startsWith(`${href}/`)' in source
    assert 'aria-current={isActive(href) ? "page" : undefined}' in source


def test_navbar_preserves_notifications_avatar_logout_and_mobile_safe_area() -> None:
    navbar = (ROOT / "frontend/components/Navbar.tsx").read_text(encoding="utf-8")
    styles = (ROOT / "frontend/app/globals.css").read_text(encoding="utf-8")
    layout = (ROOT / "frontend/app/layout.tsx").read_text(encoding="utf-8")
    assert "NotificationBell" in navbar
    assert "UserAvatar" in navbar
    assert "logout()" in navbar
    assert "mobile-navigation" in navbar
    assert "env(safe-area-inset-bottom)" in styles
    assert "InstallPrompt" in layout
