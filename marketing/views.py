import json
import pytz
import lxml
import lxml.html
from lxml.cssselect import CSSSelector
from django.conf import Settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.http.response import (JsonResponse,
                                  HttpResponse, HttpResponseRedirect)
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy, reverse
from common import status
from marketing.models import (
    Tag, ContactList, Contact, EmailTemplate, Campaign, CampaignLog, Link
)
from marketing.forms import ContactListForm, ContactForm, EmailTemplateForm, SendCampaignForm
from marketing.tasks import upload_csv_file, run_campaign


TIMEZONE_CHOICES = [(tz, tz) for tz in pytz.common_timezones]


def get_exact_match(query, m2m_field, ids):
    # query = tasks_list.annotate(count=Count(m2m_field))\
    #             .filter(count=len(ids))
    query = query
    for _id in ids:
        query = query.filter(**{m2m_field: _id})
    return query


@login_required(login_url='/login')
def dashboard(request):
    return render(request, 'marketing/dashboard.html')


@login_required(login_url='/login')
def contact_lists(request):
    tags = Tag.objects.all()
    if (request.user.is_superuser):
        queryset = ContactList.objects.all()
    else:
        queryset = ContactList.objects.filter(created_by=request.user)
    if request.method == 'POST':
        post_tags = request.POST.get('tags')
        if request.POST.get('search'):
            queryset = queryset.filter(
                Q(name__icontains=request.POST['search']) |
                Q(created_by__email__icontains=request.POST[
                    'search'])).distinct()

        if post_tags:

            filtered_list = json.loads(request.POST['tags'])

            if len(filtered_list) > 1:
                queryset = get_exact_match(queryset, 'tags', filtered_list)
            else:
                queryset = queryset.filter(tags__id__in=filtered_list)

    per_page = request.GET.get("per_page", 10)
    paginator = Paginator(queryset, per_page)
    page = request.GET.get('page', 1)
    try:
        contact_lists = paginator.page(page)
    except PageNotAnInteger:
        contact_lists = paginator.page(1)
    except EmptyPage:
        contact_lists = paginator.page(paginator.num_pages)
    data = {'contact_lists': contact_lists, 'tags': tags}
    return render(request, 'marketing/lists/index.html', data)


@login_required(login_url='/login')
def contacts_list(request):
    contacts = Contact.objects.all()
    data = {"contacts": contacts}
    return render(request, 'marketing/lists/all.html', data)


@login_required(login_url='/login')
def contact_list_new(request):
    data = {}
    if request.method == "POST":
        form = ContactListForm(request.POST, request.FILES)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.created_by = request.user
            instance.save()
            tags = request.POST['tags'].split(
                ',') if request.POST['tags'] else []
            for each in tags:
                tag, _ = Tag.objects.get_or_create(
                    name=each, created_by=request.user)
                instance.tags.add(tag)
            if request.FILES.get('contacts_file'):
                upload_csv_file.delay(
                    form.validated_rows, request.user.id, [instance.id])

            return JsonResponse({'error': False,
                                 'data': form.data},
                                status=status.HTTP_201_CREATED)
        else:
            # return JsonResponse({'error': True, 'errors': form.errors},
            #                     status=status.HTTP_400_BAD_REQUEST)
            return JsonResponse(
                {'error': True, 'errors': form.errors},
                status=status.HTTP_200_OK)
    else:
        return render(request, 'marketing/lists/new.html', data)


