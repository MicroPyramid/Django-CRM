import json
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.views.generic import CreateView, UpdateView, DetailView, ListView, TemplateView, View
from accounts.models import Account, Tags
from common.models import User, Comment, Attachments
from common.utils import STAGES, SOURCES, CURRENCY_CODES
from contacts.models import Contact
from opportunity.forms import OpportunityForm, OpportunityCommentForm, OpportunityAttachmentForm
from opportunity.models import Opportunity
from django.urls import reverse
from django.db.models import Q
from django.core.exceptions import PermissionDenied


class OpportunityListView(LoginRequiredMixin, TemplateView):
    model = Opportunity
    context_object_name = "opportunity_list"
    template_name = "opportunity.html"

    def get_queryset(self):
        queryset = self.model.objects.all().prefetch_related("contacts", "account")
        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            queryset = queryset.filter(
                Q(assigned_to__in=[self.request.user]) | Q(created_by=self.request.user.id))

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
        return queryset

    def get_context_data(self, **kwargs):
        context = super(OpportunityListView, self).get_context_data(**kwargs)
        context["opportunity_list"] = self.get_queryset()
        context["accounts"] = Account.objects.filter(status="open")
        context["contacts"] = Contact.objects.all()
        context["stages"] = STAGES
        context["sources"] = SOURCES
        context["per_page"] = self.request.POST.get('per_page')

        search = False
        if (
            self.request.POST.get('name') or self.request.POST.get('stage') or
            self.request.POST.get('lead_source') or self.request.POST.get('account') or
            self.request.POST.get('contacts')
        ):
            search = True

        context["search"] = search
        return context

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)


class CreateOpportunityView(LoginRequiredMixin, CreateView):
    model = Opportunity
    form_class = OpportunityForm
    template_name = "create_opportunity.html"

    def dispatch(self, request, *args, **kwargs):
        self.users = User.objects.filter(is_active=True).order_by('email')
        self.accounts = Account.objects.filter(status="open")
        self.contacts = Contact.objects.all()
        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            self.accounts = Account.objects.filter(
                created_by=self.request.user)
            self.contacts = Contact.objects.filter(
                Q(assigned_to__in=[self.request.user]) | Q(created_by=self.request.user))
        return super(CreateOpportunityView, self).dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(CreateOpportunityView, self).get_form_kwargs()
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
        opportunity_obj = form.save(commit=False)
        opportunity_obj.created_by = self.request.user
        if self.request.POST.get('stage') in ['CLOSED WON', 'CLOSED LOST']:
            opportunity_obj.closed_by = self.request.user
        opportunity_obj.save()
        if self.request.POST.getlist('assigned_to', []):
            opportunity_obj.assigned_to.add(
                *self.request.POST.getlist('assigned_to'))
            assigned_to_list = self.request.POST.getlist('assigned_to')
            current_site = get_current_site(self.request)
            for assigned_to_user in assigned_to_list:
                user = get_object_or_404(User, pk=assigned_to_user)
                mail_subject = 'Assigned to opportunity.'
                message = render_to_string('assigned_to/opportunity_assigned.html', {
                    'user': user,
                    'domain': current_site.domain,
                    'protocol': self.request.scheme,
                    'opportunity': opportunity_obj
                })
                email = EmailMessage(mail_subject, message, to=[user.email])
                email.content_subtype = "html"
                email.send()
        if self.request.POST.getlist('contacts', []):
            opportunity_obj.contacts.add(
                *self.request.POST.getlist('contacts'))
        if self.request.POST.get('tags', ''):
            tags = self.request.POST.get("tags")
            splitted_tags = tags.split(",")
            for t in splitted_tags:
                tag = Tags.objects.filter(name=t.lower())
                if tag:
                    tag = tag[0]
                else:
                    tag = Tags.objects.create(name=t.lower())
                opportunity_obj.tags.add(tag)
        if self.request.FILES.get('oppurtunity_attachment'):
            attachment = Attachments()
            attachment.created_by = self.request.user
            attachment.file_name = self.request.FILES.get(
                'oppurtunity_attachment').name
            attachment.opportunity = opportunity_obj
            attachment.attachment = self.request.FILES.get(
                'oppurtunity_attachment')
            attachment.save()
        if self.request.is_ajax():
            return JsonResponse({'error': False})
        if self.request.POST.get("savenewform"):
            return redirect("opportunities:save")
        if self.request.POST.get('from_account'):
            from_account = self.request.POST.get('from_account')
            return redirect("accounts:view_account", pk=from_account)
        return redirect('opportunities:list')

    def form_invalid(self, form):
        if self.request.is_ajax():
            return JsonResponse({'error': True, 'opportunity_errors': form.errors})
        return self.render_to_response(
            self.get_context_data(form=form))

    def get_context_data(self, **kwargs):
        context = super(CreateOpportunityView, self).get_context_data(**kwargs)
        context["opportunity_form"] = context["form"]

        context["accounts"] = self.accounts
        if self.request.GET.get('view_account'):
            context['account'] = get_object_or_404(
                Account, id=self.request.GET.get('view_account'))
        context["contacts"] = self.contacts
        context["users"] = self.users
        context["currencies"] = CURRENCY_CODES
        context["stages"] = STAGES
        context["sources"] = SOURCES
        context["assignedto_list"] = [
            int(i) for i in self.request.POST.getlist('assigned_to', []) if i]

        context["contacts_list"] = [
            int(i) for i in self.request.POST.getlist('contacts', []) if i]
        return context


