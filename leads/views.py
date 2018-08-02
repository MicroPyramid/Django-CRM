from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.forms.models import modelformset_factory
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import (
    CreateView, UpdateView, DetailView, ListView, TemplateView, View)

from accounts.models import Account
from common.forms import BillingAddressForm
from common.models import User, Address, Comment, Team
from common.utils import LEAD_STATUS, LEAD_SOURCE, COUNTRIES
from leads.models import Lead
from leads.forms import LeadCommentForm, LeadForm
from planner.models import Event, Reminder
from planner.forms import ReminderForm


class LeadListView(LoginRequiredMixin, TemplateView):
    model = Lead
    context_object_name = "lead_obj"
    template_name = "leads.html"

    def get_queryset(self):
        queryset = self.model.objects.all().exclude(status='converted')
        request_post = self.request.POST
        if request_post:
            if request_post.get('first_name'):
                queryset = queryset.filter(first_name__icontains=request_post.get('first_name'))
            if request_post.get('last_name'):
                queryset = queryset.filter(last_name__icontains=request_post.get('last_name'))
            if request_post.get('city'):
                queryset = queryset.filter(address__city__icontains=request_post.get('city'))
            if request_post.get('email'):
                queryset = queryset.filter(email__icontains=request_post.get('email'))
            if request_post.get('status'):
                queryset = queryset.filter(status=request_post.get('status'))
        return queryset

    def get_context_data(self, **kwargs):
        context = super(LeadListView, self).get_context_data(**kwargs)
        context["lead_obj"] = self.get_queryset()
        context["status"] = LEAD_STATUS
        context["per_page"] = self.request.POST.get('per_page')
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
        address_form = BillingAddressForm(request.POST)
        if form.is_valid() and address_form.is_valid():
            return self.form_valid(form, address_form)
        else:
            return self.form_invalid(form, address_form)

    def form_valid(self, form, address_form):
        address_object = address_form.save()
        lead_obj = form.save(commit=False)
        lead_obj.address = address_object
        lead_obj.created_by = self.request.user
        lead_obj.save()
        if self.request.POST.getlist('assigned_to', []):
            lead_obj.assigned_to.add(*self.request.POST.getlist('assigned_to'))
        if self.request.POST.getlist('teams', []):
            lead_obj.teams.add(*self.request.POST.getlist('teams'))

        if self.request.POST.get('status') == "converted":
            account_object = Account.objects.create(
                created_by=self.request.user, name=lead_obj.account_name,
                email=lead_obj.email, phone=lead_obj.phone,
                description=self.request.POST.get('description'),
                website=self.request.POST.get('website')
            )
            account_object.billing_address = address_object
            if self.request.POST.getlist('assigned_to', []):
                account_object.assigned_to.add(*self.request.POST.getlist('assigned_to'))
            if self.request.POST.getlist('teams', []):
                account_object.teams.add(*self.request.POST.getlist('teams'))
            account_object.save()
        if self.request.POST.get("savenewform"):
            return redirect("leads:add_lead")
        else:
            return redirect('leads:list')

    def form_invalid(self, form, address_form):
        return self.render_to_response(
            self.get_context_data(form=form, address_form=address_form))

    def get_context_data(self, **kwargs):
        context = super(CreateLeadView, self).get_context_data(**kwargs)
        context["lead_form"] = context["form"]
        context["teams"] = Team.objects.all()
        context["accounts"] = Account.objects.all()
        context["users"] = self.users
        context["countries"] = COUNTRIES
        context["status"] = LEAD_STATUS
        context["source"] = LEAD_SOURCE
        context["assignedto_list"] = [
            int(i) for i in self.request.POST.getlist('assigned_to', []) if i]
        context["teams_list"] = [
            int(i) for i in self.request.POST.getlist('teams', []) if i]
        if "address_form" in kwargs:
            context["address_form"] = kwargs["address_form"]
        else:
            if self.request.POST:
                context["address_form"] = BillingAddressForm(self.request.POST)
            else:
                context["address_form"] = BillingAddressForm()
        return context


