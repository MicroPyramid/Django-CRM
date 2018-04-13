from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.urls import reverse

from common.models import User, Address, Comment, Team
from common.forms import BillingAddressForm
from common.utils import COUNTRIES
from accounts.models import Account
from contacts.models import Contact
from contacts.forms import ContactForm, ContactCommentForm


# CRUD Operations Start


@login_required
def contacts_list(request):
    contact_obj_list = Contact.objects.all()
    accounts = Account.objects.all()
    page = request.POST.get('per_page')
    first_name = request.POST.get('first_name')
    account = request.POST.get('account')
    city = request.POST.get('city')
    phone = request.POST.get('phone')
    email = request.POST.get('email')
    if first_name:
        contact_obj_list = contact_obj_list.filter(first_name__icontains=first_name)
    if account:
        contact_obj_list = contact_obj_list.filter(account=account)
    if city:
        a = Address.objects.filter(city__icontains=city)
        contact_obj_list = contact_obj_list.filter(address__in=a)
    if phone:
        contact_obj_list = contact_obj_list.filter(phone__icontains=phone)
    if email:
        contact_obj_list = contact_obj_list.filter(email__icontains=email)
    return render(request, 'contacts.html', {
        'contact_obj_list': contact_obj_list,
        'accounts': accounts,
        'per_page': page
    })


@login_required
def add_contact(request):
    accounts = Account.objects.all()
    users = User.objects.filter(is_active=True).order_by('email')
    form = ContactForm(assigned_to=users, account=accounts)
    address_form = BillingAddressForm()
    teams = Team.objects.all()
    assignedto_list = request.POST.getlist('assigned_to')
    teams_list = request.POST.getlist('teams')
    if request.method == 'POST':
        form = ContactForm(request.POST, assigned_to=users, account=accounts)
        address_form = BillingAddressForm(request.POST)
        if form.is_valid() and address_form.is_valid():
            address_obj = address_form.save()
            contact_obj = form.save(commit=False)
            contact_obj.address = address_obj
            contact_obj.created_by = request.user
            contact_obj.save()
            contact_obj.assigned_to.add(*assignedto_list)
            contact_obj.teams.add(*teams_list)
            if request.is_ajax():
                return JsonResponse({'error': False})
            if request.POST.get("savenewform"):
                return HttpResponseRedirect(reverse("contacts:add_contact"))
            else:
                return HttpResponseRedirect(reverse('contacts:list'))
        else:
            if request.is_ajax():
                return JsonResponse({'error': True, 'contact_errors': form.errors})
            return render(request, 'create_contact.html', {
                'contact_form': form,
                'address_form': address_form,
                'accounts': accounts,
                'countries': COUNTRIES,
                'teams': teams,
                'users': users,
                'assignedto_list': [int(user_id) for user_id in assignedto_list],
                'teams_list': teams_list
            })
    else:
        return render(request, 'create_contact.html', {
            'contact_form': form,
            'address_form': address_form,
            'accounts': accounts,
            'countries': COUNTRIES,
            'teams': teams,
            'users': users,
            'assignedto_list': assignedto_list,
            'teams_list': teams_list
        })


@login_required
def view_contact(request, contact_id):
    contact_record = get_object_or_404(
        Contact.objects.select_related("address"), id=contact_id)
    comments = contact_record.contact_comments.all()
    return render(request, 'view_contact.html', {
        'contact_record': contact_record,
        'comments': comments})


@login_required
def edit_contact(request, pk):
    contact_obj = get_object_or_404(Contact, id=pk)
    address_obj = get_object_or_404(Address, id=contact_obj.address.id)
    accounts = Account.objects.all()
    users = User.objects.filter(is_active=True).order_by('email')
    form = ContactForm(instance=contact_obj, assigned_to=users, account=accounts)
    address_form = BillingAddressForm(instance=address_obj)
    teams = Team.objects.all()
    assignedto_list = request.POST.getlist('assigned_to')
    teams_list = request.POST.getlist('teams')
    if request.method == 'POST':
        form = ContactForm(request.POST, instance=contact_obj, assigned_to=users, account=accounts)
        address_form = BillingAddressForm(request.POST, instance=address_obj)
        if form.is_valid() and address_form.is_valid():
            addres_obj = address_form.save()
            contact_obj = form.save(commit=False)
            contact_obj.address = addres_obj
            contact_obj.created_by = request.user
            contact_obj.save()
            contact_obj.assigned_to.clear()
            contact_obj.assigned_to.add(*assignedto_list)
            contact_obj.teams.clear()
            contact_obj.teams.add(*teams_list)
            if request.is_ajax():
                return JsonResponse({'error': False})
            return HttpResponseRedirect(reverse('contacts:list'))
        else:
            if request.is_ajax():
                return JsonResponse({'error': True, 'contact_errors': form.errors})
            return render(request, 'create_contact.html', {
                'contact_form': form,
                'address_form': address_form,
                'contact_obj': contact_obj,
                'accounts': accounts,
                'countries': COUNTRIES,
                'teams': teams,
                'users': users,
                'assignedto_list': [int(user_id) for user_id in assignedto_list],
                'teams_list': teams_list
            })
    else:
        return render(request, 'create_contact.html', {
            'contact_form': form,
            'address_form': address_form,
            'contact_obj': contact_obj,
            'address_obj': address_obj,
            'accounts': accounts,
            'countries': COUNTRIES,
            'teams': teams,
            'users': users,
            'assignedto_list': assignedto_list,
            'teams_list': teams_list
        })


@login_required
def remove_contact(request, pk):
    contact_record = get_object_or_404(Contact, id=pk)
    contact_record.delete()
    if request.is_ajax():
        return JsonResponse({'error': False})
    else:
        return HttpResponseRedirect(reverse('contacts:list'))

# CRUD Operations End
# Comments Section Starts


@login_required
def add_comment(request):
    if request.method == 'POST':
        contact = get_object_or_404(Contact, id=request.POST.get('contactid'))
        if request.user in contact.assigned_to.all() or request.user == contact.created_by:
            form = ContactCommentForm(request.POST)
            if form.is_valid():
                contact_comment = form.save(commit=False)
                contact_comment.comment = request.POST.get('comment')
                contact_comment.commented_by = request.user
                contact_comment.contact = contact
                contact_comment.save()
                data = {"comment_id": contact_comment.id, "comment": contact_comment.comment,
                        "commented_on": contact_comment.commented_on,
                        "commented_by": contact_comment.commented_by.email}
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
        form = ContactCommentForm(request.POST)
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

# Comments Section Ends
# Other Views


@login_required
def get_contacts(request):
    if request.method == 'GET':
        contacts = Contact.objects.filter()
        return render(request, 'contacts_list.html', {'contacts': contacts})
    else:
        return HttpResponse('Invalid Method or Not Authanticated in load_calls')
