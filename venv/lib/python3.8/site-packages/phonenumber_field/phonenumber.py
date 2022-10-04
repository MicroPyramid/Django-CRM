from functools import total_ordering

import phonenumbers
from django.conf import settings
from django.core import validators


@total_ordering
class PhoneNumber(phonenumbers.PhoneNumber):
    """
    A extended version of phonenumbers.PhoneNumber that provides
    some neat and more pythonic, easy to access methods. This makes using a
    PhoneNumber instance much easier, especially in templates and such.
    """

    format_map = {
        "E164": phonenumbers.PhoneNumberFormat.E164,
        "INTERNATIONAL": phonenumbers.PhoneNumberFormat.INTERNATIONAL,
        "NATIONAL": phonenumbers.PhoneNumberFormat.NATIONAL,
        "RFC3966": phonenumbers.PhoneNumberFormat.RFC3966,
    }

    @classmethod
    def from_string(cls, phone_number, region=None):
        phone_number_obj = cls()
        if region is None:
            region = getattr(settings, "PHONENUMBER_DEFAULT_REGION", None)
        phonenumbers.parse(
            number=phone_number,
            region=region,
            keep_raw_input=True,
            numobj=phone_number_obj,
        )
        return phone_number_obj

    def __str__(self):
        if self.is_valid():
            format_string = getattr(settings, "PHONENUMBER_DEFAULT_FORMAT", "E164")
            fmt = self.format_map[format_string]
            return self.format_as(fmt)
        else:
            return self.raw_input

    def __repr__(self):
        if not self.is_valid():
            return f"Invalid{type(self).__name__}(raw_input={self.raw_input})"
        return super().__repr__()

    def is_valid(self):
        """
        checks whether the number supplied is actually valid
        """
        return phonenumbers.is_valid_number(self)

    def format_as(self, format):
        return phonenumbers.format_number(self, format)

    @property
    def as_international(self):
        return self.format_as(phonenumbers.PhoneNumberFormat.INTERNATIONAL)

    @property
    def as_e164(self):
        return self.format_as(phonenumbers.PhoneNumberFormat.E164)

    @property
    def as_national(self):
        return self.format_as(phonenumbers.PhoneNumberFormat.NATIONAL)

    @property
    def as_rfc3966(self):
        return self.format_as(phonenumbers.PhoneNumberFormat.RFC3966)

    def __len__(self):
        return len(str(self))

    def __eq__(self, other):
        """
        Override parent equality because we store only string representation
        of phone number, so we must compare only this string representation
        """
        if other in validators.EMPTY_VALUES:
            return False
        elif isinstance(other, str):
            default_region = getattr(settings, "PHONENUMBER_DEFAULT_REGION", None)
            other = to_python(other, region=default_region)
        elif isinstance(other, type(self)):
            # Nothing to do. Good to compare.
            pass
        elif isinstance(other, phonenumbers.PhoneNumber):
            # The parent class of PhoneNumber does not have .is_valid().
            # We need to make it match ours.
            old_other = other
            other = type(self)()
            other.merge_from(old_other)
        else:
            return False

        format_string = getattr(settings, "PHONENUMBER_DB_FORMAT", "E164")
        fmt = self.format_map[format_string]
        self_str = self.format_as(fmt) if self.is_valid() else self.raw_input
        other_str = other.format_as(fmt) if other.is_valid() else other.raw_input
        return self_str == other_str

    def __lt__(self, other):
        if isinstance(other, phonenumbers.PhoneNumber):
            old_other = other
            other = type(self)()
            other.merge_from(old_other)
        elif not isinstance(other, type(self)):
            raise TypeError(
                "'<' not supported between instances of "
                "'%s' and '%s'" % (type(self).__name__, type(other).__name__)
            )

        invalid = None
        if not self.is_valid():
            invalid = self
        elif not other.is_valid():
            invalid = other
        if invalid is not None:
            raise ValueError("Invalid phone number: %r" % invalid)

        format_string = getattr(settings, "PHONENUMBER_DB_FORMAT", "E164")
        fmt = self.format_map[format_string]
        return self.format_as(fmt) < other.format_as(fmt)

    def __hash__(self):
        return hash(str(self))


def to_python(value, region=None):
    if value in validators.EMPTY_VALUES:  # None or ''
        phone_number = value
    elif isinstance(value, str):
        try:
            phone_number = PhoneNumber.from_string(phone_number=value, region=region)
        except phonenumbers.NumberParseException:
            # the string provided is not a valid PhoneNumber.
            phone_number = PhoneNumber(raw_input=value)
    elif isinstance(value, PhoneNumber):
        phone_number = value
    elif isinstance(value, phonenumbers.PhoneNumber):
        phone_number = PhoneNumber()
        phone_number.merge_from(value)
    else:
        raise TypeError("Can't convert %s to PhoneNumber." % type(value).__name__)
    return phone_number


def validate_region(region):
    if (
        region is not None
        and region not in phonenumbers.shortdata._AVAILABLE_REGION_CODES
    ):
        raise ValueError(
            "“%s” is not a valid region code. Choices are %r"
            % (region, phonenumbers.shortdata._AVAILABLE_REGION_CODES)
        )
