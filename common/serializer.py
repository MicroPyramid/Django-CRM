import re
from rest_framework import serializers
from common.models import (
    User,
    Company,
    Comment,
    Address,
    Attachments,
    Document,
    APISettings,
)
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ("id", "name", "address", "sub_domain", "user_limit", "country")


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "file_prepend",
            "username",
            "first_name",
            "last_name",
            "email",
            "is_active",
            "is_admin",
            "is_staff",
            "date_joined",
            "role",
            "profile_pic",
            "has_sales_access",
            "has_marketing_access",
            # "get_app_name",
        )


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = (
            "id",
            "comment",
            "commented_on",
            "commented_by",
            "account",
            "lead",
            "opportunity",
            "contact",
            "case",
            "task",
            "invoice",
            "event",
            "user",
        )


class LeadCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = (
            "id",
            "comment",
            "commented_on",
            "commented_by",
            "lead",
        )


class RegisterUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField()

    class Meta:
        model = User
        fields = (
            "email",
            "username",
            "password",
        )

    def __init__(self, *args, **kwargs):
        self.request_user = kwargs.pop("request_user", None)
        super(RegisterUserSerializer, self).__init__(*args, **kwargs)
        if not self.instance:
            self.fields["password"].required = True
        else:
            self.fields["password"].required = False

    def validate_password(self, password):
        if password:
            if len(password) < 4:
                raise serializers.ValidationError(
                    "Password must be at least 4 characters long!"
                )
        return password

    def validate_username(self, username):
        if not username[0].isalpha():
            raise serializers.ValidationError("Username should start with Alphabet")
        if User.objects.filter(username__iexact=username).exists():
            raise serializers.ValidationError("Username already exist")
        return username


class CreateUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField()

    class Meta:
        model = User
        fields = (
            "email",
            "first_name",
            "last_name",
            "username",
            "role",
            "profile_pic",
            "has_sales_access",
            "has_marketing_access",
            "password",
        )

    def __init__(self, *args, **kwargs):
        self.request_user = kwargs.pop("request_user", None)
        super(CreateUserSerializer, self).__init__(*args, **kwargs)
        self.fields["first_name"].required = True
        if not self.instance:
            self.fields["password"].required = True
        else:
            self.fields["password"].required = False
            self.fields["email"].required = False
            self.fields["role"].required = False

    def validate_password(self, password):
        if password:
            if len(password) < 4:
                raise serializers.ValidationError(
                    "Password must be at least 4 characters long!"
                )
        return password

    def validate_has_sales_access(self, has_sales_access):
        user_role = self.initial_data.get("role")
        if user_role == "ADMIN":
            is_admin = True
        else:
            is_admin = False
        if self.request_user.role == "ADMIN" or self.request_user.is_superuser:
            if not is_admin:
                marketing = self.initial_data.get("has_marketing_access", False)
                if not has_sales_access and not marketing:
                    raise serializers.ValidationError("Select atleast one option.")
        if self.request_user.role == "USER":
            has_sales_access = self.instance.has_sales_access
        return has_sales_access

    def validate_has_marketing_access(self, marketing):
        if self.request_user.role == "USER":
            marketing = self.instance.has_marketing_access
        return marketing

    def validate_email(self, email):
        if self.instance:
            if self.instance.email != email:
                if not User.objects.filter(email=email).exists():
                    return email
                raise serializers.ValidationError("Email already exists")
            else:
                return email
        else:
            if not User.objects.filter(email=email).exists():
                return email
            raise serializers.ValidationError("User already exists with this email")


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.CharField(max_length=200)

    def validate(self, data):
        email = data.get("email")
        user = User.objects.filter(email__iexact=email).last()
        if not user:
            raise serializers.ValidationError(
                "You don't have an account. Please create one."
            )
        return data


