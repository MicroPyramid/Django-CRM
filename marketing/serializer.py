from rest_framework import serializers
from .models import (
    ContactEmailCampaign,
    BlockedDomain,
    BlockedEmail,
)
from common.serializer import UserSerializer, CompanySerializer
import re


class ContactEmailCampaignSerailizer(serializers.ModelSerializer):
    created_by = UserSerializer()
    company = CompanySerializer()

    def __init__(self, *args, **kwargs):
        request_obj = kwargs.pop("request_obj", None)
        super(ContactEmailCampaignSerailizer, self).__init__(*args, **kwargs)
        self.fields["name"].required = False
        self.fields["created_by"].required = False
        self.fields["company"].required = False

    class Meta:
        model = ContactEmailCampaign
        fields = (
            "id",
            "name",
            "last_name",
            "email",
            "created_on",
            "created_by",
            "company",
        )


class BlockedDomainAddSerailizer(serializers.ModelSerializer):
    created_by = UserSerializer()
    company = CompanySerializer()

    def __init__(self, *args, **kwargs):
        request_obj = kwargs.pop("request_obj", None)
        super(BlockedDomainAddSerailizer, self).__init__(*args, **kwargs)
        self.fields["created_by"].required = False
        self.fields["company"].required = False
        self.company = request_obj.company

    def validate_domain(self, domain):
        domain_regex = "^([a-z0-9]+(-[a-z0-9]+)*\.)+[a-z]{2,}$"
        if re.match(domain_regex, domain) is None:
            raise serializers.ValidationError("Enter a valid domain.")
        if self.instance:
            if (
                BlockedDomain.objects.filter(
                    domain__iexact=domain, company=self.company
                )
                .exclude(id=self.instance.id)
                .exists()
            ):
                raise serializers.ValidationError(
                    "Domain already exists with this name"
                )
        else:
            if BlockedDomain.objects.filter(
                domain__iexact=domain, company=self.company
            ).exists():
                raise serializers.ValidationError(
                    "Domain already exists with this name"
                )
        return domain

    class Meta:
        model = BlockedDomain
        fields = ("id", "domain", "created_on", "created_by", "company")


class BlockedEmailAddSerailizer(serializers.ModelSerializer):
    created_by = UserSerializer()
    company = CompanySerializer()
    email = serializers.EmailField

    def __init__(self, *args, **kwargs):
        request_obj = kwargs.pop("request_obj", None)
        super(BlockedEmailAddSerailizer, self).__init__(*args, **kwargs)
        self.fields["created_by"].required = False
        self.fields["company"].required = False
        self.company = request_obj.company

    def validate_email(self, email):
        if self.instance:
            if (
                BlockedEmail.objects.filter(email=email, company=self.company)
                .exclude(id=self.instance.id)
                .exists()
            ):
                raise serializers.ValidationError("Email already exists")
        else:
            if BlockedEmail.objects.filter(email=email, company=self.company).exists():
                raise serializers.ValidationError("email already exists")
        return email

    class Meta:
        model = BlockedEmail
        fields = ("id", "email", "created_on", "created_by", "company")


class BlockedDomainSerailizer(serializers.ModelSerializer):
    created_by = UserSerializer()
    company = CompanySerializer()

    class Meta:
        model = BlockedDomain
        fields = ("id", "domain", "created_on", "created_by", "company")


class BlockedEmailSerailizer(serializers.ModelSerializer):
    created_by = UserSerializer()
    company = CompanySerializer()
    email = serializers.EmailField

    class Meta:
        model = BlockedEmail
        fields = ("id", "email", "created_on", "created_by", "company")
