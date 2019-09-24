import json
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.views.generic import (CreateView, DetailView,
                                  ListView, TemplateView, View)
from accounts.models import Account, Tags
from common.models import User, Comment, Attachments
from common.utils import STAGES, SOURCES, CURRENCY_CODES
from contacts.models import Contact
from opportunity.forms import (OpportunityForm, OpportunityCommentForm,
                               OpportunityAttachmentForm)
from opportunity.models import Opportunity
from django.urls import reverse
from django.db.models import Q
from django.core.exceptions import PermissionDenied
from common.tasks import send_email_user_mentions
from opportunity.tasks import send_email_to_assigned_user
from common.access_decorators_mixins import (
    sales_access_required, marketing_access_required, SalesAccessRequiredMixin, MarketingAccessRequiredMixin)
from teams.models import Teams

class OpportunityListView(SalesAccessRequiredMixin, LoginRequiredMixin, TemplateView):
    model = Opportunity
    context_object_name = "opportunity_list"
    template_name = "opportunity.html"

    def get_queryset(self):
        queryset = self.model.objects.all().prefetch_related(
            "contacts", "account")
        if self.request.user.role != "ADMIN" and not \
                self.request.user.is_superuser:
            queryset = queryset.filter(
                Q(assigned_to__in=[self.request.user]) |
                Q(created_by=self.request.user.id))

        if self.request.GET.get('tag', None):
            queryset = queryset.filter(tags__in = self.request.GET.getlist('tag'))

        request_post = self.request.POST
        if request_post:
            if request_post.get('name'):
                queryset = queryset.filter(
                    name__icontains=request_post.get('name'))
            if request_post.get('stage'):
                queryset = queryset.filter(stage=request_post.get('stage'))
            if request_post.get('lead_source'):
                queryset = queryset.filter(
                    lead_source=request_post.get('lead_source'))
            if request_post.get('account'):
                queryset = queryset.filter(
                    account_id=request_post.get('account'))
            if request_post.get('contacts'):
                queryset = queryset.filter(
                    contacts=request_post.get('contacts'))
            if request_post.get('tag'):
                queryset = queryset.filter(tags__in=request_post.getlist('tag'))
        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super(OpportunityListView, self).get_context_data(**kwargs)
        context["opportunity_list"] = self.get_queryset()
        context["accounts"] = Account.objects.filter(status="open")
        context["contacts"] = Contact.objects.all()
        context["stages"] = STAGES
        context["sources"] = SOURCES
        context["per_page"] = self.request.POST.get('per_page')
        tag_ids = list(set(Opportunity.objects.values_list('tags', flat=True)))
        context["tags"] = Tags.objects.filter(id__in=tag_ids)
        if self.request.POST.get('tag', None):
            context["request_tags"] = self.request.POST.getlist('tag')
        elif self.request.GET.get('tag', None):
            context["request_tags"] = self.request.GET.getlist('tag')
        else:
            context["request_tags"] = None
        search = False
        if (
            self.request.POST.get('name') or self.request.POST.get('stage') or
            self.request.POST.get('lead_source') or
            self.request.POST.get('account') or
            self.request.POST.get('contacts')
        ):
            search = True

        context["search"] = search
        return context

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)


