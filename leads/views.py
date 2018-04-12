from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.forms.models import modelformset_factory

from leads.models import Lead
from contacts.forms import ContactForm
from common.models import User, Address, Comment, Team
from common.utils import LEAD_STATUS, LEAD_SOURCE, INDCHOICES, TYPECHOICES, COUNTRIES
from leads.forms import LeadCommentForm, LeadForm
from accounts.forms import AccountForm
from common.forms import BillingAddressForm, ShippingAddressForm
from accounts.models import Account
from planner.models import Event, Reminder
from planner.forms import ReminderForm
from opportunity.forms import OpportunityForm

# CRUD Operations Start


@login_required
def leads_list(request):
    lead_obj = Lead.objects.all().exclude(status='converted')
    page = request.POST.get('per_page')
    first_name = request.POST.get('first_name')
    last_name = request.POST.get('last_name')
    city = request.POST.get('city')
    email = request.POST.get('email')
    if first_name:
        lead_obj = lead_obj.filter(first_name__icontains=first_name)
    if last_name:
        lead_obj = lead_obj.filter(last_name__icontains=last_name)
    if city:
        lead_obj = lead_obj.filter(address=Address.objects.filter
                                       (city__icontains=city))
    if email:
        lead_obj = lead_obj.filter(email__icontains=email)

    return render(request, 'leads/leads.html', {
        'lead_obj': lead_obj, 'per_page': page})


@login_required
def add_lead(request):
    accounts = Account.objects.all()
    users = User.objects.filter(is_active=True).order_by('email')
    teams = Team.objects.all()
    assignedto_list = request.POST.getlist('assigned_to')
    teams_list = request.POST.getlist('teams')
    lead_account = request.POST.get('account_name')
    lead_email = request.POST.get('email')
    lead_phone = request.POST.get('phone')
    form = LeadForm(assigned_to=users)
    address_form = BillingAddressForm()
    if request.method == 'POST':
        form = LeadForm(request.POST, assigned_to=users)
        address_form = BillingAddressForm(request.POST)
        if form.is_valid() and address_form.is_valid():
            lead_obj = form.save(commit=False)
            address_object = address_form.save()
            lead_obj.address = address_object
            lead_obj.created_by = request.user
            lead_obj.save()
            lead_obj.assigned_to.add(*assignedto_list)
            lead_obj.teams.add(*teams_list)
            if request.POST.get('status') == "converted":
                account_object = Account.objects.create(
                    created_by=request.user, name=lead_account,
                    email=lead_email, phone=lead_phone
                )
                account_object.billing_address = address_object
                account_object.save()
            if request.POST.get("savenewform"):
                return HttpResponseRedirect(reverse("leads:add_lead"))
            else:
                return HttpResponseRedirect(reverse('leads:list'))
        else:
            return render(request, 'leads/create_lead.html', {
                          'lead_form': form, 'address_form': address_form,
                          'accounts': accounts, 'countries': COUNTRIES,
                          'teams': teams, 'users': users,
                          'status': LEAD_STATUS, 'source': LEAD_SOURCE,
                          'assignedto_list': assignedto_list, 'teams_list': teams_list})
    else:
        return render(request, 'leads/create_lead.html', {
                      'lead_form': form, 'address_form': address_form,
                      'accounts': accounts, 'countries': COUNTRIES, 'teams': teams,
                      'users': users, 'status': LEAD_STATUS, 'source': LEAD_SOURCE,
                      'assignedto_list': assignedto_list, 'teams_list': teams_list})


@login_required
@csrf_exempt
def view_lead(request, lead_id):
    lead_record = get_object_or_404(Lead, id=lead_id)
    comments = Comment.objects.filter(lead__id=lead_id).order_by('-id')
    meetings = Event.objects.filter(Q(created_by=request.user) | Q(updated_by=request.user),
                                    event_type='Meeting', attendees_leads=lead_record).order_by('-id')
    calls = Event.objects.filter(Q(created_by=request.user) | Q(updated_by=request.user),
                                 event_type='Call', attendees_leads=lead_record).order_by('-id')
    RemindersFormSet = modelformset_factory(Reminder, form=ReminderForm, can_delete=True)
    data = {
        'form-TOTAL_FORMS': '1',
        'form-INITIAL_FORMS': '0',
        'form-MAX_NUM_FORMS': '10',
    }
    reminder_form_set = RemindersFormSet(data)
    return render(request, "leads/view_leads.html", {
                  "lead_record": lead_record, 'status': LEAD_STATUS, 'countries': COUNTRIES,
                  'comments': comments, 'reminder_form_set': reminder_form_set,
                  'meetings': meetings, 'calls': calls
                  })


