"""
Common validators for CRM models.
"""

import re

from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _


# E.164 format: +[country code][number] (max 15 digits total)
# Examples: +12025551234, +442071234567
e164_phone_validator = RegexValidator(
    regex=r"^\+[1-9]\d{1,14}$",
    message=_("Phone must be in E.164 format (e.g., +12025551234)"),
)

# Flexible phone format allowing common separators
# Allows: digits, spaces, dashes, parentheses, plus sign
# Examples: +1 (202) 555-1234, 202-555-1234, +44 20 7123 4567
flexible_phone_validator = RegexValidator(
    regex=r"^[\d\s\-\(\)\+\.]{7,25}$",
    message=_(
        "Enter a valid phone number (7-25 characters, digits and separators only)"
    ),
)


def normalize_phone(phone: str) -> str:
    """
    Normalize a phone number by removing all non-digit characters.
    Returns the last 10 digits for comparison purposes.
    """
    if not phone:
        return ""
    digits_only = re.sub(r"[^\d]", "", phone)
    # Return last 10 digits for normalized comparison
    return digits_only[-10:] if len(digits_only) >= 10 else digits_only
