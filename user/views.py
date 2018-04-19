from django.forms.formsets import formset_factory
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
# from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as auth_logout, authenticate as auth_authenticate, login as auth_login, update_session_auth_hash

# from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.views.generic import View, ListView
from .models import User
from .forms import LoginForm, UserForm, PasswordForm, ResetPassForm
# from .models import User

#TODO there is still missing things like view_user and edit_user so still some
#TODO work left for me to clean it out of the old common app


class UserLogin(View):
    """
    Class made for users to login
    """
    #TODO next not implemented
    form_class = LoginForm
    template_name = 'user/login.html'

    def get(self, request):
        if request.user.is_authenticated:
            return HttpResponseRedirect('/')
        context = {'form': self.form_class()}
        return render(request, self.template_name, context)

    def post(self, request):
        bound_form = self.form_class(request.POST, request=request)
        if bound_form.is_valid():
            user = auth_authenticate(username=request.POST.get('email'), password=request.POST.get('password'))
            auth_login(request, user)
            return HttpResponseRedirect('/')
        # else:
            #context = {'form': self.form_class()}
        return render(request, self.template_name, {'form': bound_form})

class UserCreate(View):
    form_class = UserForm
    formset_password = formset_factory(PasswordForm)
    # users_list = User.objects.all()
    template_name = 'user/user_create_form.html'

    def get(self, request):
        context = {'form': self.form_class, 'passform': self.formset_password}
        return render(request, self.template_name, context)

    def post(self, request):
        bound_form = self.form_class(request.POST)
        password_form = self.formset_password(request.POST)
        if all([bound_form.is_valid(), password_form.is_valid()]):
            new_user = bound_form.save(commit=False)
            for inline_form in password_form:
                if inline_form.cleaned_data:
                    password = inline_form.cleaned_data
                    new_user.set_password(password)
            new_user.save()
            return redirect("user:list")

        return render(request, self.template_name, {'form': bound_form, 'passform': password_form})

class UserUpdatePass(View):
    form_class = ResetPassForm
    formset_class = formset_factory(PasswordForm)
    template_name = 'user/user_update_pass_form.html'

    def get(self, request):
        form = self.form_class(request.user)
        context = {'form': form }
        return render(request, self.template_name, context)

    def post(self, request):
        bound_form = self.form_class(request.user, request.POST)
        if bound_form.is_valid():
            user = bound_form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Your password was successfully updated!')
            return redirect('common:users_list')

        messages.error(request, 'Please correct the error below.')
        return render(request, self.template_name, {'form': bound_form})

class UserList(ListView):
    """
        class view for user list
    """
    model = User
    template_name = 'user/user_list.html'  # Default: <app_label>/<model_name>_list.html
    context_object_name = 'users'  # Default: object_list
    paginate_by = 10
    queryset = User.objects.all()  # Default: Model.objects.all()

class UserView(View):
    """
        class view for user profile
    """
    template_name = 'user/user_view.html'

    def get(self, request, user_id):
        user_obj = get_object_or_404(User, pk=user_id)
        context = {'user_obj': user_obj}
        return render(request, self.template_name, context)




class UserEdit(View):
    """
        class view for editing user
    """
    model = User
    form_class = UserForm
    success_url = reverse_lazy('user:list')
    template_name = 'user/user_update_form.html'

    def get(self, request, user_id):
        obj = get_object_or_404(self.model, pk=user_id)
        context = {'form': self.form_class(instance=obj), 'user_obj': obj}
        return render(request, self.template_name, context)

    def post(self, request, user_id):
        obj = get_object_or_404(self.model, pk=user_id)
        bound_form = self.form_class(request.POST, instance=obj)
        if bound_form.is_valid():
            bound_form.save()
            return redirect(self.success_url)
        else:
            context = {'form': bound_form, self.model.__name__.lower(): obj}
            return render(request, self.template_name,context)


class UserDelete(View):
    pass


@login_required
def logout(request):
    form_class = LoginForm
    context = {'form':form_class}
    template_name = "user/logged_out.html"
    auth_logout(request)
    request.session.flush()
    return render(request, template_name, context)
