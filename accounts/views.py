import json
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.views.generic import (
    CreateView, UpdateView, DetailView, TemplateView, View, DeleteView)
from accounts.forms import AccountForm, AccountCommentForm, AccountAttachmentForm
from accounts.models import Account
from common.models import User, Address, Team, Comment, Attachments
from common.utils import INDCHOICES, COUNTRIES, CURRENCY_CODES, CASE_TYPE, PRIORITY_CHOICE, STATUS_CHOICE
from contacts.models import Contact
from opportunity.models import Opportunity, STAGES, SOURCES
from cases.models import Case
from common.forms import BillingAddressForm, ShippingAddressForm


class AccountsListView(LoginRequiredMixin, TemplateView):
    model = Account
    context_object_name = "accounts_list"
    template_name = "accounts.html"

    def get_queryset(self):
        queryset = self.model.objects.all().select_related("billing_address")
        request_post = self.request.POST
        if request_post:
            if request_post.get('name'):
                queryset = queryset.filter(name__icontains=request_post.get('name'))
            if request_post.get('city'):
                queryset = queryset.filter(
                    billing_address__in=[i.id for i in Address.objects.filter(
                        city__contains=request_post.get('city'))])
            if request_post.get('industry'):
                queryset = queryset.filter(industry__icontains=request_post.get('industry'))
        return queryset

    def get_context_data(self, **kwargs):
        context = super(AccountsListView, self).get_context_data(**kwargs)
        context["accounts_list"] = self.get_queryset()
        context["industries"] = INDCHOICES
        context["per_page"] = self.request.POST.get('per_page')
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)


class CreateAccountView(LoginRequiredMixin, CreateView):
    model = Account
    form_class = AccountForm
    template_name = "create_account.html"

    def dispatch(self, request, *args, **kwargs):
        self.users = User.objects.filter(is_active=True).order_by('email')
        return super(CreateAccountView, self).dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(CreateAccountView, self).get_form_kwargs()
        kwargs.update({'assigned_to': self.users})
        return kwargs

    def post(self, request, *args, **kwargs):
        self.object = None
        form = self.get_form()
        billing_form = BillingAddressForm(request.POST)
        shipping_form = ShippingAddressForm(request.POST, prefix='ship')
        if form.is_valid() and billing_form.is_valid() and shipping_form.is_valid():
            return self.form_valid(form, billing_form, shipping_form)
        else:
            return self.form_invalid(form, billing_form, shipping_form)

    def form_valid(self, form, billing_form, shipping_form):
        # Save Billing & Shipping Address
        billing_address_object = billing_form.save()
        shipping_address_object = shipping_form.save()
        # Save Account
        account_object = form.save(commit=False)
        account_object.billing_address = billing_address_object
        account_object.shipping_address = shipping_address_object
        account_object.created_by = self.request.user
        account_object.save()
        if self.request.POST.getlist('assigned_to', []):
            account_object.assigned_to.add(*self.request.POST.getlist('assigned_to'))
            assigned_to_list = self.request.POST.getlist('assigned_to')
            current_site = get_current_site(self.request)
            for assigned_to_user in assigned_to_list:
                user = get_object_or_404(User, pk=assigned_to_user)
                mail_subject = 'Assigned to account.'
                message = render_to_string('assigned_to/account_assigned.html', {
                    'user': user,
                    'domain': current_site.domain,
                    'protocol': self.request.scheme,
                    'account': account_object
                })
                email = EmailMessage(mail_subject, message, to=[user.email])
                email.send()
        if self.request.POST.getlist('teams', []):
            account_object.teams.add(*self.request.POST.getlist('teams'))
        if self.request.POST.get("savenewform"):
            return redirect("accounts:new_account")
        else:
            return redirect("accounts:list")

    def form_invalid(self, form, billing_form, shipping_form):
        return self.render_to_response(
            self.get_context_data(
                form=form, billing_form=billing_form, shipping_form=shipping_form)
        )

    def get_context_data(self, **kwargs):
        context = super(CreateAccountView, self).get_context_data(**kwargs)
        context["account_form"] = context["form"]
        context["users"] = self.users
        context["industries"] = INDCHOICES
        context["countries"] = COUNTRIES
        context["teams"] = Team.objects.all()
        if "billing_form" in kwargs and "shipping_form" in kwargs:
            context["billing_form"] = kwargs["billing_form"]
            context["shipping_form"] = kwargs["shipping_form"]
        else:
            if self.request.POST:
                context["billing_form"] = BillingAddressForm(self.request.POST)
                context["shipping_form"] = ShippingAddressForm(self.request.POST, prefix='ship')
            else:
                context["billing_form"] = BillingAddressForm()
                context["shipping_form"] = ShippingAddressForm(prefix='ship')
        context["assignedto_list"] = [
            int(i) for i in self.request.POST.getlist('assigned_to', []) if i]
        context["teams_list"] = [
            int(i) for i in self.request.POST.getlist('teams', []) if i]
        return context


