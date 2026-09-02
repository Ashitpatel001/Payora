"""Centralized configuration constants for the Revenue Recovery Agent.

All magic numbers, thresholds, and external-service pricing live here.
Import from this module — never hardcode values in node/API code.
"""

# --- Guardrail Thresholds ---
HIGH_VALUE_THRESHOLD_PAISE = 2500000  # ₹25,000 in paise

# --- Token Cost Tracking ---
# Groq pricing per 1M tokens (as of 2024-Q4)
# Source: https://console.groq.com/settings/billing
GROQ_MODEL_PRICING = {
    "groq/compound": {
        "input_cost_per_1m": 0.00,   # Free tier — $0/1M input
        "output_cost_per_1m": 0.00,  # Free tier — $0/1M output
    },
    "llama-3.3-70b-versatile": {
        "input_cost_per_1m": 0.59,
        "output_cost_per_1m": 0.79,
    },
    "llama-3.1-8b-instant": {
        "input_cost_per_1m": 0.05,
        "output_cost_per_1m": 0.08,
    },
    # Fallback for unknown models
    "default": {
        "input_cost_per_1m": 1.00,
        "output_cost_per_1m": 1.00,
    },
}

# Lifetime token budget cap (USD). Set to 0 to disable.
LIFETIME_TOKEN_BUDGET_USD = 10.00
