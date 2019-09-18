import pytz
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import (CreateView, DeleteView, DetailView, FormView,
                                  TemplateView, UpdateView, View)

from accounts.forms import (AccountAttachmentForm, AccountCommentForm,
                            AccountForm, EmailForm)
from accounts.models import Account, Email, Tags
from accounts.tasks import send_email, send_email_to_assigned_user
from cases.models import Case
from common.access_decorators_mixins import (MarketingAccessRequiredMixin,
                                             SalesAccessRequiredMixin,
                                             marketing_access_required,
                                             sales_access_required)
from common.models import Attachments, Comment, User
from common.tasks import send_email_user_mentions
from common.utils import (CASE_TYPE, COUNTRIES, CURRENCY_CODES, INDCHOICES,
                          PRIORITY_CHOICE, STATUS_CHOICE)
from contacts.models import Contact
from leads.models import Lead
from opportunity.models import SOURCES, STAGES, Opportunity
from teams.models import Teams


class AccountsListView(SalesAccessRequiredMixin, LoginRequiredMixin, TemplateView):
    model = Account
    context_object_name = "accounts_list"
    template_name = "accounts.html"

    def get_queryset(self):
        queryset = self.model.objects.all()
        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            queryset = queryset.filter(
                Q(created_by=self.request.user) | Q(assigned_to=self.request.user)).distinct()

        if self.request.GET.get('tag', None):
            queryset = queryset.filter(tags__in = self.request.GET.getlist('tag'))

        request_post = self.request.POST
        if request_post:
            if request_post.get('name'):
                queryset = queryset.filter(
                    name__icontains=request_post.get('name'))
            if request_post.get('city'):
                queryset = queryset.filter(
                    billing_city__contains=request_post.get('city'))
            if request_post.get('industry'):
                queryset = queryset.filter(
                    industry__icontains=request_post.get('industry'))
            if request_post.get('tag'):
                queryset = queryset.filter(tags__in=request_post.getlist('tag'))

        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super(AccountsListView, self).get_context_data(**kwargs)
        open_accounts = self.get_queryset().filter(status='open')
        close_accounts = self.get_queryset().filter(status='close')
        context["accounts_list"] = self.get_queryset()
        context["users"] = User.objects.filter(
            is_active=True).order_by('email')
        context['open_accounts'] = open_accounts
        context['close_accounts'] = close_accounts
        context["industries"] = INDCHOICES
        context["per_page"] = self.request.POST.get('per_page')
        tag_ids = list(set(Account.objects.values_list('tags', flat=True)))
        context["tags"] = Tags.objects.filter(id__in=tag_ids)
        if self.request.POST.get('tag', None):
            context["request_tags"] = self.request.POST.getlist('tag')
        elif self.request.GET.get('tag', None):
            context["request_tags"] = self.request.GET.getlist('tag')
        else:
            context["request_tags"] = None

        search = False
        if (
            self.request.POST.get('name') or self.request.POST.get('city') or
            self.request.POST.get('industry') or self.request.POST.get('tag')
        ):
            search = True

        context["search"] = search

        tab_status = 'Open'
        if self.request.POST.get('tab_status'):
            tab_status = self.request.POST.get('tab_status')
        context['tab_status'] = tab_status
        TIMEZONE_CHOICES = [(tz, tz) for tz in pytz.common_timezones]
        context["timezones"] = TIMEZONE_CHOICES
        context["settings_timezone"] = settings.TIME_ZONE

        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)


