from django.contrib import admin

from common.models import Address, Comment, CommentFiles, SessionToken, User

# Register your models here.

admin.site.register(User)
admin.site.register(Address)
admin.site.register(Comment)
admin.site.register(CommentFiles)


@admin.register(SessionToken)
class SessionTokenAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "token_jti_short",
        "is_active",
        "expires_at",
        "last_used_at",
        "created_at",
    )
    list_filter = ("is_active", "expires_at", "created_at")
    search_fields = ("user__email", "token_jti", "ip_address")
    raw_id_fields = ("user",)
    readonly_fields = (
        "token_jti",
        "refresh_token_jti",
        "created_at",
        "last_used_at",
        "revoked_at",
    )
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    actions = ["revoke_tokens", "cleanup_expired"]

    def token_jti_short(self, obj):
        return f"{obj.token_jti[:16]}..."

    token_jti_short.short_description = "Token JTI"

    def revoke_tokens(self, request, queryset):
        for token in queryset:
            token.revoke()
        self.message_user(request, f"{queryset.count()} tokens revoked successfully.")

    revoke_tokens.short_description = "Revoke selected tokens"

    def cleanup_expired(self, request, queryset):
        count, _ = SessionToken.cleanup_expired()
        self.message_user(request, f"{count} expired tokens cleaned up.")

    cleanup_expired.short_description = "Cleanup expired tokens"