class OpportunityDetailView(LoginRequiredMixin, DetailView):
    model = Opportunity
    context_object_name = "opportunity_record"
    template_name = "view_opportunity.html"

    def get_queryset(self):
        queryset = super(OpportunityDetailView, self).get_queryset()
        queryset = queryset.prefetch_related("contacts", "account")
        return queryset

    def get_context_data(self, **kwargs):
        context = super(OpportunityDetailView, self).get_context_data(**kwargs)
        user_assgn_list = [i.id for i in context['object'].assigned_to.all()]
        if self.request.user == context['object'].created_by:
            user_assgn_list.append(self.request.user.id)
        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            if self.request.user.id not in user_assgn_list:
                raise PermissionDenied
        assigned_data = []
        for each in context['opportunity_record'].assigned_to.all():
            assigned_dict = {}
            assigned_dict['id'] = each.id
            assigned_dict['name'] = each.email
            assigned_data.append(assigned_dict)

        comments = context["opportunity_record"].opportunity_comments.all()
        context.update({
            "comments": comments, 'attachments': context["opportunity_record"].opportunity_attachment.all(),
            "assigned_data": json.dumps(assigned_data)})
        return context


class UpdateOpportunityView(LoginRequiredMixin, UpdateView):
    model = Opportunity
    form_class = OpportunityForm
    template_name = "create_opportunity.html"

    def dispatch(self, request, *args, **kwargs):
        self.users = User.objects.filter(is_active=True).order_by('email')
        self.accounts = Account.objects.filter(status="open")
        self.contacts = Contact.objects.all()
        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            self.accounts = Account.objects.filter(
                created_by=self.request.user)
            self.contacts = Contact.objects.filter(
                Q(assigned_to__in=[self.request.user]) | Q(created_by=self.request.user))
        return super(UpdateOpportunityView, self).dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(UpdateOpportunityView, self).get_form_kwargs()
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
        opportunity_obj = form.save(commit=False)
        if self.request.POST.get('stage') in ['CLOSED WON', 'CLOSED LOST']:
            opportunity_obj.closed_by = self.request.user
        opportunity_obj.save()

        opportunity_obj.contacts.clear()
        all_members_list = []
        if self.request.POST.getlist('assigned_to', []):
            current_site = get_current_site(self.request)
            assigned_form_users = form.cleaned_data.get(
                'assigned_to').values_list('id', flat=True)
            all_members_list = list(
                set(list(assigned_form_users)) - set(list(assigned_to_ids)))
            if len(all_members_list):
                for assigned_to_user in all_members_list:
                    user = get_object_or_404(User, pk=assigned_to_user)
                    mail_subject = 'Assigned to opportunity.'
                    message = render_to_string('assigned_to/opportunity_assigned.html', {
                        'user': user,
                        'domain': current_site.domain,
                        'protocol': self.request.scheme,
                        'opportunity': opportunity_obj
                    })
                    email = EmailMessage(
                        mail_subject, message, to=[user.email])
                    email.content_subtype = "html"
                    email.send()

            opportunity_obj.assigned_to.clear()
            opportunity_obj.assigned_to.add(
                *self.request.POST.getlist('assigned_to'))
        else:
            opportunity_obj.assigned_to.clear()

        if self.request.POST.getlist('contacts', []):
            opportunity_obj.contacts.add(
                *self.request.POST.getlist('contacts'))
        opportunity_obj.tags.clear()
        if self.request.POST.get('tags', ''):
            tags = self.request.POST.get("tags")
            splitted_tags = tags.split(",")
            for t in splitted_tags:
                tag = Tags.objects.filter(name=t.lower())
                if tag:
                    tag = tag[0]
                else:
                    tag = Tags.objects.create(name=t.lower())
                opportunity_obj.tags.add(tag)
        if self.request.FILES.get('oppurtunity_attachment'):
            attachment = Attachments()
            attachment.created_by = self.request.user
            attachment.file_name = self.request.FILES.get(
                'oppurtunity_attachment').name
            attachment.opportunity = opportunity_obj
            attachment.attachment = self.request.FILES.get(
                'oppurtunity_attachment')
            attachment.save()
        if self.request.POST.get('from_account'):
            from_account = self.request.POST.get('from_account')
            return redirect("accounts:view_account", pk=from_account)
        if self.request.is_ajax():
            return JsonResponse({'error': False})
        return redirect('opportunities:list')

    def form_invalid(self, form):
        if self.request.is_ajax():
            return JsonResponse({'error': True, 'opportunity_errors': form.errors})
        return self.render_to_response(
            self.get_context_data(form=form))

    def get_context_data(self, **kwargs):
        context = super(UpdateOpportunityView, self).get_context_data(**kwargs)
        context["opportunity_obj"] = self.object
        user_assgn_list = [
            i.id for i in context["opportunity_obj"].assigned_to.all()]
        if self.request.user == context['opportunity_obj'].created_by:
            user_assgn_list.append(self.request.user.id)
        if self.request.user.role != "ADMIN" and not self.request.user.is_superuser:
            if self.request.user.id not in user_assgn_list:
                raise PermissionDenied
        context["opportunity_form"] = context["form"]
        context["accounts"] = self.accounts
        if self.request.GET.get('view_account'):
            context['account'] = get_object_or_404(
                Account, id=self.request.GET.get('view_account'))
        context["contacts"] = self.contacts
        context["users"] = self.users
        context["currencies"] = CURRENCY_CODES
        context["stages"] = STAGES
        context["sources"] = SOURCES
        context["assignedto_list"] = [
            int(i) for i in self.request.POST.getlist('assigned_to', []) if i]
        context["contacts_list"] = [
            int(i) for i in self.request.POST.getlist('contacts', []) if i]

        return context


