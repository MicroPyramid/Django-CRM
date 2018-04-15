from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout  as auth_logout, authenticate as auth_authenticate, login as auth_login
from django.http import HttpResponseRedirect
from django.views.generic import View

from .forms import LoginForm

# Create your views here.
class UserLogin(View):
    form_class=LoginForm
    #model=Post
    template_name = 'user/login.html'

    def get(self, request):
        if request.user.is_authenticated:
            return HttpResponseRedirect('/')
        else:
            context = {'form': self.form_class()}
            return render(request, self.template_name, context)

    def post(self, request):
        bound_form = self.form_class(request.POST,  request=request)
        print("here i am and i dont understand")
        if bound_form.is_valid():
            print("form was valid moving on")
            user = auth_authenticate(username=request.POST.get('email'), password=request.POST.get('password'))
            auth_login(request, user)
            return HttpResponseRedirect('/')
        else:
            context = {'form': self.form_class()}
            return render(request, self.template_name, context)

@login_required
def logout(request):
    form_class=LoginForm
    context={'form':form_class}
    template_name = "user/logged_out.html"
    auth_logout(request)
    request.session.flush()
    return render(request, template_name, context)
