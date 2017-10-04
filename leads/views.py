from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from leads.models import Lead
from contacts.forms import ContactForm
from django.views.decorators.csrf import csrf_exempt
from common.models import Address, Comment, Team
from common.utils import LEAD_STATUS, LEAD_SOURCE, INDCHOICES, TYPECHOICES
from leads.forms import CommentForm, CreateLeadform, AddressLeadForm
from django.urls import reverse
from accounts.forms import AccountForm
# from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from common.forms import BillingAddressForm, ShippingAddressForm
from accounts.models import Account


@login_required
def add_lead(request):
    acount = Account.objects.all()
    countries = Country.objects.all()
    assigned_user = User.objects.filter(is_active=True)
    if request.method == 'POST':
        address_form = AddressLeadForm(request.POST)
        form = CreateLeadform(request.POST)
        if form.is_valid() and address_form.is_valid():
            address_obj = address_form.save()
            lead_obj = form.save(commit=False)
            lead_obj.address = address_obj
            lead_obj.save()
            return HttpResponseRedirect(reverse('leads:list'))
        else:
            return render(request, 'leads/create_lead.html', {
                          'error_lead_form': form.errors,
                          'error_address_form': address_form.errors,
                          'acount': acount, 'countries': countries,
                          'teams': TEAMS,
                          'assigned_user': assigned_user,
                          'status': lead_status,
                          'source': lead_source})

    else:
        return render(request, 'leads/create_lead.html', {
                      'acount': acount, 'countries': countries, 'teams': TEAMS,
                      'assigned_user': assigned_user,
                      'status': lead_status, 'source': lead_source})


@login_required
def edit_lead(request, pk):
    post = get_object_or_404(Lead, id=pk)
    comments = Comments.objects.filter(leadid=pk).order_by('-id')
    dis_address_obj = get_object_or_404(Address, id=post.address.id)
    acount = Account.objects.all()
    countries = Country.objects.all()
    assigned_user = User.objects.filter(is_active=True)
    address_form = AddressLeadForm(instance=dis_address_obj)
    form = CreateLeadform(instance=post)

    if request.method == 'POST':

        address_form = AddressLeadForm(request.POST, instance=dis_address_obj)
        form = CreateLeadform(request.POST, instance=post)

        if form.is_valid() and address_form.is_valid():

            dis_address_obj = address_form.save()
            lead_obj = form.save(commit=False)
            lead_obj.address = dis_address_obj
            lead_obj.save()

            return HttpResponseRedirect(reverse('leads:list'))

        else:
            return render(request, 'leads/create_lead.html', {
                          'post': post,
                          'error_lead_form': form.errors,
                          'error_address_form': address_form.errors,
                          'acount': acount, 'countries': countries,
                          'teams': TEAMS,
                          'assigned_user': assigned_user, 'comments': comments,
                          'status': lead_status, 'source': lead_source})
    else:
        return render(request, 'leads/create_lead.html', {
                      'post': post, 'dis_address_obj': dis_address_obj,
                      'acount': acount, 'countries': countries, 'teams': TEAMS,
                      'assigned_user': assigned_user, 'comments': comments,
                      'status': lead_status, 'source': lead_source})


@login_required
def delete_lead(request, pk):
    post = Lead.objects.filter(id=pk)
    post.delete()
    return HttpResponseRedirect(reverse('leads:list'))


@login_required
def display(request):
    crm_task = Lead.objects.all()
    count = Lead.objects.count()
    dis_address_obj = Address.objects.all()
    account = Account.objects.all()
    if request.method == 'POST':
        name = request.POST.get('name')
        account = request.POST.get('account')
        status = request.POST.get('status')
        email = request.POST.get('email')
        crm_task = Lead.objects.all()
        if name:
            crm_task = Lead.objects.filter(name=name)
        if account:
            crm_task = Lead.objects.filter(account=account)
        if status:
            crm_task = Lead.objects.filter(status=status)
        if email:
            crm_task = Lead.objects.filter(email__contains=email)
        return render(request, 'leads/leads.html', {
            'crm_task': crm_task, 'dis_address_obj': dis_address_obj,
            'count': count, 'status': lead_status})
    else:
        return render(request, 'leads/leads.html', {
            'dis_address_obj': dis_address_obj, 'count': count,
            'crm_task': crm_task, 'account': account, 'status': lead_status})


@login_required
@csrf_exempt
def view_lead(request, pk):
    ss = Lead.objects.get(id=pk)
    crm_task = Lead.objects.all()
    countries = Country.objects.all()
    comments = Comments.objects.filter(leadid=pk).order_by('-id')
    return render(request, "leads/view_leads.html", {
                  "ss": ss, 'status': lead_status, 'countries': countries,
                  'crm_task': crm_task, 'comments': comments})