class DeleteOpportunityView(LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = get_object_or_404(Opportunity, id=kwargs.get("pk"))
        if self.request.user.role == "ADMIN" or self.request.user.is_superuser or self.request.user == self.object.created_by:
            self.object.delete()
            if request.is_ajax():
                return JsonResponse({'error': False})

            if request.GET.get('view_account'):
                account = request.GET.get('view_account')
                return redirect("accounts:view_account", pk=account)

            return redirect("opportunities:list")
        else:
            raise PermissionDenied


class GetContactView(LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        account_id = request.GET.get("account")
        if account_id:
            account = get_object_or_404(Account, id=account_id)
            contacts = Contact.objects.filter(account=account)
        else:
            contacts = Contact.objects.all()
        data = {i.pk: i.first_name for i in contacts.distinct()}
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
                request.user == self.opportunity.created_by or request.user.is_superuser or
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

    def get_context_data(self, **kwargs):
        context = super(GetOpportunitiesView, self).get_context_data(**kwargs)
        context["opportunities"] = self.get_queryset()
        return context


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
                request.user == self.opportunity.created_by or request.user.is_superuser or
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
            "created_by": attachment.created_by.email,
            "download_url": reverse('common:download_attachment', kwargs={'pk': attachment.id}),
            "attachment_display": attachment.get_file_type_display()
        })

    def form_invalid(self, form):
        return JsonResponse({"error": form['attachment'].errors})


class DeleteAttachmentsView(LoginRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        self.object = get_object_or_404(
            Attachments, id=request.POST.get("attachment_id"))
        if (request.user == self.object.created_by or request.user.is_superuser or request.user.role == 'ADMIN'):
            self.object.delete()
            data = {"aid": request.POST.get("attachment_id")}
            return JsonResponse(data)

        data = {'error': "You don't have permission to delete this attachment."}
        return JsonResponse(data)
