from datetime import date, datetime, timedelta

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    FormView,
    TemplateView,
    UpdateView,
    View,
)

from common.models import User
from teams.models import Teams
from teams.forms import TeamForm
from teams.tasks import update_team_users, remove_users


@login_required
def teams_list(request):
    context = {}
    if request.user.role == "ADMIN" or request.user.is_superuser:
        queryset = Teams.objects.filter(company=request.company).order_by("-created_on")
        users = User.objects.filter(company=request.company)
        context["teams"] = queryset
        context["users"] = users
    else:
        raise PermissionDenied

    if request.method == "GET":
        user_ids = list(queryset.values_list("created_by", flat=True))
        user_ids.append(request.user.id)
        context["created_by_users"] = users.filter(is_active=True, id__in=user_ids)
        return render(request, "teams.html", context)
    if request.method == "POST":
        if request.POST.get("team_name"):
            queryset = queryset.filter(name__icontains=request.POST.get("team_name"))
        if request.POST.get("created_by"):
            queryset = queryset.filter(created_by=request.POST.get("created_by"))
        if request.POST.get("assigned_to"):
            queryset = queryset.filter(
                users__id__in=request.POST.getlist("assigned_to")
            )
        context["assigned_to"] = request.POST.getlist("assigned_to")
        context["teams"] = queryset
        user_ids = list(queryset.values_list("created_by", flat=True))
        user_ids.append(request.user.id)
        context["created_by_users"] = users.filter(is_active=True, id__in=user_ids)
        return render(request, "teams.html", context)


@login_required
def team_create(request):
    context = {}
    if request.user.role == "ADMIN" or request.user.is_superuser:
        teams = Teams.objects.filter(company=request.company)
        context["teams"] = teams
    else:
        raise PermissionDenied

    if request.method == "GET":
        form = TeamForm(request_obj=request)
        context["form"] = form
        return render(request, "team_create.html", context)

    if request.method == "POST":
        form = TeamForm(request.POST, request_obj=request)
        if form.is_valid():
            task_obj = form.save(commit=False)
            task_obj.created_by = request.user
            task_obj.company = request.company
            task_obj.save()
            form.save_m2m()
            return JsonResponse(
                {"error": False, "success_url": reverse("teams:teams_list")}
            )
        else:
            return JsonResponse({"error": True, "errors": form.errors})


@login_required
def team_detail(request, team_id):
    if not (request.user.role == "ADMIN" or request.user.is_superuser):
        raise PermissionDenied
    team_obj = get_object_or_404(Teams, pk=team_id)
    if team_obj.company != request.company:
        raise PermissionDenied
    context = {}

    if request.method == "GET":
        context["team_obj"] = team_obj
        return render(request, "team_detail.html", context)


@login_required
def team_edit(request, team_id):
    if not (request.user.role == "ADMIN" or request.user.is_superuser):
        raise PermissionDenied
    team_obj = get_object_or_404(Teams, pk=team_id)
    if team_obj.company != request.company:
        raise PermissionDenied
    actual_users = team_obj.get_users()
    context = {}

    if request.method == "GET":
        form = TeamForm(instance=team_obj, request_obj=request)
        context["form"] = form
        return render(request, "team_create.html", context)

    if request.method == "POST":
        removed_users = []
        form = TeamForm(request.POST, instance=team_obj, request_obj=request)
        if form.is_valid():
            task_obj = form.save(commit=False)
            if "users" in form.changed_data:
                update_team_users.delay(team_id)
                # pass
            task_obj.save()
            form.save_m2m()
            latest_users = task_obj.get_users()
            for user in actual_users:
                if user in latest_users:
                    pass
                else:

                    removed_users.append(user)
            remove_users.delay(removed_users, team_id)
            return JsonResponse(
                {"error": False, "success_url": reverse("teams:teams_list")}
            )
        else:
            return JsonResponse({"error": True, "errors": form.errors})


@login_required
def team_delete(request, team_id):
    if not (request.user.role == "ADMIN" or request.user.is_superuser):
        raise PermissionDenied
    team_obj = get_object_or_404(Teams, pk=team_id)
    if team_obj.company != request.company:
        raise PermissionDenied
    context = {}

    if request.method == "GET":
        team_obj.delete()
        return redirect("teams:teams_list")
