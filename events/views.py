from datetime import date, datetime, timedelta

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.views.generic import (CreateView, DeleteView, DetailView, FormView,
                                  TemplateView, UpdateView, View)

from common.models import Attachments, Comment, User
from common.tasks import send_email_user_mentions
from events.forms import EventAttachmentForm, EventCommentForm, EventForm
from events.models import Event
from events.tasks import send_email
from common.access_decorators_mixins import (
    sales_access_required, marketing_access_required, SalesAccessRequiredMixin, MarketingAccessRequiredMixin)
from teams.models import Teams


@login_required
@sales_access_required
def events_list(request):

    if request.user.role == 'ADMIN' or request.user.is_superuser:
        users = User.objects.all()
    # elif request.user.google.all():
    #     # users = User.objects.none()
    #     users = User.objects.filter(Q(role='ADMIN') | Q(id=request.user.id))
    elif request.user.role == 'USER':
        # users = User.objects.filter(role='ADMIN')
        users = User.objects.filter(Q(role='ADMIN') | Q(id=request.user.id))
    else:
        pass


    if request.method == 'GET':
        context = {}
        if request.user.role == 'ADMIN' or request.user.is_superuser:
            events = Event.objects.all().distinct()
        else:
            events = Event.objects.filter(
                Q(created_by=request.user) | Q(assigned_to=request.user)).distinct()
        context['events'] = events.order_by('id')
        # context['status'] = status
        context['users'] = users
        user_ids = list(events.values_list('created_by', flat=True))
        user_ids.append(request.user.id)
        context['created_by_users'] = users.filter(is_active=True, id__in=user_ids)
        return render(request, 'events_list.html', context)

    if request.method == 'POST':
        context = {}
        # context['status'] = status
        context['users'] = users
        events = Event.objects.filter()
        if request.user.role == 'ADMIN' or request.user.is_superuser:
            events = events
        else:
            events = events.filter(
                Q(created_by=request.user) | Q(assigned_to=request.user)).distinct()

        if request.POST.get('event_name', None):
            events = events.filter(
                name__icontains=request.POST.get('event_name'))

        if request.POST.get('created_by', None):
            events = events.filter(
                created_by__id=request.POST.get('created_by'))

        if request.POST.getlist('assigned_to', None):
            events = events.filter(
                assigned_to__in=request.POST.getlist('assigned_to'))
            context['assigned_to'] = request.POST.getlist('assigned_to')

        if request.POST.get('date_of_meeting', None):
            events = events.filter(
                date_of_meeting=request.POST.get('date_of_meeting'))

        context['events'] = events.distinct().order_by('id')
        user_ids = list(events.values_list('created_by', flat=True))
        user_ids.append(request.user.id)
        context['created_by_users'] = users.filter(is_active=True, id__in=user_ids)
        return render(request, 'events_list.html', context)