@login_required(login_url='/login')
def edit_contact_list(request, pk):
    user = request.user
    try:
        contact_list = ContactList.objects.get(pk=pk)
    except ContactList.DoesNotExist:
        contact_list = ContactList.objects.none()
        return JsonResponse({}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        # contact_lists = ContactList.objects.filter(company=request.company)
        if (user.is_superuser):
            contact_lists = ContactList.objects.all()
        else:
            contact_lists = ContactList.objects.filter(created_by=request.user)

        data = {'contact_list': contact_list, 'contact_lists': contact_lists}
        return render(request, 'marketing/lists/new.html', data)
    else:
        form = ContactListForm(
            request.POST, request.FILES, instance=contact_list)
        if form.is_valid():
            instance = form.save()
            instance.tags.clear()
            tags = request.POST['tags'].split(
                ',') if request.POST['tags'] else []
            for each in tags:
                tag, _ = Tag.objects.get_or_create(
                    name=each, created_by=request.user)
                instance.tags.add(tag)
            if request.FILES.get('contacts_file'):
                upload_csv_file.delay(
                    form.validated_rows, request.user.id, [instance.id])

            return JsonResponse({'error': False,
                                 'data': form.data}, status=status.HTTP_200_OK)
        return JsonResponse({'error': True,
                             'errors': form.errors}, status=status.HTTP_200_OK)


@login_required(login_url='/login')
def view_contact_list(request, pk):
    contact_list = get_object_or_404(ContactList, pk=pk)
    contacts = Contact.objects.filter(contact_list__in=[contact_list])
    if request.POST and request.POST.get("search"):
        contacts = contacts.filter(
            Q(name__icontains=request.POST['search']) |
            Q(email__icontains=request.POST['search']))

    per_page = request.GET.get("per_page", 10)
    paginator = Paginator(contacts.order_by('id'), per_page)
    page = request.GET.get('page', 1)
    try:
        contacts = paginator.page(page)
    except PageNotAnInteger:
        contacts = paginator.page(1)
    except EmptyPage:
        contacts = paginator.page(paginator.num_pages)

    data = {'contact_list': contact_list, "contacts": contacts}
    template_name = "marketing/lists/all.html"
    return render(request, template_name, data)


@login_required(login_url='/login')
def delete_contact_list(request, pk):
    try:
        # ContactList.objects.get(pk=pk).delete()
        redirect_to = reverse('marketing:contact_lists')
    except ContactList.DoesNotExist:
        redirect_to = reverse('marketing:contact_lists')
    return HttpResponseRedirect(redirect_to)


@login_required(login_url='/login')
def contacts_list_new(request):
    if request.POST:
        form = ContactForm(request.POST)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.created_by = request.user
            instance.save()
            for each in json.loads(request.POST['contact_list']):
                instance.contact_list.add(ContactList.objects.get(id=each))
            # return JsonResponse(form.data, status=status.HTTP_201_CREATED)
            return reverse('marketing:contact_list')
        else:
            data = {'error': True, 'errors': form.errors}
    else:
        if (request.user.is_superuser):
            queryset = ContactList.objects.all()
        else:
            queryset = ContactList.objects.filter(created_by=request.user)
        data = {"contact_list": queryset}
    return render(request, 'marketing/lists/cnew.html', data)


@login_required(login_url='/login')
def edit_contact(request):
    return render(request, 'marketing/lists/edit_contact.html')


@login_required(login_url='/login')
def contact_list_detail(request):
    return render(request, 'marketing/lists/detail.html')


@login_required(login_url='/login')
def email_template_list(request):
    if (request.user.is_admin or request.user.is_superuser):
        queryset = EmailTemplate.objects.all()
    else:
        queryset = EmailTemplate.objects.filter(
            created_by=request.user)
    if request.method == 'POST':
        queryset = queryset.filter(
            Q(title__icontains=request.POST['search']) |
            Q(subject__icontains=request.POST['search']) |
            Q(created_by__email__icontains=request.POST['search']))

    per_page = request.GET.get("per_page", 10)
    paginator = Paginator(queryset.distinct(), per_page)
    page = request.GET.get('page')
    try:
        email_templates = paginator.page(page)
    except PageNotAnInteger:
        email_templates = paginator.page(1)
    except EmptyPage:
        email_templates = paginator.page(paginator.num_pages)
    data = {'email_templates': email_templates}
    return render(request, 'marketing/email_template/index.html', data)


@login_required(login_url='/login')
def email_template_new(request):
    if request.POST:
        form = EmailTemplateForm(request.POST)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.created_by = request.user
            instance.save()
            return JsonResponse({'error': False, 'data': form.data}, status=status.HTTP_201_CREATED)
        else:
            return JsonResponse({'error': True, 'errors': form.errors}, status=status.HTTP_200_OK)
    else:
        return render(request, 'marketing/email_template/new.html')


@login_required(login_url='/login')
def email_template_edit(request, pk):
    email_template = get_object_or_404(EmailTemplate, pk=pk)

    if request.method == 'GET':
        data = {'email_template': email_template}
        return render(request, 'marketing/email_template/new.html', data)
    else:
        form = EmailTemplateForm(request.POST, instance=email_template)
        if form.is_valid():
            instance = form.save(commit=False)
            # instance.created_by = request.user
            instance.save()
            return JsonResponse({'error': False, 'data': form.data}, status=status.HTTP_201_CREATED)
        return JsonResponse({'error': True, 'errors': form.errors}, status=status.HTTP_200_OK)


@login_required(login_url='/login')
def email_template_detail(request, pk):
    queryset = get_object_or_404(EmailTemplate, id=pk)
    data = {'email_template': queryset}
    return render(request, 'marketing/email_template/details.html', data)


@login_required(login_url='/login')
def email_template_delete(request, pk):
    try:
        # EmailTemplate.objects.get(id=pk).delete()
        redirect_to = reverse('marketing:email_template_list')
    except ContactList.DoesNotExist:
        redirect_to = reverse('marketing:email_template_list')
    return HttpResponseRedirect(redirect_to)


@login_required(login_url='/login')
def campaign_list(request):
    campaigns = Campaign.objects.all()
    if request.method == 'POST':
        campaigns = campaigns.filter(
            Q(title__icontains=request.POST['search']) |
            Q(created_by__email__icontains=request.POST['search'])
        )
        if request.POST['scheduled_on']:
            campaigns = campaigns.filter(
                schedule_date_time__date__lte=request.POST['scheduled_on'])
    per_page = request.GET.get("per_page", 10)  # Show 15 contacts per page
    paginator = Paginator(campaigns.distinct().order_by('-created_on'), per_page)
    page = request.GET.get('page')
    try:
        campaigns = paginator.page(page)
    except PageNotAnInteger:
        campaigns = paginator.page(1)
    except EmptyPage:
        campaigns = paginator.page(paginator.num_pages)
    data = {'campaigns_list': campaigns}
    return render(request, 'marketing/campaign/index.html', data)


@login_required(login_url='/login')
def campaign_new(request):
    if request.method == 'GET':
        if request.user.is_admin or request.user.is_superuser:
            email_templates = EmailTemplate.objects.all()
        else:
            email_templates = EmailTemplate.objects.filter(
                created_by=request.user)
        if request.user.is_admin or request.user.is_superuser:
            contact_lists = ContactList.objects.all()
        else:
            contact_lists = ContactList.objects.filter(
                created_by=request.user)
        # if request.GET.get('contact_list'):
        #     contacts = Contact.objects.filter(
        #         contact_list__id__in=json.loads(request.GET.get('contact_list'))).distinct()

        data = {
            'contact_lists': contact_lists, 'email_templates': email_templates, "timezones": TIMEZONE_CHOICES}
        # return JsonResponse(data, status=status.HTTP_200_OK)
        return render(request, 'marketing/campaign/new.html', data)
    else:
        print ("request.POST", request.POST)
        form = SendCampaignForm(request.POST)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.created_by = request.user
            if request.POST['from_email']:
                instance.from_email = request.POST['from_email']
            if request.POST['from_name']:
                instance.from_name = request.POST['from_name']
            if request.POST['reply_to_email']:
                instance.reply_to_email = request.POST['reply_to_email']
            instance.save()
            for each in json.loads(request.POST['contact_list']):
                instance.contact_lists.add(ContactList.objects.get(id=each))
            # contacts = Contact.objects.filter(contact_list__in=json.loads(request.POST['contact_list'])).distinct()
            # for each_contact in contacts:
            #     instance.contacts.add(each_contact)

            camp = instance

            html = camp.html
            dom = lxml.html.document_fromstring(html)
            selAnchor = CSSSelector('a')
            links = selAnchor(dom)
            llist = []
            # Extract links and unique links
            for e in links:
                llist.append(e.get('href'))

            # get uniaue linnk
            links = set(llist)

            # Replace Links with new One
            domain_url = '%s://%s' % (request.scheme, request.META['HTTP_HOST'])
            if Link.objects.filter(campaign_id=camp.id):
                Link.objects.filter(campaign_id=camp.id).delete()
            for l in links:
                link = Link.objects.create(campaign_id=camp.id, original=l)
                html = html.replace(
                    'href="' + l + '"', 'href="' + domain_url + '/a/' + str(link.id) + '/e/{{email_id}}"')
            camp.html_processed = html
            camp.sent_status = "scheduled"
            camp.save()

            if request.POST['schedule_later'] == 'false':
                run_campaign.delay(instance.id)
            else:
                schedule_date_time = request.POST.get('schedule_date_time', '')
                # user_timezone = request.POST.get('timezone', '')
                # if user_timezone and schedule_date_time:
                #     print ("schedule_date_time", schedule_date_time)
                #     print ("timezone", user_timezone)
                #     start_time_object = ddatetime.strptime(schedule_date_time, '%Y-%m-%d %H:%M:%S')
                #     schedule_date_time = convert_to_custom_timezone(start_time_object, user_timezone, to_utc=True)
                #     print ("After", schedule_date_time)
                instance.schedule_date_time = schedule_date_time
                # instance.timezone = request.POST['timezone']
            instance.save()

            return JsonResponse({'error': True, 'data': form.data}, status=status.HTTP_201_CREATED)
        return JsonResponse({'error': True, 'errors': form.errors}, status=status.HTTP_200_OK)


@login_required(login_url='/login')
def campaign_edit(request):
    return render(request, 'marketing/campaign/edit.html')


@login_required(login_url='/login')
def campaign_details(request):
    return render(request, 'marketing/campaign/details.html')


@login_required(login_url='/login')
def campaign_delete(request):
    return render(request, 'marketing/campaign/details.html')
