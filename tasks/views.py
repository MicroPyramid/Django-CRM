from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.views.generic import (CreateView, DeleteView, DetailView, FormView,
                                  TemplateView, UpdateView, View)

from accounts.models import Account
from common.models import Attachments, Comment, User
from common.tasks import send_email_user_mentions
from contacts.models import Contact
from tasks.celery_tasks import send_email
from tasks.forms import TaskAttachmentForm, TaskCommentForm, TaskForm
from tasks.models import Task
from tasks.utils import *
from common.access_decorators_mixins import (
    sales_access_required, marketing_access_required, SalesAccessRequiredMixin, MarketingAccessRequiredMixin)


@login_required
@sales_access_required
def tasks_list(request):
    if request.method == 'GET':

        if request.user.role == 'ADMIN' or request.user.is_superuser:
            tasks = Task.objects.all().distinct()
        else:
            tasks = Task.objects.filter(
                Q(created_by=request.user) | Q(assigned_to=request.user)).distinct()
        today = datetime.today().date()
        return render(request, 'tasks_tasks_list.html', {'tasks': tasks, 'today': today, 'status_choices': STATUS_CHOICES, 'priority_choices': PRIORITY_CHOICES})

    if request.method == 'POST':
        tasks = Task.objects.filter()
        if request.user.role == 'ADMIN' or request.user.is_superuser:
            tasks = tasks
        else:
            tasks = Task.objects.filter(created_by=request.user)

        if request.POST.get('task_title', None):
            tasks = tasks.filter(
                title__icontains=request.POST.get('task_title'))

        if request.POST.get('status', None):
            tasks = tasks.filter(status=request.POST.get('status'))

        if request.POST.get('priority', None):
            tasks = tasks.filter(priority=request.POST.get('priority'))

        tasks = tasks.distinct()

        today = datetime.today().date()
        return render(request, 'tasks_tasks_list.html', {'tasks': tasks, 'today': today, 'status_choices': STATUS_CHOICES, 'priority_choices': PRIORITY_CHOICES})


@login_required
@sales_access_required
def task_create(request):
    if request.method == 'GET':
        if request.user.role == 'ADMIN' or request.user.is_superuser:
            users = User.objects.filter(is_active=True).order_by('email')
        elif request.user.google.all():
            users = []
        else:
            users = User.objects.filter(role='ADMIN').order_by('email')
        form = TaskForm(request_user=request.user)
        return render(request, 'task_create.html', {'form': form, 'users': users})

    if request.method == 'POST':
        form = TaskForm(request.POST, request_user=request.user)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            task.save()
            task.assigned_to.add(*request.POST.getlist('assigned_to'))
            task.contacts.add(*request.POST.getlist('contacts'))
            kwargs = {'domain': request.get_host(), 'protocol': request.scheme}
            send_email.delay(task.id, **kwargs)
            return JsonResponse({'error': False, 'success_url': reverse('tasks:tasks_list')})
        else:
            return JsonResponse({'error': True, 'errors': form.errors})


@login_required
@sales_access_required
def task_detail(request, task_id):

    task = get_object_or_404(Task, pk=task_id)

    if not (request.user.role == 'ADMIN' or request.user.is_superuser or task.created_by == request.user or request.user in task.assigned_to.all()):
        raise PermissionDenied

    if request.method == 'GET':
        # if Task.objects.filter(id=task_id).exists():
        #     task = Task.objects.select_related('account').prefetch_related(
        #         'assigned_to', 'contacts').get(id=task_id)
        attachments = task.tasks_attachment.all()
        comments = task.tasks_comments.all()
        if request.user.is_superuser or request.user.role == 'ADMIN':
            users_mention = list(User.objects.all().values('username'))
        elif request.user != task.created_by:
            users_mention = [{'username': task.created_by.username}]
        else:
            users_mention = list(task.assigned_to.all().values('username'))
        return render(request, 'task_detail.html',
                      {'task': task, 'users_mention': users_mention,
                       'attachments': attachments, 'comments': comments})


@login_required
@sales_access_required
def task_edit(request, task_id):
    task_obj = get_object_or_404(Task, pk=task_id)

    if not (request.user.role == 'ADMIN' or request.user.is_superuser or task_obj.created_by == request.user):
        raise PermissionDenied

    if request.method == 'GET':
        if request.user.role == 'ADMIN' or request.user.is_superuser:
            users = User.objects.filter(is_active=True).order_by('email')
        elif request.user.google.all():
            users = []
        else:
            users = User.objects.filter(role='ADMIN').order_by('email')
        # form = TaskForm(request_user=request.user)
        form = TaskForm(instance=task_obj, request_user=request.user)
        return render(request, 'task_create.html', {'form': form, 'task_obj': task_obj, 'users': users})

    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task_obj,
                        request_user=request.user)
        if form.is_valid():
            task = form.save(commit=False)
            form.save_m2m()
            # task.assigned_to.clear()
            # task.contacts.clear()
            # task.assigned_to.add(*request.POST.getlist('assigned_to'))
            # task.contacts.add(*request.POST.getlist('contacts'))
            kwargs = {'domain': request.get_host(), 'protocol': request.scheme}
            send_email.delay(task.id, **kwargs)
            return JsonResponse({'error': False, 'success_url': reverse('tasks:tasks_list')})
        else:
            return JsonResponse({'error': True, 'errors': form.errors})


@login_required
@sales_access_required
def task_delete(request, task_id):
    task_obj = get_object_or_404(Task, pk=task_id)

    if not (request.user.role == 'ADMIN' or request.user.is_superuser or task_obj.created_by == request.user):
        raise PermissionDenied

    if request.method == 'GET':
        task_obj.delete()
        if request.GET.get('view_account', None):
            return redirect(reverse('accounts:view_account', args=(request.GET.get('view_account'))))

        if request.GET.get('view_account', None):
            return redirect(reverse('accounts:view_account', args=(request.GET.get('view_account'))))
        return redirect('tasks:tasks_list')


class AddCommentView(LoginRequiredMixin, CreateView):
    model = Comment
    form_class = TaskCommentForm
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        self.object = None
        self.task = get_object_or_404(
            Task, id=request.POST.get('task_id'))
        if (
            request.user == self.task.created_by or request.user.is_superuser or
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
        comment.task = self.task
        comment.save()
        comment_id = comment.id
        current_site = get_current_site(self.request)
        send_email_user_mentions.delay(comment_id, 'tasks', domain=current_site.domain,
                                       protocol=self.request.scheme)
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
            form = TaskCommentForm(request.POST, instance=self.comment_obj)
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
        send_email_user_mentions.delay(comment_id, 'tasks', domain=current_site.domain,
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
    form_class = TaskAttachmentForm
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        self.object = None
        self.task = get_object_or_404(
            Task, id=request.POST.get('task_id'))
        if (
            request.user == self.task.created_by or
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
        attachment.task = self.task
        attachment.save()
        return JsonResponse({
            "attachment_id": attachment.id,
            "attachment": attachment.file_name,
            "attachment_url": attachment.attachment.url,
            "download_url": reverse('common:download_attachment',
                                    kwargs={'pk': attachment.id}),
            "attachment_display": attachment.get_file_type_display(),
            "created_on": attachment.created_on,
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
