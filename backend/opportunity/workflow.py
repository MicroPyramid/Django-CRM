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
