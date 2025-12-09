import binascii
import datetime
import os
import time
import uuid

from django.contrib.auth.models import AbstractBaseUser, AbstractUser, PermissionsMixin
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.utils.timesince import timesince
from django.utils.translation import gettext_lazy as _
from common.base import BaseModel
from common.utils import (
    COUNTRIES,
    CURRENCY_CODES,
    ROLES,
    is_document_file_audio,
    is_document_file_code,
    is_document_file_image,
    is_document_file_pdf,
    is_document_file_sheet,
    is_document_file_text,
    is_document_file_video,
    is_document_file_zip,
)

from .manager import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(
        default=uuid.uuid4, unique=True, editable=False, db_index=True, primary_key=True
    )
    email = models.EmailField(_("email address"), blank=True, unique=True)
    profile_pic = models.CharField(max_length=1000, null=True, blank=True)
    activation_key = models.CharField(max_length=150, null=True, blank=True)
    key_expires = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(_("staff status"), default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        db_table = "users"
        ordering = ("-is_active",)

    def __str__(self):
        return self.email


class Address(BaseModel):
    address_line = models.CharField(
        _("Address"), max_length=255, blank=True, default=""
    )
    street = models.CharField(_("Street"), max_length=55, blank=True, default="")
    city = models.CharField(_("City"), max_length=255, blank=True, default="")
    state = models.CharField(_("State"), max_length=255, blank=True, default="")
    postcode = models.CharField(
        _("Post/Zip-code"), max_length=64, blank=True, default=""
    )
    country = models.CharField(max_length=3, choices=COUNTRIES, blank=True, default="")
    org = models.ForeignKey(
        "Org",
        on_delete=models.CASCADE,
        related_name="addresses",
    )

    class Meta:
        verbose_name = "Address"
        verbose_name_plural = "Addresses"
        db_table = "address"
        ordering = ("-created_at",)

    def __str__(self):
        return self.city if self.city else ""


def generate_unique_key():
    return str(uuid.uuid4())


class Org(BaseModel):
    name = models.CharField(max_length=100, blank=True, null=True)
    api_key = models.TextField(default=generate_unique_key, unique=True, editable=False)
    is_active = models.BooleanField(default=True)

    # Company Profile (for invoices, documents, etc.)
    company_name = models.CharField(
        max_length=255, blank=True, help_text="Legal company name for invoices"
    )
    logo = models.ImageField(
        upload_to="org_logos/", blank=True, null=True, help_text="Company logo"
    )
    address_line = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postcode = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=3, choices=COUNTRIES, blank=True)
    phone = models.CharField(max_length=25, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    tax_id = models.CharField(
        max_length=50, blank=True, help_text="Tax ID / VAT / Registration number"
    )

    # Locale settings
    default_currency = models.CharField(
        max_length=3, choices=CURRENCY_CODES, default="USD"
    )
    default_country = models.CharField(
        max_length=2, choices=COUNTRIES, blank=True, null=True
    )

    class Meta:
        verbose_name = "Organization"
        verbose_name_plural = "Organizations"
        db_table = "organization"
        ordering = ("-created_at",)

    def __str__(self):
        return str(self.name)


class Tags(BaseModel):
    """Tags for categorizing CRM entities (Accounts, Leads, Opportunities, etc.)"""

    COLOR_CHOICES = (
        ("gray", "Gray"),
        ("red", "Red"),
        ("orange", "Orange"),
        ("amber", "Amber"),
        ("yellow", "Yellow"),
        ("lime", "Lime"),
        ("green", "Green"),
        ("emerald", "Emerald"),
        ("teal", "Teal"),
        ("cyan", "Cyan"),
        ("sky", "Sky"),
        ("blue", "Blue"),
        ("indigo", "Indigo"),
        ("violet", "Violet"),
        ("purple", "Purple"),
        ("fuchsia", "Fuchsia"),
        ("pink", "Pink"),
        ("rose", "Rose"),
    )

    name = models.CharField(max_length=50)
    slug = models.CharField(max_length=50, blank=True)
    color = models.CharField(max_length=20, choices=COLOR_CHOICES, default="blue")
    description = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)
    org = models.ForeignKey(
        "Org",
        on_delete=models.CASCADE,
        related_name="tags",
    )

    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"
        db_table = "tags"
        ordering = ("name",)
        unique_together = ["slug", "org"]

    def __str__(self):
        return f"{self.name}"

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Profile(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="profiles")
    org = models.ForeignKey(Org, on_delete=models.CASCADE, related_name="profiles")
    phone = models.CharField(max_length=20, null=True, blank=True)
    alternate_phone = models.CharField(max_length=20, null=True, blank=True)
    address = models.ForeignKey(
        Address,
        related_name="address_users",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    role = models.CharField(max_length=50, choices=ROLES, default="USER")
    has_sales_access = models.BooleanField(default=False)
    has_marketing_access = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_organization_admin = models.BooleanField(default=False)
    date_of_joining = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = "Profile"
        verbose_name_plural = "Profiles"
        db_table = "profile"
        ordering = ("-created_at",)
        unique_together = [["user", "org"], ["phone", "org"]]

    def __str__(self):
        return f"{self.user.email} <{self.org.name}>"

    @property
    def is_admin(self):
        return self.is_organization_admin

    @property
    def user_details(self):
        return {
            "email": self.user.email,
            "id": self.user.id,
            "is_active": self.user.is_active,
            "profile_pic": self.user.profile_pic,
            "last_login": self.user.last_login,
        }


class Comment(BaseModel):
    """
    Generic comment model using ContentType framework.
    Can be attached to any model (Account, Lead, Contact, Opportunity, Case, Task, Invoice, Profile).
    """

    # Generic relation to any model
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, related_name="comments"
    )
    object_id = models.UUIDField()
    content_object = GenericForeignKey("content_type", "object_id")

    comment = models.CharField(max_length=255)
    commented_on = models.DateTimeField(auto_now_add=True)
    commented_by = models.ForeignKey(
        Profile, on_delete=models.CASCADE, blank=True, null=True
    )
    org = models.ForeignKey(
        "Org",
        on_delete=models.CASCADE,
        related_name="comments",
    )

    class Meta:
        verbose_name = "Comment"
        verbose_name_plural = "Comments"
        db_table = "comment"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
            models.Index(fields=["org", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.comment}"

    def clean(self):
        """
        Validate that the comment's org matches the content object's org.

        SECURITY: This prevents cross-org data references where a comment
        in org_a could reference an object in org_b.
        """
        from django.core.exceptions import ValidationError

        if self.content_object and hasattr(self.content_object, "org"):
            if self.content_object.org_id != self.org_id:
                raise ValidationError(
                    {
                        "org": "Comment organization must match the referenced object's organization."
                    }
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class CommentFiles(BaseModel):
    """
    File attachments for comments.
    Security: org field added for RLS protection and org-level isolation.
    """

    comment = models.ForeignKey(Comment, on_delete=models.CASCADE)
    comment_file = models.FileField(
        "File", upload_to="CommentFiles", null=True, blank=True
    )
    # Security fix: Add org field for RLS protection
    org = models.ForeignKey(
        "Org",
        on_delete=models.CASCADE,
        related_name="comment_files",
        null=True,  # Temporarily nullable for migration
        blank=True,
    )

    class Meta:
        verbose_name = "CommentFile"
        verbose_name_plural = "CommentFiles"
        db_table = "commentFiles"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.comment.comment}"

    def save(self, *args, **kwargs):
        # Auto-populate org from parent comment if not set
        if not self.org_id and self.comment_id:
            self.org_id = self.comment.org_id
        super().save(*args, **kwargs)


class Attachments(BaseModel):
    """
    Generic attachment model using ContentType framework.
    Can be attached to any model (Account, Lead, Contact, Opportunity, Case, Task, Invoice).
    """

    # Generic relation to any model
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, related_name="attachments"
    )
    object_id = models.UUIDField()
    content_object = GenericForeignKey("content_type", "object_id")

    file_name = models.CharField(max_length=60)
    attachment = models.FileField(max_length=1001, upload_to="attachments/%Y/%m/")
    org = models.ForeignKey(
        "Org",
        on_delete=models.CASCADE,
        related_name="attachments",
    )

    class Meta:
        verbose_name = "Attachment"
        verbose_name_plural = "Attachments"
        db_table = "attachments"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
            models.Index(fields=["org", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.file_name}"

    def file_type(self):
        name_ext_list = self.attachment.url.split(".")
        if len(name_ext_list) > 1:
            ext = name_ext_list[int(len(name_ext_list) - 1)]
            if is_document_file_audio(ext):
                return ("audio", "fa fa-file-audio")
            if is_document_file_video(ext):
                return ("video", "fa fa-file-video")
            if is_document_file_image(ext):
                return ("image", "fa fa-file-image")
            if is_document_file_pdf(ext):
                return ("pdf", "fa fa-file-pdf")
            if is_document_file_code(ext):
                return ("code", "fa fa-file-code")
            if is_document_file_text(ext):
                return ("text", "fa fa-file-alt")
            if is_document_file_sheet(ext):
                return ("sheet", "fa fa-file-excel")
            if is_document_file_zip(ext):
                return ("zip", "fa fa-file-archive")
            return ("file", "fa fa-file")
        return ("file", "fa fa-file")

    def clean(self):
        """
        Validate that the attachment's org matches the content object's org.

        SECURITY: This prevents cross-org data references where an attachment
        in org_a could reference an object in org_b.
        """
        from django.core.exceptions import ValidationError

        if self.content_object and hasattr(self.content_object, "org"):
            if self.content_object.org_id != self.org_id:
                raise ValidationError(
                    {
                        "org": "Attachment organization must match the referenced object's organization."
                    }
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


def document_path(self, filename):
    hash_ = int(time.time())
    return "%s/%s/%s" % ("docs", hash_, filename)


class Document(BaseModel):
    DOCUMENT_STATUS_CHOICE = (("active", "active"), ("inactive", "inactive"))

    title = models.TextField(blank=True, null=True)
    document_file = models.FileField(upload_to=document_path, max_length=5000)
    status = models.CharField(
        choices=DOCUMENT_STATUS_CHOICE, max_length=64, default="active"
    )
    shared_to = models.ManyToManyField(Profile, related_name="document_shared_to")
    teams = models.ManyToManyField("Teams", related_name="document_teams")
    org = models.ForeignKey(
        Org,
        on_delete=models.CASCADE,
        related_name="documents",
    )

    class Meta:
        verbose_name = "Document"
        verbose_name_plural = "Documents"
        db_table = "document"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.title}"

    def file_type(self):
        name_ext_list = self.document_file.url.split(".")
        if len(name_ext_list) > 1:
            ext = name_ext_list[int(len(name_ext_list) - 1)]
            if is_document_file_audio(ext):
                return ("audio", "fa fa-file-audio")
            if is_document_file_video(ext):
                return ("video", "fa fa-file-video")
            if is_document_file_image(ext):
                return ("image", "fa fa-file-image")
            if is_document_file_pdf(ext):
                return ("pdf", "fa fa-file-pdf")
            if is_document_file_code(ext):
                return ("code", "fa fa-file-code")
            if is_document_file_text(ext):
                return ("text", "fa fa-file-alt")
            if is_document_file_sheet(ext):
                return ("sheet", "fa fa-file-excel")
            if is_document_file_zip(ext):
                return ("zip", "fa fa-file-archive")
            return ("file", "fa fa-file")
        return ("file", "fa fa-file")


def generate_key():
    # Security: Increased from 8 bytes (64 bits) to 32 bytes (256 bits)
    return binascii.hexlify(os.urandom(32)).decode()


class APISettings(BaseModel):
    title = models.TextField()
    # Security: Increased max_length to accommodate 32-byte keys (64 hex chars)
    apikey = models.CharField(max_length=64, blank=True)
    website = models.URLField(max_length=255, null=True)
    lead_assigned_to = models.ManyToManyField(
        Profile, related_name="lead_assignee_users"
    )
    tags = models.ManyToManyField(Tags, blank=True)
    org = models.ForeignKey(
        Org,
        on_delete=models.CASCADE,
        related_name="api_settings",
    )

    class Meta:
        verbose_name = "APISetting"
        verbose_name_plural = "APISettings"
        db_table = "apiSettings"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.title}"

    def save(self, *args, **kwargs):
        if not self.apikey or self.apikey is None or self.apikey == "":
            self.apikey = generate_key()
        super().save(*args, **kwargs)


