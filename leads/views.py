import json
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.db.models import Q
from django.forms.models import modelformset_factory
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.generic import (
    CreateView, UpdateView, DetailView, ListView, TemplateView, View)

from accounts.models import Account, Tags
from common.models import User, Comment, Attachments
from common.utils import LEAD_STATUS, LEAD_SOURCE, COUNTRIES
from common import status
from contacts.models import Contact
from leads.models import Lead
from leads.forms import LeadCommentForm, LeadForm, LeadAttachmentForm
from planner.models import Event, Reminder
from planner.forms import ReminderForm
from leads.tasks import send_lead_assigned_emails


class LeadListView(LoginRequiredMixin, TemplateView):
    model = Lead
    context_object_name = "lead_obj"
    template_name = "leads.html"

    def get_queryset(self):
        queryset = self.model.objects.all().exclude(status='converted')
        request_post = self.request.POST
        if request_post:
            if request_post.get('name'):
                queryset = queryset.filter(
                    Q(first_name__icontains=request_post.get('name')) &
                    Q(last_name__icontains=request_post.get('name')))
            if request_post.get('city'):
                queryset = queryset.filter(city__icontains=request_post.get('city'))
            if request_post.get('email'):
                queryset = queryset.filter(email__icontains=request_post.get('email'))
            if request_post.get('status'):
                queryset = queryset.filter(status=request_post.get('status'))
            if request_post.get('tag'):
                queryset = queryset.filter(tags__in=request_post.get('tag'))
            if request_post.get('source'):
                queryset = queryset.filter(source=request_post.get('source'))
            if request_post.getlist('assigned_to'):
                queryset = queryset.filter(assigned_to__id__in=request_post.getlist('assigned_to'))
        return queryset

    def get_context_data(self, **kwargs):
        context = super(LeadListView, self).get_context_data(**kwargs)
        # context["lead_obj"] = self.get_queryset()
        open_leads = self.get_queryset().exclude(status='dead')
        close_leads = self.get_queryset().filter(status='dead')
        context["status"] = LEAD_STATUS
        context["open_leads"] = open_leads
        context["close_leads"] = close_leads
        context["per_page"] = self.request.POST.get('per_page')
        context["source"] = LEAD_SOURCE
        context["users"] = User.objects.filter(is_active=True).order_by('email')
        context["assignedto_list"] = [
            int(i) for i in self.request.POST.getlist('assigned_to', []) if i]

        context['tags'] = Tags.objects.all()

        tab_status = 'Open'
        if self.request.POST.get('tab_status'):
            tab_status = self.request.POST.get('tab_status')
        context['tab_status'] = tab_status

        return context

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)


