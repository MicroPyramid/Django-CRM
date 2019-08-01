from django import forms
from teams.models import Teams
from common.models import User


class TeamForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(TeamForm, self).__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs = {"class": "form-control"}

        self.fields['name'].required = True
        self.fields['description'].required = False
        self.fields['users'].required = True
        self.fields['users'].queryset = User.objects.filter(is_active=True)

    class Meta:
        model = Teams
        fields = ('name', 'description', 'users',)

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if Teams.objects.filter(name__iexact=name).exclude(id=self.instance.id).exists():
            raise forms.ValidationError('Team with this name already exists.')
        return name
