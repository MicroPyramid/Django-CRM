import json
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.views.generic import CreateView, UpdateView, DetailView, ListView, TemplateView, View

from cases.models import Case
from cases.forms import CaseForm, CaseCommentForm, CaseAttachmentForm
from common.models import Team, User, Comment, Attachments
from accounts.models import Account
from contacts.models import Contact
from common.utils import PRIORITY_CHOICE, STATUS_CHOICE, CASE_TYPE
from django.urls import reverse


class CasesListView(LoginRequiredMixin, TemplateView):
    model = Case
    context_object_name = "cases"
    template_name = "cases.html"

    def get_queryset(self):
        queryset = self.model.objects.all().select_related("account")
        request_post = self.request.POST
        if request_post:
            if request_post.get('name'):
                queryset = queryset.filter(name__icontains=request_post.get('name'))
            if request_post.get('account'):
                queryset = queryset.filter(account_id=request_post.get('account'))
            if request_post.get('status'):
                queryset = queryset.filter(status=request_post.get('status'))
            if request_post.get('priority'):
                queryset = queryset.filter(priority=request_post.get('priority'))
        return queryset

    def get_context_data(self, **kwargs):
        context = super(CasesListView, self).get_context_data(**kwargs)
        context["cases"] = self.get_queryset()
        context["accounts"] = Account.objects.all()
        context["per_page"] = self.request.POST.get('per_page')
        context["acc"] = int(self.request.POST.get("account")) if self.request.POST.get("account") else None
        context["case_priority"] = PRIORITY_CHOICE
        context["case_status"] = STATUS_CHOICE
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)


class CreateCaseView(LoginRequiredMixin, CreateView):
    model = Case
    form_class = CaseForm
    template_name = "create_cases.html"

    def dispatch(self, request, *args, **kwargs):
        self.users = User.objects.filter(is_active=True).order_by('email')
        self.accounts = Account.objects.all()
        self.contacts = Contact.objects.all()
        return super(CreateCaseView, self).dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(CreateCaseView, self).get_form_kwargs()
        kwargs.update({"assigned_to": self.users, "account": self.accounts,
                       "contacts": self.contacts})
        return kwargs

    def post(self, request, *args, **kwargs):
        self.object = None
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        
        return self.form_invalid(form)

    def form_valid(self, form):
        case = form.save(commit=False)
        case.created_by = self.request.user
        case.save()
        if self.request.POST.getlist('assigned_to', []):
            case.assigned_to.add(*self.request.POST.getlist('assigned_to'))
            assigned_to_list = self.request.POST.getlist('assigned_to')
            current_site = get_current_site(self.request)
            for assigned_to_user in assigned_to_list:
                user = get_object_or_404(User, pk=assigned_to_user)
                mail_subject = 'Assigned to case.'
                message = render_to_string('assigned_to/cases_assigned.html', {
                    'user': user,
                    'domain': current_site.domain,
                    'protocol': self.request.scheme,
                    'case': case
                })
                email = EmailMessage(mail_subject, message, to=[user.email])
                email.send()
        if self.request.POST.getlist('teams', []):
            case.teams.add(*self.request.POST.getlist('teams'))
        if self.request.POST.getlist('contacts', []):
            case.contacts.add(*self.request.POST.getlist('contacts'))
        if self.request.is_ajax():
            return JsonResponse({'error': False})
        if self.request.POST.get("savenewform"):
            return redirect("cases:add_case")
        if self.request.POST.get('from_account'):
            from_account = self.request.POST.get('from_account')
            return redirect("accounts:view_account", pk=from_account)
        
        return redirect('cases:list')

    def form_invalid(self, form):
        if self.request.is_ajax():
            return JsonResponse({'error': True, 'case_errors': form.errors})
        return self.render_to_response(self.get_context_data(form=form))

    def get_context_data(self, **kwargs):
        context = super(CreateCaseView, self).get_context_data(**kwargs)
        context["teams"] = Team.objects.all()
        context["case_form"] = context["form"]
        context["accounts"] = self.accounts
        context["contacts"] = self.contacts
        context["users"] = self.users
        context["case_types"] = CASE_TYPE
        context["case_priority"] = PRIORITY_CHOICE
        context["case_status"] = STATUS_CHOICE
        context["assignedto_list"] = [
            int(i) for i in self.request.POST.getlist('assigned_to', []) if i]
        context["teams_list"] = [
            int(i) for i in self.request.POST.getlist('teams', []) if i]
        context["contacts_list"] = [
            int(i) for i in self.request.POST.getlist('contacts', []) if i]
        return context


