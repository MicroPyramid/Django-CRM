"""
Conditional field requirements configuration.

Reference configuration for which fields are typically required
based on stage, status, or type. These are NOT enforced at the model
level but can be used by serializers or frontend for validation hints.
"""

# Opportunity: Suggested required fields by stage
OPPORTUNITY_REQUIRED_BY_STAGE = {
    "PROSPECTING": ["name"],
    "QUALIFICATION": ["name"],
    "PROPOSAL": ["name", "amount"],
    "NEGOTIATION": ["name", "amount"],
    "CLOSED_WON": ["name", "amount", "closed_on"],
    "CLOSED_LOST": ["name", "closed_on"],
}

# Lead: Suggested required fields by status
LEAD_REQUIRED_BY_STATUS = {
    "assigned": [],
    "in process": [],
    "converted": ["email"],  # Only email is enforced
    "recycled": [],
    "closed": [],
}

# Case: Suggested required fields by status
CASE_REQUIRED_BY_STATUS = {
    "New": ["name", "status", "priority"],
    "Assigned": ["name", "status", "priority"],
    "Pending": ["name", "status", "priority"],
    "Closed": ["name", "status", "priority", "closed_on"],
    "Rejected": ["name", "status", "priority"],
    "Duplicate": ["name", "status", "priority"],
}