@login_required
@sales_access_required
def event_create(request):
    if request.method == 'GET':
        context = {}
        context["form"] = EventForm(request_user=request.user)
        context["users"] = User.objects.filter(is_active=True)
        if request.user.role == 'ADMIN' or request.user.is_superuser:
            context['teams'] = Teams.objects.all()
        return render(request, 'event_create.html', context)

    if request.method == 'POST':
        form = EventForm(request.POST, request_user=request.user)
        if form.is_valid():
            start_date = form.cleaned_data.get('start_date')
            end_date = form.cleaned_data.get('end_date')
            # recurring_days
            recurring_days = request.POST.getlist('recurring_days')
            if form.cleaned_data.get('event_type') == 'Non-Recurring':
                event = form.save(commit=False)
                event.date_of_meeting = start_date
                event.created_by = request.user
                event.save()
                form.save_m2m()
                if request.POST.getlist('teams', []):
                    user_ids = Teams.objects.filter(id__in=request.POST.getlist('teams')).values_list('users', flat=True)
                    assinged_to_users_ids = event.assigned_to.all().values_list('id', flat=True)
                    for user_id in user_ids:
                        if user_id not in assinged_to_users_ids:
                            event.assigned_to.add(user_id)

                if request.POST.getlist('teams', []):
                    event.teams.add(*request.POST.getlist('teams'))
                assigned_to_list = list(event.assigned_to.all().values_list('id', flat=True))
                send_email.delay(
                    event.id, assigned_to_list, domain=request.get_host(), protocol=request.scheme)

            if form.cleaned_data.get('event_type') == 'Recurring':
                delta = end_date - start_date
                all_dates = []
                required_dates = []

                for day in range(delta.days + 1):
                    each_date = (start_date + timedelta(days=day))
                    if each_date.strftime("%A") in recurring_days:
                        required_dates.append(each_date)

                for each in required_dates:
                    each = datetime.strptime(str(each), '%Y-%m-%d').date()
                    data = form.cleaned_data

                    event = Event.objects.create(
                        created_by=request.user, start_date=start_date, end_date=end_date,
                        name=data['name'], event_type=data['event_type'],
                        description=data['description'], start_time=data['start_time'],
                        end_time=data['end_time'], date_of_meeting=each
                    )
                    event.contacts.add(*request.POST.getlist('contacts'))
                    event.assigned_to.add(*request.POST.getlist('assigned_to'))
                    if request.POST.getlist('teams', []):
                        user_ids = Teams.objects.filter(id__in=request.POST.getlist('teams')).values_list('users', flat=True)
                        assinged_to_users_ids = event.assigned_to.all().values_list('id', flat=True)
                        for user_id in user_ids:
                            if user_id not in assinged_to_users_ids:
                                event.assigned_to.add(user_id)

                    if request.POST.getlist('teams', []):
                        event.teams.add(*request.POST.getlist('teams'))
                    assigned_to_list = list(event.assigned_to.all().values_list('id', flat=True))
                    send_email.delay(
                        event.id, assigned_to_list,  domain=request.get_host(), protocol=request.scheme)

            return JsonResponse({'error': False, 'success_url': reverse('events:events_list')})
        else:
            return JsonResponse({'error': True, 'errors': form.errors, })


