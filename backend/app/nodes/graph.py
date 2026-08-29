from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END

from .state import RecoveryState
from .diagnose import diagnose_node
from .guardrail import guardrail_node
from .policy import policy_node
from .execute import execute_node
from .confirm import confirm_node
from .log import log_node

def route_on_diagnose(state: RecoveryState) -> Literal["guardrail", "confirm"]:
    # If the event is a webhook confirmation, skip straight to confirm_node
    if state["event"].get("event_type") == "payment_link.paid":
        return "confirm"
    return "guardrail"

def route_on_guardrail(state: RecoveryState) -> Literal["blocked", "clear"]:
    gr = state.get("guardrail_result")
    if gr and not gr.get("passed", True):
        return "blocked"
    return "clear"

graph = StateGraph(RecoveryState)
for name, fn in [("diagnose", diagnose_node), ("guardrail", guardrail_node),
                  ("policy", policy_node), ("execute", execute_node), 
                  ("confirm", confirm_node), ("log", log_node)]:
    graph.add_node(name, fn)

graph.set_entry_point("diagnose")
graph.add_conditional_edges("diagnose", route_on_diagnose, {"guardrail": "guardrail", "confirm": "confirm"})
graph.add_conditional_edges("guardrail", route_on_guardrail, {"blocked": "log", "clear": "policy"})
graph.add_edge("policy", "execute")
graph.add_edge("execute", "confirm")
graph.add_edge("confirm", "log")
graph.add_edge("log", END)

recovery_graph = graph.compile()
