"""
Marketing App Models

This app handles:
- Newsletter subscriptions and campaigns
- Contact form submissions from the public website
"""

from django.db import models
from common.base import BaseModel
from common.models import User


class NewsletterSubscriber(BaseModel):
    """
    Newsletter subscriber model

    Stores email subscriptions for marketing campaigns.
    Includes confirmation workflow and tracking.
    """
    email = models.EmailField(unique=True, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    subscribed_at = models.DateTimeField(auto_now_add=True, db_index=True)
    unsubscribed_at = models.DateTimeField(null=True, blank=True)

    # Confirmation workflow
    confirmation_token = models.CharField(max_length=100, unique=True, null=True, blank=True)
    is_confirmed = models.BooleanField(default=False)
    confirmed_at = models.DateTimeField(null=True, blank=True)

    # Tracking
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ['-subscribed_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['is_active']),
            models.Index(fields=['subscribed_at']),
        ]

    def __str__(self):
        return f"{self.email} ({'Active' if self.is_active else 'Inactive'})"

    def unsubscribe(self):
        """Unsubscribe a user"""
        from django.utils import timezone
        self.is_active = False
        self.unsubscribed_at = timezone.now()
        self.save()

    def confirm_subscription(self):
        """Confirm a subscription"""
        from django.utils import timezone
        self.is_confirmed = True
        self.confirmed_at = timezone.now()
        self.confirmation_token = None
        self.save()


class ContactFormSubmission(BaseModel):
    """
    Contact form submission from public website

    Stores inquiries from potential customers via contact forms.
    """
    name = models.CharField(max_length=255)
    email = models.EmailField()
    message = models.TextField()
    reason = models.CharField(
        max_length=100,
        choices=[
            ('general', 'General Inquiry'),
            ('sales', 'Sales Question'),
            ('support', 'Technical Support'),
            ('partnership', 'Partnership Opportunity'),
            ('other', 'Other'),
        ],
        default='general'
    )

    # Tracking fields
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    referrer = models.URLField(max_length=500, null=True, blank=True)

    # Status tracking
    STATUS_CHOICES = [
        ('new', 'New'),
        ('read', 'Read'),
        ('replied', 'Replied'),
        ('closed', 'Closed'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    replied_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='contact_replies')
    replied_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.name} - {self.email} ({self.reason})"

    def mark_as_read(self):
        """Mark submission as read"""
        if self.status == 'new':
            self.status = 'read'
            self.save()

    def mark_as_replied(self, user):
        """Mark submission as replied"""
        from django.utils import timezone
        self.status = 'replied'
        self.replied_by = user
        self.replied_at = timezone.now()
        self.save()
