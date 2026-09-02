import logging
logger = logging.getLogger(__name__)
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from ..models.database import get_db
from ..models.entities import RiskEvent, BatchRunResult, Diagnosis, GuardrailResult, Intervention, DeliveryResult, PromiseToPay, AuditLogEntry
from ..nodes.graph import recovery_graph
import uuid
import datetime

router = APIRouter()

def execute_batch_run(run_id: str):
    from ..models.database import SessionLocal
    db = SessionLocal()
    try:
        run = db.query(BatchRunResult).filter(BatchRunResult.id == run_id).first()
        if not run: return
    
        # FETCH STRICTLY FROM HOLDOUT SPLIT
        holdout_events = db.query(RiskEvent).filter(RiskEvent.split == "holdout").all()
    
        total_cases = len(holdout_events)
        if total_cases == 0:
            run.status = "completed"
            db.commit()
            return

        # CLEANUP: Ensure zero-shot purity for multiple batch runs
        # Clear any previous generated state for holdout cases to prevent leakage
        holdout_ids = [e.id for e in holdout_events]
        db.query(Diagnosis).filter(Diagnosis.event_id.in_(holdout_ids)).delete(synchronize_session=False)
        db.query(GuardrailResult).filter(GuardrailResult.event_id.in_(holdout_ids)).delete(synchronize_session=False)
        db.query(Intervention).filter(Intervention.event_id.in_(holdout_ids)).delete(synchronize_session=False)
        db.query(DeliveryResult).filter(DeliveryResult.intervention_id.in_(
            db.query(Intervention.id).filter(Intervention.event_id.in_(holdout_ids))
        )).delete(synchronize_session=False)
        db.query(PromiseToPay).filter(PromiseToPay.case_id.in_(holdout_ids)).delete(synchronize_session=False)
        db.query(AuditLogEntry).filter(AuditLogEntry.case_id.in_(holdout_ids)).delete(synchronize_session=False)
        db.commit()

        amount_at_risk = sum(e.amount for e in holdout_events)
    
        cases_processed = 0
        cases_recovered = 0
        amount_recovered = 0
        escalated_count = 0
        false_escalation_count = 0
        exceptions = []
        recovered_cases = []

        logger.info(f"Batch run {run_id} started: {total_cases} cases in holdout split.")

        for event in holdout_events:
            # Build strict execution state
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
        
            # Add pacing to avoid LLM rate limits (Groq 429s)
            import time
            time.sleep(3.0)
            
            # Execute the full orchestration graph
            try:
                final_state = recovery_graph.invoke(state)
            except Exception as e:
                exceptions.append({
                    "case_id": event.id,
                    "reason": f"Execution Error: {str(e)}",
                    "rule": "System Exception"
                })
                cases_processed += 1
                run.cases_processed = cases_processed
                db.commit()
                continue
        
            cases_processed += 1
        
            # Analyze outcome
            deliv = final_state.get("delivery_result")
            gr = final_state.get("guardrail_result")
            diag = final_state.get("diagnosis")
            inter = final_state.get("intervention")
        
            # Exceptions (Blocked by guardrails or API fail)
            if gr and not gr.get("passed", True):
                exceptions.append({
                    "case_id": event.id,
                    "reason": gr.get("reason"),
                    "rule": gr.get("rule_name")
                })
            
            # Actioned traces
            if deliv and deliv.get("status") in ["action_taken", "delivered", "responded", "recovered", "simulated_recovered", "action_failed_simulated", "responded_ptp_simulated"]:
                # Note: "action_failed_simulated" is tracked as a fallback action, but not a recovery
                pass
            
            # Count actual recoveries
            if deliv and deliv.get("status") in ["recovered", "simulated_recovered", "responded_ptp_simulated", "responded"]:
                cases_recovered += 1
                amount_recovered += event.amount
            
            # Always append to recovered_cases list for actioned traces (it's actually 'actioned_list' conceptually)
            if deliv and deliv.get("status") in ["action_taken", "delivered", "responded", "recovered", "simulated_recovered", "action_failed_simulated", "responded_ptp_simulated"]:
                recovered_cases.append({
                    "case_id": event.id,
                    "amount": event.amount,
                    "channel": deliv.get("channel"),
                    "short_url": deliv.get("response_payload", {}).get("short_url"),
                    "status": deliv.get("status")
                })
            
            # Escalations
            if inter and inter.get("intervention_type") == "escalate":
                escalated_count += 1
                # False escalation: if the root cause was actually technical or forgetful, it shouldn't have been escalated
                if diag and diag.get("risk_quadrant") in ["forgetful", "technical"]:
                    false_escalation_count += 1
                
            # Update progress in DB every 5 cases
            if cases_processed % 5 == 0:
                run.cases_processed = cases_processed
                db.commit()
            
            logger.info(f"Batch progress: case {cases_processed}/{total_cases} processed (case_id: {event.id})")

        logger.info(f"Batch run {run_id} completed. {cases_recovered} recovered, {len(exceptions)} exceptions.")
        run.total_cases = total_cases
        run.recovery_rate = (cases_recovered / total_cases) * 100 if total_cases > 0 else 0
        run.amount_at_risk = amount_at_risk
        run.amount_recovered = amount_recovered
        run.false_escalation_rate = (false_escalation_count / escalated_count) * 100 if escalated_count > 0 else 0
        run.exception_list = exceptions
        run.recovered_list = recovered_cases
        run.status = "completed"
        run.completed_at = datetime.datetime.now(datetime.timezone.utc)
    
        db.commit()
    finally:
        db.close()

