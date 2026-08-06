from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROADMAP = ROOT / "frontend" / "components" / "trip-roadmap" / "RealTripRoadmap.tsx"
MAP_PREVIEW = ROOT / "frontend" / "components" / "trip-roadmap" / "TripMapPreview.tsx"
STYLES = ROOT / "frontend" / "app" / "globals.css"
NAVBAR = ROOT / "frontend" / "components" / "Navbar.tsx"


def test_real_reservation_maps_origin_and_destination_independently():
    roadmap = ROADMAP.read_text(encoding="utf-8")
    preview = MAP_PREVIEW.read_text(encoding="utf-8")

    assert "origin={data.viaje.origen}" in roadmap
    assert "destination={data.viaje.destino}" in roadmap
    assert "<b>{origin}</b>" in preview
    assert "<b>{destination}</b>" in preview
    assert 'destination = "Destino"' in preview


def test_reservation_summary_uses_compact_chat_without_duplicate_route_action():
    roadmap = ROADMAP.read_text(encoding="utf-8")

    assert 'window.dispatchEvent(new Event("jahamina:open-chat"))' in roadmap
    assert 'href="#chat-reserva">Abrir chat' not in roadmap


def test_completed_stages_do_not_keep_pending_copy():
    roadmap = ROADMAP.read_text(encoding="utf-8")

    assert 'status === "completed"' in roadmap
    assert 'detail = "Etapa completada"' in roadmap


def test_pending_reservation_is_not_presented_as_a_roadmap_error():
    roadmap = ROADMAP.read_text(encoding="utf-8")

    assert 'caught.status === 409' in roadmap
    assert 'api.relatedReservations(token)' in roadmap
    assert 'Esperando confirmación' in roadmap
    assert 'El conductor todavía debe confirmar tu solicitud.' in roadmap
    assert '<BasicReservationDetail' in roadmap


def test_pending_reservation_actions_and_real_errors_are_distinct():
    roadmap = ROADMAP.read_text(encoding="utf-8")

    assert 'reservation.estado === "pendiente"' in roadmap
    assert 'api.cancelRequest(reservation.reserva_id, token)' in roadmap
    assert 'loadErrorStatus === 0' in roadmap
    assert 'Solicitud rechazada' in roadmap
    assert 'Solicitud cancelada' in roadmap


def test_mobile_reservation_has_the_approved_content_order():
    styles = STYLES.read_text(encoding="utf-8")

    assert 'grid-template-areas:"heading" "message" "status" "timeline" "route" "meeting" "chat" "info"' in styles
    assert "@media (max-width:768px)" in styles
    assert ".reservation-page { width:calc(100% - 2rem)" in styles


def test_mobile_menu_supports_escape_and_outside_close():
    navbar = NAVBAR.read_text(encoding="utf-8")

    assert 'event.key === "Escape"' in navbar
    assert 'className="mobile-menu-backdrop"' in navbar
    assert 'aria-controls="mobile-navigation"' in navbar
    assert 'className="mobile-account-summary"' in navbar
