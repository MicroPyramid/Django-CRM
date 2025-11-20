"""
Marketing App Admin
"""

from django.contrib import admin
from marketing.models import NewsletterSubscriber, ContactFormSubmission


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ['email', 'is_active', 'is_confirmed', 'subscribed_at', 'created_at']
    list_filter = ['is_active', 'is_confirmed', 'subscribed_at']
    search_fields = ['email']
    readonly_fields = ['subscribed_at', 'unsubscribed_at', 'confirmed_at', 'created_at', 'updated_at']
    date_hierarchy = 'subscribed_at'

    fieldsets = (
        ('Subscriber Info', {
            'fields': ('email', 'is_active')
        }),
        ('Confirmation', {
            'fields': ('is_confirmed', 'confirmed_at', 'confirmation_token')
        }),
        ('Tracking', {
            'fields': ('ip_address', 'user_agent')
        }),
        ('Timestamps', {
            'fields': ('subscribed_at', 'unsubscribed_at', 'created_at', 'updated_at')
        }),
    )


@admin.register(ContactFormSubmission)
class ContactFormSubmissionAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'reason', 'status', 'created_at']
    list_filter = ['status', 'reason', 'created_at']
    search_fields = ['name', 'email', 'message']
    readonly_fields = ['created_at', 'updated_at', 'replied_at']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Contact Info', {
            'fields': ('name', 'email', 'reason')
        }),
        ('Message', {
            'fields': ('message',)
        }),
        ('Status', {
            'fields': ('status', 'replied_by', 'replied_at')
        }),
        ('Tracking', {
            'fields': ('ip_address', 'user_agent', 'referrer')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        """Make some fields readonly after creation"""
        readonly = list(self.readonly_fields)
        if obj:  # Editing existing object
            readonly.extend(['name', 'email', 'reason', 'message'])
        return readonly