# Phase 3: JWT Token Tracking


class SessionToken(BaseModel):
    """Track active JWT sessions for security"""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="session_tokens"
    )
    token_jti = models.CharField(max_length=255, unique=True, db_index=True)  # JWT ID
    refresh_token_jti = models.CharField(
        max_length=255, unique=True, db_index=True, null=True, blank=True
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    last_used_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Session Token"
        verbose_name_plural = "Session Tokens"
        db_table = "session_token"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["user", "is_active"]),
            models.Index(fields=["token_jti"]),
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.token_jti[:8]}..."

    def revoke(self):
        """Revoke this session token"""
        from django.utils import timezone

        self.is_active = False
        self.revoked_at = timezone.now()
        self.save()

    @classmethod
    def cleanup_expired(cls):
        """Remove expired tokens (call via cron/celery)"""
        from django.utils import timezone

        return cls.objects.filter(expires_at__lt=timezone.now()).delete()


# Activity Tracking for Recent Activities Dashboard


class Activity(BaseModel):
    """Track user activities across all CRM entities"""

    ACTION_CHOICES = (
        ("CREATE", "Created"),
        ("UPDATE", "Updated"),
        ("DELETE", "Deleted"),
        ("VIEW", "Viewed"),
        ("COMMENT", "Commented"),
        ("ASSIGN", "Assigned"),
    )

    ENTITY_TYPE_CHOICES = (
        ("Account", "Account"),
        ("Lead", "Lead"),
        ("Contact", "Contact"),
        ("Opportunity", "Opportunity"),
        ("Case", "Case"),
        ("Task", "Task"),
        ("Invoice", "Invoice"),
        ("Event", "Event"),
        ("Document", "Document"),
        ("Team", "Team"),
    )

    user = models.ForeignKey(
        Profile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="activities",
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    entity_type = models.CharField(max_length=50, choices=ENTITY_TYPE_CHOICES)
    entity_id = models.UUIDField()
    entity_name = models.CharField(max_length=255, blank=True, default="")
    description = models.TextField(blank=True, default="")
    org = models.ForeignKey(Org, on_delete=models.CASCADE, related_name="activities")

    class Meta:
        verbose_name = "Activity"
        verbose_name_plural = "Activities"
        db_table = "activity"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["org", "-created_at"]),
            models.Index(fields=["entity_type", "entity_id"]),
        ]

    def __str__(self):
        return f"{self.user} {self.get_action_display()} {self.entity_type}: {self.entity_name}"

    @property
    def created_on_arrow(self):
        return timesince(self.created_at) + " ago"


