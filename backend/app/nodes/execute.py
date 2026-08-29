import os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "../../../.env"))

import uuid
import razorpay
import datetime
from .state import RecoveryState
from ..adapters.text import TextChannelAdapter
from ..adapters.voice import VoiceChannelAdapter
from ..models.database import SessionLocal
from ..models.entities import DeliveryResult, PromiseToPay

def get_razorpay_client():
    key_id = os.environ.get("RAZORPAY_KEY_ID")
    key_secret = os.environ.get("RAZORPAY_KEY_SECRET")
    if not key_id or not key_secret:
        raise ValueError("Razorpay credentials not found in environment variables.")
    print(f"Diagnostics: Razorpay credentials loaded (Key ID: {key_id})")
    return razorpay.Client(auth=(key_id, key_secret))

text_adapter = TextChannelAdapter()
voice_adapter = VoiceChannelAdapter()

def execute_node(state: RecoveryState) -> RecoveryState:
    event = state["event"]
    intervention = state.get("intervention")
    
    # ---------------------------------------------------------
    # TRUST BOUNDARY: Enforced, not assumed
    # ---------------------------------------------------------
    gr = state.get("guardrail_result", {})
    assert gr.get("passed") is True, f"TRUST BOUNDARY VIOLATION: execute_node invoked but guardrails did not pass (Rule: {gr.get('rule_name')})."
    
    if not intervention:
        return state
        
    payment_link = None
    pl_id = None
    
    # If the intervention is a retry, hit Razorpay API to generate a payment link
    if intervention["intervention_type"] in ["retry_now", "retry_scheduled"]:
        try:
            rzp_client = get_razorpay_client()
            link_data = {
                "amount": event.get("amount", 100),
                "currency": event.get("currency", "INR"),
                "description": f"Recovery for {event.get('id')}",
                "customer": {
                    "name": "Test Customer",
                    "contact": "9876543210",
                    "email": "test@example.com"
                },
                "notify": {"sms": False, "email": False},
                "reminder_enable": False,
            }
            rzp_response = rzp_client.payment_link.create(link_data)
            payment_link = rzp_response.get("short_url")
            pl_id = rzp_response.get("id")
            
            # Safe Diagnostics
            print(f"Diagnostics: Razorpay API success. Payment Link ID: {pl_id} | Short URL: {payment_link}")
            
        except Exception as e:
            # Loud failure handling
            error_msg = f"Razorpay API Error: {str(e)}"
            state["audit_log"].append({
                "case_id": event["id"],
                "actor": "system",
                "action": "execute",
                "reasoning": error_msg,
                "timestamp": "now"
            })
            # Do not continue and send a broken message without a link!
            raise RuntimeError(error_msg)
            
    contact_info = {"opted_out": False}
    db = SessionLocal()
    
    if intervention["channel"] == "text":
        delivery_res = text_adapter.send(intervention, contact_info, payment_link, pl_id)
    elif intervention["channel"] == "voice":
        delivery_res = voice_adapter.send(intervention, contact_info, event, db)
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
        status=delivery_res["status"],
        response_payload=delivery_res["response_payload"]
    )
    db.add(db_del)
    
    # Check for PTP detection in response
    if "ptp" in delivery_res["response_payload"]:
        ptp_data = delivery_res["response_payload"]["ptp"]
        ptp_date_str = ptp_data.get("date")
        ptp_date = datetime.datetime.strptime(ptp_date_str, "%Y-%m-%d").date() if ptp_date_str else datetime.date.today()
        
        db_ptp = PromiseToPay(
            id=f"ptp_{uuid.uuid4().hex}",
            case_id=event["id"],
            promised_amount=ptp_data.get("amount", 0),
            promised_date=ptp_date,
            status="pending",
            detected_via=intervention["channel"]
        )
        db.add(db_ptp)
        
        state["audit_log"].append({
            "case_id": event["id"],
            "actor": "agent",
            "action": "ptp_detected",
            "reasoning": f"Extracted Promise to Pay for {ptp_data.get('amount')} by {ptp_date_str}",
            "timestamp": "now"
        })
    
    db.commit()
    db.close()
    
    state["delivery_result"] = {
        "id": del_id,
        "intervention_id": intervention["id"],
        "channel": delivery_res["channel"],
        "status": delivery_res["status"],
        "response_payload": delivery_res["response_payload"]
    }
    
    state["audit_log"].append({
        "case_id": event["id"],
        "actor": "system",
        "action": "execute",
        "reasoning": f"Delivered via {delivery_res['channel']} with status {delivery_res['status']}",
        "timestamp": "now"
    })
    
    return state
