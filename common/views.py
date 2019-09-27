import datetime
import json
import os

import boto3
import botocore
import requests
from django.core.cache import cache
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password
from django.contrib.auth.mixins import AccessMixin, LoginRequiredMixin
from django.contrib.auth.views import PasswordResetView
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import PermissionDenied
from django.core.mail import EmailMessage
from django.db.models import Q
from django.http import (Http404, HttpResponse, HttpResponseRedirect,
    JsonResponse)
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views.generic import (CreateView, DeleteView, DetailView,
    TemplateView, UpdateView, View)

from accounts.models import Account, Tags
from cases.models import Case
from common.access_decorators_mixins import (MarketingAccessRequiredMixin,
    SalesAccessRequiredMixin, marketing_access_required, sales_access_required,
    admin_login_required)
from common.forms import (APISettingsForm, ChangePasswordForm, DocumentForm,
    LoginForm, PasswordResetEmailForm, UserCommentForm, UserForm)
from common.models import (APISettings, Attachments, Comment, Document, Google,
    Profile, User)
from common.tasks import (resend_activation_link_to_user,
    send_email_to_new_user, send_email_user_delete, send_email_user_status)
from common.token_generator import account_activation_token
from common.utils import ROLES
from contacts.models import Contact
from leads.models import Lead
from opportunity.models import Opportunity
from teams.models import Teams
from marketing.models import ContactEmailCampaign, BlockedDomain, BlockedEmail 


def handler404(request, exception):
    return render(request, '404.html', status=404)


def handler500(request):
    return render(request, '500.html', status=500)


class AdminRequiredMixin(AccessMixin):

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        self.raise_exception = True
        if not request.user.role == "ADMIN":
            if not request.user.is_superuser:
                return self.handle_no_permission()
        return super(AdminRequiredMixin, self).dispatch(
            request, *args, **kwargs)


class HomeView(SalesAccessRequiredMixin, LoginRequiredMixin, TemplateView):
    template_name = "sales/index.html"

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        accounts = Account.objects.filter(status="open")
        contacts = Contact.objects.all()
        leads = Lead.objects.exclude(
            status='converted').exclude(status='closed')
        opportunities = Opportunity.objects.all()
        if self.request.user.role == "ADMIN" or self.request.user.is_superuser:
            pass
        else:
            accounts = accounts.filter(
                Q(assigned_to__id__in=[self.request.user.id]) |
                Q(created_by=self.request.user.id))
            contacts = contacts.filter(
                Q(assigned_to__id__in=[self.request.user.id]) |
                Q(created_by=self.request.user.id))
            leads = leads.filter(
                Q(assigned_to__id__in=[self.request.user.id]) |
                Q(created_by=self.request.user.id)).exclude(status='closed')
            opportunities = opportunities.filter(
                Q(assigned_to__id__in=[self.request.user.id]) |
                Q(created_by=self.request.user.id))

        context["accounts"] = accounts
        context["contacts_count"] = contacts.count()
        context["leads_count"] = leads
        context["opportunities"] = opportunities
        return context


class ChangePasswordView(LoginRequiredMixin, TemplateView):
    template_name = "change_password.html"

    def get_context_data(self, **kwargs):
        context = super(ChangePasswordView, self).get_context_data(**kwargs)
        context["change_password_form"] = ChangePasswordForm()
        return context

    def post(self, request, *args, **kwargs):
        error, errors = "", ""
        form = ChangePasswordForm(request.POST, user=request.user)
        if form.is_valid():
            user = request.user
            # if not check_password(request.POST.get('CurrentPassword'),
            #                       user.password):
            #     error = "Invalid old password"
            # else:
            user.set_password(request.POST.get('Newpassword'))
            user.is_active = True
            user.save()
            return HttpResponseRedirect('/')
        else:
            errors = form.errors
        return render(request, "change_password.html",
                      {'error': error, 'errors': errors,
                       'change_password_form': form})


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "profile.html"

    def get_context_data(self, **kwargs):

        context = super(ProfileView, self).get_context_data(**kwargs)
        context["user_obj"] = self.request.user
        return context