class Teams(BaseModel):
    name = models.CharField(max_length=100)
    description = models.TextField()
    users = models.ManyToManyField(Profile, related_name="user_teams")
    org = models.ForeignKey(Org, on_delete=models.CASCADE, related_name="teams")

    class Meta:
        verbose_name = "Team"
        verbose_name_plural = "Teams"
        db_table = "teams"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.name}"

    def get_users(self):
        return ",".join(
            [str(_id) for _id in list(self.users.values_list("id", flat=True))]
        )


class ContactFormSubmission(BaseModel):
    """
    Contact form submission from public website.
    Stores inquiries from potential customers via contact forms.
    Not org-scoped as these are platform-level submissions.
    """

    name = models.CharField(max_length=255)
    email = models.EmailField()
    message = models.TextField()
    reason = models.CharField(
        max_length=100,
        choices=[
            ("general", "General Inquiry"),
            ("sales", "Sales Question"),
            ("support", "Technical Support"),
            ("partnership", "Partnership Opportunity"),
            ("other", "Other"),
        ],
        default="general",
    )

    # Tracking fields
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    referrer = models.URLField(max_length=500, null=True, blank=True)

    # Status tracking
    STATUS_CHOICES = [
        ("new", "New"),
        ("read", "Read"),
        ("replied", "Replied"),
        ("closed", "Closed"),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="new")
    replied_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contact_replies",
    )
    replied_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Contact Form Submission"
        verbose_name_plural = "Contact Form Submissions"
        db_table = "contact_form_submission"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.name} - {self.email} ({self.reason})"


# Import SecurityAuditLog so Django discovers it for migrations
from common.audit_log import SecurityAuditLog