class CreateLeadView(LoginRequiredMixin, CreateView):
    model = Lead
    form_class = LeadForm
    template_name = "create_lead.html"

    def dispatch(self, request, *args, **kwargs):
        self.users = User.objects.filter(is_active=True).order_by('email')
        return super(CreateLeadView, self).dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(CreateLeadView, self).get_form_kwargs()
        kwargs.update({"assigned_to": self.users})
        return kwargs

    def post(self, request, *args, **kwargs):
        self.object = None
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)

        return self.form_invalid(form)

    def form_valid(self, form):

        lead_obj = form.save(commit=False)
        lead_obj.created_by = self.request.user
        lead_obj.save()
        if self.request.POST.get('tags', ''):
            tags = self.request.POST.get("tags")
            splitted_tags = tags.split(",")
            for t in splitted_tags:
                tag = Tags.objects.filter(name=t)
                if tag:
                    tag = tag[0]
                else:
                    tag = Tags.objects.create(name=t)
                lead_obj.tags.add(tag)
        if self.request.POST.getlist('assigned_to', []):
            lead_obj.assigned_to.add(*self.request.POST.getlist('assigned_to'))
            assigned_to_list = self.request.POST.getlist('assigned_to')
            current_site = get_current_site(self.request)
            for assigned_to_user in assigned_to_list:
                user = get_object_or_404(User, pk=assigned_to_user)
                mail_subject = 'Assigned to lead.'
                message = render_to_string('assigned_to/leads_assigned.html', {
                    'user': user,
                    'domain': current_site.domain,
                    'protocol': self.request.scheme,
                    'lead': lead_obj
                })
                email = EmailMessage(mail_subject, message, to=[user.email])
                email.content_subtype = "html"
                email.send()

        if self.request.FILES.get('lead_attachment'):
            attachment = Attachments()
            attachment.created_by = self.request.user
            attachment.file_name = self.request.FILES.get('lead_attachment').name
            attachment.lead = lead_obj
            attachment.attachment = self.request.FILES.get('lead_attachment')
            attachment.save()

        if self.request.POST.get('status') == "converted":
            account_object = Account.objects.create(
                created_by=self.request.user, name=lead_obj.account_name,
                email=lead_obj.email, phone=lead_obj.phone,
                description=self.request.POST.get('description'),
                website=self.request.POST.get('website'),
            )
            account_object.billing_address_line = lead_obj.address_line
            account_object.billing_street = lead_obj.street
            account_object.billing_city = lead_obj.city
            account_object.billing_state = lead_obj.state
            account_object.billing_postcode = lead_obj.postcode
            account_object.billing_country = lead_obj.country
            for tag in lead_obj.tags.all():
                account_object.tags.add(tag)

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
                    email.content_subtype = "html"
                    email.send()

            account_object.save()
        if self.request.POST.get("savenewform"):
            return redirect("leads:add_lead")
        return redirect('leads:list')

    def form_invalid(self, form):
        return self.render_to_response(
            self.get_context_data(form=form))

    def get_context_data(self, **kwargs):
        context = super(CreateLeadView, self).get_context_data(**kwargs)
        context["lead_form"] = context["form"]
        context["accounts"] = Account.objects.all()
        context["users"] = self.users
        context["countries"] = COUNTRIES
        context["status"] = LEAD_STATUS
        context["source"] = LEAD_SOURCE
        context["assignedto_list"] = [
            int(i) for i in self.request.POST.getlist('assigned_to', []) if i]

        return context


class LeadDetailView(LoginRequiredMixin, DetailView):
    model = Lead
    context_object_name = "lead_record"
    template_name = "view_leads.html"

    def get_context_data(self, **kwargs):
        context = super(LeadDetailView, self).get_context_data(**kwargs)
        comments = Comment.objects.filter(lead__id=self.object.id).order_by('-id')
        attachments = Attachments.objects.filter(lead__id=self.object.id).order_by('-id')
        events = Event.objects.filter(
            Q(created_by=self.request.user) | Q(updated_by=self.request.user)
        ).filter(attendees_leads=context["lead_record"])
        meetings = events.filter(event_type='Meeting').order_by('-id')
        calls = events.filter(event_type='Call').order_by('-id')
        RemindersFormSet = modelformset_factory(Reminder, form=ReminderForm, can_delete=True)
        reminder_form_set = RemindersFormSet({
            'form-TOTAL_FORMS': '1',
            'form-INITIAL_FORMS': '0',
            'form-MAX_NUM_FORMS': '10',
        })

        assigned_data = []
        for each in context['lead_record'].assigned_to.all():
            assigned_dict = {}
            assigned_dict['id'] = each.id
            assigned_dict['name'] = each.email
            assigned_data.append(assigned_dict)

        context.update({
            "attachments": attachments, "comments": comments, "status": LEAD_STATUS, "countries": COUNTRIES,
            "reminder_form_set": reminder_form_set, "meetings": meetings, "calls": calls,
            "assigned_data": json.dumps(assigned_data)})
        return context


