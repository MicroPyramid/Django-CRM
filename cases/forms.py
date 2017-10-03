from django import forms
from cases.models import Case
from common.models import Comment
from accounts.models import Account


class TestTable(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.name


class caseForm(forms.ModelForm):
    account = TestTable(queryset=Account.objects.all())
    name = forms.CharField(max_length=64, required=True)

    class Meta:
        model = Case
        fields = "__all__"
        exclude = ('created', 'userid',)

    def clean_name(self):
        name = self.cleaned_data['name']
        case = Case.objects.filter(name__iexact=name).exclude(id=self.instance.id)
        if case:
            raise forms.ValidationError("Case Already Exists with this Name")
        return name


class CommentForm(forms.ModelForm):
    comment = forms.CharField(max_length=64, required=True)

    class Meta:
        model = Comment
        fields = ['comment', ]
        exclude = ('commented_on', 'commented_by', 'case')
