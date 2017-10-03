from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from accounts.models import Account
from common.models import Address, Team, Comment
from common.utils import INDCHOICES, TYPECHOICES, COUNTRIES
from oppurtunity.models import Opportunity, STAGES, SOURCES
from contacts.models import Contact
from cases.models import Case
from accounts.forms import AccountForm, BillingAddressForm, ShippingAddressForm, CommentForm
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User


@login_required
@csrf_exempt
def account(request):
    count = Account.objects.all().count()
    accounts_list = Account.objects.all()
    page = request.POST.get('per_page')
    if request.GET.get('name'):
        accounts_list = Account.objects.filter(
            name__contains=request.GET.get('name'))
    if request.GET.get('city'):
        accounts_list = accounts_list.filter(
            billing_address__in=[i.id for i in Address.objects.filter(
                city__contains=request.GET.get('city'))])
    if request.GET.get('account_type'):
        accounts_list = accounts_list.filter(
            account_type__contains=request.GET.get('account_type'))
    if request.GET.get('industry'):
        accounts_list = accounts_list.filter(
            industry__contains=request.GET.get('industry'))
    return render(request, "accounts/accounts.html", {
        'count': count, 'industries': INDCHOICES, 'types': TYPECHOICES,
        'per_page': page, 'accounts_list': accounts_list})


@login_required
@csrf_exempt
def new_account(request):
    account_form = AccountForm()
    billing_form = BillingAddressForm()
    shipping_form = ShippingAddressForm(prefix='ship')
    country_list = Country.objects.all()
    users = User.objects.filter(is_active=True)
    if request.method == 'POST':
        account_form = AccountForm(request.POST)
        billing_form = BillingAddressForm(request.POST)
        shipping_form = ShippingAddressForm(request.POST, prefix='ship')
        if account_form.is_valid() and billing_form.is_valid() and shipping_form.is_valid():
            if request.POST.get("users"):
                users = User.objects.get(id=request.POST.get("users"))
                users.save()
            billing_object = billing_form.save()
            shipping_object = shipping_form.save()
            account_object = account_form.save(commit=False)
            account_object.billing_address = billing_object
            account_object.shipping_address = shipping_object
            account_object.save()
            return HttpResponseRedirect('/accounts/list/')
        else:
            street1 = request.POST.get('ship-street')
            city1 = request.POST.get('ship-city')
            state1 = request.POST.get('ship-state')
            postcode1 = request.POST.get('ship-postcode')
            country1 = request.POST.get('ship-country')
            shipdata = {'street1': street1, 'city1': city1, 'state1': state1,
                        'postcode1': postcode1, 'country1': country1}
            return render(request, 'accounts/create_account.html', {
                'account_form': account_form, 'form1': billing_form,
                'form2': shipping_form, 'shipdata': shipdata, 'users': users,
                'form5': country_list, 'acc_error': account_form.errors,
                'industries': INDCHOICES, 'types': TYPECHOICES, 'teams': TEAMS})

    else:
        return render(request, 'accounts/create_account.html', {
            'form': account_form, 'form1': billing_form, 'users': users,
            'form2': shipping_form, 'form5': country_list, 'teams': TEAMS,
            'industries': INDCHOICES, 'types': TYPECHOICES})


@login_required
@csrf_exempt
def remove_account(request, aid):
    # aid = request.POST["acid"]
    Account.objects.filter(id=aid).delete()
    # count_list = Account.objects.all().count()
    # data = {"aid": aid, 'count_list': count_list}
    # return JsonResponse(data)
    return HttpResponseRedirect('/accounts/list/')


@login_required
@csrf_exempt
def view_account(request, aid):
    acc = Account.objects.get(id=aid)
    country = Country.objects.all()
    comments = Comment.objects.filter(accountid=aid).order_by('-id')
    opp_list = Opportunity.objects.filter(account=acc)
    contact = Contact.objects.filter(account=acc)
    user = User.objects.all()
    case = Case.objects.filter(account=acc)
    return render(request, "accounts/view_account.html", {
        'ac': acc, 'opp': opp_list, 'stages': STAGES, 'sources': SOURCES,
        'comments': comments, 'country': country, 'user': user, 'case': case,
        'teams': TEAMS, 'contact': contact, 'user': user, 'case': case})


