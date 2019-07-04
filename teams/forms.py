from django import forms
from teams.models import Teams


class TeamForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(TeamForm, self).__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs = {"class": "form-control"}

        self.fields['name'].required = True
        self.fields['description'].required = True
        self.fields['users'].required = False

    class Meta:
        model = Teams
        fields = ('name', 'description', 'users',)