class CreateAccountView(SalesAccessRequiredMixin, LoginRequiredMixin, CreateView):
    model = Account
    form_class = AccountForm
    template_name = "create_account.html"

    def dispatch(self, request, *args, **kwargs):
        if self.request.user.role == 'ADMIN' or self.request.user.is_superuser:
            self.users = User.objects.filter(is_active=True).order_by('email')
        elif request.user.google.all():
            self.users = []
        else:
            self.users = User.objects.filter(role='ADMIN').order_by('email')
        return super(
            CreateAccountView, self).dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(CreateAccountView, self).get_form_kwargs()
        kwargs.update({"account": True})
        kwargs.update({"request_user": self.request.user})
        # if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
        #     kwargs.update({"request_user": self.request.user})
        return kwargs

    def post(self, request, *args, **kwargs):
        self.object = None
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)

        return self.form_invalid(form)

    def form_valid(self, form):
        # Save Account
        account_object = form.save(commit=False)
        account_object.created_by = self.request.user
        account_object.save()

        if self.request.POST.get('tags', ''):
            tags = self.request.POST.get("tags")
            splitted_tags = tags.split(",")
            for t in splitted_tags:
                tag = Tags.objects.filter(name=t.lower())
                if tag:
                    tag = tag[0]
                else:
                    tag = Tags.objects.create(name=t.lower())
                account_object.tags.add(tag)
        if self.request.POST.getlist('contacts', []):
            account_object.contacts.add(*self.request.POST.getlist('contacts'))
        if self.request.POST.getlist('assigned_to', []):
            account_object.assigned_to.add(*self.request.POST.getlist('assigned_to'))
        if self.request.FILES.get('account_attachment'):
            attachment = Attachments()
            attachment.created_by = self.request.user
            attachment.file_name = self.request.FILES.get(
                'account_attachment').name
            attachment.account = account_object
            attachment.attachment = self.request.FILES.get(
                'account_attachment')
            attachment.save()
        if self.request.POST.getlist('teams', []):
            user_ids = Teams.objects.filter(id__in=self.request.POST.getlist('teams')).values_list('users', flat=True)
            assinged_to_users_ids = account_object.assigned_to.all().values_list('id', flat=True)
            for user_id in user_ids:
                if user_id not in assinged_to_users_ids:
                    account_object.assigned_to.add(user_id)
        if self.request.POST.getlist('teams', []):
            account_object.teams.add(*self.request.POST.getlist('teams'))

        assigned_to_list = list(account_object.assigned_to.all().values_list('id', flat=True))
        current_site = get_current_site(self.request)
        recipients = assigned_to_list
        send_email_to_assigned_user.delay(recipients, account_object.id, domain=current_site.domain,
            protocol=self.request.scheme)

        if self.request.POST.get("savenewform"):
            return redirect("accounts:new_account")

        if self.request.is_ajax():
            data = {'success_url': reverse_lazy(
                'accounts:list'), 'error': False}
            return JsonResponse(data)

        return redirect("accounts:list")

    def form_invalid(self, form):
        if self.request.is_ajax():
            return JsonResponse({'error': True, 'errors': form.errors})
        return self.render_to_response(
            self.get_context_data(form=form)
        )

    def get_context_data(self, **kwargs):
        context = super(CreateAccountView, self).get_context_data(**kwargs)
        context["account_form"] = context["form"]
        context["users"] = self.users
        context["industries"] = INDCHOICES
        context["countries"] = COUNTRIES
        # context["contact_count"] = Contact.objects.count()
        if self.request.user.role == 'ADMIN' or self.request.user.is_superuser:
            context["leads"] = Lead.objects.exclude(
                status__in=['converted', 'closed'])
            context["contacts"] = Contact.objects.all()
        else:
            context["leads"] = Lead.objects.filter(
                Q(assigned_to__in=[self.request.user]) | Q(created_by=self.request.user)).exclude(
                status__in=['converted', 'closed'])
        context["lead_count"] = context["leads"].count()
        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            context["lead_count"] = Lead.objects.filter(
                Q(assigned_to__in=[self.request.user]) | Q(created_by=self.request.user)).exclude(status='closed').count()
            context["contacts"] = Contact.objects.filter(
                Q(assigned_to__in=[self.request.user]) | Q(created_by=self.request.user))
        context["contact_count"] = context["contacts"].count()
        context["teams"] = Teams.objects.all()
        return context