class LoginView(TemplateView):
    template_name = "login.html"

    def get_context_data(self, **kwargs):
        context = super(LoginView, self).get_context_data(**kwargs)
        context["ENABLE_GOOGLE_LOGIN"] = settings.ENABLE_GOOGLE_LOGIN
        context["GP_CLIENT_SECRET"] = settings.GP_CLIENT_SECRET
        context["GP_CLIENT_ID"] = settings.GP_CLIENT_ID
        return context

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return HttpResponseRedirect('/')
        return super(LoginView, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        form = LoginForm(request.POST, request=request)
        if form.is_valid():

            user = User.objects.filter(email=request.POST.get('email')).first()
            # user = authenticate(username=request.POST.get('email'), password=request.POST.get('password'))
            if user is not None:
                if user.is_active:
                    user = authenticate(username=request.POST.get(
                        'email'), password=request.POST.get('password'))
                    if user is not None:
                        login(request, user)
                        if user.has_sales_access:
                            return HttpResponseRedirect('/')
                        elif user.has_marketing_access:
                            return redirect('marketing:dashboard')
                        else:
                            return HttpResponseRedirect('/')
                    return render(request, "login.html", {
                        "ENABLE_GOOGLE_LOGIN": settings.ENABLE_GOOGLE_LOGIN,
                        "GP_CLIENT_SECRET": settings.GP_CLIENT_SECRET,
                        "GP_CLIENT_ID": settings.GP_CLIENT_ID,
                        "error": True,
                        "message":
                        "Your username and password didn't match. \
                        Please try again."
                    })
                return render(request, "login.html", {
                    "ENABLE_GOOGLE_LOGIN": settings.ENABLE_GOOGLE_LOGIN,
                    "GP_CLIENT_SECRET": settings.GP_CLIENT_SECRET,
                    "GP_CLIENT_ID": settings.GP_CLIENT_ID,
                    "error": True,
                    "message":
                    "Your Account is inactive. Please Contact Administrator"
                })
            return render(request, "login.html", {
                "ENABLE_GOOGLE_LOGIN": settings.ENABLE_GOOGLE_LOGIN,
                "GP_CLIENT_SECRET": settings.GP_CLIENT_SECRET,
                "GP_CLIENT_ID": settings.GP_CLIENT_ID,
                "error": True,
                "message":
                "Your Account is not Found. Please Contact Administrator"
            })

        return render(request, "login.html", {
            "ENABLE_GOOGLE_LOGIN": settings.ENABLE_GOOGLE_LOGIN,
            "GP_CLIENT_SECRET": settings.GP_CLIENT_SECRET,
            "GP_CLIENT_ID": settings.GP_CLIENT_ID,
            # "error": True,
            # "message": "Your username and password didn't match. Please try again."
            "form": form
        })


class ForgotPasswordView(TemplateView):
    template_name = "forgot_password.html"


class LogoutView(LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        logout(request)
        request.session.flush()
        return redirect("common:login")


class UsersListView(AdminRequiredMixin, TemplateView):
    model = User
    context_object_name = "users"
    template_name = "list.html"

    def get_queryset(self):
        queryset = self.model.objects.all()

        request_post = self.request.POST
        if request_post:
            if request_post.get('username'):
                queryset = queryset.filter(
                    username__icontains=request_post.get('username'))
            if request_post.get('email'):
                queryset = queryset.filter(
                    email__icontains=request_post.get('email'))
            if request_post.get('role'):
                queryset = queryset.filter(
                    role=request_post.get('role'))
            if request_post.get('status'):
                queryset = queryset.filter(
                    is_active=request_post.get('status'))

        return queryset.order_by('username')

    def get_context_data(self, **kwargs):
        context = super(UsersListView, self).get_context_data(**kwargs)
        active_users = self.get_queryset().filter(is_active=True)
        inactive_users = self.get_queryset().filter(is_active=False)
        context["active_users"] = active_users
        context["inactive_users"] = inactive_users
        context["per_page"] = self.request.POST.get('per_page')
        context['admin_email'] = settings.ADMIN_EMAIL
        context['roles'] = ROLES
        context['status'] = [('True', 'Active'), ('False', 'In Active')]
        return context

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)


class CreateUserView(AdminRequiredMixin, CreateView):
    model = User
    form_class = UserForm
    template_name = "create.html"
    # success_url = '/users/list/'

    def form_valid(self, form):
        user = form.save(commit=False)
        if form.cleaned_data.get("password"):
            user.set_password(form.cleaned_data.get("password"))
        user.save()

        if self.request.POST.getlist('teams'):
            for team in self.request.POST.getlist('teams'):
                Teams.objects.filter(id=team).first().users.add(user)

        current_site = self.request.get_host()
        protocol = self.request.scheme
        send_email_to_new_user.delay(user.email, self.request.user.email,
                                     domain=current_site, protocol=protocol)
        # mail_subject = 'Created account in CRM'
        # message = render_to_string('new_user.html', {
        #     'user': user,
        #     'created_by': self.request.user

        # })
        # email = EmailMessage(mail_subject, message, to=[user.email])
        # email.content_subtype = "html"
        # email.send()

        if self.request.is_ajax():
            data = {'success_url': reverse_lazy(
                'common:users_list'), 'error': False}
            return JsonResponse(data)
        return super(CreateUserView, self).form_valid(form)

    def form_invalid(self, form):
        response = super(CreateUserView, self).form_invalid(form)
        if self.request.is_ajax():
            return JsonResponse({'error': True, 'errors': form.errors})
        return response

    def get_form_kwargs(self):
        kwargs = super(CreateUserView, self).get_form_kwargs()
        kwargs.update({"request_user": self.request.user})
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(CreateUserView, self).get_context_data(**kwargs)
        context["user_form"] = context["form"]
        context["teams"] = Teams.objects.all()
        if "errors" in kwargs:
            context["errors"] = kwargs["errors"]
        return context


class UserDetailView(AdminRequiredMixin, DetailView):
    model = User
    context_object_name = "users"
    template_name = "user_detail.html"

    def get_context_data(self, **kwargs):
        context = super(UserDetailView, self).get_context_data(**kwargs)
        user_obj = self.object
        users_data = []
        for each in User.objects.all():
            assigned_dict = {}
            assigned_dict['id'] = each.id
            assigned_dict['name'] = each.username
            users_data.append(assigned_dict)
        context.update({
            "user_obj": user_obj,
            "opportunity_list":
            Opportunity.objects.filter(assigned_to=user_obj.id),
            "contacts": Contact.objects.filter(assigned_to=user_obj.id),
            "cases": Case.objects.filter(assigned_to=user_obj.id),
            # "accounts": Account.objects.filter(assigned_to=user_obj.id),
            "assigned_data": json.dumps(users_data),
            "comments": user_obj.user_comments.all(),
        })
        return context


class UpdateUserView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserForm
    template_name = "create.html"

    def form_valid(self, form):
        user = form.save(commit=False)
        if self.request.is_ajax():
            if (self.request.user.role != "ADMIN" and not
                    self.request.user.is_superuser):
                if self.request.user.id != self.object.id:
                    data = {'error_403': True, 'error': True}
                    return JsonResponse(data)
        if user.role == "USER":
            user.is_superuser = False
        user.save()

        if self.request.POST.getlist('teams'):
            user_teams = user.user_teams.all()
            # this is for removing the user from previous team
            for user_team in user_teams:
                user_team.users.remove(user)
            # this is for assigning the user to new team
            for team in self.request.POST.getlist('teams'):
                team_obj = Teams.objects.filter(id=team).first()
                team_obj.users.add(user)

        if (self.request.user.role == "ADMIN" and
                self.request.user.is_superuser):
            if self.request.is_ajax():
                data = {'success_url': reverse_lazy(
                    'common:users_list'), 'error': False}
                if self.request.user.id == user.id:
                    data = {'success_url': reverse_lazy(
                        'common:profile'), 'error': False}
                    return JsonResponse(data)
                return JsonResponse(data)
        if self.request.is_ajax():
            data = {'success_url': reverse_lazy(
                'common:profile'), 'error': False}
            return JsonResponse(data)
        return super(UpdateUserView, self).form_valid(form)

    def form_invalid(self, form):
        response = super(UpdateUserView, self).form_invalid(form)
        if self.request.is_ajax():
            return JsonResponse({'error': True, 'errors': form.errors})
        return response

    def get_form_kwargs(self):
        kwargs = super(UpdateUserView, self).get_form_kwargs()
        kwargs.update({"request_user": self.request.user})
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(UpdateUserView, self).get_context_data(**kwargs)
        context["user_obj"] = self.object
        user_profile_name = str(context["user_obj"].profile_pic).split("/")
        user_profile_name = user_profile_name[-1]
        context["user_profile_name"] = user_profile_name
        context["user_form"] = context["form"]
        context["teams"] = Teams.objects.all()
        if "errors" in kwargs:
            context["errors"] = kwargs["errors"]
        return context


class UserDeleteView(AdminRequiredMixin, DeleteView):
    model = User

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        current_site = request.get_host()
        deleted_by = self.request.user.email
        send_email_user_delete.delay(
            self.object.email, deleted_by=deleted_by, domain=current_site, protocol=request.scheme)
        self.object.delete()
        lead_users = User.objects.filter(
            is_active=True).order_by('email').values('id', 'email')
        cache.set('lead_form_users', lead_users, 60*60)
        return redirect("common:users_list")


class PasswordResetView(PasswordResetView):
    template_name = 'registration/password_reset_form.html'
    form_class = PasswordResetEmailForm
    email_template_name = 'registration/password_reset_email.html'
    html_email_template_name = 'registration/password_reset_email.html'
    from_email = settings.PASSWORD_RESET_MAIL_FROM_USER


@login_required
@sales_access_required
def document_create(request):
    template_name = "doc_create.html"
    users = []
    if request.user.role == 'ADMIN' or request.user.is_superuser:
        users = User.objects.filter(is_active=True).order_by('email')
    else:
        users = User.objects.filter(role='ADMIN').order_by('email')
    form = DocumentForm(users=users)
    if request.POST:
        form = DocumentForm(request.POST, request.FILES, users=users)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.created_by = request.user
            doc.save()
            if request.POST.getlist('shared_to'):
                doc.shared_to.add(*request.POST.getlist('shared_to'))
            if request.POST.getlist('teams', []):
                user_ids = Teams.objects.filter(id__in=request.POST.getlist(
                    'teams')).values_list('users', flat=True)
                assinged_to_users_ids = doc.shared_to.all().values_list('id', flat=True)
                for user_id in user_ids:
                    if user_id not in assinged_to_users_ids:
                        doc.shared_to.add(user_id)

            if request.POST.getlist('teams', []):
                doc.teams.add(*request.POST.getlist('teams'))

            data = {'success_url': reverse_lazy(
                'common:doc_list'), 'error': False}
            return JsonResponse(data)
        return JsonResponse({'error': True, 'errors': form.errors})
    context = {}
    context["doc_form"] = form
    context["users"] = users
    context["teams"] = Teams.objects.all()
    context["sharedto_list"] = [
        int(i) for i in request.POST.getlist('assigned_to', []) if i]
    context["errors"] = form.errors
    return render(request, template_name, context)


class DocumentListView(SalesAccessRequiredMixin, LoginRequiredMixin, TemplateView):
    model = Document
    context_object_name = "documents"
    template_name = "doc_list_1.html"

    def get_queryset(self):
        queryset = self.model.objects.all()
        if self.request.user.is_superuser or self.request.user.role == "ADMIN":
            queryset = queryset
        else:
            if self.request.user.documents():
                doc_ids = self.request.user.documents().values_list('id',
                                                                    flat=True)
                shared_ids = queryset.filter(
                    Q(status='active') &
                    Q(shared_to__id__in=[self.request.user.id])).values_list(
                    'id', flat=True)
                queryset = queryset.filter(
                    Q(id__in=doc_ids) | Q(id__in=shared_ids))
            else:
                queryset = queryset.filter(Q(status='active') & Q(
                    shared_to__id__in=[self.request.user.id]))

        request_post = self.request.POST
        if request_post:
            if request_post.get('doc_name'):
                queryset = queryset.filter(
                    title__icontains=request_post.get('doc_name'))
            if request_post.get('status'):
                queryset = queryset.filter(status=request_post.get('status'))

            if request_post.getlist('shared_to'):
                queryset = queryset.filter(
                    shared_to__id__in=request_post.getlist('shared_to'))
        return queryset

    def get_context_data(self, **kwargs):
        context = super(DocumentListView, self).get_context_data(**kwargs)
        context["users"] = User.objects.filter(
            is_active=True).order_by('email')
        context["documents"] = self.get_queryset()
        context["status_choices"] = Document.DOCUMENT_STATUS_CHOICE
        context["sharedto_list"] = [
            int(i) for i in self.request.POST.getlist('shared_to', []) if i]
        context["per_page"] = self.request.POST.get('per_page')

        search = False
        if (
            self.request.POST.get('doc_name') or
            self.request.POST.get('status') or
            self.request.POST.get('shared_to')
        ):
            search = True

        context["search"] = search
        return context

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)


