from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.settings import settings

# URL de conexión armada dinámicamente
SQLALCHEMY_DATABASE_URL = settings.database_url

# Crear el motor de conexión
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Crear una clase Session para usar en las dependencias
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para modelos ORM
Base = declarative_base()

# Dependencia para inyectar sesión en endpoints
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
