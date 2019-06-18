from django.db import models
from django.utils.translation import ugettext_lazy as _
from common.models import Address, User
from common.utils import CURRENCY_CODES
from phonenumber_field.modelfields import PhoneNumberField


class Invoice(models.Model):
    """Model definition for Invoice."""

    INVOICE_STATUS = (
        ('Draft', 'Draft'),
        ('Sent', 'Sent'),
        ('Paid', 'Paid'),
        ('Pending', 'Pending'),
        ('Cancelled', 'Cancel'),
    )

    invoice_title = models.CharField(_('Invoice Title'), max_length=50)
    invoice_number = models.CharField(_('Invoice Number'), max_length=50)
    from_address = models.ForeignKey(
        Address, related_name='invoice_from_address', on_delete=models.SET_NULL, null=True)
    to_address = models.ForeignKey(
        Address, related_name='invoice_to_address', on_delete=models.SET_NULL, null=True)
    name = models.CharField(_('Name'), max_length=100)
    email = models.EmailField(_('Email'))
    assigned_to = models.ManyToManyField(
        User, related_name='invoice_assigned_to')
    # quantity is the number of hours worked
    quantity = models.PositiveIntegerField(default=0)
    # rate is the rate charged
    rate = models.DecimalField(default=0, max_digits=12, decimal_places=2)
    # total amount is product of rate and quantity
    total_amount = models.DecimalField(
        blank=True, null=True, max_digits=12, decimal_places=2)
    currency = models.CharField(
        max_length=3, choices=CURRENCY_CODES, blank=True, null=True)
    phone = PhoneNumberField(null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User, related_name='invoice_created_by',
        on_delete=models.SET_NULL, null=True)

    amount_due = models.DecimalField(
        blank=True, null=True, max_digits=12, decimal_places=2)
    amount_paid = models.DecimalField(
        blank=True, null=True, max_digits=12, decimal_places=2)
    is_email_sent = models.BooleanField(default=False)
    status = models.CharField(choices=INVOICE_STATUS,
                              max_length=15, default="Draft")
    details = models.TextField(_('Details'), null=True, blank=True)
    due_date = models.DateField(blank=True, null=True)

    class Meta:
        """Meta definition for Invoice."""

        verbose_name = 'Invoice'
        verbose_name_plural = 'Invoices'

    def __str__(self):
        """Unicode representation of Invoice."""
        return self.invoice_number

    def formatted_total_amount(self):
        return self.currency + '   ' + str(self.total_amount)

    def formatted_rate(self):
        return self.rate + '   ' + self.currency

    def formatted_total_quantity(self):
        return self.currency + ' ' + 'Hours'

    def is_draft(self):
        if self.status == 'Draft':
            return True
        else:
            return False

    def is_sent(self):
        if self.status == 'Sent' and self.is_email_sent == False:
            return True
        else:
            return False

    def is_resent(self):
        if self.status == 'Sent' and self.is_email_sent == True:
            return True
        else:
            return False

    def is_paid_or_cancelled(self):
        if self.status in ['Paid', 'Cancelled']:
            return True
        else:
            return False