class AccountDetailView(LoginRequiredMixin, DetailView):
    model = Account
    context_object_name = "account_record"
    template_name = "view_account.html"

    def get_context_data(self, **kwargs):
        context = super(AccountDetailView, self).get_context_data(**kwargs)
        account_record = context["account_record"]
        if (
            self.request.user in account_record.assigned_to.all() or
            self.request.user == account_record.created_by
        ):
            comment_permission = True
        else:
            comment_permission = False

        assigned_data = []
        for each in context['account_record'].assigned_to.all():
            assigned_dict = {}
            assigned_dict['id'] = each.id
            assigned_dict['name'] =  each.email
            assigned_data.append(assigned_dict)

        context.update({
            "comments": account_record.accounts_comments.all(),
            "attachments": account_record.account_attachment.all(),
            "opportunity_list": Opportunity.objects.filter(account=account_record),
            "contacts": Contact.objects.filter(account=account_record),
            "users": User.objects.filter(is_active=True).order_by('email'),
            "cases": Case.objects.filter(account=account_record),
            "teams": Team.objects.all(),
            "stages": STAGES,
            "sources": SOURCES,
            "countries": COUNTRIES,
            "currencies": CURRENCY_CODES,
            "case_types": CASE_TYPE,
            "case_priority": PRIORITY_CHOICE,
            "case_status": STATUS_CHOICE,
            'comment_permission': comment_permission,
            "assigned_data": json.dumps(assigned_data)
        })
        return context


class AccountUpdateView(LoginRequiredMixin, UpdateView):
    model = Account
    form_class = AccountForm
    template_name = "create_account.html"

    def dispatch(self, request, *args, **kwargs):
        self.users = User.objects.filter(is_active=True).order_by('email')
        return super(AccountUpdateView, self).dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(AccountUpdateView, self).get_form_kwargs()
        kwargs.update({'assigned_to': self.users})
        return kwargs

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        billing_form = BillingAddressForm(request.POST, instance=self.object.billing_address)
        shipping_form = ShippingAddressForm(
            request.POST, instance=self.object.shipping_address, prefix='ship')
        if form.is_valid() and billing_form.is_valid() and shipping_form.is_valid():
            return self.form_valid(form, billing_form, shipping_form)
        else:
            return self.form_invalid(form, billing_form, shipping_form)

    def form_valid(self, form, billing_form, shipping_form):
        assigned_to_ids = self.get_object().assigned_to.all().values_list('id', flat=True)

        # Save Billing & Shipping Address
        billing_address_object = billing_form.save()
        shipping_address_object = shipping_form.save()
        # Save Account
        account_object = form.save(commit=False)
        account_object.billing_address = billing_address_object
        account_object.shipping_address = shipping_address_object
        account_object.save()
        account_object.teams.clear()
        all_members_list = []
        if self.request.POST.getlist('assigned_to', []):
            current_site = get_current_site(self.request)
            assigned_form_users = form.cleaned_data.get('assigned_to').values_list('id', flat=True)
            all_members_list = list(set(list(assigned_form_users)) - set(list(assigned_to_ids)))

            if len(all_members_list):
                for assigned_to_user in all_members_list:
                    user = get_object_or_404(User, pk=assigned_to_user)
                    mail_subject = 'Assigned to account.'
                    message = render_to_string('assigned_to/account_assigned.html', {
                        'user': user,
                        'domain': current_site.domain,
                        'protocol': self.request.scheme,
                        'account': account_object
                    })
                    email = EmailMessage(mail_subject, message, to=[user.email])
                    email.send()

            account_object.assigned_to.clear()
            account_object.assigned_to.add(*self.request.POST.getlist('assigned_to'))
        if self.request.POST.getlist('teams', []):
            account_object.teams.add(*self.request.POST.getlist('teams'))
        return redirect("accounts:list")

    def form_invalid(self, form, billing_form, shipping_form):
        return self.render_to_response(
            self.get_context_data(
                form=form, billing_form=billing_form, shipping_form=shipping_form)
        )

    def get_context_data(self, **kwargs):
        context = super(AccountUpdateView, self).get_context_data(**kwargs)
        context["account_obj"] = self.object
        context["billing_obj"] = self.object.billing_address
        context["shipping_obj"] = self.object.shipping_address
        context["account_form"] = context["form"]
        context["users"] = self.users
        context["industries"] = INDCHOICES
        context["countries"] = COUNTRIES
        context["teams"] = Team.objects.all()
        if "billing_form" in kwargs and "shipping_form" in kwargs:
            context["billing_form"] = kwargs["billing_form"]
            context["shipping_form"] = kwargs["shipping_form"]
        else:
            if self.request.POST:
                context["billing_form"] = BillingAddressForm(
                    self.request.POST, instance=self.object.billing_address)
                context["shipping_form"] = ShippingAddressForm(
                    self.request.POST, instance=self.object.shipping_address, prefix='ship')
            else:
                context["billing_form"] = BillingAddressForm(
                    instance=self.object.billing_address)
                context["shipping_form"] = ShippingAddressForm(
                    instance=self.object.shipping_address, prefix='ship')
        context["assignedto_list"] = [
            int(i) for i in self.request.POST.getlist('assigned_to', []) if i]
        context["teams_list"] = [
            int(i) for i in self.request.POST.getlist('teams', []) if i]
        return context


