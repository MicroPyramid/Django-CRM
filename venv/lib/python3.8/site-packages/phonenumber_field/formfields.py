import phonenumbers
from django.conf import settings
from django.core import validators
from django.core.exceptions import ValidationError
from django.forms.fields import CharField
from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _

from phonenumber_field.phonenumber import PhoneNumber, to_python, validate_region
from phonenumber_field.validators import validate_international_phonenumber


class PhoneNumberField(CharField):
    default_validators = [validate_international_phonenumber]

    def __init__(self, *args, region=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.widget.input_type = "tel"

        validate_region(region)
        self.region = region or getattr(settings, "PHONENUMBER_DEFAULT_REGION", None)

        if "invalid" not in self.error_messages:
            if self.region:
                number = phonenumbers.example_number(self.region)
                example_number = to_python(number).as_national
                # Translators: {example_number} is a national phone number.
                error_message = _(
                    "Enter a valid phone number (e.g. {example_number}) "
                    "or a number with an international call prefix."
                )
            else:
                example_number = "+12125552368"  # Ghostbusters
                # Translators: {example_number} is an international phone number.
                error_message = _("Enter a valid phone number (e.g. {example_number}).")
            self.error_messages["invalid"] = format_lazy(
                error_message, example_number=example_number
            )

    def prepare_value(self, value):
        if self.region and value not in validators.EMPTY_VALUES:
            phone_number = (
                value
                if isinstance(value, PhoneNumber)
                else to_python(value, region=self.region)
            )
            try:
                phone_region_codes = phonenumbers.data._COUNTRY_CODE_TO_REGION_CODE[
                    phone_number.country_code
                ]
            except KeyError:
                pass
            else:
                if self.region in phone_region_codes:
                    value = phone_number.as_national
        return value

    def to_python(self, value):
        phone_number = to_python(value, region=self.region)

        if phone_number in validators.EMPTY_VALUES:
            return self.empty_value

        if phone_number and not phone_number.is_valid():
            raise ValidationError(self.error_messages["invalid"])

        return phone_number