class CaseDetailView(LoginRequiredMixin, DetailView):
    model = Case
    context_object_name = "case_record"
    template_name = "view_case.html"

    def get_queryset(self):
        queryset = super(CaseDetailView, self).get_queryset()
        return queryset.prefetch_related("contacts", "account")

    def get_context_data(self, **kwargs):
        context = super(CaseDetailView, self).get_context_data(**kwargs)
        assigned_data = []
        for each in context['case_record'].assigned_to.all():
            assigned_dict = {}
            assigned_dict['id'] = each.id
            assigned_dict['name'] =  each.email
            assigned_data.append(assigned_dict)

        context.update({"comments": context["case_record"].cases.all(), 
            "attachments": context['case_record'].case_attachment.all(), 
            "assigned_data": json.dumps(assigned_data)})
        return context


class UpdateCaseView(LoginRequiredMixin, UpdateView):
    model = Case
    form_class = CaseForm
    template_name = "create_cases.html"

    def dispatch(self, request, *args, **kwargs):
        self.users = User.objects.filter(is_active=True).order_by('email')
        self.accounts = Account.objects.all()
        self.contacts = Contact.objects.all()
        return super(UpdateCaseView, self).dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(UpdateCaseView, self).get_form_kwargs()
        kwargs.update({"assigned_to": self.users, "account": self.accounts,
                       "contacts": self.contacts})
        return kwargs

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        
        return self.form_invalid(form)

    def form_valid(self, form):
        assigned_to_ids = self.get_object().assigned_to.all().values_list('id', flat=True)
        case_obj = form.save(commit=False)
        case_obj.teams.clear()
        case_obj.contacts.clear()
        case_obj.save()
        all_members_list = []

        if self.request.POST.getlist('assigned_to', []):
            current_site = get_current_site(self.request)

            assigned_form_users = form.cleaned_data.get('assigned_to').values_list('id', flat=True)
            all_members_list = list(set(list(assigned_form_users)) - set(list(assigned_to_ids)))

            if len(all_members_list):
                for assigned_to_user in all_members_list:
                    user = get_object_or_404(User, pk=assigned_to_user)
                    mail_subject = 'Assigned to case.'
                    message = render_to_string('assigned_to/cases_assigned.html', {
                        'user': user,
                        'domain': current_site.domain,
                        'protocol': self.request.scheme,
                        'case': case_obj
                    })
                    email = EmailMessage(mail_subject, message, to=[user.email])
                    email.send()

            case_obj.assigned_to.clear()
            case_obj.assigned_to.add(*self.request.POST.getlist('assigned_to'))

        if self.request.POST.getlist('teams', []):
            case_obj.teams.add(*self.request.POST.getlist('teams'))
        if self.request.POST.getlist('contacts', []):
            case_obj.contacts.add(*self.request.POST.getlist('contacts'))

        if self.request.POST.get('from_account'):
            from_account = self.request.POST.get('from_account')
            return redirect("accounts:view_account", pk=from_account)

        if self.request.is_ajax():
            return JsonResponse({'error': False})
        return redirect("cases:list")

    def form_invalid(self, form):
        if self.request.is_ajax():
            return JsonResponse({'error': True, 'case_errors': form.errors})
        return self.render_to_response(self.get_context_data(form=form))

    def get_context_data(self, **kwargs):
        context = super(UpdateCaseView, self).get_context_data(**kwargs)
        context["case_obj"] = self.object
        context["teams"] = Team.objects.all()
        context["case_form"] = context["form"]
        context["accounts"] = self.accounts
        context["contacts"] = self.contacts
        context["users"] = self.users
        context["case_types"] = CASE_TYPE
        context["case_priority"] = PRIORITY_CHOICE
        context["case_status"] = STATUS_CHOICE
        context["assignedto_list"] = [
            int(i) for i in self.request.POST.getlist('assigned_to', []) if i]
        context["teams_list"] = [
            int(i) for i in self.request.POST.getlist('teams', []) if i]
        context["contacts_list"] = [
            int(i) for i in self.request.POST.getlist('contacts', []) if i]
        return context


