from django import forms
from django.db.models import Q

from accounts.models import Account
from common.models import Address, Attachments, Comment, User
from invoices.models import Invoice
from teams.models import Teams


class InvoiceForm(forms.ModelForm):
    teams_queryset = []
    teams = forms.MultipleChoiceField(choices=teams_queryset)

    def __init__(self, *args, **kwargs):
        request_user = kwargs.pop("request_user", None)
        request_obj = kwargs.pop("request_obj", None)
        assigned_users = kwargs.pop("assigned_to", [])
        super(InvoiceForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs = {"class": "form-control"}
            field.required = False

        if request_user.role == "ADMIN" or request_user.is_superuser:
            self.fields["assigned_to"].queryset = User.objects.filter(
                is_active=True, company=request_obj.company
            )
            self.fields["teams"].choices = [
                (team.get("id"), team.get("name"))
                for team in Teams.objects.filter(company=request_obj.company).values(
                    "id", "name"
                )
            ]
            self.fields["accounts"].queryset = Account.objects.filter(
                status="open", company=request_obj.company
            )
        # elif request_user.google.all():
        #     self.fields['assigned_to'].queryset = User.objects.none()
        #     self.fields['accounts'].queryset = Account.objects.filter(status='open').filter(
        #         Q(created_by=request_user) | Q(assigned_to=request_user))
        elif request_user.role == "USER":
            self.fields["assigned_to"].queryset = User.objects.filter(
                role="ADMIN", company=request_obj.company
            )
            self.fields["accounts"].queryset = Account.objects.filter(
                status="open",
                company=request_obj.company,
            ).filter(Q(created_by=request_user) | Q(assigned_to=request_user))
        else:
            pass

        self.fields["teams"].required = False
        self.fields["phone"].widget.attrs.update({"placeholder": "+911234567890"})
        self.fields["invoice_title"].required = True
        self.fields["currency"].required = True
        self.fields["email"].required = True
        self.fields["total_amount"].required = True
        self.fields["due_date"].required = True
        self.fields["accounts"].required = False

    def clean_quantity(self):
        quantity = self.cleaned_data.get("quantity")

        if quantity in [None, ""]:
            raise forms.ValidationError("This field is required")

        return quantity

    class Meta:
        model = Invoice
        fields = (
            "invoice_title",
            "from_address",
            "to_address",
            "name",
            "email",
            "phone",
            "status",
            "assigned_to",
            "quantity",
            "rate",
            "total_amount",
            "currency",
            "details",
            "due_date",
            "accounts",
            "tax",
        )


class InvoiceCommentForm(forms.ModelForm):
    comment = forms.CharField(max_length=255, required=True)

    class Meta:
        model = Comment
        fields = ("comment", "task", "commented_by")


class InvoiceAttachmentForm(forms.ModelForm):
    attachment = forms.FileField(max_length=1001, required=True)

    class Meta:
        model = Attachments
        fields = ("attachment", "task")


class InvoiceAddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ("address_line", "street", "city", "state", "postcode", "country")

    def __init__(self, *args, **kwargs):
        super(InvoiceAddressForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs = {"class": "form-control"}
        self.fields["address_line"].widget.attrs.update({"placeholder": "Address Line"})
        self.fields["street"].widget.attrs.update({"placeholder": "Street"})
        self.fields["city"].widget.attrs.update({"placeholder": "City"})
        self.fields["state"].widget.attrs.update({"placeholder": "State"})
        self.fields["postcode"].widget.attrs.update({"placeholder": "Postcode"})
        self.fields["country"].choices = [("", "--Country--"),] + list(
            self.fields["country"].choices
        )[1:]
