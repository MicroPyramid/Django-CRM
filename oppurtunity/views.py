from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from accounts.models import Account
from oppurtunity.models import Opportunity
from common.models import Comment, Team
from common.utils import STAGES, SOURCES
from oppurtunity.forms import OpportunityForm, CommentForm
from contacts.models import Contact
from django.shortcuts import get_object_or_404
from django.urls import reverse
import json
# Create your views here.


@login_required
def opp_create(request):
    users = User.objects.filter(is_active=True)
    accunt = Account.objects.all()
    if request.method == 'POST':
        form = OpportunityForm(request.POST)
        if form.is_valid():
            a = form.save()
            # a.contacts.add(*(request.POST.getlist("contacts")))
            accunt = Account.objects.all()
            a.users = request.user
            a.save()
            if request.is_ajax():
                return JsonResponse({'error': False})
            if request.POST.get("user"):
                a.users = User.objects.get(id=request.POST.get("users"))
                a.save()
            if request.POST.get("teams"):
                a.teams = request.POST.get("teams")
                a.save()
            if request.is_ajax():
                return HttpResponse(json.dumps({'error': False}))
            return HttpResponseRedirect(reverse('oppurtunities:list'))
        else:
            return render(request, 'oppurtunity/create_opportunity.html', {
                'stages': STAGES, 'sources': SOURCES,
                'accunt': accunt, 'teams': TEAMS, 'users': users,
                'error': form.errors})
    else:
        form = OpportunityForm()
        return render(request, 'oppurtunity/create_opportunity.html', {
            'form': form, 'stages': STAGES, 'sources': SOURCES,
            'accunt': accunt, 'teams': TEAMS, 'users': users})


def contacts(request):
        acc = request.GET["Account"]
        account_contact = Account.objects.filter(id=acc)
        contacts = Contact.objects.filter(account=account_contact)
        data = {}
        for i in contacts:
            new = {i.pk: i.name}
            data.update(new)
        return JsonResponse(data)


@login_required
def editdetails(request):
    eid = request.POST.get("tid")
    edata = get_object_or_404(Opportunity, id=eid)
    account = 0
    if edata.account:
        account = edata.account.id
    con = Contact.objects.filter(account=account)
    selcon = edata.contacts.all()
    print ("selcon", selcon)
    contactsHtml = render(request, "oppurtunity/opp_contacts.html", {
        "con": con, "selcon": selcon})
    data = {"name": edata.name, "stage": edata.stage, "close_date": edata.close_date,
            "sources": edata.lead_source, "probability": edata.probability,
            "description": edata.description, "account": account, "eid": eid, }
    data['contacts'] = str(contactsHtml.content)
    return JsonResponse(data)


@login_required
def opp_display(request):
    page = request.GET.get('per_page')
    count = Opportunity.objects.count()
    accounts = Account.objects.all()
    contacts = Contact.objects.all()
    opportunity = Opportunity.objects.all()
    if request.method == 'GET':
        if request.GET.get('name'):
            opportunity = Opportunity.objects.filter(
                name__contains=request.GET.get('name'))
        if request.GET.get('stage'):
            opportunity = opportunity.filter(
                stage=request.GET.get('stage'))
        if request.GET.get('lead_source'):
            opportunity = opportunity.filter(
                lead_source=request.GET.get('lead_source'))
        if request.GET.get('account'):
            opportunity = opportunity.filter(
                account=request.GET.get('account'))
        if request.GET.get('contacts'):
            opportunity = opportunity.filter(
                contacts=request.GET.get('contacts'))
        return render(request, 'oppurtunity/opportunity.html', {
            'opportunity': opportunity, 'stages': STAGES,
            'sources': SOURCES, 'accounts': accounts, 'per_page': page,
            'contacts': contacts, 'teams': TEAMS, 'count': count})
    else:
        return render(request, "oppurtunity/opportunity.html", {
            'opportunity': opportunity, 'stages': STAGES, 'sources': SOURCES,
            'per_page': page, 'accounts': accounts, 'teams': TEAMS,
            'contacts': contacts, 'count': count})


@login_required
def opp_delete(request, opp_id):
    Opportunity.objects.filter(id=opp_id).delete()
    if request.is_ajax():
        return HttpResponse(json.dumps({'error': False}))
    return HttpResponseRedirect('/oppurtunities/list/')