class AccountDetailView(SalesAccessRequiredMixin, LoginRequiredMixin, DetailView):
    model = Account
    context_object_name = "account_record"
    template_name = "view_account.html"

    def get_context_data(self, **kwargs):
        context = super(AccountDetailView, self).get_context_data(**kwargs)
        account_record = context["account_record"]
        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            if not ((self.request.user == account_record.created_by) or
                (self.request.user in account_record.assigned_to.all())):
                raise PermissionDenied

        comment_permission = True if (
            self.request.user == account_record.created_by or
            self.request.user.is_superuser or self.request.user.role == 'ADMIN'
        ) else False

        if self.request.user.is_superuser or self.request.user.role == 'ADMIN':
            users_mention = list(User.objects.filter(is_active=True).values('username'))
        elif self.request.user != account_record.created_by:
            if account_record.created_by:
                users_mention = [{'username': account_record.created_by.username}]
            else:
                users_mention = []
        else:
            users_mention = []

        context.update({
            "comments": account_record.accounts_comments.all(),
            "attachments": account_record.account_attachment.all(),
            "opportunity_list": Opportunity.objects.filter(
                account=account_record),
            "contacts": account_record.contacts.all(),
            "users": User.objects.filter(is_active=True).order_by('email'),
            "cases": Case.objects.filter(account=account_record),
            "stages": STAGES,
            "sources": SOURCES,
            "countries": COUNTRIES,
            "currencies": CURRENCY_CODES,
            "case_types": CASE_TYPE,
            "case_priority": PRIORITY_CHOICE,
            "case_status": STATUS_CHOICE,
            'comment_permission': comment_permission,
            'tasks':account_record.accounts_tasks.all(),
            'invoices':account_record.accounts_invoices.all(),
            'emails':account_record.sent_email.all(),
            'users_mention': users_mention,
        })
        return context


class AccountUpdateView(SalesAccessRequiredMixin, LoginRequiredMixin, UpdateView):
    model = Account
    form_class = AccountForm
    template_name = "create_account.html"

    def dispatch(self, request, *args, **kwargs):
        self.users = User.objects.filter(is_active=True).order_by('email')
        # if self.request.user.role == 'ADMIN' or self.request.user.is_superuser:
        # elif request.user.google.all():
        #     self.users = []
        # else:
        #     self.users = User.objects.filter(role='ADMIN').order_by('email')
        return super(AccountUpdateView, self).dispatch(
            request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(AccountUpdateView, self).get_form_kwargs()
        kwargs.update({"account": True})
        kwargs.update({"request_user": self.request.user})
        # if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
        #     kwargs.update({"request_user": self.request.user})
        return kwargs

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)

        return self.form_invalid(form)

    def form_valid(self, form):
        # Save Account
        account_object = form.save(commit=False)
        account_object.save()
        previous_assigned_to_users = list(account_object.assigned_to.all().values_list('id', flat=True))
        account_object.tags.clear()
        if self.request.POST.get('tags', ''):
            tags = self.request.POST.get("tags")
            splitted_tags = tags.split(",")
            for t in splitted_tags:
                tag = Tags.objects.filter(name=t.lower())
                if tag:
                    tag = tag[0]
                else:
                    tag = Tags.objects.create(name=t.lower())
                account_object.tags.add(tag)
        if self.request.POST.getlist('contacts', []):
            account_object.contacts.clear()
            account_object.contacts.add(*self.request.POST.getlist('contacts'))
        if self.request.POST.getlist('assigned_to', []):
            account_object.assigned_to.clear()
            account_object.assigned_to.add(*self.request.POST.getlist('assigned_to'))
        else:
            account_object.assigned_to.clear()
        if self.request.FILES.get('account_attachment'):
            attachment = Attachments()
            attachment.created_by = self.request.user
            attachment.file_name = self.request.FILES.get(
                'account_attachment').name
            attachment.account = account_object
            attachment.attachment = self.request.FILES.get(
                'account_attachment')
            attachment.save()

        if self.request.POST.getlist('teams', []):
            account_object.teams.clear()
            account_object.teams.add(*self.request.POST.getlist('teams'))
        else:
            account_object.teams.clear()


        if self.request.POST.getlist('teams', []):
            user_ids = Teams.objects.filter(id__in=self.request.POST.getlist('teams')).values_list('users', flat=True)
            assinged_to_users_ids = account_object.assigned_to.all().values_list('id', flat=True)
            for user_id in user_ids:
                if user_id not in assinged_to_users_ids:
                    account_object.assigned_to.add(user_id)

        assigned_to_list = list(account_object.assigned_to.all().values_list('id', flat=True))
        current_site = get_current_site(self.request)
        recipients = list(set(assigned_to_list) - set(previous_assigned_to_users))
        send_email_to_assigned_user.delay(recipients, account_object.id, domain=current_site.domain,
            protocol=self.request.scheme)

        if self.request.is_ajax():
            data = {'success_url': reverse_lazy(
                'accounts:list'), 'error': False}
            return JsonResponse(data)
        return redirect("accounts:list")

    def form_invalid(self, form):
        if self.request.is_ajax():
            return JsonResponse({'error': True, 'errors': form.errors})
        return self.render_to_response(
            self.get_context_data(form=form)
        )

    def get_context_data(self, **kwargs):
        context = super(AccountUpdateView, self).get_context_data(**kwargs)
        context["account_obj"] = self.object
        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            if ((self.request.user != context['account_obj'].created_by ) and
                (self.request.user not in context['account_obj'].assigned_to.all())):
                raise PermissionDenied
        context["account_form"] = context["form"]
        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            self.users = self.users.filter(Q(role='ADMIN') | Q(id__in=[self.request.user.id,]))
        context["users"] = self.users
        context["industries"] = INDCHOICES
        context["countries"] = COUNTRIES
        context["contact_count"] = Contact.objects.count()
        if self.request.user.role == 'ADMIN':
            context["leads"] = Lead.objects.exclude(
                status__in=['converted', 'closed'])
        else:
            context["leads"] = Lead.objects.filter(
                Q(assigned_to__in=[self.request.user]) | Q(created_by=self.request.user)).exclude(
                status__in=['converted', 'closed'])
        context["lead_count"] = context["leads"].count()
        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            context["lead_count"] = Lead.objects.filter(
                Q(assigned_to__in=[self.request.user]) | Q(created_by=self.request.user)).exclude(status='closed').count()
        context["teams"] = Teams.objects.all()
        return context


