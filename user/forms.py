from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate
from common.models import User

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
