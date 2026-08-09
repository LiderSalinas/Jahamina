from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_trip_card_uses_vertical_mobile_route_and_natural_availability() -> None:
    card = (ROOT / "frontend/components/TripCard.tsx").read_text(encoding="utf-8")
    styles = (ROOT / "frontend/app/globals.css").read_text(encoding="utf-8")
    assert 'aria-label={`Ruta:' in card
    assert '"1 lugar disponible"' in card
    assert '"Completo"' in card
    assert ".trip-route-stop.is-destination::before" in styles
    assert ".trip-card-action { min-height:2.75rem" in styles


def test_profile_and_vehicle_surfaces_keep_real_media_controls() -> None:
    profile = (ROOT / "frontend/app/perfil/page.tsx").read_text(encoding="utf-8")
    vehicles = (ROOT / "frontend/app/vehiculos/page.tsx").read_text(encoding="utf-8")
    styles = (ROOT / "frontend/app/globals.css").read_text(encoding="utf-8")
    assert "UserAvatar" in profile
    assert "ImageUploadControl" in profile
    assert 'aria-labelledby="profile-photo-title"' in profile
    assert "VehicleImage" in vehicles
    assert "vehicle-metadata" in vehicles
    assert "ImageUploadControl" in vehicles
    assert ".vehicle-card-visual" in styles


def test_shared_microinteraction_contract_respects_reduced_motion() -> None:
    styles = (ROOT / "frontend/app/globals.css").read_text(encoding="utf-8")
    assert ".button-primary:hover:not(:disabled)" in styles
    assert ".button-primary:disabled" in styles
    assert "@media (prefers-reduced-motion:reduce)" in styles
