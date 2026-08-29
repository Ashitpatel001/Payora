import uuid
from .state import RecoveryState
from ..models.database import SessionLocal
from ..models.entities import Intervention, AuditLogEntry

def policy_node(state: RecoveryState) -> RecoveryState:
    event = state["event"]
    diagnosis = state["diagnosis"] or {}
    
    quadrant = diagnosis.get("risk_quadrant", "technical")
    root_cause = diagnosis.get("root_cause_category", "unknown")
    
    db = SessionLocal()
    
    # Escalation Ladder: count previous attempts
    attempts = db.query(AuditLogEntry).filter(
        AuditLogEntry.case_id == event["id"],
        AuditLogEntry.action == "policy_decision"
    ).count()
    
    # Intervention Type
    intervention_type = "retry_now"
    
    # Channel and Tone ladder
    channel = "text"
    tone = "friendly_reminder"
    
    if attempts == 0:
        tone = "friendly_reminder"
        channel = "text"
        reasoning = f"Attempt 1: Soft nudge via SMS/Email for {quadrant} risk."
    elif attempts == 1:
        tone = "formal_notice"
        channel = "text"
        reasoning = f"Attempt 2: Escalating to formal WhatsApp notice due to no response."
    else:
        # Final attempt
        intervention_type = "escalate"
        channel = "text"
        tone = "firm_warning"
        reasoning = f"Attempt {attempts+1}: Firm-tone text escalation due to repeated no response."
        
    # Override for absolute hard cases
    if root_cause in ["invoice_overdue", "strategic_defaulter"]:
        intervention_type = "escalate"
        tone = "formal_notice"
        
    int_id = f"int_{uuid.uuid4().hex}"
    
    db_int = Intervention(
        id=int_id,
        event_id=event["id"],
        intervention_type=intervention_type,
        channel=channel,
        tone=tone,
        scheduled_at=None
    )
    db.add(db_int)
    db.commit()
    db.close()
    
    state["intervention"] = {
        "id": int_id,
        "event_id": event["id"],
        "intervention_type": intervention_type,
        "channel": channel,
        "tone": tone
    }
    
    state["audit_log"].append({
        "case_id": event["id"],
        "actor": "agent",
        "action": "policy_decision",
        "reasoning": reasoning,
        "timestamp": "now"
    })
    
    return state
