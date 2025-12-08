"""
Case workflow configuration.

Defines SLA defaults by priority.
"""

# Terminal statuses
TERMINAL_STATUSES = {"Closed", "Rejected", "Duplicate"}

# Statuses that require closed_on date
CLOSED_DATE_REQUIRED_STATUSES = {"Closed"}

# Default SLA by priority (in hours)
DEFAULT_FIRST_RESPONSE_SLA = {
    "Low": 24,
    "Normal": 8,
    "High": 4,
    "Urgent": 1,
}

DEFAULT_RESOLUTION_SLA = {
    "Low": 72,
    "Normal": 48,
    "High": 24,
    "Urgent": 4,
}
