from django.contrib import admin

from common.models import Address, Comment, Comment_Files, User

# Register your models here.

admin.site.register(User)
admin.site.register(Address)
admin.site.register(Comment)
admin.site.register(Comment_Files)