@login_required
@sales_access_required
def create_opportunity(request):
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
    if request.POST:
        form = OpportunityForm(request.POST, request.FILES, **kwargs_data)
        if form.is_valid():
            opportunity_obj = form.save(commit=False)
            opportunity_obj.created_by = request.user
            if request.POST.get('stage') in ['CLOSED WON', 'CLOSED LOST']:
                opportunity_obj.closed_by = request.user
            opportunity_obj.save()
            if request.POST.getlist('assigned_to', []):
                opportunity_obj.assigned_to.add(
                    *request.POST.getlist('assigned_to'))
                # assigned_to_list = request.POST.getlist('assigned_to')
                # current_site = get_current_site(request)
                # recipients = assigned_to_list
                # send_email_to_assigned_user.delay(recipients, opportunity_obj.id, domain=current_site.domain,
                #     protocol=request.scheme)
                # for assigned_to_user in assigned_to_list:
                #     user = get_object_or_404(User, pk=assigned_to_user)
                #     mail_subject = 'Assigned to opportunity.'
                #     message = render_to_string(
                #         'assigned_to/opportunity_assigned.html', {
                #             'user': user,
                #             'domain': current_site.domain,
                #             'protocol': request.scheme,
                #             'opportunity': opportunity_obj
                #         })
                #     email = EmailMessage(
                #         mail_subject, message, to=[user.email])
                #     email.content_subtype = "html"
                #     email.send()
            if request.POST.getlist('teams', []):
                user_ids = Teams.objects.filter(id__in=request.POST.getlist('teams')).values_list('users', flat=True)
                assinged_to_users_ids = opportunity_obj.assigned_to.all().values_list('id', flat=True)
                for user_id in user_ids:
                    if user_id not in assinged_to_users_ids:
                        opportunity_obj.assigned_to.add(user_id)

            if request.POST.getlist('teams', []):
                opportunity_obj.teams.add(*request.POST.getlist('teams'))

            current_site = get_current_site(request)
            recipients = list(opportunity_obj.assigned_to.all().values_list('id', flat=True))
            send_email_to_assigned_user.delay(recipients, opportunity_obj.id, domain=current_site.domain,
                protocol=request.scheme)

            if request.POST.getlist('contacts', []):
                opportunity_obj.contacts.add(
                    *request.POST.getlist('contacts'))
            if request.POST.get('tags', ''):
                tags = request.POST.get("tags")
                splitted_tags = tags.split(",")
                for t in splitted_tags:
                    tag = Tags.objects.filter(name=t.lower())
                    if tag:
                        tag = tag[0]
                    else:
                        tag = Tags.objects.create(name=t.lower())
                    opportunity_obj.tags.add(tag)
            if request.FILES.get('oppurtunity_attachment'):
                attachment = Attachments()
                attachment.created_by = request.user
                attachment.file_name = request.FILES.get(
                    'oppurtunity_attachment').name
                attachment.opportunity = opportunity_obj
                attachment.attachment = request.FILES.get(
                    'oppurtunity_attachment')
                attachment.save()
            success_url = reverse('opportunities:list')
            if request.POST.get("savenewform"):
                success_url = reverse("opportunities:save")
            if request.POST.get('from_account'):
                from_account = request.POST.get('from_account')
                success_url = reverse("accounts:view_account", kwargs={
                                      'pk': from_account})
                # print(success_url)
            return JsonResponse({'error': False, 'success_url': success_url})
        return JsonResponse({'error': True, 'errors': form.errors})
    context = {}
    context["opportunity_form"] = OpportunityForm(**kwargs_data)

    context["accounts"] = accounts
    if request.GET.get('view_account'):
        context['account'] = get_object_or_404(
            Account, id=request.GET.get('view_account'))
    context["contacts"] = contacts
    context["users"] = kwargs_data['assigned_to']
    context["currencies"] = CURRENCY_CODES
    context["stages"] = STAGES
    context["sources"] = SOURCES
    context["teams"] = Teams.objects.all()
    context["assignedto_list"] = [
        int(i) for i in request.POST.getlist('assigned_to', []) if i]

    context["contacts_list"] = [
        int(i) for i in request.POST.getlist('contacts', []) if i]
    return render(request, "create_opportunity.html", context)


class OpportunityDetailView(SalesAccessRequiredMixin, LoginRequiredMixin, DetailView):
    model = Opportunity
    context_object_name = "opportunity_record"
    template_name = "view_opportunity.html"

    def get_queryset(self):
        queryset = super(OpportunityDetailView, self).get_queryset()
        queryset = queryset.prefetch_related("contacts", "account")
        return queryset

    def get_context_data(self, **kwargs):
        context = super(OpportunityDetailView, self).get_context_data(**kwargs)
        user_assgn_list = [
            assigned_to.id for assigned_to in
            context['object'].assigned_to.all()]
        user_assigned_accounts = set(self.request.user.account_assigned_users.values_list('id', flat=True))
        if context['object'].account:
            opportunity_account = set([context['object'].account.id])
        else:
            opportunity_account = set()
        if user_assigned_accounts.intersection(opportunity_account):
            user_assgn_list.append(self.request.user.id)
        if self.request.user == context['object'].created_by:
            user_assgn_list.append(self.request.user.id)
        if self.request.user.role != "ADMIN" and not \
                self.request.user.is_superuser:
            if self.request.user.id not in user_assgn_list:
                raise PermissionDenied
        assigned_data = []
        for each in context['opportunity_record'].assigned_to.all():
            assigned_dict = {}
            assigned_dict['id'] = each.id
            assigned_dict['name'] = each.email
            assigned_data.append(assigned_dict)

        comments = context["opportunity_record"].opportunity_comments.all()

        if self.request.user.is_superuser or self.request.user.role == 'ADMIN':
            users_mention = list(User.objects.filter(is_active=True).values('username'))
        elif self.request.user != context['object'].created_by:
            users_mention = [{'username': context['object'].created_by.username}]
        else:
            users_mention = list(context['object'].assigned_to.all().values('username'))

        context.update({
            "comments": comments,
            'attachments': context[
                "opportunity_record"].opportunity_attachment.all(),
            "users_mention": users_mention,
            "assigned_data": json.dumps(assigned_data)})
        return context


