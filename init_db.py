from app.core.db import Base, engine
from app.models.usuario import Usuario
from app.models.viaje_model import Viaje
from app.models.pasajero_viaje import ViajeUnido

print("🛠️  Creando las tablas en la base de datos...")
Base.metadata.create_all(bind=engine)
print("✅ ¡Tablas creadas correctamente!")
