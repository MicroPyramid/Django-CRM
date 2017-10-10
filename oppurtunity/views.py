import json

from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.urls import reverse

from common.models import User, Comment, Team
from common.utils import STAGES, SOURCES, CURRENCY_CODES
from accounts.models import Account
from contacts.models import Contact
from oppurtunity.models import Opportunity
from oppurtunity.forms import OpportunityForm, OpportunityCommentForm

# CRUD Operations Start


@login_required
def opp_list(request):
    opportunity_list = Opportunity.objects.all().prefetch_related("contacts", "account")
    accounts = Account.objects.all()
    contacts = Contact.objects.all()
    page = request.POST.get('per_page')
    opp_name = request.POST.get('name')
    opp_account = request.POST.get('account')
    opp_contact = request.POST.get('contacts')
    opp_stage = request.POST.get('stage')
    opp_source = request.POST.get('lead_source')
    if opp_name:
        opportunity_list = Opportunity.objects.filter(name__contains=opp_name)
    if opp_stage:
        opportunity_list = opportunity_list.filter(stage=opp_stage)
    if opp_source:
        opportunity_list = opportunity_list.filter(lead_source=opp_source)
    if opp_account:
        opportunity_list = opportunity_list.filter(account=opp_account)
    if opp_contact:
        opportunity_list = opportunity_list.filter(contacts=opp_contact)
    return render(request, "oppurtunity/opportunity.html", {
        'opportunity_list': opportunity_list,
        'accounts': accounts,
        'contacts': contacts,
        'stages': STAGES,
        'sources': SOURCES,
        'per_page': page
    })


@login_required
def opp_create(request):
    users = User.objects.filter(is_active=True).order_by('email')
    accounts = Account.objects.all()
    contacts = Contact.objects.all()
    form = OpportunityForm(assigned_to=users, account=accounts, contacts=contacts)
    assignedto_list = request.POST.getlist("assigned_to")
    teams_list = request.POST.getlist("teams")
    contacts_list = request.POST.getlist("contacts")
    teams = Team.objects.all()
    if request.method == 'POST':
        form = OpportunityForm(request.POST, assigned_to=users, account=accounts, contacts=contacts)
        if form.is_valid():
            opportunity_obj = form.save(commit=False)
            opportunity_obj.created_by = request.user
            if request.POST.get('stage') in ['CLOSED WON', 'CLOSED LOST']:
                opportunity_obj.closed_by = request.user
            opportunity_obj.save()
            opportunity_obj.assigned_to.add(*assignedto_list)
            opportunity_obj.teams.add(*teams_list)
            opportunity_obj.contacts.add(*contacts_list)
            if request.is_ajax():
                return JsonResponse({'error': False})
            if request.POST.get("savenewform"):
                return HttpResponseRedirect(reverse("oppurtunities:save"))
            else:
                return HttpResponseRedirect(reverse('oppurtunities:list'))
        else:
            if request.is_ajax():
                return JsonResponse({'error': True, 'opportunity_errors': form.errors})
            return render(request, 'oppurtunity/create_opportunity.html', {
                'opportunity_form': form,
                'accounts': accounts,
                'users': users,
                'teams': teams,
                'stages': STAGES,
                'sources': SOURCES,
                'currencies': CURRENCY_CODES,
                'assignedto_list': assignedto_list,
                'teams_list': teams_list,
                'contacts_list': contacts_list
            })
    else:
        return render(request, 'oppurtunity/create_opportunity.html', {
            'opportunity_form': form,
            'accounts': accounts,
            'users': users,
            'teams': teams,
            'stages': STAGES,
            'sources': SOURCES,
            'currencies': CURRENCY_CODES,
            'assignedto_list': assignedto_list,
            'teams_list': teams_list,
            'contacts_list': contacts_list
        })


@login_required
def opp_view(request, pk):
    opportunity_record = get_object_or_404(
        Opportunity.objects.prefetch_related("contacts", "account"), id=pk)
    comments = opportunity_record.opportunity_comments.all()
    return render(request, 'oppurtunity/view_opportunity.html', {
        'opportunity_record': opportunity_record,
        'comments': comments
    })