@login_required
@sales_access_required
def update_opportunity(request, pk):
    opportunity_object = Opportunity.objects.filter(pk=pk).first()
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
    form = OpportunityForm(instance=opportunity_object, **kwargs_data)

    if request.POST:
        form = form = OpportunityForm(
            request.POST, request.FILES,
            instance=opportunity_object, **kwargs_data)
        if form.is_valid():
            assigned_to_ids = opportunity_object.assigned_to.all().values_list(
                'id', flat=True)
            opportunity_obj = form.save(commit=False)
            if request.POST.get('stage') in ['CLOSED WON', 'CLOSED LOST']:
                opportunity_obj.closed_by = request.user
            previous_assigned_to_users = list(opportunity_obj.assigned_to.all().values_list('id', flat=True))
            opportunity_obj.save()

            opportunity_obj.contacts.clear()
            all_members_list = []
            if request.POST.getlist('assigned_to', []):
                current_site = get_current_site(request)
                assigned_form_users = form.cleaned_data.get(
                    'assigned_to').values_list('id', flat=True)
                all_members_list = list(
                    set(list(assigned_form_users)) -
                    set(list(assigned_to_ids)))
                # current_site = get_current_site(request)
                # recipients = all_members_list
                # send_email_to_assigned_user.delay(recipients, opportunity_obj.id, domain=current_site.domain,
                #     protocol=request.scheme)
                # if all_members_list:
                #     for assigned_to_user in all_members_list:
                #         user = get_object_or_404(User, pk=assigned_to_user)
                #         mail_subject = 'Assigned to opportunity.'
                #         message = render_to_string(
                #             'assigned_to/opportunity_assigned.html', {
                #                 'user': user,
                #                 'domain': current_site.domain,
                #                 'protocol': request.scheme,
                #                 'opportunity': opportunity_obj
                #             })
                #         email = EmailMessage(
                #             mail_subject, message, to=[user.email])
                #         email.content_subtype = "html"
                #         email.send()

                opportunity_obj.assigned_to.clear()
                opportunity_obj.assigned_to.add(
                    *request.POST.getlist('assigned_to'))
            else:
                opportunity_obj.assigned_to.clear()

            if request.POST.getlist('teams', []):
                user_ids = Teams.objects.filter(id__in=request.POST.getlist('teams')).values_list('users', flat=True)
                assinged_to_users_ids = opportunity_obj.assigned_to.all().values_list('id', flat=True)
                for user_id in user_ids:
                    if user_id not in assinged_to_users_ids:
                        opportunity_obj.assigned_to.add(user_id)

            if request.POST.getlist('teams', []):
                opportunity_obj.teams.clear()
                opportunity_obj.teams.add(*request.POST.getlist('teams'))
            else:
                opportunity_obj.teams.clear()

            current_site = get_current_site(request)
            assigned_to_list = list(opportunity_obj.assigned_to.all().values_list('id', flat=True))
            recipients = list(set(assigned_to_list) - set(previous_assigned_to_users))
            send_email_to_assigned_user.delay(recipients, opportunity_obj.id, domain=current_site.domain,
                protocol=request.scheme)

            if request.POST.getlist('contacts', []):
                opportunity_obj.contacts.add(
                    *request.POST.getlist('contacts'))
            opportunity_obj.tags.clear()
            if request.POST.get('tags', ''):
                tags = request.POST.get("tags")
                splitted_tags = tags.split(",")
                for t in splitted_tags:
                    tag = Tags.objects.filter(name=t.lower())
                    if tag:
                        tag = tag[0]
                    else:
                        tag = Tags.objects.create(name=t.lower())
                    opportunity_obj.tags.add(tag)
            if request.FILES.get('oppurtunity_attachment'):
                attachment = Attachments()
                attachment.created_by = request.user
                attachment.file_name = request.FILES.get(
                    'oppurtunity_attachment').name
                attachment.opportunity = opportunity_obj
                attachment.attachment = request.FILES.get(
                    'oppurtunity_attachment')
                attachment.save()
            success_url = reverse('opportunities:list')
            if request.POST.get('from_account'):
                from_account = request.POST.get('from_account')
                success_url = reverse("accounts:view_account", kwargs={
                                      'pk': from_account})
            return JsonResponse({'error': False, 'success_url': success_url})
        return JsonResponse({'error': True, 'errors': form.errors})
    context = {}
    context["opportunity_obj"] = opportunity_object
    user_assgn_list = [
        assigned_to.id for assigned_to in
        context["opportunity_obj"].assigned_to.all()]
    if request.user == context['opportunity_obj'].created_by:
        user_assgn_list.append(request.user.id)
    if request.user.role != "ADMIN" and not request.user.is_superuser:
        if request.user.id not in user_assgn_list:
            raise PermissionDenied
    context["opportunity_form"] = form
    context["accounts"] = accounts
    if request.GET.get('view_account'):
        context['account'] = get_object_or_404(
            Account, id=request.GET.get('view_account'))
    context["contacts"] = contacts
    context["users"] = kwargs_data['assigned_to']
    context["currencies"] = CURRENCY_CODES
    context["stages"] = STAGES
    context["sources"] = SOURCES
    context["teams"] = Teams.objects.all()
    context["assignedto_list"] = [
        int(i) for i in request.POST.getlist('assigned_to', []) if i]
    context["contacts_list"] = [
        int(i) for i in request.POST.getlist('contacts', []) if i]
    return render(request, "create_opportunity.html", context)


