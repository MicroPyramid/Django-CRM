from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from accounts.models import Account
from common.models import User, Address, Team, Comment
from common.utils import INDCHOICES, COUNTRIES, CURRENCY_CODES, CASE_TYPE, PRIORITY_CHOICE, STATUS_CHOICE
from opportunity.models import Opportunity, STAGES, SOURCES
from contacts.models import Contact
from cases.models import Case
from accounts.forms import AccountForm, AccountCommentForm
from common.forms import BillingAddressForm, ShippingAddressForm


@login_required
def accounts_list(request):
    accounts_list = Account.objects.all()
    page = request.POST.get('per_page')
    name = request.POST.get('name')
    city = request.POST.get('city')
    industry = request.POST.get('industry')

    if name:
        accounts_list = accounts_list.filter(name__icontains=name)
    if city:
        accounts_list = accounts_list.filter(
            billing_address__in=[i.id for i in Address.objects.filter(city__contains=city)])
    if industry:
        accounts_list = accounts_list.filter(industry__icontains=industry)

    return render(request, "accounts.html", {
        'accounts_list': accounts_list,
        'industries': INDCHOICES,
        'per_page': page
    })


@login_required
def add_account(request):
    users = User.objects.filter(is_active=True).order_by('email')
    account_form = AccountForm(assigned_to=users)
    billing_form = BillingAddressForm()
    shipping_form = ShippingAddressForm(prefix='ship')
    teams = Team.objects.all()
    assignedto_list = request.POST.getlist('assigned_to')
    teams_list = request.POST.getlist('teams')
    if request.method == 'POST':
        account_form = AccountForm(request.POST, assigned_to=users)
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
            account_object.assigned_to.add(*assignedto_list)
            account_object.teams.add(*teams_list)
            if request.POST.get("savenewform"):
                return redirect("accounts:new_account")
            else:
                return redirect("accounts:list")
        else:
            return render(request, 'create_account.html', {
                'account_form': account_form,
                'billing_form': billing_form,
                'shipping_form': shipping_form,
                'industries': INDCHOICES,
                'countries': COUNTRIES,
                'users': users,
                'teams': teams,
                'assignedto_list': [int(user_id) for user_id in assignedto_list],
                'teams_list': teams_list
            })

    else:
        return render(request, 'create_account.html', {
            'account_form': account_form,
            'billing_form': billing_form,
            'shipping_form': shipping_form,
            'industries': INDCHOICES,
            'countries': COUNTRIES,
            'users': users,
            'teams': teams,
            'assignedto_list': assignedto_list,
            'teams_list': teams_list
        })


@login_required
def view_account(request, account_id):
    account_record = get_object_or_404(Account, id=account_id)
    comments = account_record.accounts_comments.all()
    opportunity_list = Opportunity.objects.filter(account=account_record)
    contacts = Contact.objects.filter(account=account_record)
    users = User.objects.filter(is_active=True).order_by('email')
    cases = Case.objects.filter(account=account_record)
    teams = Team.objects.all()
    return render(request, "view_account.html", {
        'account_record': account_record,
        'opportunity_list': opportunity_list,
        'stages': STAGES,
        'sources': SOURCES,
        'teams': teams,
        'contacts': contacts,
        'users': users,
        'cases': cases,
        'countries': COUNTRIES,
        'currencies': CURRENCY_CODES,
        'case_types': CASE_TYPE,
        'case_priority': PRIORITY_CHOICE,
        'case_status': STATUS_CHOICE,
        'comments': comments
    })


@login_required
def edit_account(request, edid):
    account_instance = get_object_or_404(Account, id=edid)
    account_billing_address = account_instance.billing_address
    account_shipping_address = account_instance.shipping_address
    users = User.objects.filter(is_active=True).order_by('email')
    account_form = AccountForm(instance=account_instance, assigned_to=users)
    billing_form = BillingAddressForm(instance=account_billing_address)
    shipping_form = ShippingAddressForm(prefix='ship', instance=account_shipping_address)
    teams = Team.objects.all()
    assignedto_list = request.POST.getlist('assigned_to')
    teams_list = request.POST.getlist('teams')
    if request.method == 'POST':
        account_form = AccountForm(request.POST, instance=account_instance, assigned_to=users)
        billing_form = BillingAddressForm(request.POST, instance=account_billing_address)
        shipping_form = ShippingAddressForm(request.POST, instance=account_shipping_address, prefix='ship')
        if account_form.is_valid() and billing_form.is_valid() and shipping_form.is_valid():
            billing_object = billing_form.save()
            shipping_object = shipping_form.save()
            account_object = account_form.save(commit=False)
            account_object.billing_address = billing_object
            account_object.shipping_address = shipping_object
            account_object.created_by = request.user
            account_object.save()
            account_object.assigned_to.clear()
            account_object.assigned_to.add(*assignedto_list)
            account_object.teams.clear()
            account_object.teams.add(*teams_list)
            return redirect("accounts:list")
        else:
            return render(request, 'create_account.html', {
                'account_form': account_form,
                'billing_form': billing_form,
                'shipping_form': shipping_form,
                'account_obj': account_instance,
                'billing_obj': account_billing_address,
                'shipping_obj': account_shipping_address,
                'countries': COUNTRIES,
                'industries': INDCHOICES,
                'teams': teams,
                'users': users,
                'assignedto_list': [int(user_id) for user_id in assignedto_list],
                'teams_list': teams_list
            })
    else:
        return render(request, 'create_account.html', {
            'account_form': account_form,
            'billing_form': billing_form,
            'shipping_form': shipping_form,
            'account_obj': account_instance,
            'billing_obj': account_billing_address,
            'shipping_obj': account_shipping_address,
            'countries': COUNTRIES,
            'industries': INDCHOICES,
            'teams': teams,
            'users': users,
            'assignedto_list': assignedto_list,
            'teams_list': teams_list
        })


@login_required
def remove_account(request, aid):
    account_record = get_object_or_404(Account, id=aid)
    account_record.delete()
    return redirect("accounts:list")


@login_required
def add_comment(request):
    if request.method == 'POST':
        account = get_object_or_404(Account, id=request.POST.get('accountid'))
        if request.user in account.assigned_to.all() or request.user == account.created_by:
            form = AccountCommentForm(request.POST)
            if form.is_valid():
                account_comment = form.save(commit=False)
                account_comment.comment = request.POST.get('comment')
                account_comment.commented_by = request.user
                account_comment.account = account
                account_comment.save()
                data = {"comment_id": account_comment.id, "comment": account_comment.comment,
                        "commented_on": account_comment.commented_on,
                        "commented_by": account_comment.commented_by.email}
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
        com = get_object_or_404(Comment, id=comment_id)
        form = AccountCommentForm(request.POST)
        if request.user == com.commented_by:
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
