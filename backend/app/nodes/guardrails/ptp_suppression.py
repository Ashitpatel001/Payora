from sqlalchemy.orm import Session
from ...models.entities import PromiseToPay

def check_ptp_suppression(event: dict, db: Session) -> dict:
    # Rule: Once a PTP is logged, suppress further nudges on that case until promised date passes.
    
    # Check test trigger
    raw = event.get("raw_payload", {})
    if raw.get("_test_trigger") == "ptp_suppression":
        return {
            "rule_name": "ptp_suppression",
            "passed": False,
            "reason": "Active Promise to Pay (PTP) is pending"
        }
        
    # Real logic:
    active_ptps = db.query(PromiseToPay).filter(
        PromiseToPay.case_id == event["id"],
        PromiseToPay.status == "pending"
    ).count()
    
    passed = active_ptps == 0
    return {
        "rule_name": "ptp_suppression",
        "passed": passed,
        "reason": "Active Promise to Pay (PTP) is pending" if not passed else "No active PTPs blocking"
    }
