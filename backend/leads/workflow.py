"""
Lead workflow configuration.

Reference configuration for lead lifecycle management.
"""

# Statuses that represent terminal states
TERMINAL_STATUSES = {"converted", "closed"}

# Status that requires email
EMAIL_REQUIRED_STATUSES = {"converted"}