@login_required
def get_leads(request):
    if request.method == 'GET':
        if request.user.is_authenticated():
            leads = Lead.objects.all()
            return render(request, 'leads/leads_list.html', {'leads': leads})
        else:
            return HttpResponseRedirect('accounts/login')
    else:
        return HttpResponse('Invalid Method or No Authanticated in load_calls')


@login_required
def comment_add(request):
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = request.POST.get('comment')
            f = form.save()
            f.comment_user = request.user
            f.save()
            return JsonResponse({"error": False})
        else:
            return JsonResponse({"error": form.errors})

    if request.method == "GET":
        comment = request.GET.get('comment')
        comment_id = request.GET.get("commentid")
        com = Comments.objects.get(id=comment_id)
        form = CommentForm(request.GET)

        if request.user == com.comment_user:
            if form.is_valid():
                com.comment = comment
                com.save()
                return JsonResponse({"comment": com.comment,
                                    "commentid": comment_id})
            else:
                return JsonResponse({"error": form.errors})
        else:
            return JsonResponse({"error":
                                "You dont have authentication to edit"})
    else:
        return render(request, "404.html")


@login_required
def comment_remove(request):
    if request.method == 'POST':
        comment_id = request.POST.get('comment_id')
        Comments.objects.get(id=comment_id).delete()
        data = {"cid": comment_id}
        return JsonResponse(data)
    else:
        return HttpResponse("Something Went Wrong")


@login_required
def leads_convert(request, pk):
    account_form = AccountForm()
    billing_form = BillingAddressForm()
    shipping_form = ShippingAddressForm(prefix='ship')
    country_list = Country.objects.all()
    users = User.objects.filter(is_active=True)
    crm_task = Lead.objects.all()
    post = Lead.objects.get(id=pk)
    assigned_user = User.objects.filter(is_active=True)
    countries = Country.objects.all()
    acount = Account.objects.all()
    form = ContactForm(request.POST)
    address_form = AddressLeadForm(request.POST)
    if request.method == "POST":
        if request.POST.get('accountname') == "on":
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
                post.delete()
                return HttpResponseRedirect(reverse('leads:list'))
            else:
                street1 = request.POST.get('ship-street')
                city1 = request.POST.get('ship-city')
                state1 = request.POST.get('ship-state')
                postcode1 = request.POST.get('ship-postcode')
                country1 = request.POST.get('ship-country')
                shipdata = {'street1': street1, 'city1': city1,
                            'state1': state1,
                            'postcode1': postcode1, 'country1': country1}
                return render(request, 'leads/checkbox.html', {
                              'account_form': account_form,
                              'form1': billing_form, 'form2': shipping_form,
                              'form5': country_list,
                              'acc_error': account_form.errors,
                              'shipdata': shipdata,
                              'industries': INDCHOICES, 'types': TYPECHOICES,
                              'teams': TEAMS,
                              'users': users,
                              'crm_task': crm_task,
                              "post": post,
                              "acount": acount,
                              "assigned_user": assigned_user,
                              "counties": countries})

        if request.POST.get('contactname') == "on":
            if form.is_valid() and address_form.is_valid():
                address_obj = address_form.save()
                contact_obj = form.save(commit=False)
                contact_obj.address = address_obj
                contact_obj.save()
                return HttpResponseRedirect(reverse('contacts:list'))
            else:
                return render(request, 'leads/checkbox.html', {
                              'post': post,
                              'acount': acount,
                              'teams': TEAMS,
                              'err_contct_form': form.errors,
                              'assigned_user': assigned_user})
    else:
        return render(request, 'leads/checkbox.html', {
                      'form': account_form,
                      'form1': billing_form, 'form2': shipping_form,
                      'form5': country_list, 'industries': INDCHOICES,
                      'types': TYPECHOICES, 'teams': TEAMS,
                      'users': users,
                      'crm_task': crm_task,
                      "post": post,
                      "assigned_user": assigned_user,
                      "counties": countries,
                      'acount': acount})


# @login_required
# def new_contact(request, pk):
#     post = get_object(Lead, id=pk)
#     edit_obj = get_object(Contact, id=pk)
#     countri = Country.objects.all()
#     acount = Account.objects.all()
#     ss = Lead.objects.get(id=pk)
#     assigned_user = User.objects.filter(is_active=True)

#     if request.method == 'POST':

#         address_form = AddressForm(request.POST)
#         form = ContactForm(request.POST)

#         if form.is_valid() and address_form.is_valid():
#             address_obj = address_form.save()
#             contact_obj = form.save(commit=False)
#             contact_obj.address = address_obj
#             contact_obj.save()
#             return HttpResponseRedirect(reverse('contacts:list'))
#         else:
#             return render(request, 'leads/checkbox.html', {'ss': ss,
#                 'post': post,
#                 'acount': acount,
#                 'teams': TEAMS,
#                 'err_contct_form':form.errors,
#                 'edit_obj': edit_obj,
#                 'assigned_user': assigned_user})
