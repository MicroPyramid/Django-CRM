import json

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import PermissionDenied
from django.core.mail import EmailMessage
from django.db.models import Q
from django.forms.models import modelformset_factory
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.generic import (CreateView, DetailView, ListView,
                                  TemplateView, View)

from accounts.models import Account, Tags
from common import status
from common.access_decorators_mixins import (MarketingAccessRequiredMixin,
                                             SalesAccessRequiredMixin,
                                             marketing_access_required,
                                             sales_access_required)
from common.models import APISettings, Attachments, Comment, User
from common.tasks import send_email_user_mentions
from common.utils import COUNTRIES, LEAD_SOURCE, LEAD_STATUS
from contacts.models import Contact
from leads.forms import (LeadAttachmentForm, LeadCommentForm, LeadForm,
                         LeadListForm)
from leads.models import Lead
from leads.tasks import (create_lead_from_file, send_email_to_assigned_user,
                         send_lead_assigned_emails, update_leads_cache)
from planner.forms import ReminderForm
from planner.models import Event, Reminder
from teams.models import Teams
from django.core.cache import cache


@login_required
def get_teams_and_users(request):
    data = {}
    teams = Teams.objects.all()
    teams_data = [{'team': team.id, 'users': [user.id for user in team.users.all()]} for team in teams]
    users = User.objects.all().values_list("id", flat=True)
    data['teams'] = teams_data
    data['users'] = list(users)
    return JsonResponse(data)


@login_required
@sales_access_required
def lead_list_view(request):

    queryset = Lead.objects.all().exclude(status='converted'
        ).select_related('created_by'
        ).prefetch_related('tags', 'assigned_to',)
    if request.user.role == 'ADMIN' or request.user.is_superuser:
        queryset = queryset
    else:
        queryset = queryset.filter(
            Q(assigned_to__in=[request.user]) |
            Q(created_by=request.user))

    if request.method == 'GET':
        context = {}
        if request.GET.get('tag', None):
            queryset = queryset.filter(tags__in = request.GET.getlist('tag'))

        open_leads = queryset.exclude(status='closed')
        close_leads = queryset.filter(status='closed')

        context["status"] = LEAD_STATUS
        context["open_leads"] = open_leads
        context["close_leads"] = close_leads
        context["per_page"] = request.POST.get('per_page')
        context["source"] = LEAD_SOURCE

        context["users"] = User.objects.filter(
            is_active=True).order_by('email').values('id', 'email')

        tag_ids = list(set(queryset.values_list('tags', flat=True,)))
        context["tags"] = Tags.objects.filter(id__in=tag_ids)
        return render(request, 'leads.html', context)

    if request.method == 'POST':
        context = {}
        search = True if (
            request.POST.get('name') or request.POST.get('city') or
            request.POST.get('email') or request.POST.get('tag') or
            request.POST.get('status') or
            request.POST.get('source') or
            request.POST.get('assigned_to')
        ) else False
        context["search"] = search

        request_post = request.POST
        if request_post:
            if request_post.get('name'):
                queryset = queryset.filter(
                    Q(first_name__icontains=request_post.get('name')) &
                    Q(last_name__icontains=request_post.get('name')))
            if request_post.get('city'):
                queryset = queryset.filter(
                    city__icontains=request_post.get('city'))
            if request_post.get('email'):
                queryset = queryset.filter(
                    email__icontains=request_post.get('email'))
            if request_post.get('status'):
                queryset = queryset.filter(status=request_post.get('status'))
            if request_post.get('tag'):
                queryset = queryset.filter(tags__in=request_post.getlist('tag'))
            if request_post.get('source'):
                queryset = queryset.filter(source=request_post.get('source'))
            if request_post.getlist('assigned_to'):
                queryset = queryset.filter(
                    assigned_to__id__in=request_post.getlist('assigned_to'))
        queryset = queryset.distinct()

        open_leads = queryset.exclude(status='closed')
        close_leads = queryset.filter(status='closed')

        context["status"] = LEAD_STATUS
        context["open_leads"] = open_leads
        context["close_leads"] = close_leads
        context["per_page"] = request.POST.get('per_page')
        context["source"] = LEAD_SOURCE

        context["users"] = User.objects.filter(
            is_active=True).order_by('email').values('id', 'email')

        tag_ids = list(set(queryset.values_list('tags', flat=True,)))
        context["tags"] = Tags.objects.filter(id__in=tag_ids)

        context["assignedto_list"] = [
            int(i) for i in request.POST.getlist('assigned_to', []) if i]
        context["request_tags"] = request.POST.getlist('tag')

        tab_status = 'Open'
        if request.POST.get('tab_status'):
            tab_status = request.POST.get('tab_status')
        context['tab_status'] = tab_status
        return render(request, 'leads.html', context)
        # return context


