from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VEHICLES_PAGE = ROOT / "frontend" / "app" / "vehiculos" / "page.tsx"
API_CLIENT = ROOT / "frontend" / "lib" / "api.ts"


def test_vehicle_creation_accepts_all_successful_2xx_responses():
    api = API_CLIENT.read_text(encoding="utf-8")

    assert "if (!response.ok)" in api
    assert "response.status === 200" not in api
    assert 'createVehicle(' in api
    assert 'request<Vehicle>(' in api


def test_vehicle_creation_and_refresh_have_independent_error_handling():
    page = VEHICLES_PAGE.read_text(encoding="utf-8")

    assert "created = await api.createVehicle" in page
    assert "setSuccess(\"Vehículo registrado correctamente.\")" in page
    assert "setVehicles((current) =>" in page
    assert "setVehicles(await api.vehicles(token))" in page
    assert "El vehículo se registró, pero no pudimos actualizar la lista." in page
    assert "Reintentar lista" in page


def test_vehicle_errors_keep_actionable_http_meanings():
    page = VEHICLES_PAGE.read_text(encoding="utf-8")

    expected = {
        0: "No pudimos conectar con el servidor.",
        401: "Tu sesión venció. Volvé a iniciar sesión.",
        403: "No tenés permiso para realizar esta acción.",
        409: "La matrícula ya está registrada.",
        422: "return caught.message",
        500: "El servidor no pudo completar la operación. Intentá nuevamente.",
    }
    for status, message in expected.items():
        assert f"caught.status === {status}" in page or (
            status == 500 and "caught.status >= 500" in page
        )
        assert message in page


def test_vehicle_submit_prevents_duplicate_posts():
    page = VEHICLES_PAGE.read_text(encoding="utf-8")

    assert "if (!token || submitting) return" in page
    assert "disabled={submitting}" in page
    assert 'submitting ? "Guardando…" : "Guardar vehículo"' in page
