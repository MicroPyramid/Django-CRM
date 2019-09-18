import json
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.views.generic import (CreateView, DetailView,
                                  ListView, TemplateView, View)

from cases.models import Case
from cases.forms import CaseForm, CaseCommentForm, CaseAttachmentForm
from common.models import User, Comment, Attachments
from accounts.models import Account
from contacts.models import Contact
from common.utils import PRIORITY_CHOICE, STATUS_CHOICE, CASE_TYPE
from django.urls import reverse
from django.core.exceptions import PermissionDenied
from common.tasks import send_email_user_mentions
from cases.tasks import send_email_to_assigned_user
from common.access_decorators_mixins import (
    sales_access_required, marketing_access_required, SalesAccessRequiredMixin, MarketingAccessRequiredMixin)
from teams.models import Teams


class CasesListView(SalesAccessRequiredMixin, LoginRequiredMixin, TemplateView):
    model = Case
    context_object_name = "cases"
    template_name = "cases.html"

    def get_queryset(self):
        queryset = self.model.objects.all().select_related("account")
        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            queryset = queryset.filter(
                Q(assigned_to__in=[self.request.user]) | Q(created_by=self.request.user))

        request_post = self.request.POST
        if request_post:
            if request_post.get('name'):
                queryset = queryset.filter(
                    name__icontains=request_post.get('name'))
            if request_post.get('account'):
                queryset = queryset.filter(
                    account_id=request_post.get('account'))
            if request_post.get('status'):
                queryset = queryset.filter(status=request_post.get('status'))
            if request_post.get('priority'):
                queryset = queryset.filter(
                    priority=request_post.get('priority'))
        return queryset

    def get_context_data(self, **kwargs):
        context = super(CasesListView, self).get_context_data(**kwargs)
        context["cases"] = self.get_queryset()
        context["accounts"] = Account.objects.filter(status="open")
        context["per_page"] = self.request.POST.get('per_page')
        context["acc"] = int(self.request.POST.get(
            "account")) if self.request.POST.get("account") else None
        context["case_priority"] = PRIORITY_CHOICE
        context["case_status"] = STATUS_CHOICE

        search = False
        if (
            self.request.POST.get('name') or self.request.POST.get('account') or
            self.request.POST.get(
                'status') or self.request.POST.get('priority')
        ):
            search = True

        context["search"] = search
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)


@login_required
@sales_access_required
def create_case(request):
    users = []
    if request.user.role == 'ADMIN' or request.user.is_superuser:
        users = User.objects.filter(is_active=True).order_by('email')
    elif request.user.google.all():
        users = []
    else:
        users = User.objects.filter(role='ADMIN').order_by('email')
    accounts = Account.objects.filter(status="open")
    contacts = Contact.objects.all()
    if request.user.role != "ADMIN" and not request.user.is_superuser:
        accounts = Account.objects.filter(
            created_by=request.user)
        contacts = Contact.objects.filter(
            Q(assigned_to__in=[request.user]) | Q(created_by=request.user))
    kwargs_data = {
        "assigned_to": users, "account": accounts, "contacts": contacts}
    form = CaseForm(**kwargs_data)
    template_name = "create_cases.html"

    if request.POST:
        form = CaseForm(request.POST, request.FILES, **kwargs_data)
        if form.is_valid():
            case = form.save(commit=False)
            case.created_by = request.user
            case.save()
            if request.POST.getlist('assigned_to', []):
                case.assigned_to.add(*request.POST.getlist('assigned_to'))
                assigned_to_list = request.POST.getlist('assigned_to')
                # current_site = get_current_site(request)
                # recipients = assigned_to_list
                # send_email_to_assigned_user.delay(recipients, case.id, domain=current_site.domain,
                #     protocol=request.scheme)
                # for assigned_to_user in assigned_to_list:
                #     user = get_object_or_404(User, pk=assigned_to_user)
                #     mail_subject = 'Assigned to case.'
                #     message = render_to_string(
                #         'assigned_to/cases_assigned.html', {
                #             'user': user,
                #             'domain': current_site.domain,
                #             'protocol': request.scheme,
                #             'case': case
                #         })
                #     email = EmailMessage(
                #         mail_subject, message, to=[user.email])
                #     email.content_subtype = "html"
                #     email.send()

            if request.POST.getlist('contacts', []):
                case.contacts.add(*request.POST.getlist('contacts'))
            if request.POST.getlist('teams', []):
                user_ids = Teams.objects.filter(id__in=request.POST.getlist('teams')).values_list('users', flat=True)
                assinged_to_users_ids = case.assigned_to.all().values_list('id', flat=True)
                for user_id in user_ids:
                    if user_id not in assinged_to_users_ids:
                        case.assigned_to.add(user_id)

            if request.POST.getlist('teams', []):
                case.teams.add(*request.POST.getlist('teams'))

            current_site = get_current_site(request)
            recipients = list(case.assigned_to.all().values_list('id', flat=True))
            send_email_to_assigned_user.delay(recipients, case.id, domain=current_site.domain,
                protocol=request.scheme)
            if request.FILES.get('case_attachment'):
                attachment = Attachments()
                attachment.created_by = request.user
                attachment.file_name = request.FILES.get(
                    'case_attachment').name
                attachment.case = case
                attachment.attachment = request.FILES.get('case_attachment')
                attachment.save()
            success_url = reverse('cases:list')
            if request.POST.get("savenewform"):
                success_url = reverse("cases:add_case")
            if request.POST.get('from_account'):
                from_account = request.POST.get('from_account')
                success_url = reverse("accounts:view_account", kwargs={
                                      'pk': from_account})
            return JsonResponse({'error': False, "success_url": success_url})
        return JsonResponse({'error': True, 'errors': form.errors})
    context = {}
    context["case_form"] = form
    context["accounts"] = accounts
    if request.GET.get('view_account'):
        context['account'] = get_object_or_404(
            Account, id=request.GET.get('view_account'))
    context["contacts"] = contacts
    context["users"] = users
    context["case_types"] = CASE_TYPE
    context["case_priority"] = PRIORITY_CHOICE
    context["case_status"] = STATUS_CHOICE
    context["teams"] = Teams.objects.all()
    context["assignedto_list"] = [
        int(i) for i in request.POST.getlist('assigned_to', []) if i]
    context["contacts_list"] = [
        int(i) for i in request.POST.getlist('contacts', []) if i]
    return render(request, template_name, context)