class DocumentDeleteView(LoginRequiredMixin, DeleteView):
    model = Document

    def get(self, request, *args, **kwargs):
        if not request.user.role == 'ADMIN':
            if not request.user == Document.objects.get(id=kwargs['pk']).created_by:
                raise PermissionDenied
        self.object = self.get_object()
        self.object.delete()
        return redirect("common:doc_list")


@login_required
@sales_access_required
def document_update(request, pk):
    template_name = "doc_create.html"
    users = []
    if request.user.role == 'ADMIN' or request.user.is_superuser:
        users = User.objects.filter(is_active=True).order_by('email')
    else:
        users = User.objects.filter(role='ADMIN').order_by('email')
    document = Document.objects.filter(id=pk).first()
    form = DocumentForm(users=users, instance=document)

    if request.POST:
        form = DocumentForm(request.POST, request.FILES,
                            instance=document, users=users)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.save()

            doc.shared_to.clear()
            if request.POST.getlist('shared_to'):
                doc.shared_to.add(*request.POST.getlist('shared_to'))

            if request.POST.getlist('teams', []):
                user_ids = Teams.objects.filter(id__in=request.POST.getlist(
                    'teams')).values_list('users', flat=True)
                assinged_to_users_ids = doc.shared_to.all().values_list('id', flat=True)
                for user_id in user_ids:
                    if user_id not in assinged_to_users_ids:
                        doc.shared_to.add(user_id)

            if request.POST.getlist('teams', []):
                doc.teams.clear()
                doc.teams.add(*request.POST.getlist('teams'))
            else:
                doc.teams.clear()

            data = {'success_url': reverse_lazy(
                'common:doc_list'), 'error': False}
            return JsonResponse(data)
        return JsonResponse({'error': True, 'errors': form.errors})
    context = {}
    context["doc_obj"] = document
    context["doc_form"] = form
    context["doc_file_name"] = context["doc_obj"].document_file.name.split(
        "/")[-1]
    context["users"] = users
    context["teams"] = Teams.objects.all()
    context["sharedto_list"] = [
        int(i) for i in request.POST.getlist('shared_to', []) if i]
    context["errors"] = form.errors
    return render(request, template_name, context)