class LeadListView(SalesAccessRequiredMixin, LoginRequiredMixin, TemplateView):
    model = Lead
    context_object_name = "lead_obj"
    template_name = "leads.html"

    def get_queryset(self):
        queryset = self.model.objects.all().exclude(status='converted').select_related('created_by'
            ).prefetch_related('tags', 'assigned_to',)#.defer('first_name', 'last_name', 'email',
            # 'phone', 'address_line', 'street', 'city', 'postcode', 'website', 'description',
            # 'account_name', 'opportunity_amount', 'enquery_type', 'created_from_site',
            # 'teams', 'contacts', 'tags__slug', 'created_by__username', 'created_by__first_name',
            # 'created_by__last_name', 'created_by__last_login', 'created_by__password',
            # 'created_by__date_joined', 'assigned_to__username', 'assigned_to__first_name',
            # 'assigned_to__last_name', 'assigned_to__last_login', 'assigned_to__password',
            # 'assigned_to__date_joined')
        if (self.request.user.role != "ADMIN" and not
                self.request.user.is_superuser):
            queryset = queryset.filter(
                Q(assigned_to__in=[self.request.user]) |
                Q(created_by=self.request.user))

        if self.request.GET.get('tag', None):
            queryset = queryset.filter(tags__in = self.request.GET.getlist('tag'))

        request_post = self.request.POST
        if request_post:
            if request_post.get('name'):
                queryset = queryset.filter(
                    Q(first_name__icontains=request_post.get('name')) &
                    Q(last_name__icontains=request_post.get('name')))
            if request_post.get('city'):
                queryset = queryset.filter(
                    city__icontains=request_post.get('city'))
            if request_post.get('email'):
                queryset = queryset.filter(
                    email__icontains=request_post.get('email'))
            if request_post.get('status'):
                queryset = queryset.filter(status=request_post.get('status'))
            if request_post.get('tag'):
                queryset = queryset.filter(tags__in=request_post.getlist('tag'))
            if request_post.get('source'):
                queryset = queryset.filter(source=request_post.get('source'))
            if request_post.getlist('assigned_to'):
                queryset = queryset.filter(
                    assigned_to__id__in=request_post.getlist('assigned_to'))
        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super(LeadListView, self).get_context_data(**kwargs)
        # context["lead_obj"] = self.get_queryset()
        open_leads = self.get_queryset().exclude(status='closed')
        close_leads = self.get_queryset().filter(status='closed')
        # # code for caching
        # if self.request.user.role == 'ADMIN' or self.request.user.is_superuser:
        #     if not cache.get('admin_leads_open_queryset'):
        #         open_leads = self.get_queryset().exclude(status='closed')
        #         close_leads = self.get_queryset().filter(status='closed')
        #         cache.set('admin_leads_open_queryset', open_leads, 60*60)
        #         cache.set('admin_leads_close_queryset', close_leads, 60*60)
        #     else:
        #         open_leads = cache.get('admin_leads_open_queryset')
        #         close_leads = cache.get('admin_leads_close_queryset')
        # else:
        #     open_leads = self.get_queryset().exclude(status='closed')
        #     close_leads = self.get_queryset().filter(status='closed')

        context["status"] = LEAD_STATUS
        context["open_leads"] = open_leads
        context["close_leads"] = close_leads
        context["per_page"] = self.request.POST.get('per_page')
        context["source"] = LEAD_SOURCE
        # if not cache.get('lead_form_users'):
        #     lead_users = User.objects.filter(
        #         is_active=True).order_by('email').values('id', 'email')
        #     cache.set('lead_form_users', lead_users, 60*60)
        # else:
        #     lead_users = cache.get('lead_form_users')
        context["users"] = User.objects.filter(
            is_active=True).order_by('email').values('id', 'email')

        context["assignedto_list"] = [
            int(i) for i in self.request.POST.getlist('assigned_to', []) if i]
        context["request_tags"] = self.request.POST.getlist('tag')

        search = True if (
            self.request.POST.get('name') or self.request.POST.get('city') or
            self.request.POST.get('email') or self.request.POST.get('tag') or
            self.request.POST.get('status') or
            self.request.POST.get('source') or
            self.request.POST.get('assigned_to')
        ) else False

        context["search"] = search

        tag_ids = list(set(self.get_queryset().values_list('tags', flat=True,)))
        context["tags"] = Tags.objects.filter(id__in=tag_ids)

        tab_status = 'Open'
        if self.request.POST.get('tab_status'):
            tab_status = self.request.POST.get('tab_status')
        context['tab_status'] = tab_status
        return context

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)