class CaseDetailView(SalesAccessRequiredMixin, LoginRequiredMixin, DetailView):
    model = Case
    context_object_name = "case_record"
    template_name = "view_case.html"

    def get_queryset(self):
        queryset = super(CaseDetailView, self).get_queryset()
        return queryset.prefetch_related("contacts", "account")

    def get_context_data(self, **kwargs):
        context = super(CaseDetailView, self).get_context_data(**kwargs)
        user_assgn_list = [
            assigned_to.id for assigned_to in context['object'].assigned_to.all()]
        user_assigned_accounts = set(self.request.user.account_assigned_users.values_list('id', flat=True))
        if context['object'].account:
            case_account = set([context['object'].account.id])
        else:
            case_account = set()
        if user_assigned_accounts.intersection(case_account):
            user_assgn_list.append(self.request.user.id)
        if self.request.user == context['object'].created_by:
            user_assgn_list.append(self.request.user.id)
        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            if self.request.user.id not in user_assgn_list:
                raise PermissionDenied
        assigned_data = []
        for each in context['case_record'].assigned_to.all():
            assigned_dict = {}
            assigned_dict['id'] = each.id
            assigned_dict['name'] = each.email
            assigned_data.append(assigned_dict)

        if self.request.user.is_superuser or self.request.user.role == 'ADMIN':
            users_mention = list(User.objects.filter(is_active=True).values('username'))
        elif self.request.user != context['object'].created_by:
            users_mention = [{'username': context['object'].created_by.username}]
        else:
            users_mention = list(context['object'].assigned_to.all().values('username'))

        context.update({"comments": context["case_record"].cases.all(),
                        "attachments": context['case_record'].case_attachment.all(),
                        "users_mention": users_mention,
                        "assigned_data": json.dumps(assigned_data)})
        return context


