import datetime
from .state import RecoveryState
from ..models.database import SessionLocal
from ..models.entities import DeliveryResult, AuditLogEntry

def confirm_node(state: RecoveryState) -> RecoveryState:
    event = state["event"]
    db = SessionLocal()
    try:
        # Is this a webhook confirmation?
        if event.get("event_type") == "payment_link.paid":
            link_id = event["raw_payload"]["payload"]["payment_link"]["entity"]["id"]
            
            # Find the delivery result
            delivery = db.query(DeliveryResult).filter(
                DeliveryResult.response_payload.contains(link_id)
            ).first()
            
            if delivery:
                delivery.status = "recovered"
                db.commit()
                
                # Find original case ID
                from ..models.entities import Intervention
                intervention = db.query(Intervention).filter(Intervention.id == delivery.intervention_id).first()
                orig_case_id = intervention.event_id if intervention else event["id"]
                
                # Log the confirmation
                state["audit_log"].append({
                    "case_id": orig_case_id,
                    "actor": "razorpay_webhook",
                    "action": "confirm_recovery",
                    "reasoning": f"Received payment.paid webhook for link {link_id}",
                    "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
                })
                
                # Put delivery_result in state so logging can see it
                state["delivery_result"] = {
                    "id": delivery.id,
                    "status": "recovered",
                    "channel": delivery.channel,
                    "response_payload": delivery.response_payload
                }
        
        # Or is this the immediate run after execution?
        elif state.get("delivery_result"):
            deliv = state["delivery_result"]
            # Enforce that it cannot be 'recovered' yet
            if deliv.get("status") not in ["action_taken", "awaiting_confirmation", "responded", "delivered"]:
                # Actually, let's just make sure it's explicitly tracked as action_taken
                deliv["status"] = "action_taken"
                
            # Log the awaiting state
            state["audit_log"].append({
                "case_id": event["id"],
                "actor": "system",
                "action": "awaiting_confirmation",
                "reasoning": "Intervention executed, awaiting external confirmation loop.",
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
            })
    finally:
        db.close()
    return state