@login_required
@sales_access_required
def create_lead(request):
    template_name = "create_lead.html"
    users = []
    if request.user.role == 'ADMIN' or request.user.is_superuser:
        users = User.objects.filter(is_active=True).order_by('email')
    elif request.user.google.all():
        users = []
    else:
        users = User.objects.filter(role='ADMIN').order_by('email')
    form = LeadForm(assigned_to=users)

    if request.POST:
        form = LeadForm(request.POST, request.FILES, assigned_to=users)
        if form.is_valid():
            lead_obj = form.save(commit=False)
            lead_obj.created_by = request.user
            lead_obj.save()
            if request.POST.get('tags', ''):
                tags = request.POST.get("tags")
                splitted_tags = tags.split(",")
                for t in splitted_tags:
                    tag = Tags.objects.filter(name=t)
                    if tag:
                        tag = tag[0]
                    else:
                        tag = Tags.objects.create(name=t)
                    lead_obj.tags.add(tag)
            if request.POST.getlist('assigned_to', []):
                lead_obj.assigned_to.add(*request.POST.getlist('assigned_to'))
                assigned_to_list = request.POST.getlist('assigned_to')
                # current_site = get_current_site(request)
                # recipients = assigned_to_list
                # send_email_to_assigned_user.delay(recipients, lead_obj.id, domain=current_site.domain,
                #     protocol=request.scheme)
                # for assigned_to_user in assigned_to_list:
                #     user = get_object_or_404(User, pk=assigned_to_user)
                #     mail_subject = 'Assigned to lead.'
                #     message = render_to_string(
                #         'assigned_to/leads_assigned.html', {
                #             'user': user,
                #             'domain': current_site.domain,
                #             'protocol': request.scheme,
                #             'lead': lead_obj
                #         })
                #     email = EmailMessage(
                #         mail_subject, message, to=[user.email])
                #     email.content_subtype = "html"
                #     email.send()
            if request.POST.getlist('teams', []):
                user_ids = Teams.objects.filter(id__in=request.POST.getlist('teams')).values_list('users', flat=True)
                assinged_to_users_ids = lead_obj.assigned_to.all().values_list('id', flat=True)
                for user_id in user_ids:
                    if user_id not in assinged_to_users_ids:
                        lead_obj.assigned_to.add(user_id)

            if request.POST.getlist('teams', []):
                lead_obj.teams.add(*request.POST.getlist('teams'))

            current_site = get_current_site(request)
            recipients = list(lead_obj.assigned_to.all().values_list('id', flat=True))
            send_email_to_assigned_user.delay(recipients, lead_obj.id, domain=current_site.domain,
                protocol=request.scheme)

            if request.FILES.get('lead_attachment'):
                attachment = Attachments()
                attachment.created_by = request.user
                attachment.file_name = request.FILES.get(
                    'lead_attachment').name
                attachment.lead = lead_obj
                attachment.attachment = request.FILES.get('lead_attachment')
                attachment.save()

            if request.POST.get('status') == "converted":
                account_object = Account.objects.create(
                    created_by=request.user, name=lead_obj.account_name,
                    email=lead_obj.email, phone=lead_obj.phone,
                    description=request.POST.get('description'),
                    website=request.POST.get('website'),
                )
                account_object.billing_address_line = lead_obj.address_line
                account_object.billing_street = lead_obj.street
                account_object.billing_city = lead_obj.city
                account_object.billing_state = lead_obj.state
                account_object.billing_postcode = lead_obj.postcode
                account_object.billing_country = lead_obj.country
                for tag in lead_obj.tags.all():
                    account_object.tags.add(tag)

                if request.POST.getlist('assigned_to', []):
                    # account_object.assigned_to.add(*request.POST.getlist('assigned_to'))
                    assigned_to_list = request.POST.getlist('assigned_to')
                    current_site = get_current_site(request)
                    recipients = assigned_to_list
                    send_email_to_assigned_user.delay(recipients, lead_obj.id, domain=current_site.domain,
                        protocol=request.scheme)
                    # for assigned_to_user in assigned_to_list:
                    #     user = get_object_or_404(User, pk=assigned_to_user)
                    #     mail_subject = 'Assigned to account.'
                    #     message = render_to_string(
                    #         'assigned_to/account_assigned.html', {
                    #             'user': user,
                    #             'domain': current_site.domain,
                    #             'protocol': request.scheme,
                    #             'account': account_object
                    #         })
                    #     email = EmailMessage(
                    #         mail_subject, message, to=[user.email])
                    #     email.content_subtype = "html"
                    #     email.send()

                account_object.save()
                # update_leads_cache.delay()
            success_url = reverse('leads:list')
            if request.POST.get("savenewform"):
                success_url = reverse("leads:add_lead")
            return JsonResponse({'error': False, 'success_url': success_url})
        return JsonResponse({'error': True, 'errors': form.errors})
    context = {}
    context["lead_form"] = form
    context["accounts"] = Account.objects.filter(status="open")
    context["users"] = users
    context["countries"] = COUNTRIES
    context["status"] = LEAD_STATUS
    context["source"] = LEAD_SOURCE
    context["teams"] = Teams.objects.all()
    context["assignedto_list"] = [
        int(i) for i in request.POST.getlist('assigned_to', []) if i]

    return render(request, template_name, context)