@router.post("/api/batch-run")
def trigger_batch_run(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # Verify holdout split actually has cases
    holdout_count = db.query(RiskEvent).filter(RiskEvent.split == "holdout").count()
    if holdout_count == 0:
        raise HTTPException(status_code=400, detail="No holdout cases found in database.")
        
    run_id = f"run_{uuid.uuid4().hex}"
    
    run = BatchRunResult(
        id=run_id,
        status="running",
        total_cases=holdout_count,
        cases_processed=0,
        recovery_rate=0.0,
        amount_at_risk=0,
        amount_recovered=0,
        false_escalation_rate=0.0,
        exception_list=[],
        recovered_list=[],
        started_at=datetime.datetime.now(datetime.timezone.utc)
    )
    db.add(run)
    db.commit()
    
    background_tasks.add_task(execute_batch_run, run_id)
    
    return {"run_id": run_id, "status": "running"}

def _derive_batch_view(run, db):
    # Derived view: merges static audit snapshot with live DeliveryResult simulation state
    # This guarantees the underlying BatchRunResult SQLite row is NEVER mutated!
    from ..models.entities import DeliveryResult, Intervention
    
    run_dict = {
        "id": run.id,
        "status": run.status,
        "total_cases": run.total_cases,
        "cases_processed": run.cases_processed,
        "recovery_rate": run.recovery_rate,
        "amount_at_risk": run.amount_at_risk,
        "amount_recovered": run.amount_recovered,
        "false_escalation_rate": run.false_escalation_rate,
        "exception_list": run.exception_list,
        "started_at": run.started_at,
        "completed_at": run.completed_at
    }
    
    live_recovered_list = []
    if run.recovered_list:
        for case_meta in run.recovered_list:
            case_view = dict(case_meta)
            # Fetch live delivery status dynamically without modifying run.recovered_list
            interventions = db.query(Intervention).filter(Intervention.event_id == case_meta["case_id"]).all()
            int_ids = [i.id for i in interventions]
            if int_ids:
                live_delivery = db.query(DeliveryResult).filter(DeliveryResult.intervention_id.in_(int_ids)).first()
                if live_delivery:
                    case_view["status"] = live_delivery.status
            live_recovered_list.append(case_view)
            
    run_dict["recovered_list"] = live_recovered_list
    return run_dict

@router.get("/api/batch-results")
def list_batch_results(db: Session = Depends(get_db)):
    runs = db.query(BatchRunResult).order_by(BatchRunResult.started_at.desc()).all()
    return [_derive_batch_view(r, db) for r in runs]

@router.get("/api/batch-results/{run_id}")
def get_batch_result(run_id: str, db: Session = Depends(get_db)):
    run = db.query(BatchRunResult).filter(BatchRunResult.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Batch run not found")
    return _derive_batch_view(run, db)

@router.get("/api/token-usage")
def get_token_usage(db: Session = Depends(get_db)):
    """Aggregate token usage and cost across all diagnoses."""
    from sqlalchemy import func
    result = db.query(
        func.count(Diagnosis.id).label("total_diagnoses"),
        func.sum(Diagnosis.tokens_used).label("total_tokens"),
        func.sum(Diagnosis.token_cost).label("total_cost_usd"),
    ).first()
    
    from ..config import LIFETIME_TOKEN_BUDGET_USD
    total_cost = result.total_cost_usd or 0.0
    
    return {
        "total_diagnoses": result.total_diagnoses or 0,
        "total_tokens": result.total_tokens or 0,
        "total_cost_usd": round(total_cost, 6),
        "lifetime_budget_usd": LIFETIME_TOKEN_BUDGET_USD,
        "budget_remaining_usd": round(LIFETIME_TOKEN_BUDGET_USD - total_cost, 6),
        "budget_utilization_pct": round((total_cost / LIFETIME_TOKEN_BUDGET_USD) * 100, 2) if LIFETIME_TOKEN_BUDGET_USD > 0 else 0,
    }
