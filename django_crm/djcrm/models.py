from django.db import models
from django.utils.translation import ugettext_lazy as _


# class CustomUser(AbstractBaseUser, PermissionsMixin):
#     username = models.CharField(max_length=100, unique=True)
#     email = models.EmailField(max_length=255, unique=True)
#     is_active = models.BooleanField(
#         default=True)
#     is_admin = models.BooleanField(default=False)
#     is_staff = models.BooleanField(default=False)
#     date_joined = models.DateTimeField(('date joined'), default=timezone.now)

#     USERNAME_FIELD = 'email'
#     REQUIRED_FIELDS = ['username', ]

#     objects = UserManager()

#     def get_short_name(self):
#         return self.username

#     def __unicode__(self):
#         return self.email


class Person(models.Model):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)


class Country(models.Model):
    """
    International Organization for Standardization (ISO) 3166-1 Country list.
    The field names are a bit awkward, but kept for backwards compatibility.
    pycountry's syntax of alpha2, alpha3, name and official_name seems sane.
    """
    iso_3166_1_a2 = models.CharField(
        _('ISO 3166-1 alpha-2'), max_length=2, blank=True, null=True)
    iso_3166_1_a3 = models.CharField(
        _('ISO 3166-1 alpha-3'), max_length=3, blank=True, null=True)
    iso_3166_1_numeric = models.CharField(
        _('ISO 3166-1 numeric'), max_length=3, blank=True, null=True)

    #: The commonly used name; e.g. 'United Kingdom'
    printable_name = models.CharField(_('Country name'), max_length=128, blank=True, null=True)
    #: The full official name of a country
    #: e.g. 'United Kingdom of Great Britain and Northern Ireland'
    name = models.CharField(_('Official name'), max_length=128, blank=True, null=True)

    is_shipping_country = models.BooleanField(
        _("Is shipping country"), default=False, db_index=True, blank=True)

    def __unicode__(self):
        return self.name


class Address(models.Model):
    street = models.CharField(("Street"), max_length=255, blank=True, null=True)
    city = models.CharField(("City of address"), max_length=255, blank=True, null=True)
    state = models.CharField(("State"), max_length=255, blank=True, null=True)
    postcode = models.CharField(("Post/Zip-code"), max_length=64, blank=True, null=True)
    country = models.ForeignKey(Country, verbose_name=("Country"), blank=True, null=True)

    def __str__(self):
        return self.city