class RemoveCaseView(LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        case_id = kwargs.get("case_id")
        self.object = get_object_or_404(Case, id=case_id)
        self.object.delete()
        if request.GET.get('view_account'):
            account = request.GET.get('view_account')
            return redirect("accounts:view_account", pk=account)
        
        return redirect("cases:list")

    def post(self, request, *args, **kwargs):
        case_id = kwargs.get("case_id")
        self.object = get_object_or_404(Case, id=case_id)
        self.object.delete()
        if request.is_ajax():
            return JsonResponse({'error': False})
        count = Case.objects.filter(
            Q(assigned_to=request.user) | Q(created_by=request.user)).distinct().count()
        data = {"case_id": case_id, "count": count}
        return JsonResponse(data)


class CloseCaseView(LoginRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        case_id = request.POST.get("case_id")
        self.object = get_object_or_404(Case, id=case_id)
        self.object.status = "Closed"
        self.object.save()
        data = {'status': "Closed", "cid": case_id}
        return JsonResponse(data)


class SelectContactsView(LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        contact_account = request.GET.get("account")
        if contact_account:
            account = get_object_or_404(Account, id=contact_account)
            contacts = Contact.objects.filter(account=account)
        else:
            contacts = Contact.objects.all()
        data = {i.pk: i.first_name for i in contacts.distinct()}
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
            request.user == self.case.created_by or request.user.is_superuser or
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
        if (
            request.user == self.comment_obj.commented_by or request.user.is_superuser or
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
        return JsonResponse({
            "comment_id": self.comment_obj.id,
            "comment": self.comment_obj.comment,
        })

    def form_invalid(self, form):
        return JsonResponse({"error": form['comment'].errors})


class DeleteCommentView(LoginRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        self.object = get_object_or_404(Comment, id=request.POST.get("comment_id"))
        if (
            request.user == self.object.commented_by or request.user.is_superuser or
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
            request.user == self.case.created_by or request.user.is_superuser or
            request.user.role == 'ADMIN'
        ):
            form = self.get_form()
            if form.is_valid():
                return self.form_valid(form)
        
            return self.form_invalid(form)
        
        data = {"error":True, "errors": "You don't have permission to add attachment for this case."}
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
            "download_url": reverse('common:download_attachment', kwargs={'pk':attachment.id}),
            "created_on": attachment.created_on,
            "created_by": attachment.created_by.email,
            "message": "attachment Created",
            "attachment_display": attachment.get_file_type_display(),
            "error": False
        })

    def form_invalid(self, form):
        return JsonResponse({"error":True, "errors": form['attachment'].errors})


class DeleteAttachmentsView(LoginRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        self.object = get_object_or_404(Attachments, id=request.POST.get("attachment_id"))
        if (
            request.user == self.object.created_by or request.user.is_superuser or 
            request.user.role == 'ADMIN'
        ):
            self.object.delete()
            data = {"attachment_object": request.POST.get("attachment_id"), "error": False}
            return JsonResponse(data)
        
        data = {"error":True, "errors": "You don't have permission to delete this attachment."}
        return JsonResponse(data)