class UpdateLeadView(LoginRequiredMixin, UpdateView):
    model = Lead
    form_class = LeadForm
    template_name = "create_lead.html"

    def dispatch(self, request, *args, **kwargs):
        self.error = ""
        self.users = User.objects.filter(is_active=True).order_by('email')
        return super(UpdateLeadView, self).dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super(UpdateLeadView, self).get_initial()
        status = self.request.GET.get('status', None)
        if status:
            initial.update({"status": status})
        return initial

    def get_form_kwargs(self):
        kwargs = super(UpdateLeadView, self).get_form_kwargs()
        kwargs.update({"assigned_to": self.users})
        return kwargs

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        status = request.GET.get('status', None)
        if status:
            self.error = "This field is required."
            self.object.status = "converted"
        return super(UpdateLeadView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()

        if request.POST.get('status') == "converted":
            form.fields['account_name'].required = True
        else:
            form.fields['account_name'].required = False
        if form.is_valid():
            return self.form_valid(form)
    
        return self.form_invalid(form)

    def form_valid(self, form):
        assigned_to_ids = self.get_object().assigned_to.all().values_list('id', flat=True)
        lead_obj = form.save(commit=False)
        lead_obj.save()
        lead_obj.tags.clear()
        all_members_list = []
        if self.request.POST.get('tags', ''):
            tags = self.request.POST.get("tags")
            splitted_tags = tags.split(",")
            for t in splitted_tags:
                tag = Tags.objects.filter(name=t)
                if tag:
                    tag = tag[0]
                else:
                    tag = Tags.objects.create(name=t)
                lead_obj.tags.add(tag)
        if self.request.POST.getlist('assigned_to', []):
            if self.request.POST.get('status') != "converted":

                current_site = get_current_site(self.request)

                assigned_form_users = form.cleaned_data.get('assigned_to').values_list('id', flat=True)
                all_members_list = list(set(list(assigned_form_users)) - set(list(assigned_to_ids)))
                if len(all_members_list):
                    for assigned_to_user in all_members_list:
                        user = get_object_or_404(User, pk=assigned_to_user)
                        mail_subject = 'Assigned to lead.'
                        message = render_to_string('assigned_to/leads_assigned.html', {
                            'user': user,
                            'domain': current_site.domain,
                            'protocol': self.request.scheme,
                            'lead': lead_obj
                        })
                        email = EmailMessage(mail_subject, message, to=[user.email])
                        email.content_subtype = "html"
                        email.send()

            lead_obj.assigned_to.clear()
            lead_obj.assigned_to.add(*self.request.POST.getlist('assigned_to'))
        else:
            lead_obj.assigned_to.clear()


        if self.request.FILES.get('lead_attachment'):
            attachment = Attachments()
            attachment.created_by = self.request.user
            attachment.file_name = self.request.FILES.get('lead_attachment').name
            attachment.lead = lead_obj
            attachment.attachment = self.request.FILES.get('lead_attachment')
            attachment.save()

        if self.request.POST.get('status') == "converted":
            account_object = Account.objects.create(
                created_by=self.request.user, name=lead_obj.account_name,
                email=lead_obj.email, phone=lead_obj.phone,
                description=self.request.POST.get('description'),
                website=self.request.POST.get('website')
            )
            account_object.billing_address_line = lead_obj.address_line
            account_object.billing_street = lead_obj.street
            account_object.billing_city = lead_obj.city
            account_object.billing_state = lead_obj.state
            account_object.billing_postcode = lead_obj.postcode
            account_object.billing_country = lead_obj.country
            for tag in lead_obj.tags.all():
                account_object.tags.add(tag)
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
                    email.content_subtype = "html"
                    email.send()

            account_object.save()
        status = self.request.GET.get('status', None)
        if status:
            return redirect('accounts:list')

        return redirect('leads:list')

    def form_invalid(self, form):
        return self.render_to_response(
            self.get_context_data(form=form))

    def get_context_data(self, **kwargs):
        context = super(UpdateLeadView, self).get_context_data(**kwargs)
        context["lead_obj"] = self.object
        context["lead_form"] = context["form"]
        context["accounts"] = Account.objects.all()
        context["users"] = self.users
        context["countries"] = COUNTRIES
        context["status"] = LEAD_STATUS
        context["source"] = LEAD_SOURCE
        context["error"] = self.error
        context["assignedto_list"] = [
            int(i) for i in self.request.POST.getlist('assigned_to', []) if i]

        return context


class DeleteLeadView(LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = get_object_or_404(Lead, id=kwargs.get("pk"))
        self.object.delete()
        return redirect("leads:list")


class ConvertLeadView(LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        lead_obj = get_object_or_404(Lead, id=kwargs.get("pk"))
        if lead_obj.account_name:
            lead_obj.status = 'converted'
            lead_obj.save()
            account_object = Account.objects.create(
                created_by=request.user, name=lead_obj.account_name,
                email=lead_obj.email, phone=lead_obj.phone,
                description=lead_obj.description,
                website=lead_obj.website,
                billing_address_line=lead_obj.address_line,
                billing_street=lead_obj.street,
                billing_city=lead_obj.city,
                billing_state=lead_obj.state,
                billing_postcode=lead_obj.postcode,
                billing_country=lead_obj.country
            )
            assignedto_list = lead_obj.assigned_to.all().values_list('id', flat=True)
            account_object.assigned_to.add(*assignedto_list)
            account_object.save()
            current_site = get_current_site(self.request)
            for assigned_to_user in assignedto_list:
                user = get_object_or_404(User, pk=assigned_to_user)
                mail_subject = 'Assigned to account.'
                message = render_to_string('assigned_to/account_assigned.html', {
                    'user': user,
                    'domain': current_site.domain,
                    'protocol': self.request.scheme,
                    'account': account_object
                })
                email = EmailMessage(mail_subject, message, to=[user.email])
                email.content_subtype = "html"
                email.send()
            return redirect("accounts:list")

        return HttpResponseRedirect(
            reverse('leads:edit_lead', kwargs={'pk': lead_obj.id}) + '?status=converted')


class AddCommentView(LoginRequiredMixin, CreateView):
    model = Comment
    form_class = LeadCommentForm
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        self.object = None
        self.lead = get_object_or_404(Lead, id=request.POST.get('leadid'))
        if (
            request.user in self.lead.assigned_to.all() or
            request.user == self.lead.created_by or request.user.is_superuser or
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
        comment.lead = self.lead
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
            form = LeadCommentForm(request.POST, instance=self.comment_obj)
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
        self.object = get_object_or_404(Comment, id=request.POST.get("comment_id"))
        if request.user == self.object.commented_by:
            self.object.delete()
            data = {"cid": request.POST.get("comment_id")}
            return JsonResponse(data)
        
        data = {'error': "You don't have permission to delete this comment."}
        return JsonResponse(data)


class GetLeadsView(LoginRequiredMixin, ListView):
    model = Lead
    context_object_name = "leads"
    template_name = "leads_list.html"

    def get_context_data(self, **kwargs):
        context = super(GetLeadsView, self).get_context_data(**kwargs)
        context["leads"] = self.get_queryset()
        return context


class AddAttachmentsView(LoginRequiredMixin, CreateView):
    model = Attachments
    form_class = LeadAttachmentForm
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        self.object = None
        self.lead = get_object_or_404(Lead, id=request.POST.get('leadid'))
        if (
                request.user in self.lead.assigned_to.all() or
                request.user == self.lead.created_by or request.user.is_superuser or
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
        attachment.lead = self.lead
        attachment.save()
        return JsonResponse({
            "attachment_id": attachment.id,
            "attachment": attachment.file_name,
            "attachment_url": attachment.attachment.url,
            "created_on": attachment.created_on,
            "created_by": attachment.created_by.email,
            "download_url": reverse('common:download_attachment', kwargs={'pk':attachment.id}),
            "attachment_display": attachment.get_file_type_display()
        })

    def form_invalid(self, form):
        return JsonResponse({"error": form['attachment'].errors})


class DeleteAttachmentsView(LoginRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        self.object = get_object_or_404(Attachments, id=request.POST.get("attachment_id"))
        if (
            request.user == self.object.created_by or request.user.is_superuser or 
            request.user.role == 'ADMIN'
        ):
            self.object.delete()
            data = {"aid": request.POST.get("attachment_id")}
            return JsonResponse(data)

        data = {'error': "You don't have permission to delete this attachment."}
        return JsonResponse(data)


def create_lead_from_site(request):

    if request.POST.get("email") and request.POST.get("full_name"):
        user = User.objects.filter(is_admin=True, is_active=True).first()
        lead = Lead.objects.create(
            title=request.POST.get("full_name"),
            status="assigned", source="micropyramid.com",
            description=request.POST.get("message"),
            email=request.POST.get("email"), phone=request.POST.get("phone"),
            is_active=True, created_by=user)
        lead.assigned_to.add(user)
        # Send Email to Assigned Users
        site_address = request.scheme + '://' + request.META['HTTP_HOST']
        send_lead_assigned_emails.delay(lead.id, [user.id], site_address)
        # Create Contact
        contact = Contact.objects.create(
            first_name=request.POST.get("full_name"),
            email=request.POST.get("email"), phone=request.POST.get("phone"),
            description=request.POST.get("message"), created_by=user,
            is_active=True)
        contact.assigned_to.add(user)

        lead.contacts.add(contact)

        return JsonResponse({'error': False, 'message': "Lead Created sucessfully."},
                            status=status.HTTP_201_CREATED)
    return JsonResponse({'error': True, 'message': "In-valid data."},
                        status=status.HTTP_400_BAD_REQUEST)
