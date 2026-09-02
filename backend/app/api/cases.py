from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from ..models.database import get_db
from ..models.entities import RiskEvent, Diagnosis, GuardrailResult, Intervention, DeliveryResult, AuditLogEntry, PromiseToPay
from ..nodes.graph import recovery_graph

router = APIRouter()

@router.get("/api/cases/{event_id}")
def get_case(event_id: str, db: Session = Depends(get_db)):
    event = db.query(RiskEvent).filter(RiskEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Case not found")
        
    diagnosis = db.query(Diagnosis).filter(Diagnosis.event_id == event_id).first()
    guardrails = db.query(GuardrailResult).filter(GuardrailResult.event_id == event_id).all()
    intervention = db.query(Intervention).filter(Intervention.event_id == event_id).first()
    deliveries = []
    if intervention:
        deliveries = db.query(DeliveryResult).filter(DeliveryResult.intervention_id == intervention.id).all()
        
    audit_logs = db.query(AuditLogEntry).filter(AuditLogEntry.case_id == event_id).order_by(AuditLogEntry.timestamp).all()
    
    ptp = db.query(PromiseToPay).filter(PromiseToPay.case_id == event_id).first()

    return {
        "event": event,
        "diagnosis": diagnosis,
        "guardrails": guardrails,
        "intervention": intervention,
        "deliveries": deliveries,
        "audit_logs": audit_logs,
        "ptp": ptp
    }

def process_case(event_id: str, db: Session):
    event = db.query(RiskEvent).filter(RiskEvent.id == event_id).first()
    if not event: return
    
    if db.query(AuditLogEntry).filter(AuditLogEntry.case_id == event_id).first():
        return
        
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

@router.post("/api/cases/{event_id}/run")
def trigger_case(event_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    process_case(event_id, db)
    return {"status": "started"}

class ResolvePTPRequest(BaseModel):
    status: str # kept or broken

@router.post("/api/cases/{event_id}/ptp/resolve")
def resolve_ptp(event_id: str, req: ResolvePTPRequest, db: Session = Depends(get_db)):
    if req.status not in ["kept", "broken"]:
        raise HTTPException(status_code=400, detail="Invalid status")
        
    ptp = db.query(PromiseToPay).filter(PromiseToPay.case_id == event_id, PromiseToPay.status == "pending").first()
    if not ptp:
        raise HTTPException(status_code=404, detail="No pending PTP found for case")
        
    ptp.status = req.status
    
    # If kept, this is equivalent to confirmation. Flip the original delivery result to recovered.
    if req.status == "kept":
        from ..models.entities import DeliveryResult, Intervention
        interventions = db.query(Intervention).filter(Intervention.event_id == event_id).all()
        int_ids = [i.id for i in interventions]
        if int_ids:
            delivery = db.query(DeliveryResult).filter(DeliveryResult.intervention_id.in_(int_ids)).first()
            if delivery:
                delivery.status = "recovered"
    
    # Log the human action
    from ..models.entities import AuditLogEntry
    import uuid
    import datetime
    log = AuditLogEntry(
        id=f"log_{uuid.uuid4().hex}",
        case_id=event_id,
        actor="human_agent",
        action="resolve_ptp",
        reasoning=f"Human operator marked PTP as {req.status}",
        timestamp=datetime.datetime.now(datetime.timezone.utc)
    )
    db.add(log)
    db.commit()
    
    return {"status": "success", "ptp_status": req.status}

@router.post("/api/cases/{event_id}/simulate-payment")
def simulate_payment(event_id: str, db: Session = Depends(get_db)):
    from ..models.entities import DeliveryResult, Intervention, AuditLogEntry
    import uuid, datetime
    
    interventions = db.query(Intervention).filter(Intervention.event_id == event_id).all()
    int_ids = [i.id for i in interventions]
    if not int_ids:
        raise HTTPException(status_code=404, detail="No interventions found")
        
    delivery = db.query(DeliveryResult).filter(DeliveryResult.intervention_id.in_(int_ids)).first()
    if not delivery:
        raise HTTPException(status_code=404, detail="No delivery result found")
        
    delivery.status = "simulated_recovered"
    
    # Add audit log
    log = AuditLogEntry(
        id=f"log_{uuid.uuid4().hex}",
        case_id=event_id,
        actor="human_agent",
        action="simulate_payment",
        reasoning="Simulated confirmation (test-mode has no auto-payment)",
        timestamp=datetime.datetime.now(datetime.timezone.utc)
    )
    db.add(log)
    db.commit()
    return {"status": "success", "message": "Simulated payment successfully"}

@router.post("/api/cases/{event_id}/simulate-ptp")
def simulate_ptp(event_id: str, db: Session = Depends(get_db)):
    from ..models.entities import DeliveryResult, Intervention, AuditLogEntry, PromiseToPay
    import uuid, datetime
    
    interventions = db.query(Intervention).filter(Intervention.event_id == event_id).all()
    int_ids = [i.id for i in interventions]
    if not int_ids:
        raise HTTPException(status_code=404, detail="No interventions found")
        
    delivery = db.query(DeliveryResult).filter(DeliveryResult.intervention_id.in_(int_ids)).order_by(DeliveryResult.id.desc()).first()
    if not delivery:
        raise HTTPException(status_code=404, detail="No delivery result found")
        
    delivery.status = "responded_ptp_simulated"
    
    promised_date = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=3)).date()
    db_ptp = PromiseToPay(
        id=f"ptp_{uuid.uuid4().hex}",
        case_id=event_id,
        promised_amount=2500000,
        promised_date=promised_date,
        status="pending",
        detected_via="simulated_human_input"
    )
    db.add(db_ptp)
    
    # Add audit log
    log = AuditLogEntry(
        id=f"log_{uuid.uuid4().hex}",
        case_id=event_id,
        actor="human_agent",
        action="simulate_ptp",
        reasoning="simulated customer response, no real WhatsApp integration",
        timestamp=datetime.datetime.now(datetime.timezone.utc)
    )
    db.add(log)
    db.commit()
    return {"status": "success", "message": "Simulated PTP successfully"}
