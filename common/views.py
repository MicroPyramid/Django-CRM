from django.contrib.auth import logout, authenticate, login
from django.contrib.auth.hashers import check_password
from django.contrib.auth.mixins import LoginRequiredMixin, AccessMixin
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import (
    CreateView, UpdateView, DetailView, TemplateView, View, DeleteView)
from common.models import User
from common.forms import UserForm, LoginForm, ChangePasswordForm, PasswordResetEmailForm
from django.contrib.auth.views import PasswordResetView
from django.urls import reverse_lazy
from django.conf import settings


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
        return super(AdminRequiredMixin, self).dispatch(request, *args, **kwargs)


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = "index.html"


class ChangePasswordView(LoginRequiredMixin, TemplateView):
    template_name = "change_password.html"

    def post(self, request, *args, **kwargs):
        error, errors = "", ""
        form = ChangePasswordForm(request.POST)
        if form.is_valid():
            user = request.user
            if not check_password(request.POST.get('CurrentPassword'), user.password):
                error = "Invalid old password"
            else:
                user.set_password(request.POST.get('Newpassword'))
                user.is_active = True
                user.save()
                return HttpResponseRedirect('/')
        else:
            errors = form.errors
        return render(request, "change_password.html", {'error': error, 'errors': errors})


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "profile.html"

    def get_context_data(self, **kwargs):
        context = super(ProfileView, self).get_context_data(**kwargs)
        context["user_obj"] = self.request.user
        return context


class LoginView(TemplateView):
    template_name = "login.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return HttpResponseRedirect('/')
        return super(LoginView, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        form = LoginForm(request.POST, request=request)
        if form.is_valid():
            user = authenticate(username=request.POST.get('email'), password=request.POST.get('password'))
            if user is not None:
                if user.is_active:
                    login(request, user)
                    return HttpResponseRedirect('/')
                else:
                    return render(request, "login.html", {
                        "error": True,
                        "message": "Your Account is InActive. Please Contact Administrator"
                    })
            else:
                return render(request, "login.html", {
                    "error": True,
                    "message": "Your Account is not Found. Please Contact Administrator"
                })
        else:
            return render(request, "login.html", {
                "error": True,
                "message": "Your username and password didn't match. Please try again."
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
            if request_post.get('first_name'):
                queryset = queryset.filter(first_name__icontains=request_post.get('first_name'))
            if request_post.get('last_name'):
                queryset = queryset.filter(last_name_id=request_post.get('last_name'))
            if request_post.get('username'):
                queryset = queryset.filter(username=request_post.get('username'))
            if request_post.get('email'):
                queryset = queryset.filter(email=request_post.get('email'))
        return queryset

    def get_context_data(self, **kwargs):
        context = super(UsersListView, self).get_context_data(**kwargs)
        context["users"] = self.get_queryset()
        context["active_users"] = self.get_queryset().filter(is_active=True)
        context["inactive_users"] = self.get_queryset().filter(is_active=False)
        context["per_page"] = self.request.POST.get('per_page')
        context['admin_email'] = settings.ADMIN_EMAIL
        return context

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)


class CreateUserView(AdminRequiredMixin, CreateView):
    model = User
    form_class = UserForm
    template_name = "create.html"

    def form_valid(self, form):
        user = form.save(commit=False)
        if form.cleaned_data.get("password"):
            user.set_password(form.cleaned_data.get("password"))
        user.save()
        if self.request.is_ajax():
            data = {'success_url': reverse_lazy('common:users_list'), 'error': False}
            return JsonResponse(data)
        return super(CreateUserView, self).form_valid(form)


    def form_invalid(self, form):
        response = super(CreateUserView, self).form_invalid(form)
        if self.request.is_ajax():
            return JsonResponse({'error': True, 'errors': form.errors})
        return response

    def get_context_data(self, **kwargs):
        context = super(CreateUserView, self).get_context_data(**kwargs)
        context["user_form"] = context["form"]
        if "errors" in kwargs:
            context["errors"] = kwargs["errors"]
        return context


class UserDetailView(AdminRequiredMixin, DetailView):
    model = User
    context_object_name = "users"
    template_name = "list.html"

    def get_context_data(self, **kwargs):
        context = super(UserDetailView, self).get_context_data(**kwargs)
        users_list = User.objects.all()
        context.update({
            "users": users_list, "user_obj": self.object,
            "active_users": users_list.filter(is_active=True),
            "inactive_users": users_list.filter(is_active=False)
        })
        return context


class UpdateUserView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserForm
    template_name = "create.html"

    def form_valid(self, form):
        user = form.save(commit=False)
        if user.role == "USER":
            user.is_superuser = False
        user.save()
        if self.request.user.role == "ADMIN" or self.request.user.is_superuser:
            if self.request.is_ajax():
                data = {'success_url': reverse_lazy('common:users_list'), 'error': False}
                return JsonResponse(data)
        if self.request.is_ajax():
            data = {'success_url': reverse_lazy('common:profile'), 'error': False}
            return JsonResponse(data)
        return super(UpdateUserView, self).form_valid(form)


    def form_invalid(self, form):
        response = super(UpdateUserView, self).form_invalid(form)
        if self.request.is_ajax():
            return JsonResponse({'error': True, 'errors': form.errors})
        return response

    def get_context_data(self, **kwargs):
        context = super(UpdateUserView, self).get_context_data(**kwargs)
        context["user_obj"] = self.object
        context["user_form"] = context["form"]
        if "errors" in kwargs:
            context["errors"] = kwargs["errors"]
        return context


class UserDeleteView(AdminRequiredMixin, DeleteView):
    model = User

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        return redirect("common:users_list")


class PasswordResetView(PasswordResetView):
    template_name = 'registration/password_reset_form.html'
    form_class = PasswordResetEmailForm
    email_template_name = 'registration/password_reset_email.html'
