from django.contrib import admin

from common.models import Address
from common.models import Comment
from common.models import Comment_Files
from common.models import User
# Register your models here.

admin.site.register(User)
admin.site.register(Address)
admin.site.register(Comment)
admin.site.register(Comment_Files)
