"""Phone numbers in one comparable form, E.164 ("+15551234567")."""

import phonenumbers


def to_e164(raw, region) -> str:
    """``raw`` as E.164, or ``""`` when it cannot be a phone number.

    ``region`` is an ISO 3166 alpha-2 code (``Org.default_country`` stores
    those) used for numbers typed without a country code; with none, only an
    international number parses. Possible rather than valid numbers are
    accepted, because the metadata trails real numbering plans, but not one
    dialable only locally (no area code). Never raises.
    """
    if raw is None:
        return ""
    text = str(raw).strip()
    if not text:
        return ""
    try:
        number = phonenumbers.parse(text, str(region or "").upper() or None)
    except phonenumbers.NumberParseException:
        return ""
    possible = phonenumbers.is_possible_number_with_reason(number)
    if possible != phonenumbers.ValidationResult.IS_POSSIBLE:
        return ""
    return phonenumbers.format_number(number, phonenumbers.PhoneNumberFormat.E164)


def set_phone_e164(record, save_kwargs) -> None:
    """Derive ``record.phone_e164`` from ``record.phone`` and its org's country.

    Called from a model's ``save`` with the save's kwargs. A save limited by
    ``update_fields`` recomputes only when ``phone`` is among them, and then
    writes ``phone_e164`` too. Queryset ``update()`` and ``bulk_create`` skip
    this, so a path that writes ``phone`` that way sets both itself.
    """
    update_fields = save_kwargs.get("update_fields")
    if update_fields is not None:
        if "phone" not in update_fields:
            return
        save_kwargs["update_fields"] = {*update_fields, "phone_e164"}
    if not record.phone:
        record.phone_e164 = ""
        return
    region = record.org.default_country if record.org_id else None
    record.phone_e164 = to_e164(record.phone, region)
