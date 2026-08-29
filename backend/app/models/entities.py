from sqlalchemy import Column, String, Integer, DateTime, Boolean, Date, Float, JSON
from .database import Base
import datetime

class RiskEvent(Base):
    __tablename__ = "risk_events"
    id = Column(String, primary_key=True)
    source = Column(String) # webhook, synthetic_receivable, synthetic_checkout
    event_type = Column(String)
    customer_id = Column(String)
    amount = Column(Integer) # paise
    currency = Column(String)
    raw_payload = Column(JSON)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    split = Column(String) # dev or holdout

class Diagnosis(Base):
    __tablename__ = "diagnoses"
    id = Column(String, primary_key=True)
    event_id = Column(String)
    root_cause_category = Column(String)
    confidence = Column(Float)
    risk_quadrant = Column(String)

class GuardrailResult(Base):
    __tablename__ = "guardrail_results"
    id = Column(String, primary_key=True)
    event_id = Column(String)
    rule_name = Column(String)
    passed = Column(Boolean)
    reason = Column(String)
    checked_at = Column(DateTime, default=datetime.datetime.utcnow)

class Intervention(Base):
    __tablename__ = "interventions"
    id = Column(String, primary_key=True)
    event_id = Column(String)
    intervention_type = Column(String)
    channel = Column(String)
    tone = Column(String)
    scheduled_at = Column(DateTime, nullable=True)

class DeliveryResult(Base):
    __tablename__ = "delivery_results"
    id = Column(String, primary_key=True)
    intervention_id = Column(String)
    channel = Column(String)
    status = Column(String)
    response_payload = Column(JSON, nullable=True)

class PromiseToPay(Base):
    __tablename__ = "promise_to_pays"
    id = Column(String, primary_key=True)
    case_id = Column(String)
    promised_amount = Column(Integer)
    promised_date = Column(Date)
    status = Column(String)
    detected_via = Column(String)

class AuditLogEntry(Base):
    __tablename__ = "audit_log_entries"
    id = Column(String, primary_key=True)
    case_id = Column(String)
    actor = Column(String)
    action = Column(String)
    reasoning = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class BatchRunResult(Base):
    __tablename__ = "batch_run_results"
    id = Column(String, primary_key=True)
    status = Column(String)
    total_cases = Column(Integer)
    cases_processed = Column(Integer)
    amount_at_risk = Column(Integer)
    amount_recovered = Column(Integer)
    recovery_rate = Column(Float)
    false_escalation_rate = Column(Float)
    exception_list = Column(JSON)
    recovered_list = Column(JSON)
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