class DeleteOpportunityView(SalesAccessRequiredMixin, LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = get_object_or_404(Opportunity, id=kwargs.get("pk"))
        if (self.request.user.role == "ADMIN" or
            self.request.user.is_superuser or
                self.request.user == self.object.created_by):
            self.object.delete()
            if request.is_ajax():
                return JsonResponse({'error': False})

            if request.GET.get('view_account'):
                account = request.GET.get('view_account')
                return redirect("accounts:view_account", pk=account)

            return redirect("opportunities:list")
        raise PermissionDenied


class GetContactView(LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        account_id = request.GET.get("account")
        if account_id:
            account = get_object_or_404(Account, id=account_id)
            contacts = account.contacts.all()
        else:
            contacts = Contact.objects.all()
        data = {contact.pk:
                contact.first_name for contact in contacts.distinct()}
        return JsonResponse(data)


class AddCommentView(LoginRequiredMixin, CreateView):
    model = Comment
    form_class = OpportunityCommentForm
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        self.object = None
        self.opportunity = get_object_or_404(
            Opportunity, id=request.POST.get('opportunityid'))
        if (
                request.user in self.opportunity.assigned_to.all() or
                request.user == self.opportunity.created_by or
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
        comment.opportunity = self.opportunity
        comment.save()
        comment_id = comment.id
        current_site = get_current_site(self.request)
        send_email_user_mentions.delay(comment_id, 'opportunity', domain=current_site.domain,
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
            form = OpportunityCommentForm(
                request.POST, instance=self.comment_obj)
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
        send_email_user_mentions.delay(comment_id, 'opportunity', domain=current_site.domain,
            protocol=self.request.scheme)
        return JsonResponse({
            "commentid": self.comment_obj.id,
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


class GetOpportunitiesView(LoginRequiredMixin, ListView):
    model = Opportunity
    context_object_name = "opportunities"
    template_name = "opportunities_list.html"


class AddAttachmentsView(LoginRequiredMixin, CreateView):
    model = Attachments
    form_class = OpportunityAttachmentForm
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        self.object = None
        self.opportunity = get_object_or_404(
            Opportunity, id=request.POST.get('opportunityid'))
        if (
                request.user in self.opportunity.assigned_to.all() or
                request.user == self.opportunity.created_by or
                request.user.is_superuser or
                request.user.role == 'ADMIN'
        ):
            form = self.get_form()
            if form.is_valid():
                return self.form_valid(form)
            return self.form_invalid(form)

        data = {'error': "You don't have permission to add attachment."}
        return JsonResponse(data)

    def form_valid(self, form):
        attachment = form.save(commit=False)
        attachment.created_by = self.request.user
        attachment.file_name = attachment.attachment.name
        attachment.opportunity = self.opportunity
        attachment.save()
        return JsonResponse({
            "attachment_id": attachment.id,
            "attachment": attachment.file_name,
            "attachment_url": attachment.attachment.url,
            "created_on": attachment.created_on,
            "created_on_arrow": attachment.created_on_arrow,
            "created_by": attachment.created_by.email,
            "download_url": reverse('common:download_attachment',
                                    kwargs={'pk': attachment.id}),
            "attachment_display": attachment.get_file_type_display(),
            "file_type": attachment.file_type()
        })

    def form_invalid(self, form):
        return JsonResponse({"error": form['attachment'].errors})


class DeleteAttachmentsView(LoginRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        self.object = get_object_or_404(
            Attachments, id=request.POST.get("attachment_id"))
        if (request.user == self.object.created_by or
            request.user.is_superuser or
                request.user.role == 'ADMIN'):
            self.object.delete()
            data = {"aid": request.POST.get("attachment_id")}
            return JsonResponse(data)

        data = {
            'error': "You don't have permission to delete this attachment."}
        return JsonResponse(data)