class DocumentDetailView(SalesAccessRequiredMixin, LoginRequiredMixin, DetailView):
    model = Document
    template_name = "doc_detail.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.role == 'ADMIN':
            if (not request.user ==
                    Document.objects.get(id=kwargs['pk']).created_by):
                raise PermissionDenied

        return super(DocumentDetailView, self).dispatch(
            request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(DocumentDetailView, self).get_context_data(**kwargs)
        # documents = Document.objects.all()
        context.update({
            "file_type_code": self.object.file_type()[1],
            "doc_obj": self.object,
        })
        return context


def download_document(request, pk):
    # doc_obj = Document.objects.filter(id=pk).last()
    doc_obj = Document.objects.get(id=pk)
    if doc_obj:
        if not request.user.role == 'ADMIN':
            if (not request.user == doc_obj.created_by and
                    request.user not in doc_obj.shared_to.all()):
                raise PermissionDenied
        if settings.STORAGE_TYPE == "normal":
            # print('no no no no')
            path = doc_obj.document_file.path
            file_path = os.path.join(settings.MEDIA_ROOT, path)
            if os.path.exists(file_path):
                with open(file_path, 'rb') as fh:
                    response = HttpResponse(
                        fh.read(), content_type="application/vnd.ms-excel")
                    response['Content-Disposition'] = 'inline; filename=' + \
                        os.path.basename(file_path)
                    return response
        else:
            file_path = doc_obj.document_file
            file_name = doc_obj.title
            # print(file_path)
            # print(file_name)
            BUCKET_NAME = "django-crm-demo"
            KEY = str(file_path)
            s3 = boto3.resource('s3')
            try:
                s3.Bucket(BUCKET_NAME).download_file(KEY, file_name)
                # print('got it')
                with open(file_name, 'rb') as fh:
                    response = HttpResponse(
                        fh.read(), content_type="application/vnd.ms-excel")
                    response['Content-Disposition'] = 'inline; filename=' + \
                        os.path.basename(file_name)
                os.remove(file_name)
                return response
            except botocore.exceptions.ClientError as e:
                if e.response['Error']['Code'] == "404":
                    print("The object does not exist.")
                else:
                    raise

            return path
    raise Http404


def download_attachment(request, pk): # pragma: no cover
    attachment_obj = Attachments.objects.filter(id=pk).last()
    if attachment_obj:
        if settings.STORAGE_TYPE == "normal":
            path = attachment_obj.attachment.path
            file_path = os.path.join(settings.MEDIA_ROOT, path)
            if os.path.exists(file_path):
                with open(file_path, 'rb') as fh:
                    response = HttpResponse(
                        fh.read(), content_type="application/vnd.ms-excel")
                    response['Content-Disposition'] = 'inline; filename=' + \
                        os.path.basename(file_path)
                    return response
        else:
            file_path = attachment_obj.attachment
            file_name = attachment_obj.file_name
            # print(file_path)
            # print(file_name)
            BUCKET_NAME = "django-crm-demo"
            KEY = str(file_path)
            s3 = boto3.resource('s3')
            try:
                s3.Bucket(BUCKET_NAME).download_file(KEY, file_name)
                with open(file_name, 'rb') as fh:
                    response = HttpResponse(
                        fh.read(), content_type="application/vnd.ms-excel")
                    response['Content-Disposition'] = 'inline; filename=' + \
                        os.path.basename(file_name)
                os.remove(file_name)
                return response
            except botocore.exceptions.ClientError as e:
                if e.response['Error']['Code'] == "404":
                    print("The object does not exist.")
                else:
                    raise
            # if file_path:
            #     print('yes tus pus')
    raise Http404


def change_user_status(request, pk):
    user = get_object_or_404(User, pk=pk)
    if user.is_active:
        user.is_active = False
    else:
        user.is_active = True
    user.save()
    current_site = request.get_host()
    status_changed_user = request.user.email
    send_email_user_status.delay(
        pk, status_changed_user=status_changed_user, domain=current_site , protocol=request.scheme)
    return HttpResponseRedirect('/users/list/')


def add_comment(request):
    if request.method == "POST":
        user = get_object_or_404(User, id=request.POST.get('userid'))
        form = UserCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.commented_by = request.user
            comment.user = user
            comment.save()
            return JsonResponse({
                "comment_id": comment.id, "comment": comment.comment,
                "commented_on": comment.commented_on,
                "commented_by": comment.commented_by.email
            })
        return JsonResponse({"error": form.errors})


def edit_comment(request, pk):
    if request.method == "POST":
        comment_obj = get_object_or_404(Comment, id=pk)
        if request.user == comment_obj.commented_by:
            form = UserCommentForm(request.POST, instance=comment_obj)
            if form.is_valid():
                comment_obj.comment = form.cleaned_data.get("comment")
                comment_obj.save(update_fields=["comment"])
                return JsonResponse({
                    "comment_id": comment_obj.id,
                    "comment": comment_obj.comment,
                })
            return JsonResponse({"error": form['comment'].errors})
        data = {'error': "You don't have permission to edit this comment."}
        return JsonResponse(data)


def remove_comment(request):
    if request.method == "POST":
        comment_obj = get_object_or_404(
            Comment, id=request.POST.get('comment_id'))
        if request.user == comment_obj.commented_by:
            comment_obj.delete()
            data = {"cid": request.POST.get("comment_id")}
            return JsonResponse(data)
        data = {'error': "You don't have permission to delete this comment."}
        return JsonResponse(data)

@login_required
@admin_login_required
def api_settings(request):
    # api_settings = APISettings.objects.all()
    blocked_domains = BlockedDomain.objects.all()
    blocked_emails = BlockedEmail.objects.all()
    contacts = ContactEmailCampaign.objects.all()
    created_by_users = User.objects.filter(role='ADMIN')
    assigned_users = User.objects.all()

    context = {
        # 'settings': api_settings,
        'contacts': contacts,
        'created_by_users': created_by_users,
        'assigned_users': assigned_users,
        'blocked_emails': blocked_emails,
        'blocked_domains': blocked_domains,
    }

    if request.method == 'POST':
        # settings = api_settings
        # if request.POST.get('api_settings', None):
        #     if request.POST.get('title', None):
        #         settings = settings.filter(title__icontains=request.POST.get('title', None))
        #     if request.POST.get('created_by', None):
        #         settings = settings.filter(created_by_id=request.POST.get('created_by', None))
        #     if request.POST.get('assigned_to', None):
        #         settings = settings.filter(lead_assigned_to__id__in=request.POST.getlist('assigned_to', None))

        #     context['settings']= settings.distinct()

        if request.POST.get('filter_contacts', None):
            contacts_filter = contacts
            if request.POST.get('contact_name', None):
                contacts_filter = contacts_filter.filter(name__icontains=request.POST.get('contact_name', None))
            if request.POST.get('contact_created_by', None):
                contacts_filter = contacts_filter.filter(created_by_id=request.POST.get('contact_created_by', None))
            if request.POST.get('contact_email', None):
                contacts_filter = contacts_filter.filter(email__icontains=request.POST.get('contact_email', None))

            context['contacts']= contacts_filter.distinct()

        if request.POST.get('filter_blocked_domains', None):
            if request.POST.get('domain', ''):
                blocked_domains = blocked_domains.filter(domain__icontains=request.POST.get('domain', ''))
            if request.POST.get('created_by', ''):
                blocked_domains = blocked_domains.filter(created_by_id=request.POST.get('created_by', ''))

            context['blocked_domains']= blocked_domains

        if request.POST.get('filter_blocked_emails', None):
            if request.POST.get('email', ''):
                blocked_emails = blocked_emails.filter(email__icontains=request.POST.get('email', ''))
            if request.POST.get('created_by', ''):
                blocked_emails = blocked_emails.filter(created_by_id=request.POST.get('created_by', ''))

            context['blocked_emails'] = blocked_emails

    return render(request, 'settings/list.html', context)


def add_api_settings(request):
    users = User.objects.filter(is_active=True).order_by('email')
    form = APISettingsForm(assign_to=users)
    assign_to_list = []
    if request.POST:
        form = APISettingsForm(request.POST, assign_to=users)
        assign_to_list = [
            int(i) for i in request.POST.getlist('lead_assigned_to', []) if i]
        if form.is_valid():
            settings_obj = form.save(commit=False)
            settings_obj.created_by = request.user
            settings_obj.save()
            if request.POST.get('tags', ''):
                tags = request.POST.get("tags")
                splitted_tags = tags.split(",")
                for t in splitted_tags:
                    tag = Tags.objects.filter(name=t)
                    if tag:
                        tag = tag[0]
                    else:
                        tag = Tags.objects.create(name=t)
                    settings_obj.tags.add(tag)
            if assign_to_list:
                settings_obj.lead_assigned_to.add(*assign_to_list)
            success_url = reverse_lazy("common:api_settings")
            if request.POST.get("savenewform"):
                success_url = reverse_lazy("common:add_api_settings")
            data = {'success_url': success_url, 'error': False}
            return JsonResponse(data)
        return JsonResponse({'error': True, 'errors': form.errors})
    data = {'form': form, "setting": api_settings,
            'users': users, 'assign_to_list': assign_to_list}
    return render(request, 'settings/create.html', data)


def view_api_settings(request, pk):
    api_settings = APISettings.objects.filter(pk=pk).first()
    data = {"setting": api_settings}
    return render(request, 'settings/view.html', data)


def update_api_settings(request, pk):
    api_settings = APISettings.objects.filter(pk=pk).first()
    users = User.objects.filter(is_active=True).order_by('email')
    form = APISettingsForm(instance=api_settings, assign_to=users)
    assign_to_list = []
    if request.POST:
        form = APISettingsForm(
            request.POST, instance=api_settings, assign_to=users)
        assign_to_list = [
            int(i) for i in request.POST.getlist('lead_assigned_to', []) if i]
        if form.is_valid():
            settings_obj = form.save(commit=False)
            settings_obj.save()
            if request.POST.get('tags', ''):
                settings_obj.tags.clear()
                tags = request.POST.get("tags")
                splitted_tags = tags.split(",")
                for t in splitted_tags:
                    tag = Tags.objects.filter(name=t)
                    if tag:
                        tag = tag[0]
                    else:
                        tag = Tags.objects.create(name=t)
                    settings_obj.tags.add(tag)
            if assign_to_list:
                settings_obj.lead_assigned_to.clear()
                settings_obj.lead_assigned_to.add(*assign_to_list)
            success_url = reverse_lazy("common:api_settings")
            if request.POST.get("savenewform"):
                success_url = reverse_lazy("common:add_api_settings")
            data = {'success_url': success_url, 'error': False}
            return JsonResponse(data)
        return JsonResponse({'error': True, 'errors': form.errors})
    data = {
        'form': form, "setting": api_settings,
        'users': users, 'assign_to_list': assign_to_list,
        'assigned_to_list':
        json.dumps(
            [setting.id for setting in api_settings.lead_assigned_to.all() if setting])
    }
    return render(request, 'settings/update.html', data)


def delete_api_settings(request, pk):
    api_settings = APISettings.objects.filter(pk=pk).first()
    if api_settings:
        api_settings.delete()
        data = {"error": False, "response": "Successfully Deleted!"}
    else:
        data = {"error": True,
                "response": "Object Not Found!"}
    # return JsonResponse(data)
    return redirect('common:api_settings')


def change_passsword_by_admin(request):
    if request.user.role == "ADMIN" or request.user.is_superuser:
        if request.method == "POST":
            user = get_object_or_404(User, id=request.POST.get("useer_id"))
            user.set_password(request.POST.get("new_passwoord"))
            user.save()
            mail_subject = 'Crm Account Password Changed'
            message = "<h3><b>hello</b> <i>" + user.username +\
                "</i></h3><br><h2><p> <b>Your account password has been changed !\
                 </b></p></h2>" \
                + "<br> <p><b> New Password</b> : <b><i>" + \
                request.POST.get("new_passwoord") + "</i><br></p>"
            email = EmailMessage(mail_subject, message, to=[user.email])
            email.content_subtype = "html"
            email.send()
            return HttpResponseRedirect('/users/list/')
    raise PermissionDenied


def google_login(request): # pragma: no cover
    if 'code' in request.GET:
        params = {
            'grant_type': 'authorization_code',
            'code': request.GET.get('code'),
            'redirect_uri': 'http://' +
            request.META['HTTP_HOST'] + reverse('common:google_login'),
            'client_id': settings.GP_CLIENT_ID,
            'client_secret': settings.GP_CLIENT_SECRET
        }

        info = requests.post(
            "https://accounts.google.com/o/oauth2/token", data=params)
        info = info.json()
        url = 'https://www.googleapis.com/oauth2/v1/userinfo'
        params = {'access_token': info['access_token']}
        kw = dict(params=params, headers={}, timeout=60)
        response = requests.request('GET', url, **kw)
        user_document = response.json()

        link = "https://plus.google.com/" + user_document['id']
        dob = user_document['birthday'] if 'birthday' in user_document.keys(
        ) else ""
        gender = user_document['gender'] if 'gender' in user_document.keys(
        ) else ""
        link = user_document['link'] if 'link' in user_document.keys(
        ) else link

        verified_email = user_document['verified_email'] if 'verified_email' in user_document.keys(
        ) else ''
        name = user_document['name'] if 'name' in user_document.keys(
        ) else 'name'
        first_name = user_document['given_name'] if 'given_name' in user_document.keys(
        ) else 'first_name'
        last_name = user_document['family_name'] if 'family_name' in user_document.keys(
        ) else 'last_name'
        email = user_document['email'] if 'email' in user_document.keys(
        ) else 'email@dummy.com'

        user = User.objects.filter(email=user_document['email'])

        if user:
            user = user[0]
            user.first_name = first_name
            user.last_name = last_name
        else:
            user = User.objects.create(
                username=email,
                email=email,
                first_name=first_name,
                last_name=last_name,
                role="USER",
                has_sales_access=True,
                has_marketing_access=True,
            )

        google, _ = Google.objects.get_or_create(user=user)
        google.user = user
        google.google_url = link
        google.verified_email = verified_email
        google.google_id = user_document['id']
        google.family_name = last_name
        google.name = name
        google.given_name = first_name
        google.dob = dob
        google.email = email
        google.gender = gender
        google.save()

        user.last_login = datetime.datetime.now()
        user.save()

        login(request, user)

        if request.GET.get('state') != '1235dfghjkf123':
            return HttpResponseRedirect(request.GET.get('state'))
        if user.has_sales_access:
            return HttpResponseRedirect('/')
        elif user.has_marketing_access:
            return redirect('marketing:dashboard')
        else:
            return HttpResponseRedirect('/')
    if request.GET.get('next'):
        next_url = request.GET.get('next')
    else:
        next_url = '1235dfghjkf123'
    rty = "https://accounts.google.com/o/oauth2/auth?client_id=" + \
        settings.GP_CLIENT_ID + "&response_type=code"
    rty += "&scope=https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/userinfo.email&redirect_uri=" \
        + 'http://' + request.META['HTTP_HOST'] + \
        reverse('common:google_login') + "&state=" + next_url
    return HttpResponseRedirect(rty)


def create_lead_from_site(request): # pragma: no cover
    allowed_domains = ['micropyramid.com', 'test.microsite.com:8000', ]
    # add origin_domain = request.get_host() in the post body
    if (request.get_host() in ['sales.micropyramid.com', ] and request.POST.get('origin_domain') in allowed_domains):
        if request.method == 'POST':
            if request.POST.get('full_name', None):
                lead = Lead.objects.create(title=request.POST.get('full_name'), email=request.POST.get(
                    'email'), phone=request.POST.get('phone'), description=request.POST.get('message'),
                    created_from_site=True)
                recipients = User.objects.filter(
                    role='ADMIN').values_list('id', flat=True)
                lead.assigned_to.add(*recipients)
                from leads.tasks import send_email_to_assigned_user
                send_email_to_assigned_user(
                    recipients, lead.id, domain='sales.micropyramid.com',
                    source=request.POST.get('origin_domain'))
                return HttpResponse('Lead Created')
    from django.http import HttpResponseBadRequest
    return HttpResponseBadRequest('Bad Request')


def activate_user(request, uidb64, token, activation_key): # pragma: no cover
    profile = get_object_or_404(Profile, activation_key=activation_key)
    if profile.user:
        if timezone.now() > profile.key_expires:
            resend_url = reverse('common:resend_activation_link', args=(profile.user.id,))
            link_content = '<a href="{}">Click Here</a> to resend the activation link.'.format(
                resend_url)
            message_content = 'Your activation link has expired, {}'.format(
                link_content)
            messages.info(request, message_content)
            return render(request, 'login.html')
        else:
            try:
                uid = force_text(urlsafe_base64_decode(uidb64))
                user = User.objects.get(pk=uid)
            except(TypeError, ValueError, OverflowError, User.DoesNotExist):
                user = None
            if user is not None and account_activation_token.check_token(user, token):
                user.is_active = True
                user.save()
                login(request, user)
                if user.has_sales_access:
                    return HttpResponseRedirect('/')
                elif user.has_marketing_access:
                    return redirect('marketing:dashboard')
                else:
                    return HttpResponseRedirect('/')
                # return HttpResponse('Thank you for your email confirmation. Now you can login your account.')
            else:
                return HttpResponse('Activation link is invalid!')


def resend_activation_link(request, userId): # pragma: no cover
    user = get_object_or_404(User, pk=userId)
    kwargs = {'user_email': user.email, 'domain': request.get_host(), 'protocol': request.scheme}
    resend_activation_link_to_user.delay(**kwargs)
    return HttpResponseRedirect('/')