@login_required
def opp_edit(request, pk):
    opportunity_obj = get_object_or_404(Opportunity, id=pk)
    users = User.objects.filter(is_active=True).order_by('email')
    accounts = Account.objects.all()
    contacts = Contact.objects.all()
    form = OpportunityForm(
        instance=opportunity_obj, assigned_to=users, account=accounts, contacts=contacts)
    assignedto_list = request.POST.getlist("assigned_to")
    teams_list = request.POST.getlist("teams")
    contacts_list = request.POST.getlist("contacts")
    teams = Team.objects.all()
    if request.method == 'POST':
        form = OpportunityForm(
            request.POST, instance=opportunity_obj, assigned_to=users, account=accounts,
            contacts=contacts
        )
        if form.is_valid():
            opportunity_obj = form.save(commit=False)
            opportunity_obj.created_by = request.user
            if request.POST.get('stage') in ['CLOSED WON', 'CLOSED LOST']:
                opportunity_obj.closed_by = request.user
            opportunity_obj.save()
            opportunity_obj.assigned_to.clear()
            opportunity_obj.assigned_to.add(*assignedto_list)
            opportunity_obj.teams.clear()
            opportunity_obj.teams.add(*teams_list)
            opportunity_obj.contacts.clear()
            opportunity_obj.contacts.add(*request.POST.getlist("contacts"))
            if request.is_ajax():
                return JsonResponse({'error': False})
            return HttpResponseRedirect(reverse('oppurtunities:list'))
        else:
            if request.is_ajax():
                return JsonResponse({'error': True, 'opportunity_errors': form.errors})
            return render(request, 'oppurtunity/create_opportunity.html', {
                'opportunity_form': form,
                'opportunity_obj': opportunity_obj,
                'accounts': accounts,
                'users': users,
                'teams': teams,
                'stages': STAGES,
                'sources': SOURCES,
                'currencies': CURRENCY_CODES,
                'assignedto_list': assignedto_list,
                'teams_list': teams_list,
                'contacts_list': contacts_list
            })
    else:
        return render(request, 'oppurtunity/create_opportunity.html', {
            'opportunity_form': form,
            'opportunity_obj': opportunity_obj,
            'accounts': accounts,
            'users': users,
            'teams': teams,
            'stages': STAGES,
            'sources': SOURCES,
            'currencies': CURRENCY_CODES,
            'assignedto_list': assignedto_list,
            'teams_list': teams_list,
            'contacts_list': contacts_list
        })


@login_required
def opp_remove(request, pk):
    opportunity_record = get_object_or_404(Opportunity, id=pk)
    opportunity_record.delete()
    if request.is_ajax():
        return JsonResponse({'error': False})
    return HttpResponseRedirect(reverse('oppurtunities:list'))


def contacts(request):
    opp_account = request.GET["account"]
    if opp_account:
        account = get_object_or_404(Account, id=opp_account)
        contacts = Contact.objects.filter(account=account)
    else:
        contacts = Contact.objects.all()
    data = {}
    for i in contacts:
        new = {i.pk: i.first_name}
        data.update(new)
    return JsonResponse(data)


# CRUD Operations Ends
# Comments Section Start


@login_required
def add_comment(request):
    if request.method == 'POST':
        opportunity = get_object_or_404(Opportunity, id=request.POST.get('opportunityid'))
        if request.user in opportunity.assigned_to.all() or request.user == opportunity.created_by:
            form = OpportunityCommentForm(request.POST)
            if form.is_valid():
                opportunity_comment = form.save(commit=False)
                opportunity_comment.comment = request.POST.get('comment')
                opportunity_comment.commented_by = request.user
                opportunity_comment.opportunity = opportunity
                opportunity_comment.save()
                data = {"comment_id": opportunity_comment.id, "comment": opportunity_comment.comment,
                        "commented_on": opportunity_comment.commented_on,
                        "commented_by": opportunity_comment.commented_by.email}
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
        comment_object = get_object_or_404(Comment, id=comment_id)
        form = OpportunityCommentForm(request.POST)
        if request.user == comment_object.commented_by:
            if form.is_valid():
                comment_object.comment = comment
                comment_object.save()
                data = {"comment": comment_object.comment, "commentid": comment_id}
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
        comment_object = get_object_or_404(Comment, id=comment_id)
        if request.user == comment_object.commented_by:
            get_object_or_404(Comment, id=comment_id).delete()
            data = {"cid": comment_id}
            return JsonResponse(data)
        else:
            return JsonResponse({"error": "You Dont have permisions to delete"})
    else:
        return HttpResponse("Something Went Wrong")


# Comments Section Start
# Other Views


@login_required
def get_opportunity(request):
    if request.method == 'GET':
        opportunities = Opportunity.objects.all()
        return render(request, 'oppurtunity/opportunities_list.html', {'opportunities': opportunities})
    else:
        return HttpResponse('Invalid Method or Not Authanticated in load_calls')
