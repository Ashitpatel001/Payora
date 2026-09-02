from fastapi import APIRouter, Depends, Request, HTTPException, Header, BackgroundTasks
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "../../../.env"))

from ..models.database import get_db
from ..models.entities import RiskEvent
from ..nodes.graph import recovery_graph
import razorpay
import uuid
import datetime

router = APIRouter()

key_id = os.environ.get("RAZORPAY_KEY_ID")
key_secret = os.environ.get("RAZORPAY_KEY_SECRET")
webhook_secret = os.environ.get("RAZORPAY_WEBHOOK_SECRET")

razorpay_client = razorpay.Client(auth=(key_id, key_secret)) if key_id and key_secret else None

def process_webhook_case(event_id: str, db: Session):
    event = db.query(RiskEvent).filter(RiskEvent.id == event_id).first()
    if not event: return
    state = {
        "event": {
            "id": event.id,
            "event_type": event.event_type,
            "amount": event.amount,
            "customer_id": event.customer_id,
            "source": event.source,
            "raw_payload": event.raw_payload
        },
        "diagnosis": None,
        "guardrail_result": None,
        "intervention": None,
        "delivery_result": None,
        "audit_log": []
    }
    recovery_graph.invoke(state)

@router.post("/api/webhooks/razorpay")
async def razorpay_webhook(request: Request, background_tasks: BackgroundTasks, x_razorpay_signature: str = Header(None), db: Session = Depends(get_db)):
    if not razorpay_client or not webhook_secret:
        raise HTTPException(status_code=500, detail="Razorpay credentials not configured")
        
    payload = await request.body()
    try:
        # Signature verification
        razorpay_client.utility.verify_webhook_signature(payload.decode('utf-8'), x_razorpay_signature, webhook_secret)
    except razorpay.errors.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    data = await request.json()
    
    event_type = data.get("event")
    
    # We push ALL events (including payment_link.paid) directly into the graph.
    # The confirm_node will intercept and handle payment_link.paid natively.
    
    # Extract details based on event structure
    amount = 0
    currency = "INR"
    customer_id = ""
    
    if "payload" in data:
        if "payment" in data["payload"]:
            payment = data["payload"]["payment"]["entity"]
            amount = payment.get("amount", 0)
            currency = payment.get("currency", "INR")
            customer_id = payment.get("customer_id", "")
        elif "subscription" in data["payload"]:
            subscription = data["payload"]["subscription"]["entity"]
            amount = subscription.get("charge_at_mrr", 0) # Just an approximation
            customer_id = subscription.get("customer_id", "")
            
    event_id = f"evt_{uuid.uuid4().hex}"
    
    # Persist the raw payload
    event = RiskEvent(
        id=event_id,
        source="webhook",
        event_type=event_type,
        customer_id=customer_id,
        amount=amount,
        currency=currency,
        raw_payload=data,
        created_at=datetime.datetime.now(datetime.timezone.utc),
        split="dev" # webhooks are always dev traffic for now
    )
    
    db.add(event)
    db.commit()
    
    # Wire it to run automatically on new dev-split events
    background_tasks.add_task(process_webhook_case, event_id, db)
    
    return {"status": "ok"}