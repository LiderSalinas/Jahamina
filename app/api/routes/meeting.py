from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import get_current_user
from app.models.usuario import Usuario
from app.schemas.meeting_schema import MeetingPointProposal, MeetingPointResponse
from app.services import meeting_service

router = APIRouter()


@router.get("/reservas/{request_id}/punto-encuentro", response_model=MeetingPointResponse)
def get_point(request_id: int, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    return meeting_service.get(db, request_id, user.id)


@router.post("/reservas/{request_id}/punto-encuentro/proponer", response_model=MeetingPointResponse)
def propose_point(request_id: int, data: MeetingPointProposal, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    return meeting_service.propose(db, request_id, user.id, data)


@router.patch("/reservas/{request_id}/punto-encuentro/confirmar", response_model=MeetingPointResponse)
def confirm_point(request_id: int, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    return meeting_service.confirm(db, request_id, user.id)


@router.patch("/reservas/{request_id}/punto-encuentro/rechazar", response_model=MeetingPointResponse)
def reject_point(request_id: int, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    return meeting_service.reject(db, request_id, user.id)
