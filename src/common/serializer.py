import re
from django.contrib.auth.hashers import check_password
from rest_framework import serializers
from common.models import (
    User,
    Org,
    Comment,
    Address,
    Attachments,
    Document,
    APISettings,
    Profile
)
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Org
        fields = ("id", "name")


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
            "profile",
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


class RegisterOrganizationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=255)
    password = serializers.CharField(max_length=100)
    org_name = serializers.CharField(max_length=100)

    def validate_password(self, password):
        if password:
            if len(password) < 4:
                raise serializers.ValidationError(
                    "Password must be at least 4 characters long!"
                )
        return password

    def validate_email(self, email):
        org_name = self.initial_data.get('org_name')
        if Profile.objects.filter(user__email__iexact=email,
                                  org__name=org_name).exists():
            raise serializers.ValidationError(
                "This email is already registered in this organization")
        return email

    def validate_org_name(self, org_name):
        if bool(re.search(r"[~\!_.@#\$%\^&\*\ \(\)\+{}\":;'/\[\]]", org_name)):
            raise serializers.ValidationError(
                "organization name should not contain any special characters")
        if Org.objects.filter(name=org_name).exists():
            raise serializers.ValidationError(
                "Organization already exists with this name")
        return org_name


class BillingAddressSerializer(serializers.ModelSerializer):
    country = serializers.SerializerMethodField()

    def get_country(self, obj):
        return obj.get_country_display()

    class Meta:
        model = Address
        fields = ("address_line", "street", "city",
                  "state", "postcode", "country")

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
    password = serializers.CharField()

    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "email",
            "alternate_email",
            "skype_ID",
            "description",
            "profile_pic",
            "password",
        )

    def __init__(self, *args, **kwargs):
        self.org = kwargs.pop("org", None)
        super().__init__(*args, **kwargs)
        self.fields["first_name"].required = True
        self.fields["password"].required = False
        self.fields["profile_pic"].required = False
        self.fields["skype_ID"].required = False

    def validate_email(self, email):
        if self.instance:
            if self.instance.email != email:
                if not Profile.objects.filter(
                        user__email=email, org=self.org).exists():
                    return email
                raise serializers.ValidationError("Email already exists")
            return email
        if not Profile.objects.filter(user__email=email.lower(), org=self.org).exists():
            return email
        raise serializers.ValidationError('Given Email id already exists')


class CreateProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = Profile
        fields = (
            "role",
            "phone",
            "alternate_phone",
            "has_sales_access",
            "has_marketing_access",
            "is_organization_admin"
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["alternate_phone"].required = False
        self.fields["role"].required = True
        self.fields["phone"].required = True


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = (
            "id",
            "first_name",
            "last_name",
            "email",
            "alternate_email",
            "skype_ID",
            "description",
            "profile_pic",
        )


class ProfileSerializer(serializers.ModelSerializer):
    user_details = serializers.SerializerMethodField()
    address = BillingAddressSerializer()

    def get_user_details(self, obj):
        return UserSerializer(obj.user).data

    class Meta:
        model = Profile
        fields = ("id", 'user_details', 'role', 'address',
                  'has_marketing_access', 'has_sales_access',
                  'phone', 'date_of_joining', 'is_active')


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
            raise serializers.ValidationError(
                "The two password fields didn't match.")
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


class DocumentSerializer(serializers.ModelSerializer):
    shared_to = ProfileSerializer(read_only=True, many=True)
    teams = serializers.SerializerMethodField()
    created_by = ProfileSerializer()
    org = OrganizationSerializer()

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
            "org"
        ]


class DocumentCreateSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        request_obj = kwargs.pop("request_obj", None)
        super().__init__(*args, **kwargs)
        self.fields["title"].required = True
        self.org = request_obj.org

    def validate_title(self, title):
        if self.instance:
            if (
                Document.objects.filter(
                    title__iexact=title, org=self.org)
                .exclude(id=self.instance.id)
                .exists()
            ):
                raise serializers.ValidationError(
                    "Document with this Title already exists"
                )
        if Document.objects.filter(title__iexact=title, org=self.org).exists():
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
            "org"
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
    created_by = ProfileSerializer()
    lead_assigned_to = ProfileSerializer(read_only=True, many=True)
    tags = serializers.SerializerMethodField()
    org = OrganizationSerializer()

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
            "org"
        ]


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(max_length=100)
    new_password = serializers.CharField(max_length=100)
    retype_password = serializers.CharField(max_length=100)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def validate_old_password(self, pwd):
        if not check_password(pwd, self.context.get('user').password):
            raise serializers.ValidationError(
                "old password entered is incorrect.")
        return pwd

    def validate(self, data):
        if len(data.get('new_password')) < 8:
            raise serializers.ValidationError(
                "Password must be at least 8 characters long!")
        if data.get('new_password') == data.get('old_password'):
            raise serializers.ValidationError(
                "New_password and old password should not be the same")
        if data.get('new_password') != data.get('retype_password'):
            raise serializers.ValidationError(
                "New_password and Retype_password did not match.")
        return data
