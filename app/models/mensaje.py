from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class Mensaje(Base):
    __tablename__ = "mensajes"
    __table_args__ = (
        CheckConstraint(
            "tipo IN ('texto','sistema')", name="ck_mensajes_tipo"
        ),
        CheckConstraint(
            "char_length(contenido) BETWEEN 1 AND 1000",
            name="ck_mensajes_contenido",
        ),
        Index(
            "uq_mensaje_client_id",
            "conversacion_id",
            "remitente_id",
            "client_message_id",
            unique=True,
            postgresql_where=text("client_message_id IS NOT NULL"),
        ),
        Index(
            "ix_mensajes_historial",
            "conversacion_id",
            "id",
        ),
        Index(
            "ix_mensajes_no_leidos",
            "conversacion_id",
            "remitente_id",
            postgresql_where=text("leido_en IS NULL AND eliminado = false"),
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    conversacion_id: Mapped[int] = mapped_column(
        ForeignKey("conversaciones.id"), nullable=False
    )
    remitente_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id"), nullable=True
    )
    contenido: Mapped[str] = mapped_column(Text, nullable=False)
    tipo: Mapped[str] = mapped_column(
        String(20), server_default="texto", default="texto", nullable=False
    )
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    editado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    leido_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    eliminado: Mapped[bool] = mapped_column(
        Boolean, server_default="false", default=False, nullable=False
    )
    client_message_id: Mapped[str | None] = mapped_column(String(100))

    conversacion = relationship("Conversacion", back_populates="mensajes")
    remitente = relationship("Usuario", back_populates="mensajes_chat")
