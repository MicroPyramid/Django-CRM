from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import (
    CreateView, UpdateView, DetailView, ListView, TemplateView, View, DeleteView)
from accounts.models import Account
from common.models import User, Comment, Team
from common.utils import STAGES, SOURCES, CURRENCY_CODES
from contacts.models import Contact
from opportunity.forms import OpportunityForm, OpportunityCommentForm
from opportunity.models import Opportunity


class OpportunityListView(LoginRequiredMixin, TemplateView):
    model = Opportunity
    context_object_name = "opportunity_list"
    template_name = "opportunity.html"

    def get_queryset(self):
        queryset = self.model.objects.all().prefetch_related("contacts", "account")
        request_post = self.request.POST
        if request_post:
            if request_post.get('name'):
                queryset = queryset.filter(name__icontains=request_post.get('name'))
            if request_post.get('stage'):
                queryset = queryset.filter(stage=request_post.get('stage'))
            if request_post.get('lead_source'):
                queryset = queryset.filter(lead_source=request_post.get('lead_source'))
            if request_post.get('account'):
                queryset = queryset.filter(account_id=request_post.get('account'))
            if request_post.get('contacts'):
                queryset = queryset.filter(contacts=request_post.get('contacts'))
        return queryset

    def get_context_data(self, **kwargs):
        context = super(OpportunityListView, self).get_context_data(**kwargs)
        context["opportunity_list"] = self.get_queryset()
        context["accounts"] = Account.objects.all()
        context["contacts"] = Contact.objects.all()
        context["stages"] = STAGES
        context["sources"] = SOURCES
        context["per_page"] = self.request.POST.get('per_page')
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
        self.accounts = Account.objects.all()
        self.contacts = Contact.objects.all()
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
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        opportunity_obj = form.save(commit=False)
        opportunity_obj.created_by = self.request.user
        if self.request.POST.get('stage') in ['CLOSED WON', 'CLOSED LOST']:
            opportunity_obj.closed_by = self.request.user
        opportunity_obj.save()
        if self.request.POST.getlist('assigned_to', []):
            opportunity_obj.assigned_to.add(*self.request.POST.getlist('assigned_to'))
        if self.request.POST.getlist('teams', []):
            opportunity_obj.teams.add(*self.request.POST.getlist('teams'))
        if self.request.POST.getlist('contacts', []):
            opportunity_obj.contacts.add(*self.request.POST.getlist('contacts'))
        if self.request.is_ajax():
            return JsonResponse({'error': False})
        if self.request.POST.get("savenewform"):
            return redirect("opportunities:save")
        else:
            return redirect('opportunities:list')

    def form_invalid(self, form):
        if self.request.is_ajax():
            return JsonResponse({'error': True, 'opportunity_errors': form.errors})
        return self.render_to_response(
            self.get_context_data(form=form))

    def get_context_data(self, **kwargs):
        context = super(CreateOpportunityView, self).get_context_data(**kwargs)
        context["opportunity_form"] = context["form"]
        context["teams"] = Team.objects.all()
        context["accounts"] = self.accounts
        context["contacts"] = self.contacts
        context["users"] = self.users
        context["currencies"] = CURRENCY_CODES
        context["stages"] = STAGES
        context["sources"] = SOURCES
        context["assignedto_list"] = [
            int(i) for i in self.request.POST.getlist('assigned_to', []) if i]
        context["teams_list"] = [
            int(i) for i in self.request.POST.getlist('teams', []) if i]
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
        comments = context["opportunity_record"].opportunity_comments.all()
        context.update({"comments": comments})
        return context


class UpdateOpportunityView(LoginRequiredMixin, UpdateView):
    model = Opportunity
    form_class = OpportunityForm
    template_name = "create_opportunity.html"

    def dispatch(self, request, *args, **kwargs):
        self.users = User.objects.filter(is_active=True).order_by('email')
        self.accounts = Account.objects.all()
        self.contacts = Contact.objects.all()
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
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        opportunity_obj = form.save(commit=False)
        if self.request.POST.get('stage') in ['CLOSED WON', 'CLOSED LOST']:
            opportunity_obj.closed_by = self.request.user
        opportunity_obj.save()
        opportunity_obj.assigned_to.clear()
        opportunity_obj.teams.clear()
        opportunity_obj.contacts.clear()
        if self.request.POST.getlist('assigned_to', []):
            opportunity_obj.assigned_to.add(*self.request.POST.getlist('assigned_to'))
        if self.request.POST.getlist('teams', []):
            opportunity_obj.teams.add(*self.request.POST.getlist('teams'))
        if self.request.POST.getlist('contacts', []):
            opportunity_obj.contacts.add(*self.request.POST.getlist('contacts'))
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
        context["opportunity_form"] = context["form"]
        context["teams"] = Team.objects.all()
        context["accounts"] = self.accounts
        context["contacts"] = self.contacts
        context["users"] = self.users
        context["currencies"] = CURRENCY_CODES
        context["stages"] = STAGES
        context["sources"] = SOURCES
        context["assignedto_list"] = [
            int(i) for i in self.request.POST.getlist('assigned_to', []) if i]
        context["teams_list"] = [
            int(i) for i in self.request.POST.getlist('teams', []) if i]
        context["contacts_list"] = [
            int(i) for i in self.request.POST.getlist('contacts', []) if i]
        return context


class DeleteOpportunityView(LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = get_object_or_404(Opportunity, id=kwargs.get("pk"))
        self.object.delete()
        if request.is_ajax():
            return JsonResponse({'error': False})
        return redirect("opportunities:list")


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
        self.opportunity = get_object_or_404(Opportunity, id=request.POST.get('opportunityid'))
        if (
            request.user in self.opportunity.assigned_to.all() or
            request.user == self.opportunity.created_by
        ):
            form = self.get_form()
            if form.is_valid():
                return self.form_valid(form)
            else:
                return self.form_invalid(form)
        else:
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
        self.comment_obj = get_object_or_404(Comment, id=request.POST.get("commentid"))
        if request.user == self.comment_obj.commented_by:
            form = OpportunityCommentForm(request.POST, instance=self.comment_obj)
            if form.is_valid():
                return self.form_valid(form)
            else:
                return self.form_invalid(form)
        else:
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
        else:
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