class LeadDetailView(SalesAccessRequiredMixin, LoginRequiredMixin, DetailView):
    model = Lead
    context_object_name = "lead_record"
    template_name = "view_leads.html"

    def get_context_data(self, **kwargs):
        context = super(LeadDetailView, self).get_context_data(**kwargs)
        user_assgn_list = [
            assigned_to.id for assigned_to in context['object'].assigned_to.all()]
        if self.request.user == context['object'].created_by:
            user_assgn_list.append(self.request.user.id)
        if (self.request.user.role != "ADMIN" and not
                self.request.user.is_superuser):
            if self.request.user.id not in user_assgn_list:
                raise PermissionDenied
        comments = Comment.objects.filter(
            lead__id=self.object.id).order_by('-id')
        attachments = Attachments.objects.filter(
            lead__id=self.object.id).order_by('-id')
        events = Event.objects.filter(
            Q(created_by=self.request.user) | Q(updated_by=self.request.user)
        ).filter(attendees_leads=context["lead_record"])
        meetings = events.filter(event_type='Meeting').order_by('-id')
        calls = events.filter(event_type='Call').order_by('-id')
        RemindersFormSet = modelformset_factory(
            Reminder, form=ReminderForm, can_delete=True)
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

        if self.request.user.is_superuser or self.request.user.role == 'ADMIN':
            users_mention = list(User.objects.filter(is_active=True).values('username'))
        elif self.request.user != context['object'].created_by:
            users_mention = [{'username': context['object'].created_by.username}]
        else:
            users_mention = list(context['object'].assigned_to.all().values('username'))

        context.update({
            "attachments": attachments, "comments": comments,
            "status": LEAD_STATUS, "countries": COUNTRIES,
            "reminder_form_set": reminder_form_set,
            "meetings": meetings, "calls": calls,
            "users_mention": users_mention,
            "assigned_data": json.dumps(assigned_data)})
        return context


