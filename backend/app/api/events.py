from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..models.database import get_db
from ..models.entities import RiskEvent, Diagnosis, GuardrailResult, Intervention, DeliveryResult, PromiseToPay, AuditLogEntry, BatchRunResult
from pydantic import BaseModel
import datetime

router = APIRouter()

@router.get("/api/events")
def get_events(split: str = "dev", db: Session = Depends(get_db)):
    if split == "holdout":
        return {"error": "Holdout split cannot be read from this endpoint"}
    
    events = db.query(RiskEvent).filter(RiskEvent.split == split).all()
    
    event_ids = [evt.id for evt in events]
    
    # Batch lookups
    diagnoses = {d.event_id: d for d in db.query(Diagnosis).filter(Diagnosis.event_id.in_(event_ids)).all()}
    guardrails = {g.event_id: g for g in db.query(GuardrailResult).filter(GuardrailResult.event_id.in_(event_ids)).all()}
    interventions = {i.event_id: i for i in db.query(Intervention).filter(Intervention.event_id.in_(event_ids)).all()}
    
    intervention_ids = [i.id for i in interventions.values()]
    deliveries = {d.intervention_id: d for d in db.query(DeliveryResult).filter(DeliveryResult.intervention_id.in_(intervention_ids)).all()}
    
    # Audit log (latest per event)
    # Since SQLite doesn't support advanced DISTINCT ON, we'll fetch them ordered and take the first seen per event
    all_audits = db.query(AuditLogEntry).filter(AuditLogEntry.case_id.in_(event_ids)).order_by(AuditLogEntry.timestamp.desc()).all()
    latest_audits = {}
    for a in all_audits:
        if a.case_id not in latest_audits:
            latest_audits[a.case_id] = a
            
    ptps = {p.case_id: p for p in db.query(PromiseToPay).filter(PromiseToPay.case_id.in_(event_ids)).all()}
    
    result = []
    for evt in events:
        status = "detected"
        channel = "-"
        reason = "-"
        
        diagnosis = diagnoses.get(evt.id)
        if diagnosis:
            cat = diagnosis.root_cause_category or 'unknown'
            reason = f"Diagnosed: {cat.replace('_', ' ').title()}"
        
        # Check guardrails
        guardrail = guardrails.get(evt.id)
        if guardrail:
            if not guardrail.passed:
                status = "blocked"
                reason = f"Guardrail Blocked: {guardrail.reason}"
            else:
                intervention = interventions.get(evt.id)
                if intervention:
                    channel = intervention.channel
                    delivery = deliveries.get(intervention.id)
                    if delivery:
                        if delivery.status == "delivered":
                            status = "in_progress"
                            reason = f"Intervention sent via {intervention.channel} ({intervention.tone})"
                        elif delivery.status == "failed":
                            status = "exhausted"
                            reason = "Delivery failed / User opted out"
                        elif delivery.status == "responded":
                            status = "recovered"
                            reason = "Customer responded / PTP committed"
                            
        # Find latest audit log reasoning if available
        last_audit = latest_audits.get(evt.id)
        if last_audit and last_audit.reasoning:
            reason = last_audit.reasoning
                        
        ptp = ptps.get(evt.id)
                        
        event_dict = {
            "id": evt.id,
            "source": evt.source,
            "event_type": evt.event_type,
            "customer_id": evt.customer_id,
            "amount": evt.amount,
            "currency": evt.currency,
            "created_at": evt.created_at,
            "status": status,
            "channel": channel,
            "reason": reason,
            "diagnosis": {
                "risk_quadrant": diagnosis.risk_quadrant,
                "confidence": diagnosis.confidence,
                "root_cause": diagnosis.root_cause_category
            } if diagnosis else None,
            "ptp": {
                "amount": ptp.promised_amount,
                "date": str(ptp.promised_date),
                "status": ptp.status
            } if ptp else None
        }
        result.append(event_dict)
        
    return result

@router.get("/api/dashboard/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    events = db.query(RiskEvent).filter(RiskEvent.split == "dev").all()
    total_cases = len(events)
    total_at_risk = sum(e.amount for e in events)
    
    # Calculate recovery metrics
    deliveries = db.query(DeliveryResult).all()
    interventions = db.query(Intervention).all()
    blocked_guardrails = db.query(GuardrailResult).filter(GuardrailResult.passed == False).count()
    
    recovered_events = set()
    in_progress_events = set()
    exhausted_events = set()
    
    int_map = {i.id: i.event_id for i in interventions}
    for d in deliveries:
        evt_id = int_map.get(d.intervention_id)
        if evt_id:
            if d.status == "responded":
                recovered_events.add(evt_id)
            elif d.status == "delivered":
                in_progress_events.add(evt_id)
            elif d.status == "failed":
                exhausted_events.add(evt_id)
                
    recovered_amount = sum(e.amount for e in events if e.id in recovered_events)
    active_cases = len([e for e in events if e.id in in_progress_events or (e.id not in recovered_events and e.id not in exhausted_events)])
    
    recovery_rate = (len(recovered_events) / total_cases * 100) if total_cases > 0 else 0.0
    
    # Risk quadrant breakdown
    diagnoses = db.query(Diagnosis).all()
    quadrant_counts = {}
    root_cause_counts = {}
    for diag in diagnoses:
        q = diag.risk_quadrant or "unassigned"
        quadrant_counts[q] = quadrant_counts.get(q, 0) + 1
        rc = diag.root_cause_category or "unknown"
        root_cause_counts[rc] = root_cause_counts.get(rc, 0) + 1
        
    # Batch run trends
    batch_runs = db.query(BatchRunResult).order_by(BatchRunResult.started_at.asc()).all()
    trend_data = [
        {
            "id": run.id,
            "date": run.started_at.strftime("%b %d, %H:%M") if run.started_at else "-",
            "recovery_rate": round(run.recovery_rate or 0, 1),
            "amount_recovered": run.amount_recovered or 0,
            "total_cases": run.total_cases or 0
        }
        for run in batch_runs
    ]
    
    return {
        "total_at_risk": total_at_risk,
        "recovered_amount": recovered_amount,
        "recovery_rate": round(recovery_rate, 1),
        "total_cases": total_cases,
        "active_cases": active_cases,
        "guardrail_blocks": blocked_guardrails,
        "quadrant_distribution": quadrant_counts,
        "root_cause_distribution": root_cause_counts,
        "batch_trends": trend_data
    }