class AccountDeleteView(SalesAccessRequiredMixin, LoginRequiredMixin, DeleteView):
    model = Account
    template_name = 'view_account.html'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            if self.request.user != self.object.created_by:
                raise PermissionDenied
        self.object.delete()
        return redirect("accounts:list")


class AddCommentView(LoginRequiredMixin, CreateView):
    model = Comment
    form_class = AccountCommentForm
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        self.object = None
        self.account = get_object_or_404(
            Account, id=request.POST.get('accountid'))
        if (
            request.user == self.account.created_by or request.user.is_superuser or
            request.user.role == 'ADMIN' or request.user in self.account.assigned_to.all()
        ):
            form = self.get_form()
            if form.is_valid():
                return self.form_valid(form)
            return self.form_invalid(form)

        data = {
            'error': "You don't have permission to comment for this account."}
        return JsonResponse(data)

    def form_valid(self, form):
        comment = form.save(commit=False)
        comment.commented_by = self.request.user
        comment.account = self.account
        comment.save()
        comment_id = comment.id
        current_site = get_current_site(self.request)
        send_email_user_mentions.delay(comment_id, 'accounts', domain=current_site.domain,
            protocol=self.request.scheme)

        return JsonResponse({
            "comment_id": comment.id, "comment": comment.comment,
            "commented_on": comment.commented_on,
            "commented_on_arrow": comment.commented_on_arrow,
            "commented_by": comment.commented_by.email
        })

    def form_invalid(self, form):
        return JsonResponse({"error": form['comment'].errors})


class UpdateCommentView(LoginRequiredMixin, View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        self.comment_obj = get_object_or_404(
            Comment, id=request.POST.get("commentid"))
        if request.user == self.comment_obj.commented_by:
            form = AccountCommentForm(request.POST, instance=self.comment_obj)
            if form.is_valid():
                return self.form_valid(form)

            return self.form_invalid(form)

        data = {'error': "You don't have permission to edit this comment."}
        return JsonResponse(data)

    def form_valid(self, form):
        self.comment_obj.comment = form.cleaned_data.get("comment")
        self.comment_obj.save(update_fields=["comment"])
        comment_id = self.comment_obj.id
        current_site = get_current_site(self.request)
        send_email_user_mentions.delay(comment_id, 'accounts', domain=current_site.domain,
            protocol=self.request.scheme)
        return JsonResponse({
            "comment_id": self.comment_obj.id,
            "comment": self.comment_obj.comment,
        })

    def form_invalid(self, form):
        return JsonResponse({"error": form['comment'].errors})


class DeleteCommentView(LoginRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        self.object = get_object_or_404(
            Comment, id=request.POST.get("comment_id"))
        if request.user == self.object.commented_by:
            self.object.delete()
            data = {"cid": request.POST.get("comment_id")}
            return JsonResponse(data)

        data = {'error': "You don't have permission to delete this comment."}
        return JsonResponse(data)


class AddAttachmentView(LoginRequiredMixin, CreateView):
    model = Attachments
    form_class = AccountAttachmentForm
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        self.object = None
        self.account = get_object_or_404(
            Account, id=request.POST.get('accountid'))
        if (
            request.user == self.account.created_by or
            request.user.is_superuser or
            request.user.role == 'ADMIN' or
            request.user in self.account.assigned_to.all()
        ):
            form = self.get_form()
            if form.is_valid():
                return self.form_valid(form)

            return self.form_invalid(form)

        data = {
            'error': "You don't have permission to add attachment \
            for this account."}
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
            "download_url": reverse('common:download_attachment',
                                    kwargs={'pk': attachment.id}),
            "attachment_display": attachment.get_file_type_display(),
            "created_on": attachment.created_on,
            "created_on_arrow": attachment.created_on_arrow,
            "created_by": attachment.created_by.email,
            "file_type": attachment.file_type()
        })

    def form_invalid(self, form):
        return JsonResponse({"error": form['attachment'].errors})


