import re
from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import PasswordResetForm
from common.models import Address, User, Document, Comment, APISettings
from django.contrib.auth import password_validation
from teams.models import Teams


class BillingAddressForm(forms.ModelForm):

    class Meta:
        model = Address
        fields = ('address_line', 'street', 'city',
                  'state', 'postcode', 'country')

    def __init__(self, *args, **kwargs):
        account_view = kwargs.pop('account', False)

        super(BillingAddressForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs = {"class": "form-control"}
        self.fields['address_line'].widget.attrs.update({
            'placeholder': 'Address Line'})
        self.fields['street'].widget.attrs.update({
            'placeholder': 'Street'})
        self.fields['city'].widget.attrs.update({
            'placeholder': 'City'})
        self.fields['state'].widget.attrs.update({
            'placeholder': 'State'})
        self.fields['postcode'].widget.attrs.update({
            'placeholder': 'Postcode'})
        self.fields["country"].choices = [
            ("", "--Country--"), ] + list(self.fields["country"].choices)[1:]

        if account_view:
            self.fields['address_line'].required = True
            self.fields['street'].required = True
            self.fields['city'].required = True
            self.fields['state'].required = True
            self.fields['postcode'].required = True
            self.fields['country'].required = True


class ShippingAddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ('address_line', 'street', 'city',
                  'state', 'postcode', 'country')

    def __init__(self, *args, **kwargs):
        super(ShippingAddressForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs = {"class": "form-control"}
        self.fields['address_line'].widget.attrs.update({
            'placeholder': 'Address Line'})
        self.fields['street'].widget.attrs.update({
            'placeholder': 'Street'})
        self.fields['city'].widget.attrs.update({
            'placeholder': 'City'})
        self.fields['state'].widget.attrs.update({
            'placeholder': 'State'})
        self.fields['postcode'].widget.attrs.update({
            'placeholder': 'Postcode'})
        self.fields["country"].choices = [
            ("", "--Country--"), ] + list(self.fields["country"].choices)[1:]


class UserForm(forms.ModelForm):

    password = forms.CharField(max_length=100, required=False)
    # sales = forms.BooleanField(required=False)
    # marketing = forms.BooleanField(required=False)

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name',
                  'username', 'role', 'profile_pic',
                  'has_sales_access', 'has_marketing_access']

    def __init__(self, *args, **kwargs):
        self.request_user = kwargs.pop('request_user', None)
        super(UserForm, self).__init__(*args, **kwargs)
        self.fields['first_name'].required = True
        if not self.instance.pk:
            self.fields['password'].required = True

        # self.fields['password'].required = True

    # def __init__(self, args: object, kwargs: object) -> object:
    #     super(UserForm, self).__init__(*args, **kwargs)
    #
    #     self.fields['first_name'].required = True
    #     self.fields['username'].required = True
    #     self.fields['email'].required = True
    #
        # if not self.instance.pk:
        #     self.fields['password'].required = True

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if password:
            if len(password) < 4:
                raise forms.ValidationError(
                    'Password must be at least 4 characters long!')
        return password

    def clean_has_sales_access(self):
        sales = self.cleaned_data.get('has_sales_access', False)
        user_role = self.cleaned_data.get('role')
        if user_role == 'ADMIN':
            is_admin = True
        else:
            is_admin = False
        if self.request_user.role == 'ADMIN' or self.request_user.is_superuser:
            if not is_admin:
                marketing = self.data.get('has_marketing_access', False)
                if not sales and not marketing:
                    raise forms.ValidationError('Select atleast one option.')
            # if not (self.instance.role == 'ADMIN' or self.instance.is_superuser):
            #     marketing = self.data.get('has_marketing_access', False)
            #     if not sales and not marketing:
            #         raise forms.ValidationError('Select atleast one option.')
        if self.request_user.role == 'USER':
            sales = self.instance.has_sales_access
        return sales

    def clean_has_marketing_access(self):
        marketing = self.cleaned_data.get('has_marketing_access', False)
        if self.request_user.role == 'USER':
            marketing = self.instance.has_marketing_access
        return marketing

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if self.instance.id:
            if self.instance.email != email:
                if not User.objects.filter(
                        email=self.cleaned_data.get("email")).exists():
                    return self.cleaned_data.get("email")
                raise forms.ValidationError('Email already exists')
            else:
                return self.cleaned_data.get("email")
        else:
            if not User.objects.filter(
                    email=self.cleaned_data.get("email")).exists():
                return self.cleaned_data.get("email")
            raise forms.ValidationError('User already exists with this email')


class LoginForm(forms.ModelForm):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['email', 'password']

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super(LoginForm, self).__init__(*args, **kwargs)

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if password:
            if len(password) < 4:
                raise forms.ValidationError(
                    'Password must be at least 4 characters long!')
        return password

    def clean(self):
        email = self.cleaned_data.get("email")
        password = self.cleaned_data.get("password")

        if email and password:
            self.user = authenticate(username=email, password=password)
            if self.user:
                if not self.user.is_active:
                    pass
                    # raise forms.ValidationError("User is Inactive")
            else:
                pass
                # raise forms.ValidationError("Invalid email and password")
        return self.cleaned_data


class ChangePasswordForm(forms.Form):
    # CurrentPassword = forms.CharField(max_length=100)
    Newpassword = forms.CharField(max_length=100)
    confirm = forms.CharField(max_length=100)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(ChangePasswordForm, self).__init__(*args, **kwargs)

    def clean_confirm(self):
        # if len(self.data.get('confirm')) < 4:
        #     raise forms.ValidationError(
        #         'Password must be at least 4 characters long!')
        if self.data.get('confirm') != self.cleaned_data.get('Newpassword'):
            raise forms.ValidationError(
                'Confirm password do not match with new password')
        password_validation.validate_password(
            self.cleaned_data.get('Newpassword'), user=self.user)
        return self.data.get('confirm')


class PasswordResetEmailForm(PasswordResetForm):

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not User.objects.filter(email__iexact=email,
                                   is_active=True).exists():
            raise forms.ValidationError("User doesn't exist with this Email")
        return email


class DocumentForm(forms.ModelForm):
    teams_queryset = []
    teams = forms.MultipleChoiceField(choices=teams_queryset)

    def __init__(self, *args, **kwargs):
        self.instance = kwargs.get('instance', None)
        users = kwargs.pop('users', [])
        super(DocumentForm, self).__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs = {"class": "form-control"}

        self.fields['status'].choices = [
            (each[0], each[1]) for each in Document.DOCUMENT_STATUS_CHOICE]
        self.fields['status'].required = False
        self.fields['title'].required = True
        if users:
            self.fields['shared_to'].queryset = users
        self.fields['shared_to'].required = False
        self.fields["teams"].choices = [(team.get('id'), team.get('name')) for team in Teams.objects.all().values('id', 'name')]
        self.fields["teams"].required = False

    class Meta:
        model = Document
        fields = ['title', 'document_file', 'status', 'shared_to']

    def clean_title(self):
        title = self.cleaned_data.get('title')
        if not self.instance.id:
            if Document.objects.filter(title=title).exists():
                raise forms.ValidationError(
                    'Document with this Title already exists')
                return title
        if Document.objects.filter(title=title).exclude(id=self.instance.id).exists():
            raise forms.ValidationError(
                'Document with this Title already exists')
            return title
        return title


class UserCommentForm(forms.ModelForm):
    comment = forms.CharField(max_length=64, required=True)

    class Meta:
        model = Comment
        fields = ('comment', 'user', 'commented_by')


def find_urls(string):
    # website_regex = "^((http|https)://)?([A-Za-z0-9.-]+\.[A-Za-z]{2,63})?$"  # (http(s)://)google.com or google.com
    # website_regex = "^https?://([A-Za-z0-9.-]+\.[A-Za-z]{2,63})?$"  # (http(s)://)google.com
    # http(s)://google.com
    website_regex = "^https?://[A-Za-z0-9.-]+\.[A-Za-z]{2,63}$"
    # http(s)://google.com:8000
    website_regex_port = "^https?://[A-Za-z0-9.-]+\.[A-Za-z]{2,63}:[0-9]{2,4}$"
    url = re.findall(website_regex, string)
    url_port = re.findall(website_regex_port, string)
    if url and url[0] != '':
        return url
    return url_port


class APISettingsForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        assigned_users = kwargs.pop('assign_to', [])
        super(APISettingsForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs = {"class": "form-control"}
        self.fields['lead_assigned_to'].queryset = assigned_users
        self.fields['lead_assigned_to'].required = False

        # self.fields['title'].widget.attrs.update({
        #     'placeholder': 'Project Name'})
        # self.fields['lead_assigned_to'].widget.attrs.update({
        #     'placeholder': 'Assign Leads To'})

    class Meta:
        model = APISettings
        fields = ('title', 'lead_assigned_to', 'website')

    def clean_website(self):
        website = self.data.get('website')
        if website and not (website.startswith('http://') or
                            website.startswith('https://')):
            raise forms.ValidationError("Please provide valid schema")
        if not len(find_urls(website)) > 0:
            raise forms.ValidationError(
                "Please provide a valid URL with schema and without trailing slash - Example: http://google.com")
        return website
