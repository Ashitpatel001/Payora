import uuid
import datetime
from .state import RecoveryState
from ..models.database import SessionLocal
from ..models.entities import GuardrailResult

from .guardrails.max_attempts import check_max_attempts
from .guardrails.dispute_status import check_dispute_status
from .guardrails.ptp_suppression import check_ptp_suppression

def guardrail_node(state: RecoveryState) -> RecoveryState:
    event = state["event"]
    db = SessionLocal()
    try:
        rules = [
            check_max_attempts,
            check_dispute_status,
            check_ptp_suppression
        ]
        
        # We will also keep the high value block from earlier for extra measure
        amount = event.get("amount", 0)
        from ..config import HIGH_VALUE_THRESHOLD_PAISE
        def check_high_value(evt, d):
            passed = amount <= HIGH_VALUE_THRESHOLD_PAISE
            return {
                "rule_name": "high_value_block",
                "passed": passed,
                "reason": "Amount exceeds automated intervention limit (25k INR)" if not passed else "Amount within bounds"
            }
        rules.append(check_high_value)
        
        all_passed = True
        failed_rule = None
        
        for rule in rules:
            res = rule(event, db)
            # Persist every check
            db_res = GuardrailResult(
                id=f"gr_{uuid.uuid4().hex}",
                event_id=event["id"],
                rule_name=res["rule_name"],
                passed=res["passed"],
                reason=res["reason"],
                checked_at=datetime.datetime.utcnow()
            )
            db.add(db_res)
            
            if not res["passed"] and all_passed:
                all_passed = False
                failed_rule = res
                
        db.commit()
    finally:
        db.close()
    
    final_res = failed_rule if not all_passed else {
        "rule_name": "all_cleared",
        "passed": True,
        "reason": "Passed all guardrail checks"
    }
    
    state["guardrail_result"] = final_res
    
    state["audit_log"].append({
        "case_id": event["id"],
        "actor": "system",
        "action": "guardrail_check",
        "reasoning": final_res["reason"],
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    })
    
    return state
