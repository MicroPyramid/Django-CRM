from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.forms import Select, TextInput
from django.forms.widgets import MultiWidget
from django.utils import translation
from phonenumbers import PhoneNumberFormat
from phonenumbers.phonenumberutil import (
    COUNTRY_CODE_TO_REGION_CODE,
    national_significant_number,
    region_code_for_number,
)

from phonenumber_field.phonenumber import PhoneNumber, to_python

try:
    import babel
except ModuleNotFoundError:
    babel = None

# ISO 3166-1 alpha-2 to national prefix
REGION_CODE_TO_COUNTRY_CODE = {
    region_code: country_code
    for country_code, region_codes in COUNTRY_CODE_TO_REGION_CODE.items()
    for region_code in region_codes
}


def localized_choices(language):
    if babel is None:
        raise ImproperlyConfigured(
            "The PhonePrefixSelect widget requires the babel package be installed."
        )

    choices = [("", "---------")]
    locale_name = translation.to_locale(language)
    locale = babel.Locale(locale_name)
    for region_code, country_code in REGION_CODE_TO_COUNTRY_CODE.items():
        region_name = locale.territories.get(region_code)
        if region_name:
            choices.append((region_code, f"{region_name} +{country_code}"))
    return choices


class PhonePrefixSelect(Select):
    initial = None

    def __init__(self, initial=None, attrs=None):
        language = translation.get_language() or settings.LANGUAGE_CODE
        choices = localized_choices(language)
        if initial is None:
            initial = getattr(settings, "PHONENUMBER_DEFAULT_REGION", None)
        if initial in REGION_CODE_TO_COUNTRY_CODE:
            self.initial = initial
        super().__init__(attrs=attrs, choices=sorted(choices, key=lambda item: item[1]))

    def get_context(self, name, value, attrs):
        attrs = (attrs or {}).copy()
        attrs.pop("maxlength", None)
        return super().get_context(name, value or self.initial, attrs)


class PhoneNumberPrefixWidget(MultiWidget):
    """
    A Widget that splits phone number input into:
    - a country select box for phone prefix
    - an input for local phone number
    """

    def __init__(self, attrs=None, initial=None, country_attrs=None, number_attrs=None):
        widgets = (
            PhonePrefixSelect(initial, attrs=country_attrs),
            TextInput(attrs=number_attrs),
        )
        super().__init__(widgets, attrs)

    def decompress(self, value):
        if isinstance(value, PhoneNumber):
            if not value.is_valid():
                region = getattr(settings, "PHONENUMBER_DEFAULT_REGION", None)
                region_code = getattr(value, "_region", region)
                return [region_code, value.raw_input]
            region_code = region_code_for_number(value)
            national_number = national_significant_number(value)
            return [region_code, national_number]
        return [None, None]

    def value_from_datadict(self, data, files, name):
        region_code, national_number = super().value_from_datadict(data, files, name)

        if national_number is None:
            national_number = ""
        number = to_python(national_number, region=region_code)
        if isinstance(number, str):
            number = PhoneNumber()
            number.raw_input = national_number
        if not number.is_valid():
            setattr(number, "_region", region_code)
        return number


class PhoneNumberInternationalFallbackWidget(TextInput):
    """
    A Widget that allows a phone number in a national format, but if given
    an international number will fall back to international format
    """

    def __init__(self, region=None, attrs=None):
        if region is None:
            region = getattr(settings, "PHONENUMBER_DEFAULT_REGION", None)
        self.region = region
        super().__init__(attrs)

    def format_value(self, value):
        if isinstance(value, PhoneNumber):
            number_region = region_code_for_number(value)
            if self.region != number_region:
                formatter = PhoneNumberFormat.INTERNATIONAL
            else:
                formatter = PhoneNumberFormat.NATIONAL
            return value.format_as(formatter)
        return super().format_value(value)
