from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import check_password
from django.contrib.auth.forms import PasswordChangeForm
#from common.models import User
from .models import User

class PasswordForm(forms.Form):
    #TODO will need to write a bigger policy on passwords
    #TODO also need to add a old password container so that we could check if the user has the original password
    password = forms.CharField(widget=forms.PasswordInput)
    password1 = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(PasswordForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs = {"class": "form-control"}
        self.fields['password'].required = True
        self.fields['password1'].required = True
        self.fields['password1'].label = "Confirm password"
        # if self.fields['password2']:
        #     self.fields['password2'].label = "old password"

    def clean(self):
        password = self.cleaned_data.get('password')
        password1 = self.cleaned_data.get('password1')
        if password != password1:
            raise forms.ValidationError('Passwords does not match each other')
        elif len(password) < 4:
            raise forms.ValidationError('Password must be at least 4 characters long!')
        return password1

class ResetPassForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super(ResetPassForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs = {"class": "form-control"}

class LoginForm(forms.ModelForm):
    email = forms.TextInput()
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['email', 'password']


    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super(LoginForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs = {"class": "form-control"}

    def clean(self):
        email = self.cleaned_data.get("email")
        password = self.cleaned_data.get("password")

        if email and password:
            self.user = authenticate(email=email, password=password)
            if self.user is not None:
                pass
            else:
                raise ValidationError('Invalid email and password')

class UserForm(forms.ModelForm):
    # password = forms.CharField(max_length=100, required=True)
    required_css_class = 'required'
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'username']

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs = {"class": "form-control"}
        self.fields['first_name'].required = True
        self.fields['username'].required = True
        self.fields['email'].required = True

        # if not self.instance.pk:
        #     self.fields['password'].required = True

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
