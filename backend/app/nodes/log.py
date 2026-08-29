import uuid
import datetime
from .state import RecoveryState
from ..models.database import SessionLocal
from ..models.entities import AuditLogEntry

def log_node(state: RecoveryState) -> RecoveryState:
    db = SessionLocal()
    for log_item in state["audit_log"]:
        # Only insert if it doesn't already exist (we might have inserted it during previous steps or we just collect them all here)
        # Actually we should just insert the ones that are new, but since we are running the graph in memory, we can just insert all of them.
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
    db.close()
    
    # clear audit log to avoid double insertion if log_node is called again?
    state["audit_log"] = []
    
    return state
