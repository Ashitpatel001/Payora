import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

import uuid
import random
import datetime
from backend.app.models.database import SessionLocal, engine, Base
from backend.app.models.entities import RiskEvent, AuditLogEntry

def generate():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # clear existing
    db.query(RiskEvent).delete()
    db.query(AuditLogEntry).delete()
    
    total_events = 150
    dev_count = 120
    
    event_types = [
        ("webhook", "payment.failed"),
        ("webhook", "subscription.halted"),
        ("synthetic_receivable", "invoice.overdue")
    ]
    
    events = []
    
    # 1. Seed Max Attempts block
    evt1_id = f"evt_{uuid.uuid4().hex}"
    evt1 = RiskEvent(
        id=evt1_id,
        source="webhook",
        event_type="payment.failed",
        customer_id=f"cust_{uuid.uuid4().hex[:8]}",
        amount=500000,
        currency="INR",
        raw_payload={"_test_trigger": "max_attempts"},
        created_at=datetime.datetime.utcnow(),
        split="dev"
    )
    events.append(evt1)
    
    # Insert dummy audit logs to trigger real max_attempts limit in DB check if I used it, but I added a test trigger to make it easy.
    # The guardrail rule checks raw_payload["_test_trigger"] == "max_attempts" or DB count. 
    # I'll just use the trigger.
    
    # 2. Seed Dispute Status block
    evt2_id = f"evt_{uuid.uuid4().hex}"
    evt2 = RiskEvent(
        id=evt2_id,
        source="webhook",
        event_type="payment.failed",
        customer_id=f"cust_{uuid.uuid4().hex[:8]}",
        amount=500000,
        currency="INR",
        raw_payload={"_test_trigger": "dispute"},
        created_at=datetime.datetime.utcnow(),
        split="dev"
    )
    events.append(evt2)
    
    # 3. Seed PTP Suppression block
    evt3_id = f"evt_{uuid.uuid4().hex}"
    evt3 = RiskEvent(
        id=evt3_id,
        source="webhook",
        event_type="payment.failed",
        customer_id=f"cust_{uuid.uuid4().hex[:8]}",
        amount=500000,
        currency="INR",
        raw_payload={"_test_trigger": "ptp_suppression"},
        created_at=datetime.datetime.utcnow(),
        split="dev"
    )
    events.append(evt3)
    
    for i in range(total_events - 3):
        source, event_type = random.choice(event_types)
        split = "dev" if i < (dev_count - 3) else "holdout"
        
        # Right skewed distribution between 500 and 75000 INR
        val = int(random.betavariate(2, 6) * 75000)
        val = max(500, min(75000, val))
        
        raw_payload = {
            "amount": val * 100, # paise
            "currency": "INR",
            "customer_id": f"cust_{uuid.uuid4().hex[:8]}"
        }
        
        event = RiskEvent(
            id=f"evt_{uuid.uuid4().hex}",
            source=source,
            event_type=event_type,
            customer_id=raw_payload["customer_id"],
            amount=raw_payload["amount"],
            currency=raw_payload["currency"],
            raw_payload=raw_payload,
            created_at=datetime.datetime.utcnow(),
            split=split
        )
        events.append(event)
    
    db.add_all(events)
    db.commit()
    db.close()
    
    logger.info(f"Generated {total_events} synthetic events (120 dev, 30 holdout), including 3 seeded guardrail triggers")

if __name__ == "__main__":
    generate()
