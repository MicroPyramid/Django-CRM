from rest_framework import serializers

from emails.models import Email


class EmailSerailizer(serializers.ModelSerializer):
    class Meta:
        model = Email
        fields = "__all__"