@login_required
def edit_lead(request, lead_id):
    lead_obj = get_object_or_404(Lead, id=lead_id)
    address_obj = get_object_or_404(Address, id=lead_obj.address.id)
    accounts = Account.objects.all()
    users = User.objects.filter().order_by('email')
    form = LeadForm(instance=lead_obj, assigned_to=users)
    address_form = BillingAddressForm(instance=address_obj)
    assignedto_list = request.POST.getlist('assigned_to')
    teams_list = request.POST.getlist('teams')
    lead_account = request.POST.get('account_name')
    lead_email = request.POST.get('email')
    lead_phone = request.POST.get('phone')
    teams = Team.objects.all()
    if request.method == 'POST':
        form = LeadForm(request.POST, instance=lead_obj, assigned_to=users)
        address_form = BillingAddressForm(request.POST, instance=address_obj)
        if request.POST.get('status') == "converted":
            form.fields['account_name'].required = True
        else:
            form.fields['account_name'].required = False
        if form.is_valid() and address_form.is_valid():
            dis_address_obj = address_form.save()
            lead_obj = form.save(commit=False)
            lead_obj.address = dis_address_obj
            lead_obj.created_by = request.user
            lead_obj.save()
            lead_obj.assigned_to.clear()
            lead_obj.assigned_to.add(*assignedto_list)
            lead_obj.teams.clear()
            lead_obj.teams.add(*teams_list)
            if request.POST.get('status') == "converted":
                account_object = Account.objects.create(
                    created_by=request.user, name=lead_account,
                    email=lead_email, phone=lead_phone
                )
                account_object.billing_address = dis_address_obj
                account_object.save()
            return HttpResponseRedirect(reverse('leads:list'))
        else:
            return render(request, 'leads/create_lead.html', {
                          'lead_obj': lead_obj,
                          'lead_form': form,
                          'address_form': address_form,
                          'accounts': accounts, 'countries': COUNTRIES,
                          'teams': teams, 'users': users,
                          'status': LEAD_STATUS, 'source': LEAD_SOURCE,
                          'assignedto_list': assignedto_list, 'teams_list': teams_list})
    else:
        return render(request, 'leads/create_lead.html', {
                      'lead_form': form, 'address_form': address_form,
                      'lead_obj': lead_obj, 'address_obj': address_obj,
                      'accounts': accounts, 'countries': COUNTRIES, 'teams': teams,
                      'users': users, 'status': LEAD_STATUS, 'source': LEAD_SOURCE,
                      'assignedto_list': assignedto_list, 'teams_list': teams_list})


@login_required
def remove_lead(request, lead_id):
    lead_obj = get_object_or_404(Lead, id=lead_id)
    lead_obj.delete()
    return HttpResponseRedirect(reverse('leads:list'))


# CRUD Operations Ends
# Leads Conversion Functionality Starts


