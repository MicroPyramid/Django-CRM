from django import forms
from oppurtunity.models import Opportunity
from common.models import Comment


class OpportunityForm(forms.ModelForm):
    class Meta:
        model = Opportunity
        fields = "__all__"


class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ['comment', ]
