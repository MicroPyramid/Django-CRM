from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.urls import reverse
from common.models import Address, Comment, Team
from accounts.models import Account
from oppurtunity.models import Opportunity, STAGES, SOURCES
from cases.models import Case
from contacts.forms import ContactForm, CommentForm, AddressForm
from contacts.models import Contact
from planner.models import Event


@login_required
def add_contact(request):
    acount = Account.objects.all()
    countri = Country.objects.all()
    assigned_user = User.objects.filter(is_active=True)

    if request.method == 'POST':

        address_form = AddressForm(request.POST)
        form = ContactForm(request.POST)

        if form.is_valid() and address_form.is_valid():
            address_obj = address_form.save()
            contact_obj = form.save(commit=False)
            contact_obj.address = address_obj
            contact_obj.save()
            contact_obj.users = request.user
            contact_obj.save()
            return HttpResponseRedirect(reverse('contacts:list'))
        else:
            return render(request, 'contacts/create_contact.html', {
                'err_contct_form': form.errors, 'acount': acount,
                'err_address_form': address_form.errors, 'teams': TEAMS,
                'countri': countri, 'assigned_user': assigned_user})

    else:
        return render(request, 'contacts/create_contact.html', {
            'acount': acount, 'countri': countri,
            'teams': TEAMS, 'assigned_user': assigned_user})


@login_required
def display_contact(request):
    display_obj = Contact.objects.all()
    count = Contact.objects.all().count()
    acount = Account.objects.all()
    page = request.GET.get('per_page')
    name = request.GET.get('name')
    account = request.GET.get('account')
    city = request.GET.get('city')
    phone = request.GET.get('phone')
    email = request.GET.get('email')

    if name:
        display_obj = display_obj.filter(name__icontains=name)

    if account:
        display_obj = display_obj.filter(account=account)

    if city:
        a = Address.objects.filter(city__icontains=city)
        display_obj = display_obj.filter(address__in=a)

    if phone:
        display_obj = display_obj.filter(phone__contains=phone)

    if email:
        display_obj = display_obj.filter(email__contains=email)

    return render(request, 'contacts/contacts.html', {
        'contacts': display_obj, 'count': count,
        'acount': acount, 'per_page': page})


@login_required
def delete_contact(request, pk):
    Contact.objects.filter(id=pk).delete()
    if request.is_ajax():
        return JsonResponse({'error': False})
    return HttpResponseRedirect(reverse('contacts:list'))


@login_required
def edit_contact(request, pk):
    edit_obj = get_object_or_404(Contact, id=pk)
    address_obj = get_object_or_404(Address, id=edit_obj.address.id)
    acount = Account.objects.all()
    countri = Country.objects.all()
    assigned_user = User.objects.filter(is_active=True)
    address_form = AddressForm(instance=address_obj)
    form = ContactForm(instance=edit_obj)
    if request.method == 'POST':
        address_form = AddressForm(request.POST, instance=address_obj)
        form = ContactForm(request.POST, instance=edit_obj)
        if form.is_valid() and address_form.is_valid():
            addres_obj = address_form.save()
            contact_obj = form.save(commit=False)
            contact_obj.address = addres_obj
            contact_obj.save()
            if request.is_ajax():
                return JsonResponse({'error': False})
            return HttpResponseRedirect(reverse('contacts:list'))
        else:
            return render(request, 'contacts/create_contact.html', {
                'edit_obj': edit_obj, 'err_contct_form': form.errors,
                'teams': TEAMS, 'err_address_form': address_form.errors,
                'acount': acount, 'countri': countri,
                'assigned_user': assigned_user})
    else:
        return render(request, 'contacts/create_contact.html', {
            'edit_obj': edit_obj, 'address_obj': address_obj,
            'acount': acount, 'countri': countri, 'teams': TEAMS,
            'assigned_user': assigned_user})


@login_required
def view_contact(request, pk):
    con = Contact.objects.get(id=pk)
    accunt = Account.objects.all()
    contact = Contact.objects.all()
    opportunity = Opportunity.objects.filter(contacts=con).order_by('id')
    cases = Case.objects.filter(contacts=con).order_by('id')
    users = User.objects.filter(is_active=True)
    comments = Comments.objects.filter(contactid=con)
    meetings = Event.objects.all()
    return render(request, 'contacts/view_contact.html', {
        'meetings': meetings, 'opportunity': opportunity, 'comments': comments,
        'con': con, 'stages': STAGES, 'sources': SOURCES,
        'accunt': accunt, 'contact': contact, 'users': users, 'cases': cases})


@login_required
def get_contacts(request):
    if request.method == 'GET':
        if request.user.is_authenticated():
            contacts = Contact.objects.all()
            return render(request, 'contacts/contacts_list.html', {
                'contacts': contacts})
        else:
            return HttpResponseRedirect('accounts/login')
    else:
        return HttpResponse
        ('Invalid Method or Not Authanticated in load_calls')


@login_required
def comment_add(request):
    if request.method == 'POST':
        contact = get_object_or_404(Contact, id=request.POST.get('contactid'))
        assigned = False
        if contact.created_user:
            assigned = (int(contact.created_user) == request.user)
        if request.user == contact.users or assigned:
            form = CommentForm(request.POST)
            if form.is_valid():
                comment = request.POST.get('comment')
                comment_user = request.user
                contactid = request.POST.get('contactid')
                c = Comments.objects.create(
                    comment=comment,
                    contactid=Contact.objects.get(id=contactid),
                    comment_user=comment_user)
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
            return JsonResponse({"error": "You dont have Access to edit"})
    else:
        return render(request, "404.html")


@login_required
def comment_remove(request):
    if request.method == 'POST':
        comment_id = request.POST.get('comment_id')
        c = get_object_or_404(Comments, id=comment_id)
        if request.user == c.comment_user:
            get_object_or_404(Comments, id=comment_id).delete()
            data = {"cid": comment_id}
            return JsonResponse(data)
        else:
            return JsonResponse({"error": "You Dont have permisions to delete"})
    else:
        return HttpResponse("Something Went Wrong!!")