@login_required
def opp_view(request, opp_id):
    view_record = get_object_or_404(Opportunity, id=opp_id)
    comments = Comments.objects.filter(oppid=opp_id).order_by('-id')
    users = User.objects.all()
    accunt = Account.objects.all()
    contact = view_record.contacts.all()
    return render(request, 'oppurtunity/view_opportunity.html', {
        'opp': view_record, 'stages': STAGES,
        'sources': SOURCES, 'accunt': accunt, 'teams': TEAMS,
        'users': users, 'contact': contact, "comments": comments})


@login_required
def opp_edit(request, opp_id):
    edata = get_object_or_404(Opportunity, id=opp_id)
    selcon = edata.contacts.all()
    con = Contact.objects.filter(account=edata.account)
    edit_opp = "editing"
    accunt = Account.objects.all()
    if request.method == 'POST':
        eid = get_object_or_404(Opportunity, id=opp_id)
        form = OpportunityForm(request.POST, instance=eid)
        if form.is_valid():
            form.save()
            if request.is_ajax():
                return HttpResponse(json.dumps({'error': False}))
            return redirect("/oppurtunities/list")
        else:
            if request.is_ajax():
                return JsonResponse({'error': True, 'errors_case': form.errors})
            return render(request, "oppurtunity/view_opportunity.html", {
                "opp": edata, "con": con, "accunt": accunt, "selcon": selcon,
                "edit_opp": edit_opp})
    assigned_user = "None"
    if edata.assigned_user:
        assigned_user = edata.get_assigned_user
    users = User.objects.filter(is_active=True)
    return render(request, "oppurtunity/view_opportunity.html", {
        "opp": edata, "con": con, "accunt": accunt, "selcon": selcon,
        "edit_opp": edit_opp, "users": users, "assigned_user": assigned_user})


def comment_add(request):
    if request.method == 'POST':
        opp = get_object_or_404(Opportunity, id=request.POST.get('oppid'))
        assigned = False
        if opp.assigned_user:
            assigned = (int(opp.assigned_user) == request.user)
        if request.user == opp.users or assigned:
            form = CommentForm(request.POST)
            if form.is_valid():
                comment = request.POST.get('comment')
                comment_user = request.user
                oppid = request.POST.get('oppid')
                c = Comments.objects.create(comment=comment, oppid=Opportunity.objects.get(id=oppid), comment_user=comment_user)
                data = {"com_id": c.id, "comment": c.comment,
                        "comment_time": c.comment_time,
                        "com_user": c.comment_user.username}
                return JsonResponse(data)
            else:
                return JsonResponse({"error": form['comment'].errors})
        else:
            data = {'error': "You Dont Have permissions to Comment"}
            return JsonResponse(data)


@login_required
def comment_edit(request):
    if request.method == "POST":
        comment = request.POST.get('comment')
        comment_id = request.POST.get("commentid")
        com = get_object_or_404(Comments, id=comment_id)
        form = CommentForm(request.POST)
        if request.user == com.comment_user:
            if form.is_valid():
                com.comment = comment
                com.save()
                data = {"comment": com.comment, "commentid": comment_id}
                return JsonResponse(data)
            else:
                return JsonResponse({"error": form['comment'].errors})
        else:
            return JsonResponse({"error": "You dont have authentication to edit"})
    else:
        return render(request, "404.html")


@login_required
def comment_remove(request):
    if request.method == 'POST':
        comment_id = request.POST.get('comment_id')
        c = get_object_or_404(Comments, id=comment_id)
        if request.user == c.comment_user:
            get_object_or_404(Comments, id=comment_id).delete()
            data = {"oid": comment_id}
            return JsonResponse(data)
        else:
            return JsonResponse({"error": "You Dont have permisions to delete"})
    else:
        return HttpResponse("Something Went Wrong")


@login_required
def get_opportunity(request):
    if request.method == 'GET':
        if request.user.is_authenticated():
            opportunities = Opportunity.objects.all()
            return render(request, 'oppurtunity/opportunities_list.html', {
                'opportunities': opportunities})
        else:
            return HttpResponseRedirect('accounts/login')
    else:
        return HttpResponse('Invalid Method or Not Authanticated in load_calls')
    return HttpResponse('Oops!! Something Went Wrong..  in load_calls')
