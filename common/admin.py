from django.contrib import admin
from common.models import User, Address, Team, Comment, Comment_Files
# Register your models here.

admin.site.register(User)
admin.site.register(Address)
admin.site.register(Team)
admin.site.register(Comment)
admin.site.register(Comment_Files)