from django.contrib import admin
from cases.models import Case, Comment_Files


class CaseAdmin(admin.ModelAdmin):
    list_display = ("name", "account")


admin.site.register(Case, CaseAdmin)
admin.site.register(Comment_Files)
