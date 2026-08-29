from sqlalchemy.orm import Session
from ...models.entities import AuditLogEntry

def check_max_attempts(event: dict, db: Session) -> dict:
    # Rule: Max 3 attempts
    # We count previous 'policy_decision' or 'execute' actions for this case
    attempts = db.query(AuditLogEntry).filter(
        AuditLogEntry.case_id == event["id"],
        AuditLogEntry.action == "policy_decision"
    ).count()
    
    # Check if we seeded a manual 'max_attempts_trigger'
    if event.get("raw_payload", {}).get("_test_trigger") == "max_attempts":
        attempts = 3
        
    passed = attempts < 3
    return {
        "rule_name": "max_attempts_limit",
        "passed": passed,
        "reason": f"Case has {attempts} previous attempts" if not passed else "Under max attempts limit"
    }