@login_required
@sales_access_required
def update_lead(request, pk):
    lead_record = Lead.objects.filter(pk=pk).first()
    template_name = "create_lead.html"
    users = []
    if request.user.role == 'ADMIN' or request.user.is_superuser:
        users = User.objects.filter(is_active=True).order_by('email')
    else:
        users = User.objects.filter(role='ADMIN').order_by('email')
    status = request.GET.get('status', None)
    initial = {}
    if status and status == "converted":
        error = "This field is required."
        lead_record.status = "converted"
        initial.update({
            "status": status, "lead": lead_record.id})
    error = ""
    form = LeadForm(instance=lead_record, initial=initial, assigned_to=users)

    if request.POST:
        form = LeadForm(request.POST, request.FILES,
                        instance=lead_record,
                        initial=initial, assigned_to=users)

        if request.POST.get('status') == "converted":
            form.fields['account_name'].required = True
            form.fields['email'].required = True
        else:
            form.fields['account_name'].required = False
            form.fields['email'].required = False
        if form.is_valid():
            assigned_to_ids = lead_record.assigned_to.all().values_list(
                'id', flat=True)
            lead_obj = form.save(commit=False)
            lead_obj.save()
            previous_assigned_to_users = list(lead_obj.assigned_to.all().values_list('id', flat=True))
            lead_obj.tags.clear()
            all_members_list = []
            if request.POST.get('tags', ''):
                tags = request.POST.get("tags")
                splitted_tags = tags.split(",")
                for t in splitted_tags:
                    tag = Tags.objects.filter(name=t)
                    if tag:
                        tag = tag[0]
                    else:
                        tag = Tags.objects.create(name=t)
                    lead_obj.tags.add(tag)
            if request.POST.getlist('assigned_to', []):
                if request.POST.get('status') != "converted":

                    current_site = get_current_site(request)

                    assigned_form_users = form.cleaned_data.get(
                        'assigned_to').values_list('id', flat=True)
                    all_members_list = list(
                        set(list(assigned_form_users)) -
                        set(list(assigned_to_ids)))
                    # current_site = get_current_site(request)
                    # recipients = all_members_list
                    # send_email_to_assigned_user.delay(recipients, lead_obj.id, domain=current_site.domain,
                    #     protocol=request.scheme)
                    # if all_members_list:
                    #     for assigned_to_user in all_members_list:
                    #         user = get_object_or_404(User, pk=assigned_to_user)
                    #         mail_subject = 'Assigned to lead.'
                    #         message = render_to_string(
                    #             'assigned_to/leads_assigned.html', {
                    #                 'user': user,
                    #                 'domain': current_site.domain,
                    #                 'protocol': request.scheme,
                    #                 'lead': lead_obj
                    #             })
                    #         email = EmailMessage(
                    #             mail_subject, message, to=[user.email])
                    #         email.content_subtype = "html"
                    #         email.send()

                lead_obj.assigned_to.clear()
                lead_obj.assigned_to.add(*request.POST.getlist('assigned_to'))
            else:
                lead_obj.assigned_to.clear()

            if request.POST.getlist('teams', []):
                user_ids = Teams.objects.filter(id__in=request.POST.getlist('teams')).values_list('users', flat=True)
                assinged_to_users_ids = lead_obj.assigned_to.all().values_list('id', flat=True)
                for user_id in user_ids:
                    if user_id not in assinged_to_users_ids:
                        lead_obj.assigned_to.add(user_id)

            if request.POST.getlist('teams', []):
                lead_obj.teams.clear()
                lead_obj.teams.add(*request.POST.getlist('teams'))
            else:
                lead_obj.teams.clear()

            current_site = get_current_site(request)
            assigned_to_list = list(lead_obj.assigned_to.all().values_list('id', flat=True))
            recipients = list(set(assigned_to_list) - set(previous_assigned_to_users))
            send_email_to_assigned_user.delay(recipients, lead_obj.id, domain=current_site.domain,
                protocol=request.scheme)
            # update_leads_cache.delay()
            if request.FILES.get('lead_attachment'):
                attachment = Attachments()
                attachment.created_by = request.user
                attachment.file_name = request.FILES.get(
                    'lead_attachment').name
                attachment.lead = lead_obj
                attachment.attachment = request.FILES.get('lead_attachment')
                attachment.save()

            if request.POST.get('status') == "converted":
                account_object = Account.objects.create(
                    created_by=request.user, name=lead_obj.account_name,
                    email=lead_obj.email, phone=lead_obj.phone,
                    description=request.POST.get('description'),
                    website=request.POST.get('website'),
                    lead=lead_obj
                )
                account_object.billing_address_line = lead_obj.address_line
                account_object.billing_street = lead_obj.street
                account_object.billing_city = lead_obj.city
                account_object.billing_state = lead_obj.state
                account_object.billing_postcode = lead_obj.postcode
                account_object.billing_country = lead_obj.country
                for tag in lead_obj.tags.all():
                    account_object.tags.add(tag)
                if request.POST.getlist('assigned_to', []):
                    # account_object.assigned_to.add(*request.POST.getlist('assigned_to'))
                    assigned_to_list = request.POST.getlist('assigned_to')
                    current_site = get_current_site(request)
                    recipients = assigned_to_list
                    send_email_to_assigned_user.delay(recipients, lead_obj.id, domain=current_site.domain,
                        protocol=request.scheme)
                    # current_site = get_current_site(request)
                    # for assigned_to_user in assigned_to_list:
                    #     user = get_object_or_404(User, pk=assigned_to_user)
                    #     mail_subject = 'Assigned to account.'
                    #     message = render_to_string(
                    #         'assigned_to/account_assigned.html', {
                    #             'user': user,
                    #             'domain': current_site.domain,
                    #             'protocol': request.scheme,
                    #             'account': account_object
                    #         })
                    #     email = EmailMessage(
                    #         mail_subject, message, to=[user.email])
                    #     email.content_subtype = "html"
                    #     email.send()

                for comment in lead_obj.leads_comments.all():
                    comment.account = account_object
                    comment.save()
                account_object.save()
            status = request.GET.get('status', None)
            success_url = reverse('leads:list')
            if status:
                success_url = reverse('accounts:list')
            return JsonResponse({'error': False, 'success_url': success_url})
        return JsonResponse({'error': True, 'errors': form.errors})
    context = {}
    context["lead_obj"] = lead_record
    user_assgn_list = [
        assigned_to.id for assigned_to in lead_record.get_assigned_users_not_in_teams]

    if request.user == lead_record.created_by:
        user_assgn_list.append(request.user.id)
    if request.user.role != "ADMIN" and not request.user.is_superuser:
        if request.user.id not in user_assgn_list:
            raise PermissionDenied
    team_ids = [user.id for user in lead_record.get_team_users]
    all_user_ids = [user.id for user in users]
    users_excluding_team_id = set(all_user_ids) - set(team_ids)
    users_excluding_team = User.objects.filter(id__in=users_excluding_team_id)
    context["lead_form"] = form
    context["accounts"] = Account.objects.filter(status="open")
    context["users"] = users
    context["users_excluding_team"] = users_excluding_team
    context["countries"] = COUNTRIES
    context["status"] = LEAD_STATUS
    context["source"] = LEAD_SOURCE
    context["error"] = error
    context["teams"] = Teams.objects.all()
    context["assignedto_list"] = [
        int(i) for i in request.POST.getlist('assigned_to', []) if i]
    return render(request, template_name, context)


