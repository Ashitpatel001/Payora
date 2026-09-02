import uuid
import datetime
from .state import RecoveryState
from ..models.database import SessionLocal
from ..models.entities import AuditLogEntry

def log_node(state: RecoveryState) -> RecoveryState:
    db = SessionLocal()
    try:
        for log_item in state["audit_log"]:
            db_log = AuditLogEntry(
                id=f"log_{uuid.uuid4().hex}",
                case_id=log_item["case_id"],
                actor=log_item["actor"],
                action=log_item["action"],
                reasoning=log_item["reasoning"],
                timestamp=datetime.datetime.utcnow()
            )
            db.add(db_log)
        db.commit()
    finally:
        db.close()
    
    # clear audit log to avoid double insertion if log_node is called again?
    state["audit_log"] = []
    
    return state
