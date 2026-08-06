PARAGUAY_COUNTRY_CODE = "py"
PARAGUAY_COUNTRY_NAME = "Paraguay"
PARAGUAY_WEST = -62.65
PARAGUAY_SOUTH = -27.61
PARAGUAY_EAST = -54.26
PARAGUAY_NORTH = -19.29
PARAGUAY_VIEWBOX = f"{PARAGUAY_WEST},{PARAGUAY_NORTH},{PARAGUAY_EAST},{PARAGUAY_SOUTH}"


def is_within_paraguay(latitude: float, longitude: float) -> bool:
    return PARAGUAY_SOUTH <= latitude <= PARAGUAY_NORTH and PARAGUAY_WEST <= longitude <= PARAGUAY_EAST


def validate_paraguay_coordinates(latitude: float, longitude: float) -> None:
    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180 or not is_within_paraguay(latitude, longitude):
        raise ValueError("La ubicación debe estar dentro de Paraguay.")