class CheckTokenSerializer(serializers.Serializer):
    uidb64_regex = r"[0-9A-Za-z_\-]+"
    token_regex = r"[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20}"
    uidb64 = serializers.RegexField(uidb64_regex)
    token = serializers.RegexField(token_regex)
    error_message = {"__all__": ("Invalid password reset token")}

    def get_user(self, uidb64):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User._default_manager.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None
        return user


class ResetPasswordSerailizer(CheckTokenSerializer):
    new_password1 = serializers.CharField()
    new_password2 = serializers.CharField()

    def validate(self, data):
        self.user = self.get_user(data.get("uid"))
        if not self.user:
            raise serializers.ValidationError(self.error_message)
        is_valid_token = default_token_generator.check_token(
            self.user, data.get("token")
        )
        if not is_valid_token:
            raise serializers.ValidationError(self.error_message)
        new_password2 = data.get("new_password2")
        new_password1 = data.get("new_password1")
        if new_password1 != new_password2:
            raise serializers.ValidationError("The two password fields didn't match.")
        return new_password2


class AttachmentsSerializer(serializers.ModelSerializer):
    file_path = serializers.SerializerMethodField()

    def get_file_path(self, obj):
        if obj.attachment:
            return obj.attachment.url
        None

    class Meta:
        model = Attachments
        fields = ["id", "created_by", "file_name", "created_on", "file_path"]


class BillingAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ("address_line", "street", "city", "state", "postcode", "country")

    def __init__(self, *args, **kwargs):
        account_view = kwargs.pop("account", False)

        super(BillingAddressSerializer, self).__init__(*args, **kwargs)

        if account_view:
            self.fields["address_line"].required = True
            self.fields["street"].required = True
            self.fields["city"].required = True
            self.fields["state"].required = True
            self.fields["postcode"].required = True
            self.fields["country"].required = True


class DocumentSerializer(serializers.ModelSerializer):
    shared_to = UserSerializer(read_only=True, many=True)
    teams = serializers.SerializerMethodField()
    created_by = UserSerializer()

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
            "created_on",
            "created_by",
        ]


class DocumentCreateSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        request_obj = kwargs.pop("request_obj", None)
        super(DocumentCreateSerializer, self).__init__(*args, **kwargs)
        self.fields["title"].required = True

    def validate_title(self, title):
        if self.instance:
            if (
                Document.objects.filter(title__iexact=title)
                .exclude(id=self.instance.id)
                .exists()
            ):
                raise serializers.ValidationError(
                    "Document with this Title already exists"
                )
        else:
            if Document.objects.filter(title__iexact=title).exists():
                raise serializers.ValidationError(
                    "Document with this Title already exists"
                )
        return title

    class Meta:
        model = Document
        fields = [
            "title",
            "document_file",
            "status",
        ]


def find_urls(string):
    # website_regex = "^((http|https)://)?([A-Za-z0-9.-]+\.[A-Za-z]{2,63})?$"  # (http(s)://)google.com or google.com
    # website_regex = "^https?://([A-Za-z0-9.-]+\.[A-Za-z]{2,63})?$"  # (http(s)://)google.com
    # http(s)://google.com
    website_regex = "^https?://[A-Za-z0-9.-]+\.[A-Za-z]{2,63}$"
    # http(s)://google.com:8000
    website_regex_port = "^https?://[A-Za-z0-9.-]+\.[A-Za-z]{2,63}:[0-9]{2,4}$"
    url = re.findall(website_regex, string)
    url_port = re.findall(website_regex_port, string)
    if url and url[0] != "":
        return url
    return url_port


class APISettingsSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        super(APISettingsSerializer, self).__init__(*args, **kwargs)

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
    lead_assigned_to = UserSerializer(read_only=True, many=True)
    tags = serializers.SerializerMethodField()

    def get_tags(self, obj):
        return obj.tags.all().values()

    class Meta:
        model = APISettings
        fields = [
            "title",
            "apikey",
            "website",
            "created_on",
            "created_by",
            "lead_assigned_to",
            "tags",
        ]