class AccountDeleteView(LoginRequiredMixin, DeleteView):
    model = Account
    template_name = 'view_account.html'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.billing_address:
            self.object.billing_address.delete()
        if self.object.shipping_address:
            self.object.shipping_address.delete()
        self.object.delete()
        return redirect("accounts:list")


class AddCommentView(LoginRequiredMixin, CreateView):
    model = Comment
    form_class = AccountCommentForm
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        self.object = None
        self.account = get_object_or_404(Account, id=request.POST.get('accountid'))
        if (
            request.user in self.account.assigned_to.all() or
            request.user == self.account.created_by or request.user.is_superuser or
            request.user.role == 'ADMIN'
        ):
            form = self.get_form()
            if form.is_valid():
                return self.form_valid(form)
            else:
                return self.form_invalid(form)
        else:
            data = {'error': "You don't have permission to comment for this account."}
            return JsonResponse(data)

    def form_valid(self, form):
        comment = form.save(commit=False)
        comment.commented_by = self.request.user
        comment.account = self.account
        comment.save()
        return JsonResponse({
            "comment_id": comment.id, "comment": comment.comment,
            "commented_on": comment.commented_on,
            "commented_by": comment.commented_by.email
        })

    def form_invalid(self, form):
        return JsonResponse({"error": form['comment'].errors})


class UpdateCommentView(LoginRequiredMixin, View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        self.comment_obj = get_object_or_404(Comment, id=request.POST.get("commentid"))
        if request.user == self.comment_obj.commented_by:
            form = AccountCommentForm(request.POST, instance=self.comment_obj)
            if form.is_valid():
                return self.form_valid(form)
            else:
                return self.form_invalid(form)
        else:
            data = {'error': "You don't have permission to edit this comment."}
            return JsonResponse(data)

    def form_valid(self, form):
        self.comment_obj.comment = form.cleaned_data.get("comment")
        self.comment_obj.save(update_fields=["comment"])
        return JsonResponse({
            "comment_id": self.comment_obj.id,
            "comment": self.comment_obj.comment,
        })

    def form_invalid(self, form):
        return JsonResponse({"error": form['comment'].errors})


class DeleteCommentView(LoginRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        self.object = get_object_or_404(Comment, id=request.POST.get("comment_id"))
        if request.user == self.object.commented_by:
            self.object.delete()
            data = {"cid": request.POST.get("comment_id")}
            return JsonResponse(data)
        else:
            data = {'error': "You don't have permission to delete this comment."}
            return JsonResponse(data)


class AddAttachmentView(LoginRequiredMixin, CreateView):
    model = Attachments
    form_class = AccountAttachmentForm
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        self.object = None
        self.account = get_object_or_404(Account, id=request.POST.get('accountid'))
        if (
            request.user in self.account.assigned_to.all() or
            request.user == self.account.created_by or request.user.is_superuser or
            request.user.role == 'ADMIN'
        ):
            form = self.get_form()
            if form.is_valid():
                return self.form_valid(form)
            else:
                return self.form_invalid(form)
        else:
            data = {'error': "You don't have permission to add attachment for this account."}
            return JsonResponse(data)

    def form_valid(self, form):
        attachment = form.save(commit=False)
        attachment.created_by = self.request.user
        attachment.file_name = attachment.attachment.name
        attachment.account = self.account
        attachment.save()
        return JsonResponse({
            "attachment_id": attachment.id,
            "attachment": attachment.file_name,
            "attachment_url": attachment.attachment.url,
            "created_on": attachment.created_on,
            "created_by": attachment.created_by.email
        })

    def form_invalid(self, form):
        return JsonResponse({"error": form['attachment'].errors})


class DeleteAttachmentsView(LoginRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        self.object = get_object_or_404(Attachments, id=request.POST.get("attachment_id"))
        if (request.user == self.object.created_by or request.user.is_superuser or
            request.user.role == 'ADMIN'):
            self.object.delete()
            data = {"acd": request.POST.get("attachment_id")}
            return JsonResponse(data)
        else:
            data = {'error': "You don't have permission to delete this attachment."}
            return JsonResponse(data)