@login_required
@csrf_exempt
def edit_account(request, edid):
    account_instance = get_object_or_404(Account, id=edid)
    billing_instance = get_object_or_404(Address, id=account_instance.billing_address.id)
    shipping_instance = get_object_or_404(Address, id=account_instance.shipping_address.id)
    account_form = AccountForm(instance=account_instance)
    billing_form = BillingAddressForm(instance=billing_instance)
    shipping_form = ShippingAddressForm(prefix='ship', instance=shipping_instance)
    country_list = Country.objects.all()
    users = User.objects.filter(is_active=True)
    if request.method == 'POST':
        account_form = AccountForm(request.POST, instance=account_instance)
        billing_form = BillingAddressForm(request.POST, instance=billing_instance)
        shipping_form = ShippingAddressForm(request.POST, instance=shipping_instance, prefix='ship')
        if account_form.is_valid() and billing_form.is_valid() and shipping_form.is_valid():
            if request.POST.get("users"):
                users = User.objects.get(id=request.POST.get("users"))
                users.save()
            billing_object = billing_form.save()
            shipping_object = shipping_form.save()
            account_object = account_form.save(commit=False)
            account_object.billing_address = billing_object
            account_object.shipping_address = shipping_object
            account_object.save()
            return HttpResponseRedirect('/accounts/list/')
        else:
            return render(request, 'accounts/create_account.html', {
                'form': account_form, 'form1': billing_form, 'teams': TEAMS,
                'form2': shipping_form, 'edit2': shipping_instance,
                'edit': account_instance, 'edit1': billing_instance,
                'form5': country_list, 'acc_error': account_form.errors,
                'types': TYPECHOICES, 'industries': INDCHOICES, 'users': users})
    else:
        return render(request, 'accounts/create_account.html', {
            'form': account_form, 'form1': billing_form,
            'form2': shipping_form, 'edit': account_instance,
            'edit1': billing_instance, 'edit2': shipping_instance,
            'form5': country_list, 'industries': INDCHOICES,
            'types': TYPECHOICES, 'teams': TEAMS, 'users': users})


@login_required
def comment_add(request):
    if request.method == 'POST':
        account = get_object_or_404(Account, id=request.POST.get('accountid'))
        assigned = False
        if account.assigned_user:
            assigned = (int(account.assigned_user) == request.user)
        if request.user == account.users or assigned:
            form = CommentForm(request.POST)
            if form.is_valid():
                comment = request.POST.get('comment')
                comment_user = request.user
                accountid = request.POST.get('accountid')
                c = Comment.objects.create(comment=comment, accountid=Account.objects.get(id=accountid), comment_user=comment_user)
                data = {"com_id": c.id, "comment": c.comment,
                        "comment_date": c.comment_date,
                        "com_user": c.comment_user.username}
                return JsonResponse(data)
            else:
                return JsonResponse({"error": form['comment'].errors})
        else:
            data = {'error': "You Dont Have permissions to Comment"}
            return JsonResponse(data)


@login_required
def comment_remove(request):
    if request.method == 'POST':
        comment_id = request.POST.get('comment_id')
        c = get_object_or_404(Comment, id=comment_id)
        if request.user == c.comment_user:
            get_object_or_404(Comment, id=comment_id).delete()
            data = {"cid": comment_id}
            return JsonResponse(data)
        else:
            return JsonResponse({"error": "You Dont have permisions to delete"})
    else:
        return HttpResponse("Something Went Wrong")


@login_required
def comment_edit(request):
    if request.method == "POST":
        comment = request.POST.get('comment')
        comment_id = request.POST.get("commentid")
        com = get_object_or_404(Comment, id=comment_id)
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
def get_accounts(request):
    if request.method == 'GET':
        if request.user.is_authenticated():
            accounts = Account.objects.all()
            return render(request, 'accounts/accounts_list.html', {
                'accounts': accounts})
        else:
            return HttpResponseRedirect('accounts/login')
    else:
        return HttpResponse('Invalid Method or Not Authanticated in load_calls')
    return HttpResponse('Oops!! Something Went Wrong..  in load_calls')
