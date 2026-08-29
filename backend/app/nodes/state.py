from typing import TypedDict, Optional, List, Dict, Any

class RecoveryState(TypedDict):
    event: Dict[str, Any]
    diagnosis: Optional[Dict[str, Any]]
    guardrail_result: Optional[Dict[str, Any]]
    intervention: Optional[Dict[str, Any]]
    delivery_result: Optional[Dict[str, Any]]
    audit_log: List[Dict[str, Any]]
