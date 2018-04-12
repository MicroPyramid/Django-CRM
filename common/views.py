from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseRedirect, JsonResponse
from django.http.response import Http404
from django.contrib.auth import logout, authenticate, login
from django.contrib.auth.hashers import check_password

from common.models import User
from common.forms import UserForm, LoginForm, ChangePasswordForm


def admin_required(function):

    def wrapper(request, *args, **kwargs):
        user = request.user
        if user.is_authenticated:
            if user.role == "ADMIN":
                return function(request, *args, **kwargs)
            else:
                raise Http404
        else:
            return redirect("common:login")
    return wrapper


@login_required
def home(request):
    return render(request, 'index.html')


@login_required
def change_pass(request):
    error, errors = "", ""
    form = ChangePasswordForm()
    if request.method == 'POST':
        form = ChangePasswordForm(request.POST)
        if form.is_valid():
            user = request.user
            if not check_password(request.POST['CurrentPassword'], user.password):
                error = "Invalid old password"
            else:
                user.set_password(request.POST.get('Newpassword'))
                user.is_active = True
                user.save()
                return HttpResponseRedirect('/')
        else:
            errors = form.errors
    return render(request, "change_password.html", {'error': error,
                                                    'errors': errors})


@login_required
def profile(request):
    user = request.user
    user_obj = User.objects.get(id=user.id)
    return render(request, "profile.html", {'user_obj': user_obj})


@csrf_exempt
def login_crm(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('/')
    if request.method == 'POST':
        form = LoginForm(request.POST, request=request)
        if form.is_valid():
            user = authenticate(username=request.POST.get('email'), password=request.POST.get('password'))
            if user is not None:
                if user.is_active:
                    login(request, user)
                    return HttpResponseRedirect('/')
                else:
                    return render(request, "login.html", {"error": True, "inactiveuser": form.errors})
            else:
                return render(request, "login.html", {"error": True, "usernone": form.errors})
        else:
            return render(request, "login.html", {"error": True, "errors": form.errors})
    return render(request, 'login.html')


@csrf_exempt
def logout_crm(request):
    logout(request)
    request.session.flush()
    return redirect("common:login")


@admin_required
@csrf_exempt
def users_list(request):
    users_list = User.objects.all()
    page = request.POST.get('per_page')
    first_name = request.POST.get('first_name')
    last_name = request.POST.get('last_name')
    username = request.POST.get('username')
    email = request.POST.get('email')
    active_users = User.objects.filter(is_active=True)
    inactive_users = User.objects.filter(is_active=False)
    if first_name:
        users_list = users_list.filter(first_name__icontains=first_name)
    if last_name:
        users_list = users_list.filter(last_name__icontains=last_name)
    if username:
        users_list = users_list.filter(username__icontains=username)
    if email:
        users_list = users_list.filter(email__icontains=email)
    return render(request, "users/list.html", {
        'users': users_list, 'active_users': active_users,
        'per_page': page, 'inactive_users': inactive_users
    })


@admin_required
@csrf_exempt
def create_user(request):
    user_form = UserForm()
    users_list = User.objects.all()
    if request.method == 'POST':
        user_form = UserForm(request.POST)
        if user_form.is_valid():
            user = user_form.save(commit=False)
            if request.POST.get("password"):
                user.set_password(request.POST.get("password"))
            user.save()
            return redirect("common:users_list")
        else:
            return render(request, 'users/create.html', {'user_form': user_form, "errors": user_form.errors})
    else:
        return render(request, 'users/create.html', {'user_form': user_form})


@admin_required
@csrf_exempt
def view_user(request, user_id):
    users_list = User.objects.all()
    user_obj = User.objects.filter(id=user_id)
    active_users = User.objects.filter(is_active=True)
    inactive_users = User.objects.filter(is_active=False)
    return render(request, "users/list.html", {
        'users': users_list, 'user_obj': user_obj,
        'active_users': active_users, 'inactive_users': inactive_users
    })


@admin_required
@csrf_exempt
def edit_user(request, user_id):
    user_obj = get_object_or_404(User, id=user_id)
    user_form = UserForm(instance=user_obj)
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=user_obj)
        if user_form.is_valid():
            user_form.save()
            if not request.user.is_staff:
                return redirect("common:profile")
            else:
                return redirect("common:users_list")
        else:
            return render(request, 'users/create.html', {'user_form': user_form, "errors": user_form.errors})
    else:
        return render(request, 'users/create.html', {'user_form': user_form, 'user_obj': user_obj})


@admin_required
@csrf_exempt
def remove_user(request, user_id):
    user_obj = get_object_or_404(User, id=user_id)
    user_obj.delete()
    return redirect("common:users_list")
