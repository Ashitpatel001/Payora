from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..models.database import get_db
from ..models.entities import GuardrailResult

router = APIRouter()

@router.get("/api/guardrails")
def get_guardrails(db: Session = Depends(get_db)):
    results = db.query(GuardrailResult).order_by(GuardrailResult.checked_at.desc()).all()
    return results
