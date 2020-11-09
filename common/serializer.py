from rest_framework import serializers
from common.models import User, Company, Comment, Address, Attachments
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator


class CompanySerializer(serializers.ModelSerializer):

    class Meta:
        model = Company
        fields = (
            'id',
            "name",
            "address",
            "sub_domain",
            "user_limit",
            "country"
        )


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = (
            'id',
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
            "company",
            "get_app_name"

        )


class CommentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Comment
        fields = "__all__"


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
        )

    def __init__(self, *args, **kwargs):
        self.request_user = kwargs.pop("request_user", None)
        super(CreateUserSerializer, self).__init__(*args, **kwargs)
        self.fields["first_name"].required = True
        if not self.instance.pk:
            self.fields["password"].required = True

        # self.fields['password'].required = True

    def validate_password(self):
        password = self.cleaned_data.get("password")
        if password:
            if len(password) < 4:
                raise serializers.ValidationError(
                    "Password must be at least 4 characters long!"
                )
        return password

    def validate_has_sales_access(self):
        sales = self.cleaned_data.get("has_sales_access", False)
        user_role = self.cleaned_data.get("role")
        if user_role == "ADMIN":
            is_admin = True
        else:
            is_admin = False
        if self.request_user.role == "ADMIN" or self.request_user.is_superuser:
            if not is_admin:
                marketing = self.data.get("has_marketing_access", False)
                if not sales and not marketing:
                    raise serializers.ValidationError(
                        "Select atleast one option.")
            # if not (self.instance.role == 'ADMIN' or self.instance.is_superuser):
            #     marketing = self.data.get('has_marketing_access', False)
            #     if not sales and not marketing:
            #         raise forms.ValidationError('Select atleast one option.')
        if self.request_user.role == "USER":
            sales = self.instance.has_sales_access
        return sales

    def validate_has_marketing_access(self):
        marketing = self.cleaned_data.get("has_marketing_access", False)
        if self.request_user.role == "USER":
            marketing = self.instance.has_marketing_access
        return marketing

    def validate_email(self):
        email = self.cleaned_data.get("email")
        if self.instance.id:
            if self.instance.email != email:
                if not User.objects.filter(
                    email=self.cleaned_data.get("email")
                ).exists():
                    return self.cleaned_data.get("email")
                raise serializers.ValidationError("Email already exists")
            else:
                return self.cleaned_data.get("email")
        else:
            if not User.objects.filter(email=self.cleaned_data.get("email")).exists():
                return self.cleaned_data.get("email")
            raise serializers.ValidationError(
                "User already exists with this email")


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.CharField(max_length=200)

    def validate(self, data):
        email = data.get('email')
        user = User.objects.filter(email__iexact=email).last()
        if not user:
            raise serializers.ValidationError(
                "You don't have an account. Please create one."
            )
        return data


class CheckTokenSerializer(serializers.Serializer):
    uidb64_regex = r'[0-9A-Za-z_\-]+'
    token_regex = r'[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20}'
    uidb64 = serializers.RegexField(uidb64_regex)
    token = serializers.RegexField(token_regex)
    error_message = {'__all__': ('Invalid password reset token')}

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
        self.user = self.get_user(data.get('uidb64'))
        if not self.user:
            raise serializers.ValidationError(self.error_message)
        is_valid_token = default_token_generator.check_token(
            self.user, data.get('token'))
        if not is_valid_token:
            raise serializers.ValidationError(self.error_message)
        new_password2 = data.get('new_password2')
        new_password1 = data.get('new_password1')
        if new_password1 != new_password2:
            raise serializers.ValidationError(
                "The two password fields didn't match.")
        return new_password2


class AttachmentsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Attachments
        fields = ['created_by', 'file_name', 'created_on']


class BillingAddressSerializer(serializers.ModelSerializer):

    class Meta:
        model = Address
        fields = ("address_line", "street", "city",
                  "state", "postcode", "country")

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