@login_required
@sales_access_required
def event_detail_view(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    if not (request.user.role == 'ADMIN' or request.user.is_superuser or event.created_by == request.user or request.user in event.assigned_to.all()):
        raise PermissionDenied

    if request.method == 'GET':
        context = {}
        context['event'] = event
        context['attachments'] = event.events_attachment.all()
        context['comments'] = event.events_comments.all()
        if request.user.is_superuser or request.user.role == 'ADMIN':
            context['users_mention'] = list(
                User.objects.filter(is_active=True).values('username'))
        elif request.user != event.created_by:
            context['users_mention'] = [
                {'username': event.created_by.username}]
        else:
            context['users_mention'] = list(
                event.assigned_to.all().values('username'))
        return render(request, 'event_detail.html', context)


@login_required
@sales_access_required
def event_update(request, event_id):
    event_obj = get_object_or_404(Event, pk=event_id)
    if not (request.user.role == 'ADMIN' or request.user.is_superuser or event_obj.created_by == request.user or request.user in event_obj.assigned_to.all()):
        raise PermissionDenied

    if request.method == 'GET':
        context = {}
        context["event_obj"] = event_obj
        context["users"] = User.objects.filter(is_active=True)
        context["form"] = EventForm(
            instance=event_obj, request_user=request.user)
        selected_recurring_days = Event.objects.filter(
            name=event_obj.name).values_list('date_of_meeting', flat=True)
        selected_recurring_days = [day.strftime(
            '%A') for day in selected_recurring_days]
        context['selected_recurring_days'] = selected_recurring_days
        if request.user.role == 'ADMIN' or request.user.is_superuser:
            context['teams'] = Teams.objects.all()
        return render(request, 'event_create.html', context)

    if request.method == 'POST':
        form = EventForm(request.POST, instance=event_obj,
                         request_user=request.user)
        if form.is_valid():
            start_date = form.cleaned_data.get('start_date')
            end_date = form.cleaned_data.get('end_date')
            previous_assigned_to_users = list(event_obj.assigned_to.all().values_list('id', flat=True))

            # recurring_days
            # recurring_days = request.POST.getlist('days')
            if form.data.get('event_type') == 'Non-Recurring':
                event = form.save(commit=False)
                event.date_of_meeting = start_date
                # event.created_by = request.user
                event.save()
                form.save_m2m()
                if request.POST.getlist('teams', []):
                    user_ids = Teams.objects.filter(id__in=request.POST.getlist('teams')).values_list('users', flat=True)
                    assinged_to_users_ids = event.assigned_to.all().values_list('id', flat=True)
                    for user_id in user_ids:
                        if user_id not in assinged_to_users_ids:
                            event.assigned_to.add(user_id)
                if request.POST.getlist('teams', []):
                    event.teams.clear()
                    event.teams.add(*request.POST.getlist('teams'))
                else:
                    event.teams.clear()
                assigned_to_list = list(event.assigned_to.all().values_list('id', flat=True))
                recipients = list(set(assigned_to_list) - set(previous_assigned_to_users))
                send_email.delay(
                    event.id, recipients, domain=request.get_host(), protocol=request.scheme)

            if form.data.get('event_type') == 'Recurring':
                event = form.save(commit=False)
                event.save()
                form.save_m2m()
                if request.POST.getlist('teams', []):
                    user_ids = Teams.objects.filter(id__in=request.POST.getlist('teams')).values_list('users', flat=True)
                    assinged_to_users_ids = event.assigned_to.all().values_list('id', flat=True)
                    for user_id in user_ids:
                        if user_id not in assinged_to_users_ids:
                            event.assigned_to.add(user_id)
                if request.POST.getlist('teams', []):
                    event.teams.clear()
                    event.teams.add(*request.POST.getlist('teams'))
                else:
                    event.teams.clear()
                assigned_to_list = list(event.assigned_to.all().values_list('id', flat=True))
                recipients = list(set(assigned_to_list) - set(previous_assigned_to_users))
                send_email.delay(
                    event.id, recipients, domain=request.get_host(), protocol=request.scheme)

                # event.contacts.add(*request.POST.getlist('contacts'))
                # event.assigned_to.add(*request.POST.getlist('assigned_to'))

            return JsonResponse({'error': False, 'success_url': reverse('events:events_list')})
        else:
            return JsonResponse({'error': True, 'errors': form.errors, })


@login_required
@sales_access_required
def event_delete(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    if not (request.user.role == 'ADMIN' or request.user.is_superuser or event.created_by == request.user):
        raise PermissionDenied

    event.delete()
    return redirect('events:events_list')


class AddCommentView(LoginRequiredMixin, CreateView):
    model = Comment
    form_class = EventCommentForm
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        self.object = None
        self.event = get_object_or_404(
            Event, id=request.POST.get('event_id'))
        if (
            request.user == self.event.created_by or request.user.is_superuser or
            request.user.role == 'ADMIN'
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
        comment.event = self.event
        comment.save()
        comment_id = comment.id
        current_site = get_current_site(self.request)
        send_email_user_mentions.delay(comment_id, 'events', domain=current_site.domain,
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
            form = EventCommentForm(request.POST, instance=self.comment_obj)
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
        send_email_user_mentions.delay(comment_id, 'events', domain=current_site.domain,
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
    form_class = EventAttachmentForm
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        self.object = None
        self.event = get_object_or_404(
            Event, id=request.POST.get('event_id'))
        if (
            request.user == self.event.created_by or
            request.user.is_superuser or
            request.user.role == 'ADMIN'
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
        attachment.event = self.event
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