@login_required
@sales_access_required
def update_case(request, pk):
    case_object = Case.objects.filter(pk=pk).first()
    accounts = Account.objects.filter(status="open")
    contacts = Contact.objects.all()
    if request.user.role != "ADMIN" and not request.user.is_superuser:
        accounts = Account.objects.filter(
            created_by=request.user)
        contacts = Contact.objects.filter(
            Q(assigned_to__in=[request.user]) | Q(created_by=request.user))
    users = []
    if request.user.role == 'ADMIN' or request.user.is_superuser:
        users = User.objects.filter(is_active=True).order_by('email')
    elif request.user.google.all():
        users = []
    else:
        users = User.objects.filter(role='ADMIN').order_by('email')
    kwargs_data = {
        "assigned_to": users,
        "account": accounts, "contacts": contacts}
    form = CaseForm(instance=case_object, **kwargs_data)

    if request.POST:
        form = CaseForm(request.POST, request.FILES,
                        instance=case_object, **kwargs_data)
        if form.is_valid():
            assigned_to_ids = case_object.assigned_to.all().values_list(
                'id', flat=True)
            case_obj = form.save(commit=False)
            case_obj.contacts.clear()
            case_obj.save()
            previous_assigned_to_users = list(case_obj.assigned_to.all().values_list('id', flat=True))
            all_members_list = []

            if request.POST.getlist('assigned_to', []):
                current_site = get_current_site(request)

                assigned_form_users = form.cleaned_data.get(
                    'assigned_to').values_list('id', flat=True)
                all_members_list = list(
                    set(list(assigned_form_users)) -
                    set(list(assigned_to_ids)))
                # recipients = all_members_list
                # send_email_to_assigned_user.delay(recipients, case_obj.id, domain=current_site.domain,
                #     protocol=request.scheme)
                # if all_members_list:
                #     for assigned_to_user in all_members_list:
                #         user = get_object_or_404(User, pk=assigned_to_user)
                #         mail_subject = 'Assigned to case.'
                #         message = render_to_string(
                #             'assigned_to/cases_assigned.html', {
                #                 'user': user,
                #                 'domain': current_site.domain,
                #                 'protocol': request.scheme,
                #                 'case': case_obj
                #             })
                #         email = EmailMessage(
                #             mail_subject, message, to=[user.email])
                #         email.content_subtype = "html"
                #         email.send()

                case_obj.assigned_to.clear()
                case_obj.assigned_to.add(*request.POST.getlist('assigned_to'))
            else:
                case_obj.assigned_to.clear()

            if request.POST.getlist('teams', []):
                user_ids = Teams.objects.filter(id__in=request.POST.getlist('teams')).values_list('users', flat=True)
                assinged_to_users_ids = case_obj.assigned_to.all().values_list('id', flat=True)
                for user_id in user_ids:
                    if user_id not in assinged_to_users_ids:
                        case_obj.assigned_to.add(user_id)

            if request.POST.getlist('teams', []):
                case_obj.teams.clear()
                case_obj.teams.add(*request.POST.getlist('teams'))
            else:
                case_obj.teams.clear()

            current_site = get_current_site(request)
            assigned_to_list = list(case_obj.assigned_to.all().values_list('id', flat=True))
            recipients = list(set(assigned_to_list) - set(previous_assigned_to_users))
            send_email_to_assigned_user.delay(recipients, case_obj.id, domain=current_site.domain,
                protocol=request.scheme)

            if request.POST.getlist('contacts', []):
                case_obj.contacts.add(*request.POST.getlist('contacts'))

            success_url = reverse("cases:list")
            if request.POST.get('from_account'):
                from_account = request.POST.get('from_account')
                success_url = reverse("accounts:view_account", kwargs={
                                      'pk': from_account})
            if request.FILES.get('case_attachment'):
                attachment = Attachments()
                attachment.created_by = request.user
                attachment.file_name = request.FILES.get(
                    'case_attachment').name
                attachment.case = case_obj
                attachment.attachment = request.FILES.get('case_attachment')
                attachment.save()

            return JsonResponse({'error': False, 'success_url': success_url})
        return JsonResponse({'error': True, 'errors': form.errors})
    context = {}
    context["case_obj"] = case_object
    user_assgn_list = [
        assgined_to.id for assgined_to in context["case_obj"].assigned_to.all()]

    if request.user == case_object.created_by:
        user_assgn_list.append(request.user.id)
    if request.user.role != "ADMIN" and not request.user.is_superuser:
        if request.user.id not in user_assgn_list:
            raise PermissionDenied
    context["case_form"] = form
    context["accounts"] = accounts
    if request.GET.get('view_account'):
        context['account'] = get_object_or_404(
            Account, id=request.GET.get('view_account'))
    context["contacts"] = contacts
    context["users"] = kwargs_data['assigned_to']
    context["case_types"] = CASE_TYPE
    context["case_priority"] = PRIORITY_CHOICE
    context["case_status"] = STATUS_CHOICE
    context["teams"] = Teams.objects.all()
    context["assignedto_list"] = [
        int(i) for i in request.POST.getlist('assigned_to', []) if i]
    context["contacts_list"] = [
        int(i) for i in request.POST.getlist('contacts', []) if i]

    return render(request, "create_cases.html", context)