class LeadDetailView(LoginRequiredMixin, DetailView):
    model = Lead
    context_object_name = "lead_record"
    template_name = "view_leads.html"

    def get_context_data(self, **kwargs):
        context = super(LeadDetailView, self).get_context_data(**kwargs)
        comments = Comment.objects.filter(lead__id=self.object.id).order_by('-id')
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
        context.update({
            "comments": comments, "status": LEAD_STATUS, "countries": COUNTRIES,
            "reminder_form_set": reminder_form_set, "meetings": meetings, "calls": calls})
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
        address_obj = self.object.address
        form = self.get_form()
        address_form = BillingAddressForm(request.POST, instance=address_obj)
        if request.POST.get('status') == "converted":
            form.fields['account_name'].required = True
        else:
            form.fields['account_name'].required = False
        if form.is_valid() and address_form.is_valid():
            return self.form_valid(form, address_form)
        else:
            return self.form_invalid(form, address_form)

    def form_valid(self, form, address_form):
        address_obj = address_form.save()
        lead_obj = form.save(commit=False)
        lead_obj.address = address_obj
        lead_obj.save()
        lead_obj.assigned_to.clear()
        lead_obj.teams.clear()
        if self.request.POST.getlist('assigned_to', []):
            lead_obj.assigned_to.add(*self.request.POST.getlist('assigned_to'))
        if self.request.POST.getlist('teams', []):
            lead_obj.teams.add(*self.request.POST.getlist('teams'))
        if self.request.POST.get('status') == "converted":
            account_object = Account.objects.create(
                created_by=self.request.user, name=lead_obj.account_name,
                email=lead_obj.email, phone=lead_obj.phone,
                description=self.request.POST.get('description'),
                website=self.request.POST.get('website')
            )
            account_object.billing_address = address_obj
            if self.request.POST.getlist('assigned_to', []):
                account_object.assigned_to.add(*self.request.POST.getlist('assigned_to'))
            if self.request.POST.getlist('teams', []):
                account_object.teams.add(*self.request.POST.getlist('teams'))
            account_object.save()
        status = self.request.GET.get('status', None)
        if status:
            return redirect('accounts:list')
        else:
            return redirect('leads:list')

    def form_invalid(self, form, address_form):
        return self.render_to_response(
            self.get_context_data(form=form, address_form=address_form))

    def get_context_data(self, **kwargs):
        context = super(UpdateLeadView, self).get_context_data(**kwargs)
        context["lead_obj"] = self.object
        context["address_obj"] = self.object.address
        context["lead_form"] = context["form"]
        context["teams"] = Team.objects.all()
        context["accounts"] = Account.objects.all()
        context["users"] = self.users
        context["countries"] = COUNTRIES
        context["status"] = LEAD_STATUS
        context["source"] = LEAD_SOURCE
        context["error"] = self.error
        context["assignedto_list"] = [
            int(i) for i in self.request.POST.getlist('assigned_to', []) if i]
        context["teams_list"] = [
            int(i) for i in self.request.POST.getlist('teams', []) if i]
        if "address_form" in kwargs:
            context["address_form"] = kwargs["address_form"]
        else:
            if self.request.POST:
                context["address_form"] = BillingAddressForm(
                    self.request.POST, instance=context["address_obj"])
            else:
                context["address_form"] = BillingAddressForm(
                    instance=context["address_obj"])
        return context


class DeleteLeadView(LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = get_object_or_404(Lead, id=kwargs.get("pk"))
        if self.object.address_id:
            self.object.address.delete()
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
                website=lead_obj.website, billing_address=lead_obj.address
            )
            assignedto_list = lead_obj.assigned_to.all().values_list('id', flat=True)
            account_object.assigned_to.add(*assignedto_list)
            account_object.save()
            return redirect("accounts:list")
        else:
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
            request.user == self.lead.created_by
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


class GetLeadsView(LoginRequiredMixin, ListView):
    model = Lead
    context_object_name = "leads"
    template_name = "leads_list.html"

    def get_context_data(self, **kwargs):
        context = super(GetLeadsView, self).get_context_data(**kwargs)
        context["leads"] = self.get_queryset()
        return context
