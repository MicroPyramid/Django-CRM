from django.contrib import admin
from .models import Country, Address, Person
# Register your models here.

admin.site.register(Address)
admin.site.register(Country)
admin.site.register(Person)
