from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_location_search_is_natural_ranked_and_mobile_friendly():
    component = (ROOT / "frontend/components/maps/LocationSearch.tsx").read_text(encoding="utf-8")
    styles = (ROOT / "frontend/app/globals.css").read_text(encoding="utf-8")

    assert "}, 300);" in component
    assert "controller.abort()" in component
    assert "items.slice(0, 6)" in component
    assert "item.primary" in component
    assert "item.secondary" in component
    assert 'role="listbox"' in component
    assert "max-height:min(14rem,42vh)" in styles


def test_map_camera_only_changes_for_a_new_geographic_selection():
    component = (ROOT / "frontend/components/maps/MapView.tsx").read_text(encoding="utf-8")

    assert "selectionSignature" in component
    assert "lastAutomaticCameraRef.current" in component
    assert "Centrar recorrido" in component
    assert "duration: 650" in component
