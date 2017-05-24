from django import forms
from oppurtunity.models import Opportunity, Comments


class OpportunityForm(forms.ModelForm):
    class Meta:
        model = Opportunity
        fields = "__all__"


class CommentForm(forms.ModelForm):

    class Meta:
        model = Comments
        fields = ['comment', ]
