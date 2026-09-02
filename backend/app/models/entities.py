from sqlalchemy import Column, String, Integer, DateTime, Boolean, Date, Float, JSON, ForeignKey
from .database import Base
from datetime import datetime, timezone

def utc_now():
    return datetime.now(timezone.utc)

class RiskEvent(Base):
    __tablename__ = "risk_events"
    id = Column(String(255), primary_key=True)
    source = Column(String(255)) # webhook, synthetic_receivable, synthetic_checkout
    event_type = Column(String(255))
    customer_id = Column(String(255), index=True)
    amount = Column(Integer) # paise
    currency = Column(String(10))
    raw_payload = Column(JSON)
    created_at = Column(DateTime(timezone=True), default=utc_now, index=True)
    split = Column(String(50), index=True) # dev or holdout

class Diagnosis(Base):
    __tablename__ = "diagnoses"
    id = Column(String(255), primary_key=True)
    event_id = Column(String(255), ForeignKey("risk_events.id", ondelete="CASCADE"), index=True)
    root_cause_category = Column(String(255))
    confidence = Column(Float)
    risk_quadrant = Column(String(255))
    reasoning = Column(String)
    tokens_used = Column(Integer, default=0)
    token_cost = Column(Float, default=0.0)

class GuardrailResult(Base):
    __tablename__ = "guardrail_results"
    id = Column(String(255), primary_key=True)
    event_id = Column(String(255), ForeignKey("risk_events.id", ondelete="CASCADE"), index=True)
    rule_name = Column(String(255))
    passed = Column(Boolean)
    reason = Column(String)
    checked_at = Column(DateTime(timezone=True), default=utc_now)

class Intervention(Base):
    __tablename__ = "interventions"
    id = Column(String(255), primary_key=True)
    event_id = Column(String(255), ForeignKey("risk_events.id", ondelete="CASCADE"), index=True)
    intervention_type = Column(String(255))
    channel = Column(String(255))
    tone = Column(String(255))
    scheduled_at = Column(DateTime(timezone=True), nullable=True)

class DeliveryResult(Base):
    __tablename__ = "delivery_results"
    id = Column(String(255), primary_key=True)
    intervention_id = Column(String(255), ForeignKey("interventions.id", ondelete="CASCADE"), index=True)
    channel = Column(String(255))
    status = Column(String(255), index=True)
    payment_link_id = Column(String(255), index=True, nullable=True)
    response_payload = Column(JSON, nullable=True)

class PromiseToPay(Base):
    __tablename__ = "promise_to_pays"
    id = Column(String(255), primary_key=True)
    case_id = Column(String(255), ForeignKey("risk_events.id", ondelete="CASCADE"), index=True)
    promised_amount = Column(Integer)
    promised_date = Column(Date)
    status = Column(String(50), index=True)
    detected_via = Column(String(255))

class AuditLogEntry(Base):
    __tablename__ = "audit_log_entries"
    id = Column(String(255), primary_key=True)
    case_id = Column(String(255), ForeignKey("risk_events.id", ondelete="CASCADE"), index=True)
    actor = Column(String(255))
    action = Column(String(255))
    reasoning = Column(String)
    timestamp = Column(DateTime(timezone=True), default=utc_now, index=True)

class BatchRunResult(Base):
    __tablename__ = "batch_run_results"
    id = Column(String(255), primary_key=True)
    status = Column(String(50), index=True)
    total_cases = Column(Integer)
    cases_processed = Column(Integer)
    amount_at_risk = Column(Integer)
    amount_recovered = Column(Integer)
    recovery_rate = Column(Float)
    false_escalation_rate = Column(Float)
    exception_list = Column(JSON)
    recovered_list = Column(JSON)
    started_at = Column(DateTime(timezone=True), default=utc_now)
    completed_at = Column(DateTime(timezone=True), nullable=True)