# The Below View Should be Discussed for Functionality
@login_required
def leads_convert(request, pk):
    account_form = AccountForm()
    billing_form = BillingAddressForm()
    shipping_form = ShippingAddressForm(prefix='ship')
    lead_objects = Lead.objects.all()
    lead_obj = Lead.objects.get(id=pk)
    accounts = Account.objects.all()
    contact_form = ContactForm()
    opportunity_form = OpportunityForm()
    teams = Team.objects.all()
    if request.method == "POST":
        if request.POST.get('accountname') == "on":
            account_form = AccountForm(request.POST)
            billing_form = BillingAddressForm(request.POST)
            shipping_form = ShippingAddressForm(request.POST, prefix='ship')
            if account_form.is_valid() and billing_form.is_valid() and shipping_form.is_valid():
                billing_object = billing_form.save()
                shipping_object = shipping_form.save()
                account_object = account_form.save(commit=False)
                account_object.billing_address = billing_object
                account_object.shipping_address = shipping_object
                account_object.created_by = request.user
                account_object.save()
                lead_obj.delete()
                return HttpResponseRedirect(reverse('leads:list'))
            else:
                street1 = request.POST.get('street')
                city1 = request.POST.get('city')
                state1 = request.POST.get('state')
                postcode1 = request.POST.get('postcode')
                country1 = request.POST.get('country')
                shipdata = {'street1': street1, 'city1': city1, 'state1': state1,
                            'postcode1': postcode1, 'country1': country1}
                return render(request, 'leads/checkbox.html', {
                              'account_form': account_form, 'form1': billing_form, 'form2': shipping_form,
                              'form5': COUNTRIES, 'stages': STAGES, 'acc_error': account_form.errors,
                              'shipdata': shipdata, 'sources': LEAD_SOURCE, 'industries': INDCHOICES,
                              'teams': teams, 'task': lead_objects, 'post': lead_obj,
                              'accounts': accounts,
                              'counties': COUNTRIES})

        if request.POST.get('contactname') == "on":
            contact_form = ContactForm(request.POST)
            address_form = BillingAddressForm(request.POST)
            if contact_form.is_valid() and address_form.is_valid():
                address_obj = address_form.save()
                contact_obj = contact_form.save(commit=False)
                contact_obj.address = address_obj
                contact_obj.created_by = request.user
                contact_obj.save()
                return HttpResponseRedirect(reverse('contacts:list'))
            else:
                return render(request, 'leads/checkbox.html', {
                              'post': lead_obj, 'accounts': accounts, 'teams': teams,
                              'contact_form': contact_form, 'address_form': address_form})
        if request.POST.get('opportunityname') == "on":
            opportunity_form = OpportunityForm(request.POST)
            if opportunity_form.is_valid():
                opportunity_form.save()
                return HttpResponseRedirect(reverse('opportunities:list'))
            else:
                return render(request, 'leads/checkbox.html', {
                              'post': lead_obj, 'accounts': accounts, 'sources': LEAD_SOURCE,
                              'teams': teams, 'stages': STAGES, 'opportunity_form': opportunity_form})
    else:
        return render(request, 'leads/checkbox.html', {
                      'form': account_form, 'form1': billing_form, 'form2': shipping_form,
                      'form5': COUNTRIES, 'industries': INDCHOICES, 'teams': teams,
                      'task': lead_objects, 'counties': COUNTRIES,
                      'post': lead_obj, 'accounts': accounts})


# Leads Conversion Functionality Ends
# Comments Section Start


@login_required
def add_comment(request):
    if request.method == 'POST':
        lead = get_object_or_404(Lead, id=request.POST.get('leadid'))
        if request.user in lead.assigned_to.all() or request.user == lead.created_by:
            form = LeadCommentForm(request.POST)
            if form.is_valid():
                lead_comment = form.save(commit=False)
                lead_comment.comment = request.POST.get('comment')
                lead_comment.commented_by = request.user
                lead_comment.lead = lead
                lead_comment.save()
                data = {
                    "comment_id": lead_comment.id, "comment": lead_comment.comment,
                    "commented_on": lead_comment.commented_on,
                    "commented_by": lead_comment.commented_by.email
                }
                return JsonResponse(data)
            else:
                return JsonResponse({"error": form['comment'].errors})
        else:
            data = {'error': "You Dont Have permissions to Comment"}
            return JsonResponse(data)


@login_required
def edit_comment(request):
    if request.method == "POST":
        comment = request.POST.get('comment')
        comment_id = request.POST.get("commentid")
        lead_comment = get_object_or_404(Comment, id=comment_id)
        form = LeadCommentForm(request.POST)
        if request.user == lead_comment.commented_by:
            if form.is_valid():
                lead_comment.comment = comment
                lead_comment.save()
                data = {"comment": lead_comment.comment, "commentid": comment_id}
                return JsonResponse(data)
            else:
                return JsonResponse({"error": form['comment'].errors})
        else:
            return JsonResponse({"error": "You dont have authentication to edit"})
    else:
        return render(request, "404.html")


@login_required
def remove_comment(request):
    if request.method == 'POST':
        comment_id = request.POST.get('comment_id')
        comment = get_object_or_404(Comment, id=comment_id)
        if request.user == comment.commented_by:
            comment.delete()
            data = {"cid": comment_id}
            return JsonResponse(data)
        else:
            return JsonResponse({"error": "You Dont have permisions to delete"})
    else:
        return HttpResponse("Something Went Wrong")

# Comments Section End
# Other Views


@login_required
def get_leads(request):
    if request.method == 'GET':
        leads = Lead.objects.all()
        return render(request, 'leads/leads_list.html', {'leads': leads})
    else:
        return HttpResponse('Invalid Method or No Authanticated in load_calls')
