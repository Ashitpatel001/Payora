import os
import uuid
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "../../../.env"))
from .state import RecoveryState
from ..models.database import SessionLocal
from ..models.entities import Diagnosis
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

# DIAGNOSIS_PROMPT remains the same

DIAGNOSIS_PROMPT = """You are the Razorpay AI Revenue Recovery Diagnosis Engine.
Your task is to analyze a failed payment or at-risk event and determine the root cause and risk quadrant.

INPUT:
Event Data:
{event_data}

LOGIC:
1. Determine the root_cause_category based on event type and payload details. (e.g., 'insufficient_funds', 'bank_timeout', 'expired_mandate', 'risk_decline', 'invoice_overdue')
2. Determine the risk_quadrant based on these definitions:
   - technical: Transient errors, bank timeouts, API failures.
   - hardship: Customer lacks funds or requested delay.
   - serial_non_payer: History of unpaid invoices or repeated card declines.
   - high_value: Large invoice or critical subscription account (e.g. amount > 10000 INR).
3. Assign a confidence score (0.0 to 1.0).

OUTPUT:
Return a JSON object with these exactly:
- root_cause_category (string)
- confidence (float)
- risk_quadrant (string)
- reasoning (string)
"""

def diagnose_node(state: RecoveryState) -> RecoveryState:
    event = state["event"]
    event_type = event.get("event_type", "")
    amount = event.get("amount", 0)
    
    # Rule-based first pass
    root_cause = "unknown"
    quadrant = "technical"
    confidence = 1.0
    reasoning = "Rule-based: Default fallback."
    
    if event_type == "payment.failed":
        # Simplified rule for missing LLM
        root_cause = "bank_timeout"
        quadrant = "technical"
        reasoning = "Rule-based: Standard payment failure mapped to technical retry."
    elif event_type == "subscription.halted":
        root_cause = "expired_mandate"
        quadrant = "technical"
        reasoning = "Rule-based: Subscription halted usually indicates mandate failure."
    elif event_type == "invoice.overdue":
        root_cause = "invoice_overdue"
        quadrant = "serial_non_payer"
        reasoning = "Rule-based: Overdue B2B invoice."
        
    if amount > 1000000: # 10000 INR in paise
        quadrant = "high_value"
        reasoning += " Upgraded to high_value due to amount."

    # LLM Fallback (if real LLM key is provided)
    if "synthetic" not in event.get("source", ""):
        try:
            from ..services.llm_client import get_llm
            llm = get_llm(temperature=0.0)
            prompt = ChatPromptTemplate.from_template(DIAGNOSIS_PROMPT)
            chain = prompt | llm | JsonOutputParser()
            result = chain.invoke({"event_data": str(event)})
            root_cause = result.get("root_cause_category", root_cause)
            quadrant = result.get("risk_quadrant", quadrant)
            confidence = result.get("confidence", confidence)
            reasoning = result.get("reasoning", reasoning)
        except Exception as e:
            print("LLM fallback failed, using rules:", e)

    diag_id = f"diag_{uuid.uuid4().hex}"
    diag_record = {
        "id": diag_id,
        "event_id": event["id"],
        "root_cause_category": root_cause,
        "confidence": confidence,
        "risk_quadrant": quadrant,
        "reasoning": reasoning
    }
    
    # Persist
    db = SessionLocal()
    db_diag = Diagnosis(
        id=diag_id,
        event_id=event["id"],
        root_cause_category=root_cause,
        confidence=confidence,
        risk_quadrant=quadrant
    )
    db.add(db_diag)
    db.commit()
    db.close()
    
    state["diagnosis"] = diag_record
    
    # also add to audit log (we'll implement log node properly later, but good to have)
    state["audit_log"].append({
        "case_id": event["id"],
        "actor": "agent",
        "action": "diagnose",
        "reasoning": reasoning,
        "timestamp": "now"
    })
    
    return state
