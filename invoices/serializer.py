from rest_framework import serializers
from invoices.models import Invoice


class InvoiceSerailizer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = "__all__"
