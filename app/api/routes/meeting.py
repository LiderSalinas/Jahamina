from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import get_current_user
from app.models.usuario import Usuario
from app.schemas.meeting_schema import MeetingPointProposal, MeetingPointResponse
from app.services import meeting_service
from app.services import notification_service
from app.models.solicitud_viaje import SolicitudViaje

router = APIRouter()


@router.get("/reservas/{request_id}/punto-encuentro", response_model=MeetingPointResponse)
def get_point(request_id: int, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    return meeting_service.get(db, request_id, user.id)


@router.post("/reservas/{request_id}/punto-encuentro/proponer", response_model=MeetingPointResponse)
def propose_point(request_id: int, data: MeetingPointProposal, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    return meeting_service.propose(db, request_id, user.id, data)


@router.patch("/reservas/{request_id}/punto-encuentro/confirmar", response_model=MeetingPointResponse)
async def confirm_point(request_id: int, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    response = meeting_service.confirm(db, request_id, user.id)
    request = db.get(SolicitudViaje, request_id)
    if request and response.estado == "confirmado":
        recipient_id = request.viaje.creador_id if user.id == request.pasajero_id else request.pasajero_id
        await notification_service.notify(
            db, user_id=recipient_id, actor_id=user.id, notification_type="punto_confirmado",
            title="Punto de encuentro confirmado", body="El punto de encuentro quedó acordado.",
            idempotency_key=f"meeting:{request.id}:confirmed:{recipient_id}", destination_url=f"/reservas/{request.id}",
            reservation_id=request.id, trip_id=request.viaje_id, conversation_id=request.conversacion.id if request.conversacion else None,
        )
    return response


@router.patch("/reservas/{request_id}/punto-encuentro/rechazar", response_model=MeetingPointResponse)
def reject_point(request_id: int, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    return meeting_service.reject(db, request_id, user.id)
