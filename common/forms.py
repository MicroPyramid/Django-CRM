from django import forms
from django.contrib.auth import authenticate

from common.models import Address, User


class BillingAddressForm(forms.ModelForm):

    class Meta:
        model = Address
        fields = ('address_line', 'street', 'city', 'state', 'postcode', 'country')

    def __init__(self, *args, **kwargs):
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
        self.fields["country"].choices = [("", "--Country--"), ] + list(self.fields["country"].choices)[1:]


class ShippingAddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ('address_line', 'street', 'city', 'state', 'postcode', 'country')

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
        self.fields["country"].choices = [("", "--Country--"), ] + list(self.fields["country"].choices)[1:]


class UserForm(forms.ModelForm):

    password = forms.CharField(max_length=100, required=False)

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'username', 'role', 'profile_pic']

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)

        self.fields['first_name'].required = True
        self.fields['username'].required = True
        self.fields['email'].required = True

        if not self.instance.pk:
            self.fields['password'].required = True

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if password:
            if len(password) < 4:
                raise forms.ValidationError(
                    'Password must be at least 4 characters long!')
        return password

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if self.instance.id:
            if self.instance.email != email:
                if not User.objects.filter(email=self.cleaned_data.get("email")).exists():
                    return self.cleaned_data.get("email")
                else:
                    raise forms.ValidationError('Email already exists')
            else:
                return self.cleaned_data.get("email")
        else:
            if not User.objects.filter(email=self.cleaned_data.get("email")).exists():
                    return self.cleaned_data.get("email")
            else:
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

    def clean(self):
        email = self.cleaned_data.get("email")
        password = self.cleaned_data.get("password")

        if email and password:
            self.user = authenticate(email=email, password=password)
            if self.user:
                if not self.user.is_active:
                    raise forms.ValidationError("User is Inactive")
            else:
                raise forms.ValidationError("Invalid email and password")
        return self.cleaned_data


class ChangePasswordForm(forms.Form):
    CurrentPassword = forms.CharField(max_length=100)
    Newpassword = forms.CharField(max_length=100)
    confirm = forms.CharField(max_length=100)

    def __init__(self, *args, **kwargs):
        super(ChangePasswordForm, self).__init__(*args, **kwargs)

    def clean_confirm(self):
        if len(self.data.get('confirm')) < 4:
            raise forms.ValidationError(
                'Password must be at least 4 characters long!')
        if self.data.get('confirm') != self.cleaned_data.get('Newpassword'):
            raise forms.ValidationError(
                'Confirm password do not match with new password')
        return self.data.get('confirm')