class RemoveCaseView(SalesAccessRequiredMixin, LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        case_id = kwargs.get("case_id")
        self.object = get_object_or_404(Case, id=case_id)
        if (
            self.request.user.role == "ADMIN" or
            self.request.user.is_superuser or
            self.request.user == self.object.created_by
        ):
            self.object.delete()
            if request.GET.get('view_account'):
                account = request.GET.get('view_account')
                return redirect("accounts:view_account", pk=account)
            return redirect("cases:list")
        raise PermissionDenied

    def post(self, request, *args, **kwargs):
        case_id = kwargs.get("case_id")
        self.object = get_object_or_404(Case, id=case_id)
        if (self.request.user.role == "ADMIN" or
            self.request.user.is_superuser or
                self.request.user == self.object.created_by):
            self.object.delete()
            if request.is_ajax():
                return JsonResponse({'error': False})
            count = Case.objects.filter(
                Q(assigned_to__in=[request.user]) | Q(created_by=request.user)).distinct().count()
            data = {"case_id": case_id, "count": count}
            return JsonResponse(data)
        raise PermissionDenied


class CloseCaseView(SalesAccessRequiredMixin, LoginRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        case_id = request.POST.get("case_id")
        self.object = get_object_or_404(Case, id=case_id)
        if (
            self.request.user.role == "ADMIN" or
            self.request.user.is_superuser or
            self.request.user == self.object.created_by
        ):
            self.object.status = "Closed"
            self.object.save()
            data = {'status': "Closed", "cid": case_id}
            return JsonResponse(data)
        raise PermissionDenied


def select_contact(request):
    contact_account = request.GET.get("account")
    if contact_account:
        account = get_object_or_404(Account, id=contact_account)
        contacts = account.contacts.all()
    else:
        contacts = Contact.objects.all()
    data = {contact.pk: contact.first_name for contact in contacts.distinct()}
    return JsonResponse(data)


class GetCasesView(LoginRequiredMixin, ListView):
    model = Case
    context_object_name = "cases"
    template_name = "cases_list.html"


class AddCommentView(LoginRequiredMixin, CreateView):
    model = Comment
    form_class = CaseCommentForm
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        self.object = None
        self.case = get_object_or_404(Case, id=request.POST.get('caseid'))
        if (
            request.user in self.case.assigned_to.all() or
            request.user == self.case.created_by or
            request.user.is_superuser or
            request.user.role == 'ADMIN'
        ):
            form = self.get_form()
            if form.is_valid():
                return self.form_valid(form)

            return self.form_invalid(form)

        data = {'error': "You don't have permission to comment."}
        return JsonResponse(data)

    def form_valid(self, form):
        comment = form.save(commit=False)
        comment.commented_by = self.request.user
        comment.case = self.case
        comment.save()
        comment_id = comment.id
        current_site = get_current_site(self.request)
        send_email_user_mentions.delay(comment_id, 'cases', domain=current_site.domain,
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
        if (
            request.user == self.comment_obj.commented_by or
            request.user.is_superuser or
            request.user.role == 'ADMIN'
        ):
            form = CaseCommentForm(request.POST, instance=self.comment_obj)
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
        send_email_user_mentions.delay(comment_id, 'cases', domain=current_site.domain,
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
        if (
            request.user == self.object.commented_by or
            request.user.is_superuser or
            request.user.role == 'ADMIN'
        ):
            self.object.delete()
            data = {"cid": request.POST.get("comment_id")}
            return JsonResponse(data)

        data = {'error': "You don't have permission to delete this comment."}
        return JsonResponse(data)


class AddAttachmentView(LoginRequiredMixin, CreateView):
    model = Attachments
    form_class = CaseAttachmentForm
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        self.object = None
        self.case = get_object_or_404(Case, id=request.POST.get('caseid'))
        if (
            request.user in self.case.assigned_to.all() or
            request.user == self.case.created_by or
            request.user.is_superuser or
            request.user.role == 'ADMIN'
        ):
            form = self.get_form()
            if form.is_valid():
                return self.form_valid(form)

            return self.form_invalid(form)

        data = {"error": True,
                "errors":
                "You don't have permission to add attachment for this case."}
        return JsonResponse(data)

    def form_valid(self, form):
        attachment = form.save(commit=False)
        attachment.created_by = self.request.user
        attachment.file_name = attachment.attachment.name
        attachment.case = self.case
        attachment.save()
        # return JsonResponse({"error": False, "message": "Attachment Saved"
        # })
        return JsonResponse({
            "attachment_id": attachment.id,
            "attachment": attachment.file_name,
            "attachment_url": attachment.attachment.url,
            "download_url":
            reverse('common:download_attachment',
                    kwargs={'pk': attachment.id}),
            "created_on": attachment.created_on,
            "created_on_arrow": attachment.created_on_arrow,
            "created_by": attachment.created_by.email,
            "message": "attachment Created",
            "attachment_display": attachment.get_file_type_display(),
            "file_type": attachment.file_type(),
            "error": False
        })

    def form_invalid(self, form):
        return JsonResponse({"error": True,
                             "errors": form['attachment'].errors})


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
            data = {"attachment_object": request.POST.get(
                "attachment_id"), "error": False}
            return JsonResponse(data)

        data = {"error": True,
                "errors":
                "You don't have permission to delete this attachment."}
        return JsonResponse(data)
