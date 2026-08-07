from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "frontend" / "app" / "viajes" / "nuevo" / "page.tsx"
FLOW = ROOT / "frontend" / "components" / "publish-trip" / "PublishTripFlow.tsx"
STYLES = ROOT / "frontend" / "app" / "globals.css"
SCHEMATIC = ROOT / "frontend" / "components" / "publish-trip" / "PublishRouteSchematic.tsx"
MAP_VIEW = ROOT / "frontend" / "components" / "maps" / "MapView.tsx"
POLYLINE = ROOT / "frontend" / "lib" / "polyline.ts"


def test_real_publish_route_reuses_single_three_step_flow():
    page = PAGE.read_text(encoding="utf-8")
    flow = FLOW.read_text(encoding="utf-8")
    assert "<PublishTripFlow/>" in page
    assert '["Recorrido", "Detalles", "Confirmación"]' in flow
    assert "¿A dónde vamos?" in flow
    assert "Prepará tu viaje" in flow
    assert "Revisá antes de publicar" in flow


def test_route_requires_selected_coordinates_and_keeps_paraguay_search():
    flow = FLOW.read_text(encoding="utf-8")
    assert 'placeholder="Buscar origen en Paraguay"' in flow
    assert 'placeholder="Buscar destino en Paraguay"' in flow
    assert "if (!originPoint)" in flow
    assert "if (!destinationPoint)" in flow
    assert "El destino debe ser diferente del origen." in flow
    assert "isWithinParaguay(point)" in flow


def test_details_use_real_vehicles_capacity_and_future_departure():
    flow = FLOW.read_text(encoding="utf-8")
    assert "api.vehicles(token)" in flow
    assert "selectedVehicle.capacidad" in flow
    assert "departureDate <= new Date()" in flow
    assert "Necesitás registrar un vehículo antes de publicar." in flow
    assert 'href="/vehiculos"' in flow


def test_publish_layout_has_official_desktop_and_mobile_proportions():
    styles = STYLES.read_text(encoding="utf-8")
    assert "grid-template-columns:minmax(22rem,.46fr) minmax(0,.54fr)" in styles
    assert "@media (max-width:800px)" in styles
    assert ".publish-map { position:static; order:-1; }" in styles
    assert "@media (max-width:360px)" in styles


def test_schematic_appears_only_with_real_selected_endpoints():
    flow = FLOW.read_text(encoding="utf-8")
    schematic = SCHEMATIC.read_text(encoding="utf-8")

    assert "step === 1 && <PublishRouteSchematic" in flow
    assert "origin={originPoint ? origin : undefined}" in flow
    assert "destination={destinationPoint ? destination : undefined}" in flow
    assert "Tu recorrido" in schematic
    assert "{origin}" in schematic
    assert "{destination}" in schematic
    assert "No representa calles" in schematic


def test_mobile_step_one_orders_inputs_map_schematic_and_action():
    styles = STYLES.read_text(encoding="utf-8")

    assert ".publish-layout.is-step-1 .publish-card { order:1; }" in styles
    assert ".publish-layout.is-step-1 .publish-map { order:2; }" in styles
    assert ".publish-layout.is-step-1 .publish-schematic { order:3; }" in styles
    assert ".publish-layout.is-step-1 .publish-route-continue { order:4; }" in styles


def test_schematic_supports_empty_partial_loading_and_complete_states():
    schematic = SCHEMATIC.read_text(encoding="utf-8")

    assert '"empty" | "partial" | "loading" | "ready" | "schematic"' in schematic
    assert "Elegí origen y destino para preparar tu recorrido." in schematic
    assert "Ahora elegí el destino." in schematic
    assert "Recorrido preparado" in schematic
    assert "Vista esquemática disponible" in schematic


def test_schematic_renders_only_stops_received_through_typed_props():
    schematic = SCHEMATIC.read_text(encoding="utf-8")

    assert "export interface PublishRouteStop" in schematic
    assert "stops = []" in schematic
    assert "stops.slice(0, STOP_POSITIONS.length).map" in schematic
    assert "schematic-waypoints" not in schematic
    assert "Paradas" in schematic


def test_schematic_has_svg_accessibility_and_text_equivalent():
    schematic = SCHEMATIC.read_text(encoding="utf-8")

    assert 'role="img"' in schematic
    assert 'aria-labelledby="publish-route-svg-title publish-route-svg-description"' in schematic
    assert '<title id="publish-route-svg-title">' in schematic
    assert '<desc id="publish-route-svg-description">' in schematic
    assert "No representa calles" in schematic


def test_real_map_uses_provider_geometry_with_direct_fallback():
    flow = FLOW.read_text(encoding="utf-8")
    polyline = POLYLINE.read_text(encoding="utf-8")

    assert "decodePolyline(route.geometry)" in flow
    assert "return [originPoint, destinationPoint]" in flow
    assert "route={mapRoute}" in flow
    assert "export function decodePolyline" in polyline
    assert "Recorrido disponible" in flow


def test_real_map_route_has_premium_depth_layers():
    map_view = MAP_VIEW.read_text(encoding="utf-8")

    assert 'id: "route-shadow"' in map_view
    assert '"line-color": "#b9d9ca"' in map_view
    assert '"line-color": "#075b49"' in map_view
    assert '"line-cap": "round"' in map_view
    assert 'map.fitBounds(bounds' in map_view


def test_real_map_has_an_https_production_safe_default_style():
    map_view = MAP_VIEW.read_text(encoding="utf-8")

    assert 'const DEFAULT_STYLE_URL = "https://tiles.openfreemap.org/styles/liberty"' in map_view
    assert "return { url: DEFAULT_STYLE_URL, usingFallback: true }" in map_view
    assert 'process.env.NODE_ENV === "development"\n    ?' not in map_view
    assert 'import("maplibre-gl")' in map_view
    assert "hasLoadedRef.current" in map_view


def test_route_summary_is_below_map_instead_of_covering_it():
    flow = FLOW.read_text(encoding="utf-8")

    assert 'className="publish-map-overlay"' not in flow
    assert 'className="publish-map-stage"><MapView' in flow
    assert 'className="publish-map-summary"' in flow
    assert "Tiempo estimado" in flow
    assert "{route && <dl>" in flow


def test_details_use_selectable_vehicle_cards_and_bounded_seat_stepper():
    flow = FLOW.read_text(encoding="utf-8")

    assert 'className="vehicle-picker"' in flow
    assert 'type="radio" name="publish-vehicle"' in flow
    assert 'className="seat-picker"' in flow
    assert 'aria-label="Quitar un lugar"' in flow
    assert 'aria-label="Agregar un lugar"' in flow
    assert "selectedVehicle.capacidad" in flow


def test_confirmation_keeps_map_primary_and_uses_one_compact_record():
    flow = FLOW.read_text(encoding="utf-8")
    styles = STYLES.read_text(encoding="utf-8")

    assert 'className="publish-step publish-confirmation"' in flow
    assert "Editar recorrido" in flow
    assert "Editar detalles" in flow
    assert "Confirmá que todos los datos estén correctos." in flow
    assert ".publish-layout.is-step-3 .publish-map { grid-column:1; grid-row:1; }" in styles
    assert ".publish-layout.is-step-3 .publish-card { grid-column:2; grid-row:1; }" in styles
