import logging
logger = logging.getLogger(__name__)
import os
import uuid
import datetime
from .state import RecoveryState
from ..adapters.text import TextChannelAdapter
from ..adapters.voice import VoiceChannelAdapter
from ..models.database import SessionLocal
from ..models.entities import DeliveryResult, PromiseToPay

def get_razorpay_client():
    key_id = os.environ.get("RAZORPAY_KEY_ID")
    key_secret = os.environ.get("RAZORPAY_KEY_SECRET")
    
    # We gracefully mock missing real credentials since we can simulate
    if not key_id or not key_secret:
        return None
        
    import razorpay
    return razorpay.Client(auth=(key_id, key_secret))

def execute_node(state: RecoveryState) -> RecoveryState:
    event = state["event"]
    intervention = state["intervention"]
    
    logger.info("execute_node started", extra={"event_id": event["id"], "channel": intervention.get("channel") if intervention else None})
    
    if not intervention:
        return state

    rzp_client = get_razorpay_client()
    payment_link = None
    pl_id = None
    fallback_used = None
    
    if intervention.get("action") == "send_payment_link":
        try:
            if not rzp_client:
                raise RuntimeError("Razorpay credentials not provided.")
                
            link_data = {
                "amount": event.get("amount", 0),
                "currency": event.get("currency", "INR"),
                "description": "Payment Recovery",
                "customer": {
                    "name": "Valued Customer",
                    "email": "customer@example.com"
                },
                "notify": {"sms": False, "email": False},
                "reminder_enable": False
            }
            from failsafe import Failsafe, CircuitBreaker, RetryPolicy, CircuitOpen
            if not hasattr(execute_node, "rzp_circuit"):
                execute_node.rzp_circuit = CircuitBreaker(maximum_failures=5)
                
            async def robust_create_link():
                import asyncio
                for attempt in range(2): # 1 initial + 1 retry
                    try:
                        return await asyncio.to_thread(rzp_client.payment_link.create, link_data)
                    except Exception as e:
                        if attempt == 1:
                            raise e
                        logger.warning(f"Razorpay API failed (attempt {attempt+1}/2). Retrying in 2s...")
                        await asyncio.sleep(2.0)

            # Wrap the ENTIRE retry-inclusive call as a single unit passed to the breaker.
            rzp_failsafe = Failsafe(circuit_breaker=execute_node.rzp_circuit)
            import asyncio
            res = asyncio.run(rzp_failsafe.run(robust_create_link))
            pl_id = res["id"]
            payment_link = res["short_url"]
            logger.info(f"Diagnostics: Razorpay API success. Payment Link ID: {pl_id} | Short URL: {payment_link}")
            
        except CircuitOpen:
            error_msg = "Razorpay API call failed: Circuit Breaker is OPEN, demo fallback link generated"
            logger.error(error_msg)
            pl_id = f"pl_sim_{uuid.uuid4().hex[:8]}"
            payment_link = f"https://rzp.io/i/{pl_id}"
            fallback_used = error_msg
        except Exception as e:
            real_e = e.__cause__ if getattr(e, '__cause__', None) else e
            error_msg = f"Razorpay API call failed: {str(real_e)}, demo fallback link generated"
            logger.info(error_msg)
            pl_id = f"pl_sim_{uuid.uuid4().hex[:8]}"
            payment_link = f"https://rzp.io/i/{pl_id}"
            fallback_used = error_msg
            
    contact_info = {"opted_out": False}
    db = SessionLocal()
    try:
        if intervention["channel"] == "text":
            adapter = TextChannelAdapter()
            delivery_res = adapter.send(intervention, contact_info, payment_link_url=payment_link, payment_link_id=pl_id)
        elif intervention["channel"] == "voice":
            adapter = VoiceChannelAdapter()
            delivery_res = adapter.send(intervention, contact_info, event=event, db=db)
        else:
            delivery_res = {
                "channel": intervention["channel"],
                "status": "failed",
                "response_payload": {"error": "Channel not supported yet"}
            }
            
        del_id = f"del_{uuid.uuid4().hex}"
        
        db_del = DeliveryResult(
            id=del_id,
            intervention_id=intervention["id"],
            channel=delivery_res["channel"],
            status="action_failed_simulated" if fallback_used else "delivered",
            payment_link_id=pl_id,
            response_payload=delivery_res["response_payload"]
        )
        db.add(db_del)
        status_val = db_del.status
        db.commit()
    finally:
        db.close()
    
    state["delivery_result"] = {
        "id": del_id,
        "intervention_id": intervention["id"],
        "channel": delivery_res["channel"],
        "status": status_val
    }
    
    state["audit_log"].append({
        "case_id": event["id"],
        "actor": "system",
        "action": "execute",
        "reasoning": fallback_used if fallback_used else "Executed automated intervention",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    })
    
    return state
