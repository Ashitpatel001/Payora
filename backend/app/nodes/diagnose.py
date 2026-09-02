import logging
logger = logging.getLogger(__name__)
import os
import uuid
import datetime
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
1. Determine the root_cause_category. You MUST choose EXACTLY one of these strings (do not invent others):
   - "insufficient_funds"
   - "bank_timeout"
   - "expired_mandate"
   - "risk_decline"
   - "invoice_overdue"
   - "strategic_defaulter"
   - "unknown"
2. Determine the risk_quadrant based on these definitions. You MUST choose EXACTLY one of these strings:
   - "technical": Transient errors, bank timeouts, API failures.
   - "hardship": Customer lacks funds or requested delay.
   - "serial_non_payer": History of unpaid invoices or repeated card declines.
   - "high_value": Large invoice or critical subscription account (e.g. amount > 25000 INR).
3. Assign a confidence score (0.0 to 1.0).

OUTPUT:
Return a JSON object with these exactly:
- root_cause_category (string, strictly from the list above)
- confidence (float)
- risk_quadrant (string, strictly from the list above)
- reasoning (string)
"""

def diagnose_node(state: RecoveryState) -> RecoveryState:
    event = state["event"]
    event_type = event.get("event_type", "")
    amount = event.get("amount", 0)
    
    logger.info("diagnose_node started", extra={"event_id": event["id"], "amount": amount, "event_type": event_type})
    
    # Rule-based first pass
    root_cause = "unknown"
    quadrant = "technical"
    confidence = 1.0
    reasoning = "Rule-based: Default fallback."
    tokens_used = 0
    token_cost = 0.0
    
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
        
    from ..config import HIGH_VALUE_THRESHOLD_PAISE
    if amount > HIGH_VALUE_THRESHOLD_PAISE:
        quadrant = "high_value"
        reasoning += " Upgraded to high_value due to amount."

    # AI Diagnosis (No shortcuts!)
    try:
        # Enforce Token Budget Before Calling LLM
        from sqlalchemy import func
        from ..config import LIFETIME_TOKEN_BUDGET_USD
        if LIFETIME_TOKEN_BUDGET_USD > 0:
            db_check = SessionLocal()
            try:
                total_cost = db_check.query(func.sum(Diagnosis.token_cost)).scalar() or 0.0
                if total_cost >= LIFETIME_TOKEN_BUDGET_USD:
                    raise Exception(f"Lifetime token budget exceeded (${total_cost:.2f} / ${LIFETIME_TOKEN_BUDGET_USD:.2f}).")
            finally:
                db_check.close()
                
        from ..services.llm_client import get_llm
        import time
        llm = get_llm(temperature=0.0)
        prompt = ChatPromptTemplate.from_template(DIAGNOSIS_PROMPT)
        
        # We invoke the LLM directly, getting the raw AIMessage
        import json
        safe_event = {k: v for k, v in event.items() if k != "raw_payload"}
        prompt_val = prompt.invoke({"event_data": json.dumps(safe_event)})
        import time
        from failsafe import Failsafe, CircuitBreaker, RetryPolicy
        from failsafe import CircuitOpen
        
        # Singleton circuit breaker for LLM
        if not hasattr(diagnose_node, "llm_circuit"):
            diagnose_node.llm_circuit = CircuitBreaker(maximum_failures=10)
            
        async def robust_llm_call():
            import asyncio
            max_retries = 3
            base_delay = 5.0
            
            for attempt in range(max_retries + 1):
                try:
                    return await llm.ainvoke(prompt_val)
                except Exception as e:
                    if attempt == max_retries:
                        raise e  # Final failure propagates out to circuit breaker
                        
                    # Check if it's a rate limit error (Groq uses 429)
                    if "429" in str(e) or "RateLimit" in type(e).__name__:
                        delay = base_delay * (2 ** attempt)
                        # Try to extract retry-after if it's an httpx or Groq exception
                        try:
                            if hasattr(e, 'response') and hasattr(e.response, 'headers'):
                                retry_after = e.response.headers.get('retry-after')
                                if retry_after:
                                    delay = float(retry_after)
                        except Exception:
                            pass
                            
                        logger.warning(f"LLM Rate Limited (attempt {attempt+1}/{max_retries}). Backing off for {delay}s...")
                        await asyncio.sleep(delay)
                    else:
                        raise e # If it's a different exception (e.g. auth), don't retry here
        
        try:
            # Wrap the ENTIRE retry-inclusive call as a single unit passed to the breaker.
            # No RetryPolicy here, so the circuit breaker only sees one final failure per case.
            failsafe = Failsafe(circuit_breaker=diagnose_node.llm_circuit)
            import asyncio
            ai_msg = asyncio.run(failsafe.run(robust_llm_call))
        except CircuitOpen:
            raise Exception("LLM Circuit Breaker is OPEN. Fast failing to rules.")
        except Exception as e:
            raise e
        
        logger.info("\n--- RAW LLM RESPONSE ---")
        try:
            logger.info(ai_msg.content.encode('ascii', 'replace').decode('ascii'))
        except Exception:
            pass
        logger.info("------------------------\n")
        
        # Parse and strictly validate LLM output against enum constraints
        from ..schemas import DiagnosisResult
        
        raw_result = JsonOutputParser().invoke(ai_msg)
        validated = DiagnosisResult(**raw_result)
        
        root_cause = validated.root_cause_category.value
        quadrant = validated.risk_quadrant.value
        confidence = validated.confidence
        reasoning = validated.reasoning
        
        # Track Tokens with real per-model pricing
        if hasattr(ai_msg, "response_metadata") and "token_usage" in ai_msg.response_metadata:
            usage = ai_msg.response_metadata["token_usage"]
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            tokens_used = usage.get("total_tokens", prompt_tokens + completion_tokens)
            
            # Look up model-specific pricing
            from ..config import GROQ_MODEL_PRICING
            model_name = ai_msg.response_metadata.get("model_name", "default")
            pricing = GROQ_MODEL_PRICING.get(model_name, GROQ_MODEL_PRICING["default"])
            
            token_cost = (
                (prompt_tokens / 1_000_000) * pricing["input_cost_per_1m"]
                + (completion_tokens / 1_000_000) * pricing["output_cost_per_1m"]
            )
            
            logger.info(
                "Token usage: prompt=%d completion=%d total=%d cost=$%.6f model=%s",
                prompt_tokens, completion_tokens, tokens_used, token_cost, model_name
            )
    except Exception as e:
        logger.error(f"LLM failed, using rules: {type(e)} {e}")

    diag_id = f"diag_{uuid.uuid4().hex}"
    diag_record = {
        "id": diag_id,
        "event_id": event["id"],
        "root_cause_category": root_cause,
        "confidence": confidence,
        "risk_quadrant": quadrant,
        "reasoning": reasoning,
        "tokens_used": tokens_used,
        "token_cost": token_cost
    }
    
    # Persist
    db = SessionLocal()
    try:
        db_diag = Diagnosis(
            id=diag_id,
            event_id=event["id"],
            root_cause_category=root_cause,
            confidence=confidence,
            risk_quadrant=quadrant,
            reasoning=reasoning,
            tokens_used=tokens_used,
            token_cost=token_cost
        )
        db.add(db_diag)
        db.commit()
    finally:
        db.close()
    
    state["diagnosis"] = diag_record
    
    # also add to audit log (we'll implement log node properly later, but good to have)
    state["audit_log"].append({
        "case_id": event["id"],
        "actor": "agent",
        "action": "diagnose",
        "reasoning": reasoning,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    })
    
    logger.info("diagnose_node completed", extra={"event_id": event["id"], "root_cause": root_cause, "quadrant": quadrant, "confidence": confidence, "tokens_used": tokens_used})
    
    return state
