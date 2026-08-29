from sqlalchemy.orm import Session

def check_dispute_status(event: dict, db: Session) -> dict:
    # Rule: Automatic stop on dispute-opened
    # Assuming dispute flag is passed in the event payload
    raw = event.get("raw_payload", {})
    
    is_disputed = raw.get("dispute_opened", False)
    
    # Check test trigger
    if raw.get("_test_trigger") == "dispute":
        is_disputed = True
        
    passed = not is_disputed
    return {
        "rule_name": "no_active_dispute",
        "passed": passed,
        "reason": "Active dispute found on account" if not passed else "No active dispute"
    }