class DeleteLeadView(SalesAccessRequiredMixin, LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = get_object_or_404(Lead, id=kwargs.get("pk"))
        if (
            self.request.user.role == "ADMIN" or
            self.request.user.is_superuser or
            self.request.user == self.object.created_by
        ):
            self.object.delete()
            # update_leads_cache.delay()
            return redirect("leads:list")
        raise PermissionDenied


def convert_lead(request, pk):
    lead_obj = get_object_or_404(Lead, id=pk)
    if lead_obj.account_name and lead_obj.email:
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
            billing_country=lead_obj.country,
            lead=lead_obj
        )
        contacts_list = lead_obj.contacts.all().values_list('id', flat=True)
        account_object.contacts.add(*contacts_list)
        account_obj = account_object.save()
        current_site = get_current_site(request)
        for assigned_to_user in lead_obj.assigned_to.all().values_list(
                'id', flat=True):
            user = get_object_or_404(User, pk=assigned_to_user)
            mail_subject = 'Assigned to account.'
            message = render_to_string('assigned_to/account_assigned.html', {
                'user': user,
                'domain': current_site.domain,
                'protocol': request.scheme,
                'account': account_object
            })
            email = EmailMessage(mail_subject, message, to=[user.email])
            email.content_subtype = "html"
            email.send()
        return redirect("accounts:list")

    return HttpResponseRedirect(
        reverse('leads:edit_lead', kwargs={
            'pk': lead_obj.id}) + '?status=converted')


