import re

from django.contrib.auth import authenticate
from django.contrib.auth.hashers import check_password
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from common.utils import CURRENCY_SYMBOLS
from common.models import (
    Activity,
    Address,
    APISettings,
    Attachments,
    Comment,
    Document,
    Org,
    Profile,
    Tags,
    Teams,
    User,
)


class OrgAwareRefreshToken(RefreshToken):
    """
    Custom RefreshToken that includes org context in the token payload.

    This ensures the org context is cryptographically signed and cannot be
    forged by the client. The middleware should validate org_id from this
    token instead of trusting the org header.

    Embedded claims (to avoid extra API calls):
    - org_id: Organization UUID
    - org_name: Organization name (for display)
    - role: User's role in the org (ADMIN/USER)
    - org_settings: Currency and locale settings
    """

    @classmethod
    def for_user_and_org(cls, user, org, profile=None):
        """
        Generate a refresh token for a user with org context.

        Args:
            user: User instance
            org: Org instance or org_id UUID
            profile: Optional Profile instance for role

        Returns:
            OrgAwareRefreshToken with org claims
        """
        token = cls.for_user(user)

        # Add org context to the token payload
        if org:
            org_id = str(org.id) if hasattr(org, "id") else str(org)
            token["org_id"] = org_id
            # Add org_name for display (avoids /api/auth/profile call)
            if hasattr(org, "name"):
                token["org_name"] = org.name
            # Add org settings for currency/locale
            if hasattr(org, "default_currency"):
                token["org_settings"] = {
                    "default_currency": org.default_currency or "USD",
                    "currency_symbol": CURRENCY_SYMBOLS.get(
                        org.default_currency or "USD", "$"
                    ),
                    "default_country": org.default_country,
                }

        # Add role if profile provided (avoids /api/auth/profile call)
        if profile:
            token["role"] = profile.role

        return token


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Org
        fields = ("id", "name", "api_key")


class OrgSettingsSerializer(serializers.ModelSerializer):
    """Serializer for org settings (currency, country, locale)"""

    currency_symbol = serializers.SerializerMethodField()

    class Meta:
        model = Org
        fields = ["id", "name", "default_currency", "default_country", "currency_symbol"]
        read_only_fields = ["id", "currency_symbol"]

    @extend_schema_field(str)
    def get_currency_symbol(self, obj):
        return CURRENCY_SYMBOLS.get(obj.default_currency or "USD", "$")


class TagsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tags
        fields = ("id", "name", "slug")


class SocialLoginSerializer(serializers.Serializer):
    token = serializers.CharField()


class CommentSerializer(serializers.ModelSerializer):
    """Serializer for Comment model using ContentType"""

    content_type = serializers.SlugRelatedField(slug_field="model", read_only=True)

    class Meta:
        model = Comment
        fields = (
            "id",
            "comment",
            "commented_on",
            "commented_by",
            "content_type",
            "object_id",
            "org",
        )


class CommentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating comments with ContentType"""

    content_type = serializers.CharField(write_only=True)
    object_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = Comment
        fields = (
            "comment",
            "content_type",
            "object_id",
        )

    def create(self, validated_data):
        from django.contrib.contenttypes.models import ContentType

        content_type_str = validated_data.pop("content_type")
        try:
            content_type = ContentType.objects.get(model=content_type_str.lower())
        except ContentType.DoesNotExist:
            raise serializers.ValidationError(
                f"Invalid content type: {content_type_str}"
            )

        validated_data["content_type"] = content_type
        return super().create(validated_data)


class LeadCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = (
            "id",
            "comment",
            "commented_on",
            "commented_by",
        )


class OrgProfileCreateSerializer(serializers.ModelSerializer):
    """
    It is for creating organization
    """

    name = serializers.CharField(max_length=255)

    class Meta:
        model = Org
        fields = ["name"]
        extra_kwargs = {"name": {"required": True}}

    def validate_name(self, name):
        if bool(re.search(r"[~\!@#\$%\^&\*\(\)\+{}\":;'/\[\]]", name)):
            raise serializers.ValidationError(
                "organization name should not contain any special characters"
            )
        if Org.objects.filter(name=name).exists():
            raise serializers.ValidationError(
                "Organization already exists with this name"
            )
        return name


class ShowOrganizationListSerializer(serializers.ModelSerializer):
    """
    we are using it for show orjanization list
    """

    org = OrganizationSerializer()

    class Meta:
        model = Profile
        fields = (
            "role",
            "alternate_phone",
            "has_sales_access",
            "has_marketing_access",
            "is_organization_admin",
            "org",
        )


class BillingAddressSerializer(serializers.ModelSerializer):
    country = serializers.SerializerMethodField()

    @extend_schema_field(str)
    def get_country(self, obj):
        return obj.get_country_display()

    class Meta:
        model = Address
        fields = ("address_line", "street", "city", "state", "postcode", "country")

    def __init__(self, *args, **kwargs):
        account_view = kwargs.pop("account", False)

        super().__init__(*args, **kwargs)

        if account_view:
            self.fields["address_line"].required = True
            self.fields["street"].required = True
            self.fields["city"].required = True
            self.fields["state"].required = True
            self.fields["postcode"].required = True
            self.fields["country"].required = True


class CreateUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = (
            "email",
            "profile_pic",
        )

    def __init__(self, *args, **kwargs):
        self.org = kwargs.pop("org", None)
        super().__init__(*args, **kwargs)
        self.fields["email"].required = True

    def validate_email(self, email):
        if self.instance:
            if self.instance.email != email:
                if not Profile.objects.filter(user__email=email, org=self.org).exists():
                    return email
                raise serializers.ValidationError("Email already exists")
            return email
        if not Profile.objects.filter(user__email=email.lower(), org=self.org).exists():
            return email
        raise serializers.ValidationError("Given Email id already exists")


class CreateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = (
            "role",
            "phone",
            "alternate_phone",
            "has_sales_access",
            "has_marketing_access",
            "is_organization_admin",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["alternate_phone"].required = False
        self.fields["role"].required = True
        self.fields["phone"].required = True


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ["id", "email", "profile_pic"]


class ProfileSerializer(serializers.ModelSerializer):
    # address = BillingAddressSerializer()
    user_details = serializers.SerializerMethodField()

    @extend_schema_field(dict)
    def get_user_details(self, obj):
        return obj.user_details

    class Meta:
        model = Profile
        fields = (
            "id",
            "user_details",
            "role",
            "address",
            "has_marketing_access",
            "has_sales_access",
            "phone",
            "date_of_joining",
            "is_active",
            "created_at",
        )


class AttachmentsSerializer(serializers.ModelSerializer):
    """Serializer for Attachments model using ContentType"""

    file_path = serializers.SerializerMethodField()
    content_type = serializers.SlugRelatedField(slug_field="model", read_only=True)

    @extend_schema_field(str)
    def get_file_path(self, obj):
        if obj.attachment:
            return obj.attachment.url
        return None

    class Meta:
        model = Attachments
        fields = [
            "id",
            "created_by",
            "file_name",
            "created_at",
            "file_path",
            "content_type",
            "object_id",
            "org",
        ]


class AttachmentsCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating attachments with ContentType"""

    content_type = serializers.CharField(write_only=True)
    object_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = Attachments
        fields = (
            "file_name",
            "attachment",
            "content_type",
            "object_id",
        )

    def create(self, validated_data):
        from django.contrib.contenttypes.models import ContentType

        content_type_str = validated_data.pop("content_type")
        try:
            content_type = ContentType.objects.get(model=content_type_str.lower())
        except ContentType.DoesNotExist:
            raise serializers.ValidationError(
                f"Invalid content type: {content_type_str}"
            )

        validated_data["content_type"] = content_type
        return super().create(validated_data)


class DocumentSerializer(serializers.ModelSerializer):
    shared_to = ProfileSerializer(read_only=True, many=True)
    teams = serializers.SerializerMethodField()
    created_by = UserSerializer()
    org = OrganizationSerializer()

    @extend_schema_field(list)
    def get_teams(self, obj):
        return obj.teams.all().values()

    class Meta:
        model = Document
        fields = [
            "id",
            "title",
            "document_file",
            "status",
            "shared_to",
            "teams",
            "created_at",
            "created_by",
            "org",
        ]


class DocumentCreateSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        request_obj = kwargs.pop("request_obj", None)
        super().__init__(*args, **kwargs)
        self.fields["title"].required = True
        self.org = request_obj.profile.org

    def validate_title(self, title):
        if self.instance:
            if (
                Document.objects.filter(title__iexact=title, org=self.org)
                .exclude(id=self.instance.id)
                .exists()
            ):
                raise serializers.ValidationError(
                    "Document with this Title already exists"
                )
        if Document.objects.filter(title__iexact=title, org=self.org).exists():
            raise serializers.ValidationError("Document with this Title already exists")
        return title

    class Meta:
        model = Document
        fields = ["title", "document_file", "status", "org"]


def find_urls(string):
    # website_regex = "^((http|https)://)?([A-Za-z0-9.-]+\.[A-Za-z]{2,63})?$"  # (http(s)://)google.com or google.com
    # website_regex = "^https?://([A-Za-z0-9.-]+\.[A-Za-z]{2,63})?$"  # (http(s)://)google.com
    # http(s)://google.com
    website_regex = r"^https?://[A-Za-z0-9.-]+\.[A-Za-z]{2,63}$"
    # http(s)://google.com:8000
    website_regex_port = r"^https?://[A-Za-z0-9.-]+\.[A-Za-z]{2,63}:[0-9]{2,4}$"
    url = re.findall(website_regex, string)
    url_port = re.findall(website_regex_port, string)
    if url and url[0] != "":
        return url
    return url_port


class APISettingsSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    class Meta:
        model = APISettings
        fields = ("title", "website")

    def validate_website(self, website):
        if website and not (
            website.startswith("http://") or website.startswith("https://")
        ):
            raise serializers.ValidationError("Please provide valid schema")
        if not len(find_urls(website)) > 0:
            raise serializers.ValidationError(
                "Please provide a valid URL with schema and without trailing slash - Example: http://google.com"
            )
        return website


class APISettingsListSerializer(serializers.ModelSerializer):
    created_by = UserSerializer()
    lead_assigned_to = ProfileSerializer(read_only=True, many=True)
    tags = serializers.SerializerMethodField()
    org = OrganizationSerializer()

    @extend_schema_field(list)
    def get_tags(self, obj):
        return obj.tags.all().values()

    class Meta:
        model = APISettings
        fields = [
            "title",
            "apikey",
            "website",
            "created_at",
            "created_by",
            "lead_assigned_to",
            "tags",
            "org",
        ]


class APISettingsSwaggerSerializer(serializers.ModelSerializer):
    class Meta:
        model = APISettings
        fields = [
            "title",
            "website",
            "lead_assigned_to",
            "tags",
        ]


class DocumentCreateSwaggerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = [
            "title",
            "document_file",
            "teams",
            "shared_to",
        ]


class DocumentEditSwaggerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ["title", "document_file", "teams", "shared_to", "status"]


class UserCreateSwaggerSerializer(serializers.Serializer):
    """
    It is swagger for creating or updating user
    """

    ROLE_CHOICES = ["ADMIN", "USER"]

    email = serializers.CharField(max_length=1000, required=True)
    role = serializers.ChoiceField(choices=ROLE_CHOICES, required=True)
    phone = serializers.CharField(max_length=12)
    alternate_phone = serializers.CharField(max_length=12)
    address_line = serializers.CharField(max_length=10000, required=True)
    street = serializers.CharField(max_length=1000)
    city = serializers.CharField(max_length=1000)
    state = serializers.CharField(max_length=1000)
    pincode = serializers.CharField(max_length=1000)
    country = serializers.CharField(max_length=1000)


class UserUpdateStatusSwaggerSerializer(serializers.Serializer):

    STATUS_CHOICES = ["Active", "Inactive"]

    status = serializers.ChoiceField(choices=STATUS_CHOICES, required=True)