class DeleteAttachmentsView(LoginRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        self.object = get_object_or_404(
            Attachments, id=request.POST.get("attachment_id"))
        if (
            request.user == self.object.created_by or
            request.user.is_superuser or
            request.user.role == 'ADMIN'
        ):
            self.object.delete()
            data = {"acd": request.POST.get("attachment_id")}
            return JsonResponse(data)

        data = {
            'error': "You don't have permission to delete this attachment."}
        return JsonResponse(data)

@login_required
def create_mail(request):
    if request.method == 'GET':
        account = get_object_or_404(Account, pk=request.GET.get('account_id'))
        contacts_list = list(account.contacts.all().values('email'))
        TIMEZONE_CHOICES = [(tz, tz) for tz in pytz.common_timezones]
        email_form = EmailForm(account=account)
        return render(request, 'create_mail_accounts.html', {'account_id': request.GET.get('account_id'),
            'contacts_list': contacts_list, 'email_form': email_form,
            "timezones": TIMEZONE_CHOICES, "settings_timezone": settings.TIME_ZONE})

    if request.method == 'POST':
        account = Account.objects.filter(id=request.POST.get('account_id')).first()
        if account:
            form = EmailForm(request.POST, account=account)
            if form.is_valid():
                contacts = form.data.get('recipients').split(',')
                email_obj = Email.objects.create(
                    from_account=account,
                    message_body=form.cleaned_data.get('message_body'),
                    message_subject=form.cleaned_data.get('message_subject'),
                    from_email=form.cleaned_data.get('from_email'),
                    timezone=form.cleaned_data.get('timezone'),
                )
                email_obj.recipients.add(*contacts)
                if request.POST.get('scheduled_later') != 'true':
                    send_email.delay(email_obj.id)
                else:
                    email_obj.scheduled_later = True
                    email_obj.scheduled_date_time = form.cleaned_data.get('scheduled_date_time')
                    email_obj.save()

                return JsonResponse({'error': False})
            else:
                return JsonResponse({'error': True, 'errors': form.errors})
        else:
            return JsonResponse({'error':True, 'message': "Account does not exist."})

# @login_required
# @sales_access_required
# def create_mail(request, pk):
#     account_obj = get_object_or_404(Account, pk=pk)
#     if request.method == 'GET':
#         context = {}
#         context['account_obj'] = account_obj
#         return render(request, 'create_email_for_contacts.html')


def get_contacts_for_account(request):
    account_id = request.POST.get('account_id')
    if account_id:
        account_obj = Account.objects.filter(pk=account_id).first()
        if account_obj:
            if account_obj.contacts.all():
                data = list(account_obj.contacts.values('id', 'email'))
                import json
                return HttpResponse(json.dumps(data))
        return JsonResponse({})
    return JsonResponse({})


def get_email_data_for_account(request):
    email_obj = Email.objects.filter(id=request.POST.get('email_account_id')).first()
    if email_obj:
        ctx  = {}
        ctx['subject'] = email_obj.message_subject
        ctx['body'] = email_obj.message_body
        ctx['created_on'] = email_obj.created_on
        ctx['contacts'] = list(email_obj.recipients.values('email'))
        ctx['error'] = False
        return JsonResponse(ctx)
    else:
        return JsonResponse({'error': True, 'data' : 'No emails found.'})