class AddCommentView(LoginRequiredMixin, CreateView):
    model = Comment
    form_class = LeadCommentForm
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        self.object = None
        self.lead = get_object_or_404(Lead, id=request.POST.get('leadid'))
        if (
            request.user in self.lead.assigned_to.all() or
            request.user == self.lead.created_by or
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
        comment.lead = self.lead
        comment.save()
        comment_id = comment.id
        current_site = get_current_site(self.request)
        send_email_user_mentions.delay(comment_id, 'leads', domain=current_site.domain,
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
            form = LeadCommentForm(request.POST, instance=self.comment_obj)
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
        send_email_user_mentions.delay(comment_id, 'leads', domain=current_site.domain,
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


class GetLeadsView(LoginRequiredMixin, ListView):
    model = Lead
    context_object_name = "leads"
    template_name = "leads_list.html"


class AddAttachmentsView(LoginRequiredMixin, CreateView):
    model = Attachments
    form_class = LeadAttachmentForm
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        self.object = None
        self.lead = get_object_or_404(Lead, id=request.POST.get('leadid'))
        if (
                request.user in self.lead.assigned_to.all() or
                request.user == self.lead.created_by or
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
        attachment.lead = self.lead
        attachment.save()
        return JsonResponse({
            "attachment_id": attachment.id,
            "attachment": attachment.file_name,
            "attachment_url": attachment.attachment.url,
            "created_on": attachment.created_on,
            "created_on_arrow": attachment.created_on_arrow,
            "created_by": attachment.created_by.email,
            "download_url": reverse(
                'common:download_attachment', kwargs={'pk': attachment.id}),
            "attachment_display": attachment.get_file_type_display(),
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
            data = {"aid": request.POST.get("attachment_id")}
            return JsonResponse(data)

        data = {'error':
                "You don't have permission to delete this attachment."}
        return JsonResponse(data)


def create_lead_from_site(request):
    if request.method == "POST":
        # ip_addres = get_client_ip(request)
        # website_address = request.scheme + '://' + ip_addres
        api_key = request.POST.get('apikey')
        # api_setting = APISettings.objects.filter(
        #     website=website_address, apikey=api_key).first()
        api_setting = APISettings.objects.filter(apikey=api_key).first()
        if not api_setting:
            return JsonResponse({
                'error': True,
                'message':
                "You don't have permission, please contact the admin!."},
                status=status.HTTP_400_BAD_REQUEST)

        if (api_setting and request.POST.get("email") and
                request.POST.get("full_name")):
            # user = User.objects.filter(is_admin=True, is_active=True).first()
            user = api_setting.created_by
            lead = Lead.objects.create(
                title=request.POST.get("full_name"),
                status="assigned", source=api_setting.website,
                description=request.POST.get("message"),
                email=request.POST.get("email"),
                phone=request.POST.get("phone"),
                is_active=True, created_by=user)
            lead.assigned_to.add(user)
            # Send Email to Assigned Users
            site_address = request.scheme + '://' + request.META['HTTP_HOST']
            send_lead_assigned_emails.delay(lead.id, [user.id], site_address)
            # Create Contact
            contact = Contact.objects.create(
                first_name=request.POST.get("full_name"),
                email=request.POST.get("email"),
                phone=request.POST.get("phone"),
                description=request.POST.get("message"), created_by=user,
                is_active=True)
            contact.assigned_to.add(user)

            lead.contacts.add(contact)

            return JsonResponse({'error': False,
                                 'message': "Lead Created sucessfully."},
                                status=status.HTTP_201_CREATED)
        return JsonResponse({'error': True, 'message': "In-valid data."},
                            status=status.HTTP_400_BAD_REQUEST)
    return JsonResponse({
        'error': True, 'message': "In-valid request method."},
        status=status.HTTP_400_BAD_REQUEST)


@login_required
@sales_access_required
def update_lead_tags(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    if request.user == lead.created_by or request.user.role == 'ADMIN' or request.user.is_superuser:
        lead.tags.clear()
        if request.POST.get('tags', ''):
            tags = request.POST.get("tags")
            splitted_tags = tags.split(",")
            for t in splitted_tags:
                tag = Tags.objects.filter(name=t)
                if tag:
                    tag = tag[0]
                else:
                    tag = Tags.objects.create(name=t)
                lead.tags.add(tag)
    else:
        raise PermissionDenied
    return HttpResponseRedirect(request.POST.get('full_path'))


@login_required
@sales_access_required
def remove_lead_tag(request):
    data = {}
    lead_id = request.POST.get('lead')
    tag_id = request.POST.get('tag')
    lead = get_object_or_404(Lead, pk=lead_id)
    if request.user == lead.created_by or request.user.role == 'ADMIN' or request.user.is_superuser:
        lead.tags.remove(tag_id)
        data = {'data':'Tag Removed'}
    else:
        data = {'error': "You don't have permission to delete this tag."}
    return JsonResponse(data)

@login_required
@sales_access_required
def upload_lead_csv_file(request):
    if request.method == 'POST':
        lead_form = LeadListForm(request.POST, request.FILES)
        if lead_form.is_valid():
            create_lead_from_file.delay(
                    lead_form.validated_rows, lead_form.invalid_rows, request.user.id,
                    request.get_host())
            return JsonResponse({'error': False, 'data': lead_form.data},
                status=status.HTTP_201_CREATED)
        else:
            return JsonResponse({'error': True, 'errors': lead_form.errors},
                status=status.HTTP_200_OK)


def sample_lead_file(request):
    sample_data = [
        'title,first name,last name,website,phone,email,address\n',
        'lead1,john,doe,www.example.com,+91-123-456-7890,user1@email.com,address for lead1\n',
        'lead2,jane,doe,www.website.com,+91-123-456-7891,user2@email.com,address for lead2\n',
        'lead3,joe,doe,www.test.com,+91-123-456-7892,user3@email.com,address for lead3\n',
        'lead4,john,doe,www.sample.com,+91-123-456-7893,user4@email.com,address for lead4\n',
    ]
    response = HttpResponse(
        sample_data, content_type='text/plain')
    response['Content-Disposition'] = 'attachment; filename={}'.format(
        'sample_data.csv')
    return response
