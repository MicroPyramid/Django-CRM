from django.contrib import admin

from leads.models import Lead


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    # is_sample marks leads created by the vertical-pack applier's sample
    # data and is the guard `clear_sample_data` uses to decide what it may
    # delete (see common/packs/applier.py). It must never be editable here.
    # A bare ModelAdmin would let a staff user flip it on a real lead,
    # putting that lead in scope for the next clear-sample-data call.
    readonly_fields = ("is_sample",)
