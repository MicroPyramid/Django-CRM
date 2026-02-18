"""
Opportunity workflow configuration.

Defines auto-probability mapping for the sales pipeline.
"""

# Default probability by stage (auto-set if probability is 0/None)
STAGE_PROBABILITIES = {
    "PROSPECTING": 10,
    "QUALIFICATION": 25,
    "PROPOSAL": 50,
    "NEGOTIATION": 75,
    "CLOSED_WON": 100,
    "CLOSED_LOST": 0,
}

# Stages that require closed_on date
CLOSED_STAGES = {"CLOSED_WON", "CLOSED_LOST"}

# Stages that require amount
AMOUNT_REQUIRED_STAGES = {"CLOSED_WON"}

# Default expected days per stage for deal aging
DEFAULT_STAGE_EXPECTED_DAYS = {
    "PROSPECTING": 14,
    "QUALIFICATION": 14,
    "PROPOSAL": 10,
    "NEGOTIATION": 10,
}

# Red threshold multiplier: deal is "rotten" when days >= expected_days * ROTTEN_MULTIPLIER
ROTTEN_MULTIPLIER = 1.5