# JWT Authentication Serializers for SvelteKit Integration


class LoginSerializer(serializers.Serializer):
    """Serializer for user login with email and password"""

    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        if email and password:
            user = authenticate(username=email, password=password)
            if not user:
                raise serializers.ValidationError("Invalid email or password")
            if not user.is_active:
                raise serializers.ValidationError("User account is disabled")
        else:
            raise serializers.ValidationError('Must include "email" and "password"')

        attrs["user"] = user
        return attrs


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""

    password = serializers.CharField(write_only=True, required=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ["email", "password", "confirm_password"]

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"password": "Password fields didn't match."}
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop("confirm_password")
        user = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            is_active=False,  # User needs to activate account
        )
        return user


class UserDetailSerializer(serializers.ModelSerializer):
    """Detailed user serializer with profile and organizations"""

    organizations = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "email", "profile_pic", "is_active", "organizations"]

    @extend_schema_field(list)
    def get_organizations(self, obj):
        """Get all organizations the user belongs to"""
        profiles = Profile.objects.filter(user=obj, is_active=True)
        return [
            {
                "id": str(profile.org.id),
                "name": profile.org.name,
                "role": profile.role,
                "is_organization_admin": profile.is_organization_admin,
                "has_sales_access": profile.has_sales_access,
                "has_marketing_access": profile.has_marketing_access,
            }
            for profile in profiles
        ]


class ProfileDetailSerializer(serializers.ModelSerializer):
    """Detailed profile serializer for authenticated user"""

    user = UserSerializer(read_only=True)
    org = OrganizationSerializer(read_only=True)

    class Meta:
        model = Profile
        fields = [
            "id",
            "user",
            "org",
            "role",
            "is_organization_admin",
            "has_sales_access",
            "has_marketing_access",
            "phone",
            "date_of_joining",
            "is_active",
        ]


# Activity Serializers for Dashboard Recent Activities


class ActivityUserSerializer(serializers.Serializer):
    """Simplified user info for activity display"""

    id = serializers.UUIDField(source="user.id")
    email = serializers.EmailField(source="user.email")
    name = serializers.SerializerMethodField()
    profile_pic = serializers.CharField(source="user.profile_pic", allow_null=True)

    @extend_schema_field(str)
    def get_name(self, obj):
        """Get display name from email"""
        return obj.user.email.split("@")[0]


class ActivitySerializer(serializers.ModelSerializer):
    """Serializer for recent activities"""

    user = ActivityUserSerializer(read_only=True)
    action_display = serializers.CharField(source="get_action_display", read_only=True)
    timestamp = serializers.DateTimeField(source="created_at", read_only=True)
    humanized_time = serializers.CharField(source="created_on_arrow", read_only=True)

    class Meta:
        model = Activity
        fields = [
            "id",
            "user",
            "action",
            "action_display",
            "entity_type",
            "entity_id",
            "entity_name",
            "description",
            "timestamp",
            "humanized_time",
        ]


class TeamsSerializer(serializers.ModelSerializer):
    users = ProfileSerializer(read_only=True, many=True)
    created_by = UserSerializer()

    class Meta:
        model = Teams
        fields = (
            "id",
            "name",
            "description",
            "users",
            "created_at",
            "created_by",
        )


class TeamCreateSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        request_obj = kwargs.pop("request_obj", None)
        super().__init__(*args, **kwargs)
        self.org = request_obj.profile.org

        self.fields["name"].required = True
        self.fields["description"].required = False

    def validate_name(self, name):
        if self.instance:
            if (
                Teams.objects.filter(name__iexact=name, org=self.org)
                .exclude(id=self.instance.id)
                .exists()
            ):
                raise serializers.ValidationError("Team already exists with this name")
        else:
            if Teams.objects.filter(name__iexact=name).exists():
                raise serializers.ValidationError("Team already exists with this name")
        return name

    class Meta:
        model = Teams
        fields = (
            "name",
            "description",
            "created_at",
            "created_by",
            "org",
        )


class TeamswaggerCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Teams
        fields = (
            "name",
            "description",
            "users",
        )
