import csv
import json
from datetime import datetime as ddatetime

import lxml
import lxml.html
import pytz
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Q
from django.http.response import (HttpResponse, HttpResponseRedirect,
                                  JsonResponse)
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from lxml.cssselect import CSSSelector

from common import status
from common.utils import convert_to_custom_timezone
from common.models import User
from marketing.forms import (ContactForm, ContactListForm, EmailTemplateForm,
                             SendCampaignForm, EmailCampaignForm, BlockedDomainsForm,
                             BlockedEmailForm, MarketingContactEmailSearchForm)
from marketing.models import (Campaign, CampaignLinkClick, CampaignLog,
                              CampaignOpen, Contact, ContactList,
                              EmailTemplate, Link, Tag, FailedContact, ContactUnsubscribedCampaign,
                              ContactEmailCampaign, BlockedDomain, BlockedEmail)
from marketing.tasks import (run_campaign, upload_csv_file,
                            delete_multiple_contacts_tasks,
                            send_campaign_email_to_admin_contact,
                            update_elastic_search_index)
from common.access_decorators_mixins import marketing_access_required, MarketingAccessRequiredMixin, admin_login_required
from haystack.generic_views import SearchView
from haystack.query import SearchQuerySet

TIMEZONE_CHOICES = [(tz, tz) for tz in pytz.common_timezones]


# def get_exact_match(query, m2m_field, ids):
#     # query = tasks_list.annotate(count=Count(m2m_field))\
#     #             .filter(count=len(ids))
#     query = query
#     for _id in ids:
#         query = query.filter(**{m2m_field: _id})
#     return query


@login_required(login_url='/login')
@marketing_access_required
def dashboard(request):
    if request.user.role == 'ADMIN' or request.user.is_superuser:
        email_templates = EmailTemplate.objects.all()
        contacts = Contact.objects.all()
        campaign = Campaign.objects.all()
        contacts_list = ContactList.objects.all()
    else:
        email_templates = EmailTemplate.objects.filter(created_by=request.user)
        contacts = Contact.objects.filter(created_by=request.user)
        campaign = Campaign.objects.filter(created_by=request.user)
        contacts_list = ContactList.objects.filter(created_by=request.user)

    # x_axis_titles = [
    #     campaign_obj.title for campaign_obj in campaign[:5]]
    x_axis_titles = [
        campaign_obj.title[0:10] + '...' if len(campaign_obj.title) > 15 else campaign_obj.title for campaign_obj in campaign[:5]]
    y_axis_bounces = [
        campaign_obj.get_all_email_bounces_count for campaign_obj in campaign[:5]]
    y_axis_unsubscribed = [
        campaign_obj.get_all_emails_unsubscribed_count for campaign_obj in campaign[:5]]
    y_axis_subscribed = [
        campaign_obj.get_all_emails_subscribed_count for campaign_obj in campaign[:5]]
    y_axis_opened = [
        campaign_obj.get_all_emails_contacts_opened for campaign_obj in campaign[:5]]


    context = {
        'email_templates': email_templates,
        'contacts': contacts,
        'campaigns': campaign,
        'contacts_list': contacts_list,
        'y_axis_subscribed': y_axis_subscribed,
        'y_axis_unsubscribed': y_axis_unsubscribed,
        'y_axis_bounces': y_axis_bounces,
        'y_axis_opened': y_axis_opened,
        'x_axis_titles': x_axis_titles,
    }
    return render(request, 'marketing/dashboard.html', context)


@login_required(login_url='/login')
@marketing_access_required
def contact_lists(request):
    tags = Tag.objects.all()
    if (request.user.role == "ADMIN"):
        queryset = ContactList.objects.all()
    else:
        queryset = ContactList.objects.filter(
            Q(created_by=request.user) | Q(visible_to=request.user))

    users = User.objects.filter(
        id__in=queryset.values_list('created_by_id', flat=True))
    if request.GET.get('tag'):
        queryset = queryset.filter(tags=request.GET.get('tag'))
    if request.method == 'POST':
        post_tags = request.POST.getlist('tag')

        if request.POST.get('contact_list_name'):
            queryset = queryset.filter(
                name__icontains=request.POST.get('contact_list_name'))

        if request.POST.get('created_by'):
            queryset = queryset.filter(
                created_by=request.POST.get('created_by'))

        if request.POST.get('tag'):
            queryset = queryset.filter(tags__id__in=post_tags)
            request_tags = request.POST.getlist('tag')

    data = {'contact_lists': queryset, 'tags': tags, 'users': users,
            'request_tags': request.POST.getlist('tag'), }
    return render(request, 'marketing/lists/index.html', data)


@login_required(login_url='/login')
@marketing_access_required
def contacts_list(request):
    if (request.user.role == "ADMIN"):
        contacts = Contact.objects.all()
        contact_lists = ContactList.objects.all()
    else:
        contact_ids = request.user.marketing_contactlist.all().values_list('contacts',
                                                                           flat=True)
        contacts = Contact.objects.filter(id__in=contact_ids)
        contact_lists = ContactList.objects.filter(created_by=request.user)
        # contacts = Contact.objects.filter(created_by=request.user)
    users = User.objects.filter(
        id__in=contacts.values_list('created_by_id', flat=True))

    if request.method == 'GET':
        context = {'contacts': contacts, 'users': users, 'contact_lists': contact_lists}
        return render(request, 'marketing/lists/all.html', context)

    if request.method == 'POST':
        data = request.POST
        if data.get('contact_name'):
            contacts = contacts.filter(
                name__icontains=data.get('contact_name'))

        if data.get('contact_email'):
            contacts = contacts.filter(email__icontains=data.get('contact_email'))

        if data.get('created_by'):
            contacts = contacts.filter(created_by=data.get('created_by'))

        if data.get('contact_list'):
            contacts = contacts.filter(contact_list=data.get('contact_list'))

        context = {'contacts': contacts, 'users': User.objects.all(),
            'contact_lists': contact_lists}
        return render(request, 'marketing/lists/all.html', context)


@login_required(login_url='/login')
@marketing_access_required
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
                    form.validated_rows, form.invalid_rows, request.user.id, [instance.id])

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
@marketing_access_required
def edit_contact_list(request, pk):
    user = request.user
    contact_list = get_object_or_404(ContactList, pk=pk)
    if request.method == 'GET':
        # contact_lists = ContactList.objects.filter(company=request.company)
        if (user.is_superuser or request.user.role == 'ADMIN'):
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
                    form.validated_rows, form.invalid_rows, request.user.id, [instance.id])

            return JsonResponse({'error': False,
                                 'data': form.data}, status=status.HTTP_200_OK)
        return JsonResponse({'error': True,
                             'errors': form.errors}, status=status.HTTP_200_OK)


# @login_required(login_url='/login')
# @marketing_access_required
# def view_contact_list(request, pk):
#     contact_list = get_object_or_404(ContactList, pk=pk)
#     contacts = Contact.objects.filter(contact_list__in=[contact_list])
#     if request.POST and request.POST.get("search"):
#         contacts = contacts.filter(
#             Q(name__icontains=request.POST['search']) |
#             Q(email__icontains=request.POST['search']))

#     per_page = request.GET.get("per_page", 10)
#     paginator = Paginator(contacts.order_by('id'), per_page)
#     page = request.GET.get('page', 1)
#     try:
#         contacts = paginator.page(page)
#     except PageNotAnInteger:
#         contacts = paginator.page(1)
#     except EmptyPage:
#         contacts = paginator.page(paginator.num_pages)

#     data = {'contact_list': contact_list, "contacts": contacts}
#     template_name = "marketing/lists/all.html"
#     return render(request, template_name, data)


# @login_required(login_url='/login')
# @marketing_access_required
# def delete_contact_list(request, pk):
#     contact_list_obj = get_object_or_404(ContactList, pk=pk)
#     if not (request.user.role == 'ADMIN' or request.user.is_superuser or contact_list_obj.created_by == request.user):
#         raise PermissionDenied

#     contact_list_obj.delete()
#     redirect_to = reverse('marketing:contact_lists')
#     return HttpResponseRedirect(redirect_to)


# @login_required(login_url='/login')
# @marketing_access_required
# def contacts_list_new(request):
#     if request.POST:
#         form = ContactForm(request.POST)
#         if form.is_valid():
#             instance = form.save(commit=False)
#             instance.created_by = request.user
#             instance.save()
#             for each in json.loads(request.POST['contact_list']):
#                 instance.contact_list.add(ContactList.objects.get(id=each))
#             # return JsonResponse(form.data, status=status.HTTP_201_CREATED)
#             return reverse('marketing:contact_list')
#         else:
#             data = {'error': True, 'errors': form.errors}
#     else:
#         if (request.user.is_superuser):
#             queryset = ContactList.objects.all()
#         else:
#             queryset = ContactList.objects.filter(created_by=request.user)
#         data = {"contact_list": queryset}
#     return render(request, 'marketing/lists/cnew.html', data)


@login_required(login_url='/login')
@marketing_access_required
def edit_contact(request, pk):
    url_redirect_to = None
    contact_obj = get_object_or_404(Contact, pk=pk)
    if not (request.user.role == 'ADMIN' or request.user.is_superuser or contact_obj.created_by == request.user or
            (contact_obj.id in request.user.marketing_contactlist.all().values_list('contacts', flat=True))):
        raise PermissionDenied
    if request.method == 'GET':
        form = ContactForm(instance=contact_obj)
        return render(request, 'marketing/lists/edit_contact.html', {'form': form})

    if request.method == 'POST':
        form = ContactForm(request.POST, instance=contact_obj)
        if form.is_valid():
            if form.has_changed():
                if contact_obj.contact_list.count() > 1:
                    contact_list_obj = ContactList.objects.filter(
                        id=request.POST.get('from_url')).first()
                    if contact_list_obj:
                        contact_obj.contact_list.remove(contact_list_obj)
                    updated_contact = ContactForm(request.POST)
                    if updated_contact.is_valid():
                        updated_contact_obj = updated_contact.save()
                        updated_contact_obj.created_by = request.user
                        updated_contact_obj.save()
                        updated_contact_obj.contact_list.add(contact_list_obj)
                else:
                    contact = form.save(commit=False)
                    if form.is_valid():
                        contact.save()
                        form.save_m2m()
            else:
                contact = form.save(commit=False)
                if form.is_valid():
                    contact.save()
                    form.save_m2m()
            if request.POST.get('from_url'):
                return JsonResponse({'error': False,
                                     'success_url': reverse('marketing:contact_list_detail', args=(request.POST.get('from_url'),))})
            return JsonResponse({'error': False, 'success_url': reverse('marketing:contacts_list')})
        else:
            return JsonResponse({'error': True, 'errors': form.errors, })


@login_required(login_url='/login')
@marketing_access_required
def delete_contact(request, pk):
    contact_obj = get_object_or_404(Contact, pk=pk)

    if not (request.user.role == 'ADMIN' or request.user.is_superuser or contact_obj.created_by == request.user or
            (contact_obj.id in request.user.marketing_contactlist.all().values_list('contacts', flat=True))):
        raise PermissionDenied
    if request.GET.get('from_contact'):
        if contact_obj.contact_list.count() == 1:
            contact_obj.delete()
            # update_elastic_search_index.delay()
            return redirect(reverse('marketing:contact_list_detail', args=(request.GET.get('from_contact'),)))
        else:
            contact_list_obj = get_object_or_404(ContactList, pk=request.GET.get('from_contact'))
            contact_obj.contact_list.remove(contact_list_obj)
            # update_elastic_search_index.delay()
            return redirect(reverse('marketing:contact_list_detail', args=(request.GET.get('from_contact'),)))
    else:
        contact_obj.delete()
        # update_elastic_search_index.delay()
    return redirect('marketing:contacts_list')


@login_required(login_url='/login')
@marketing_access_required
def contact_list_detail(request, pk):
    contact_list = get_object_or_404(ContactList, pk=pk)
    if not (request.user.role == 'ADMIN' or request.user.is_superuser or contact_list.created_by == request.user):
        raise PermissionDenied
    contacts_list = contact_list.contacts.filter(is_bounced=False)
    contacts_list_count = contact_list.contacts.filter(is_bounced=False).count()
    bounced_contacts_list = contact_list.contacts.filter(is_bounced=True)
    bounced_contacts_list_count = contact_list.contacts.filter(is_bounced=True).count()
    duplicate_contacts = contact_list.duplicate_contact_contact_list.all()
    if request.POST:
        if request.POST.get('name'):
            contacts_list = contacts_list.filter(
                name__icontains=request.POST.get('name'))
        if request.POST.get('email'):
            contacts_list = contacts_list.filter(
                email__icontains=request.POST.get('email'))
        if request.POST.get('company_name'):
            contacts_list = contacts_list.filter(
                company_name=request.POST.get('company_name'))

        if request.POST.get('name'):
            bounced_contacts_list = bounced_contacts_list.filter(
                name__icontains=request.POST.get('name'))
        if request.POST.get('email'):
            bounced_contacts_list = bounced_contacts_list.filter(
                email__icontains=request.POST.get('email'))
        if request.POST.get('company_name'):
            bounced_contacts_list = bounced_contacts_list.filter(
                company_name=request.POST.get('company_name'))

    page = request.GET.get('bounced_contacts_page', 1)
    paginator = Paginator(bounced_contacts_list, 10)
    try:
        bounced_contacts_list = paginator.page(page)
    except:
        bounced_contacts_list = paginator.page(paginator.num_pages)

    data = {'contact_list': contact_list, "contacts_list": contacts_list,
        "bounced_contacts_list":bounced_contacts_list,
        'bounced_contacts_list_count': bounced_contacts_list_count,
        'contacts_list_count': contacts_list_count,
        'duplicate_contacts': duplicate_contacts,
        # these two are added for digg pagintor
        'paginator':paginator,'page_obj': bounced_contacts_list,}
    return render(request, 'marketing/lists/detail.html', data)


# @login_required(login_url='/login')
# @marketing_access_required
# def failed_contact_list_detail(request, pk):
#     contact_list = get_object_or_404(ContactList, pk=pk)
#     failed_contacts_list = contact_list.failed_contacts.all()
#     data = {'contact_list': contact_list,
#             "failed_contacts_list": failed_contacts_list}
#     return render(request, 'marketing/lists/failed_detail.html', data)


@login_required(login_url='/login')
@marketing_access_required
def failed_contact_list_download_delete(request, pk):
    contact_list = get_object_or_404(ContactList, pk=pk)
    failed_contacts_list = contact_list.failed_contacts.all()
    if failed_contacts_list.count() > 0:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="failed_contacts.csv"'
        writer = csv.writer(response)
        writer.writerow(["company name", "email", "first name",
                         "last name", "city", "state"])

        for contact in failed_contacts_list:
            writer.writerow([
                contact.company_name, contact.email, contact.name, contact.last_name, contact.city, contact.state])
        failed_contacts_list.delete()
        return response
    else:
        return HttpResponseRedirect(reverse('marketing:contact_list_detail', kwargs={"pk": pk}))


@login_required(login_url='/login')
@marketing_access_required
def email_template_list(request):
    # users = User.objects.all()
    if (request.user.role == 'ADMIN' or request.user.is_superuser):
        queryset = EmailTemplate.objects.all()
    else:
        queryset = EmailTemplate.objects.filter(
            created_by=request.user)
    users = User.objects.filter(
        id__in=queryset.values_list('created_by_id', flat=True))
    if request.method == 'POST':
        if request.POST.get('template_name'):
            queryset = queryset.filter(
                title__icontains=request.POST.get('template_name'))

        if request.POST.get('created_by'):
            queryset = queryset.filter(
                created_by=request.POST.get('created_by'))

    data = {'email_templates': queryset, 'users': users}
    return render(request, 'marketing/email_template/index.html', data)


@login_required(login_url='/login')
@marketing_access_required
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
@marketing_access_required
def email_template_edit(request, pk):
    email_template = get_object_or_404(EmailTemplate, pk=pk)

    if not (request.user.role == 'ADMIN' or request.user.is_superuser or request.user == email_template.created_by):
        raise PermissionDenied

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
@marketing_access_required
def email_template_detail(request, pk):
    queryset = get_object_or_404(EmailTemplate, id=pk)
    if not (request.user.role == 'ADMIN' or request.user.is_superuser or request.user == queryset.created_by):
        raise PermissionDenied
    data = {'email_template': queryset}
    return render(request, 'marketing/email_template/details.html', data)


@login_required(login_url='/login')
@marketing_access_required
def email_template_delete(request, pk):
    email_template_obj = get_object_or_404(EmailTemplate, pk=pk)
    if not (request.user.role == 'ADMIN' or request.user.is_superuser or request.user == email_template_obj.created_by):
        raise PermissionDenied
    email_template_obj.delete()
    redirect_to = reverse('marketing:email_template_list')
    return HttpResponseRedirect(redirect_to)


@login_required(login_url='/login')
@marketing_access_required
def campaign_list(request):
    # users = User.objects.all()
    if (request.user.role == "ADMIN"):
        queryset = Campaign.objects.all()
    else:
        queryset = Campaign.objects.all().filter(created_by=request.user)
    users = User.objects.filter(
        id__in=queryset.values_list('created_by_id', flat=True))
    if request.GET.get('tag'):
        queryset = queryset.filter(tags=request.GET.get('tag'))
    if request.method == 'POST':
        if request.POST.get('campaign_name'):
            queryset = queryset.filter(
                title__icontains=request.POST.get('campaign_name'))

        if request.POST.get('created_by'):
            queryset = queryset.filter(
                created_by=request.POST.get('created_by'))

    data = {'campaigns_list': queryset, 'users': users}
    return render(request, 'marketing/campaign/index.html', data)


@login_required(login_url='/login')
@marketing_access_required
def campaign_new(request):
    if request.method == 'GET':
        if request.user.role == 'ADMIN' or request.user.is_superuser:
            email_templates = EmailTemplate.objects.all()
        else:
            email_templates = EmailTemplate.objects.filter(
                created_by=request.user)
        if request.user.role == 'ADMIN' or request.user.is_superuser:
            contact_lists = ContactList.objects.all()
        else:
            contact_lists = ContactList.objects.filter(
                created_by=request.user)
        # if request.GET.get('contact_list'):
        #     contacts = Contact.objects.filter(
        #         contact_list__id__in=json.loads(request.GET.get('contact_list'))).distinct()

        data = {
            'contact_lists': contact_lists, 'email_templates': email_templates,
            "timezones": TIMEZONE_CHOICES, "settings_timezone": settings.TIME_ZONE}
        # return JsonResponse(data, status=status.HTTP_200_OK)
        return render(request, 'marketing/campaign/new.html', data)
    else:
        form = SendCampaignForm(request.POST, request.FILES,
                                contacts_list=request.POST.getlist('contact_list'))
        if form.is_valid():
            instance = form.save(commit=False)
            instance.created_by = request.user
            if request.POST.get('from_email'):
                instance.from_email = request.POST['from_email']
            if request.POST.get('from_name'):
                instance.from_name = request.POST['from_name']
            if request.POST.get('reply_to_crm') == 'true':
                instance.reply_to_email = settings.MARKETING_REPLY_EMAIL
            else:
                if request.POST.get('reply_to_email'):
                    instance.reply_to_email = request.POST['reply_to_email']
            # if request.FILES.get('attachment'):
            #     instance.attachment = request.FILES.get('attachment')
            instance.save()
            for each in request.POST.getlist('contact_list'):
                instance.contact_lists.add(ContactList.objects.get(id=each))
            # contacts = Contact.objects.filter(contact_list__in=json.loads(request.POST['contact_list'])).distinct()
            # for each_contact in contacts:
            #     instance.contacts.add(each_contact)
            instance.original_contact_count = instance.contact_lists.exclude(
                contacts__email=None).values_list('contacts__email').count()
            instance.save()
            tags = request.POST['tags'].split(
                ',') if request.POST['tags'] else []
            for each in tags:
                tag, _ = Tag.objects.get_or_create(
                    name=each, created_by=request.user)
                instance.tags.add(tag)

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
            # domain_url = '%s://%s' % (request.scheme, request.META['HTTP_HOST'])
            domain_url = request.scheme + '://' + request.get_host()
            if Link.objects.filter(campaign_id=camp.id):
                Link.objects.filter(campaign_id=camp.id).delete()
            for l in links:
                link = Link.objects.create(campaign_id=camp.id, original=l)
                html = html.replace(
                    'href="' + l + '"', 'href="' + domain_url + '/marketing/cm/link/' + str(link.id) + '/e/{{email_id}}"')

            camp.html_processed = html
            camp.sent_status = "scheduled"
            camp.save()

            if request.POST.get('schedule_later', None) == 'true':
                schedule_date_time = request.POST.get('schedule_date_time', '')
                user_timezone = request.POST.get('timezone', '')
                if user_timezone and schedule_date_time:
                    start_time_object = ddatetime.strptime(
                        schedule_date_time, '%Y-%m-%d %H:%M')
                    schedule_date_time = convert_to_custom_timezone(
                        start_time_object, user_timezone, to_utc=True)
                instance.schedule_date_time = schedule_date_time
                instance.timezone = user_timezone
                instance.save()
                send_campaign_email_to_admin_contact.delay(
                    instance.id, domain=request.get_host(), protocol=request.scheme)
            else:
                run_campaign.delay(
                    instance.id, domain=request.get_host(), protocol=request.scheme)
                send_campaign_email_to_admin_contact.delay(
                    instance.id, domain=request.get_host(), protocol=request.scheme)
            return JsonResponse({'error': False, 'data': form.data}, status=status.HTTP_201_CREATED)
        return JsonResponse({'error': True, 'errors': form.errors}, status=status.HTTP_200_OK)


# @login_required(login_url='/login')
# @marketing_access_required
# def campaign_edit(request):
#     return render(request, 'marketing/campaign/edit.html')


@login_required(login_url='/login')
@marketing_access_required
def campaign_details(request, pk):
    campaign = get_object_or_404(Campaign, pk=pk)
    if not (request.user.role == 'ADMIN' or request.user.is_superuser or request.user == campaign.created_by):
        raise PermissionDenied
    contact_lists = campaign.contact_lists.all()
    if (request.user.role == 'ADMIN' or request.user.is_superuser):
        contact_lists = contact_lists
    else:
        # contact_lists = contact_lists.filter(
        #     is_public=True, created_by=request.user)
        contact_lists = contact_lists.filter(created_by=request.user)

    contacts = Contact.objects.filter(contact_list__in=contact_lists)
    contact_list_ids = campaign.contact_lists.all().values_list('id', flat=True)

    contacts = Contact.objects.filter(contact_list__id__in=contact_list_ids)

    all_contacts = contacts
    bounced_contacts = contacts.filter(is_bounced=True).distinct()
    unsubscribe_contacts = contacts.filter(
        is_unsubscribed=True).distinct()
    # unsubscribe_contacts_ids = ContactUnsubscribedCampaign.objects.filter(
    #     campaigns=campaign, is_unsubscribed=True).values_list('contacts_id', flat=True)
    # unsubscribe_contacts = Contact.objects.filter(
    #     id__in=unsubscribe_contacts_ids)
    # read_contacts = campaign.marketing_links.filter(Q(clicks__gt=0)).distinct()
    contact_ids = CampaignOpen.objects.filter(
        campaign=campaign).values_list('contact_id', flat=True)
    read_contacts = Contact.objects.filter(id__in=contact_ids)
    sent_contacts = contacts.exclude(
        Q(is_bounced=True) | Q(is_unsubscribed=True))
    # if request.POST:
    #     contacts = contacts.filter(Q(name__icontains=request.POST['search']))

    tab = request.GET.get('tab', 'contacts')
    per_page = request.GET.get("per_page", 10)
    page = request.GET.get('page', 1)

    # contacts_paginator = Paginator(contacts.order_by('id'), per_page)
    # if (tab == "contacts"):
    #     page = page
    # else:
    #     page = 1
    # try:
    #     contacts = contacts_paginator.page(page)
    # except PageNotAnInteger:
    #     contacts = contacts_paginator.page(1)
    # except EmptyPage:
    #     contacts = contacts_paginator.page(contacts_paginator.num_pages)

    # unsubscribe_contacts_paginator = Paginator(
    #     unsubscribe_contacts.order_by('id'), per_page)
    # if (tab == "unsubscribe_contacts"):
    #     page = page
    # else:
    #     page = 1

    # try:
    #     unsubscribe_contacts = unsubscribe_contacts_paginator.page(page)
    # except PageNotAnInteger:
    #     unsubscribe_contacts = unsubscribe_contacts_paginator.page(1)
    # except EmptyPage:
    #     unsubscribe_contacts = unsubscribe_contacts_paginator.page(
    #         unsubscribe_contacts_paginator.num_pages)

    # bounced_contacts_paginator = Paginator(
    #     bounced_contacts.order_by('id'), per_page)
    # if (tab == "bounced_contacts"):
    #     page = page
    # else:
    #     page = 1

    # try:
    #     bounced_contacts = bounced_contacts_paginator.page(page)
    # except PageNotAnInteger:
    #     bounced_contacts = bounced_contacts_paginator.page(1)
    # except EmptyPage:
    #     bounced_contacts = bounced_contacts_paginator.page(
    #         bounced_contacts_paginator.num_pages)

    # sent_contacts_paginator = Paginator(sent_contacts.order_by('id'), per_page)
    # if (tab == "sent_contacts"):
    #     page = page
    # else:
    #     page = 1

    # try:
    #     sent_contacts = sent_contacts_paginator.page(page)
    # except PageNotAnInteger:
    #     sent_contacts = sent_contacts_paginator.page(1)
    # except EmptyPage:
    #     sent_contacts = sent_contacts_paginator.page(
    #         sent_contacts_paginator.num_pages)

    # all_contacts_paginator = Paginator(all_contacts.order_by('id'), per_page)
    # if (tab == "all_contacts"):
    #     page = page
    # else:
    #     page = 1

    # try:
    #     all_contacts = all_contacts_paginator.page(page)
    # except PageNotAnInteger:
    #     all_contacts = all_contacts_paginator.page(1)
    # except EmptyPage:
    #     all_contacts = all_contacts_paginator.page(
    #         all_contacts_paginator.num_pages)

    # read_contacts_paginator = Paginator(read_contacts.order_by('id'), per_page)
    # if (tab == "read_contacts"):
    #     page = page
    # else:
    #     page = 1

    # try:
    #     read_contacts = read_contacts_paginator.page(page)
    # except PageNotAnInteger:
    #     read_contacts = read_contacts_paginator.page(1)
    # except EmptyPage:
    #     read_contacts = read_contacts_paginator.page(
    #         read_contacts_paginator.num_pages)

    data = {'contact_lists': contact_lists, "campaign": campaign,
            "contacts": contacts, 'unsubscribe_contacts': unsubscribe_contacts,
            'bounced_contacts': bounced_contacts, 'read_contacts': read_contacts,
            'sent_contacts': sent_contacts, 'all_contacts': all_contacts, 'tab': tab}

    return render(request, 'marketing/campaign/details.html', data)


@login_required(login_url='/login')
@marketing_access_required
def campaign_delete(request, pk):
    campaign = get_object_or_404(Campaign, pk=pk)
    if not (request.user.role == 'ADMIN' or request.user.is_superuser or request.user == campaign.created_by):
        raise PermissionDenied
    campaign.delete()
    redirect_url = reverse('marketing:campaign_list')
    return redirect(redirect_url)


def campaign_link_click(request, link_id, email_id):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')

    if x_forwarded_for:
        ipaddress = x_forwarded_for.split(',')[-1].strip()
    else:
        ipaddress = request.META.get('REMOTE_ADDR')

    link = Link.objects.filter(id=link_id).first()
    contact = Contact.objects.filter(id=email_id).first()
    if link and contact:
        campaign_link_click = CampaignLinkClick.objects.filter(
            link=link, campaign=link.campaign, contact=contact).first()
        if not campaign_link_click:
            campaign_link_click = CampaignLinkClick.objects.create(
                link=link, campaign=link.campaign, contact=contact, ip_address=ipaddress)
            link.unique += 1
        else:
            campaign_link_click.ip_address = ipaddress
        link.clicks += 1
        link.save()
        campaign_link_click.save()
        url = link.original
    else:
        # url = settings.URL_FOR_LINKS
        url = link.original
    return redirect(url)


def campaign_open(request, campaign_log_id, email_id): # pragma: no cover
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')

    if x_forwarded_for:
        ipaddress = x_forwarded_for.split(',')[-1].strip()
    else:
        ipaddress = request.META.get('REMOTE_ADDR')

    campaign_log = CampaignLog.objects.filter(id=campaign_log_id).first()
    contact = Contact.objects.filter(id=email_id).first()
    image_data = open('static/images/company.png', 'rb').read()
    if campaign_log and contact:
        campaign_open = CampaignOpen.objects.filter(
            campaign=campaign_log.campaign, contact=contact).first()
        if not campaign_open:
            campaign_open = CampaignOpen.objects.create(
                campaign=campaign_log.campaign, contact=contact, ip_address=ipaddress)
            campaign_log.campaign.opens_unique += 1
        else:
            campaign_open.ip_address = ipaddress
        campaign_log.campaign.opens += 1
        campaign_log.campaign.status = "Sent"
        campaign_log.campaign.save()
        campaign_open.save()
    return HttpResponse(image_data, content_type="image/png")


def demo_file_download(request):
    sample_data = [
        'company name,email,first name,last name,city,state\n',
        'company_name_1,user1@email.com,first_name,last_name,Hyderabad,Telangana\n',
        'company_name_2,user2@email.com,first_name,last_name,Hyderabad,Telangana\n',
        'company_name_3,user3@email.com,first_name,last_name,Hyderabad,Telangana\n',
        'company_name_4,user4@email.com,first_name,last_name,Hyderabad,Telangana\n'
    ]
    response = HttpResponse(
        sample_data, content_type='text/plain')
    response['Content-Disposition'] = 'attachment; filename={}'.format(
        'sample_data.csv')
    return response


def unsubscribe_from_campaign(request, contact_id, campaign_id):
    contact_obj = get_object_or_404(Contact, pk=contact_id)
    contact_obj.is_unsubscribed = True
    contact_obj.save()
    campaign_obj = Campaign.objects.filter(id=campaign_id).first()
    # campaign_obj = get_object_or_404(Campaign, pk=campaign_id)
    if campaign_obj:
        ContactUnsubscribedCampaign.objects.create(
            campaigns=campaign_obj, contacts=contact_obj, is_unsubscribed=True)
    return render(request, 'unsubscribe_from_campaign_template.html')


@login_required
@marketing_access_required
def contact_detail(request, contact_id):
    contact_obj = get_object_or_404(Contact, pk=contact_id)
    if not (request.user.role == 'ADMIN' or request.user.is_superuser or contact_obj.created_by == request.user or
            (contact_obj.id in request.user.marketing_contactlist.all().values_list('contacts', flat=True))):
        # the above query is for: a contact may be common to multiple contact lists, so query from
        # a contact list can be created by multiple users
        raise PermissionDenied
    if request.method == 'GET':
        return render(request, 'contact_detail.html', {'contact_obj': contact_obj})


# @login_required(login_url='/login')
# @marketing_access_required
# def edit_failed_contact(request, pk):
#     contact_obj = get_object_or_404(FailedContact, pk=pk)
#     if not (request.user.role == 'ADMIN' or request.user.is_superuser or contact_obj.created_by == request.user):
#         raise PermissionDenied
#     if request.method == 'GET':
#         form = ContactForm(instance=contact_obj)
#         return render(request, 'marketing/lists/edit_contact.html', {'form': form})

#     if request.method == 'POST':
#         form = ContactForm(request.POST, instance=contact_obj)
#         if form.is_valid():
#             contact = form.save(commit=False)
#             contact.save()
#             form.save_m2m()
#             return JsonResponse({'error': False, 'success_url': reverse('marketing:contacts_list')})
#         else:
#             return JsonResponse({'error': True, 'errors': form.errors, })


# @login_required(login_url='/login')
# @marketing_access_required
# def delete_failed_contact(request, pk):
#     contact_obj = get_object_or_404(FailedContact, pk=pk)
#     if not (request.user.role == 'ADMIN' or request.user.is_superuser or contact_obj.created_by == request.user):
#         raise PermissionDenied
#     if request.method == 'GET':
#         contact_obj.delete()
#         return redirect('marketing:contacts_list')


@login_required
@marketing_access_required
def download_contacts_for_campaign(request, compaign_id):
    campaign_obj = get_object_or_404(Campaign, pk=compaign_id)
    if not (request.user.role == 'ADMIN' or request.user.is_superuser or campaign_obj.created_by == request.user):
        raise PermissionDenied
    if request.method == 'GET':
        if request.GET.get('is_bounced') == 'true':
            contact_ids = campaign_obj.campaign_log_contacts.filter(contact__is_bounced=True).values_list(
                'contact__id', flat=True)
            contacts = Contact.objects.filter(id__in=contact_ids).values(
                'company_name', 'email', 'name', 'last_name', 'city', 'state')

        if request.GET.get('is_unsubscribed') == 'true':

            # unsubscribe_contacts_ids = ContactUnsubscribedCampaign.objects.filter(
            #     campaigns=campaign_obj, is_unsubscribed=True).values_list('contacts_id', flat=True)
            contact_ids = campaign_obj.campaign_log_contacts.filter(contact__is_unsubscribed=True).values_list(
                'contact__id', flat=True)
            contacts = Contact.objects.filter(id__in=contact_ids).values(
                'company_name', 'email', 'name', 'last_name', 'city', 'state')

        if request.GET.get('is_opened') == 'true':
            contact_ids = CampaignOpen.objects.filter(
                campaign=campaign_obj).values_list('contact_id', flat=True)
            contacts = Contact.objects.filter(id__in=contact_ids).values(
                'company_name', 'email', 'name', 'last_name', 'city', 'state')

        data = [
            'company name,email,first name,last name,city,state\n',
        ]
        for contact in contacts:
            data.append(
                str(contact.get('company_name')) + ',' +
                str(contact.get('email')) + ',' +
                str(contact.get('name')) + ',' +
                str(contact.get('last_name')) + ',' +
                str(contact.get('city')) + ',' +
                str(contact.get('state')) + '\n'
            )
        response = HttpResponse(
            data, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename={}'.format(
            'data_downloads.csv')
        return response


@login_required
@marketing_access_required
def create_campaign_from_template(request, template_id):
    email_template_obj = get_object_or_404(EmailTemplate, pk=template_id)
    if request.method == 'GET':
        url_location = reverse('marketing:campaign_new')
        url_query_params = '?email_template={}'.format(template_id)
        url = url_location + url_query_params
        return HttpResponseRedirect(url)


def download_links_clicked(request, campaign_id):
    campaign_obj = get_object_or_404(Campaign, pk=campaign_id)
    campaign_link_click_objects = campaign_obj.campaign_link_click.all().select_related('link', 'campaign', 'contact')
    csv_row_headers = ['email', 'company', 'first name', 'last name', 'city', 'state', 'original link', 'unique clicks', 'total clicks', 'campaign title']
    data = []
    data.append(','.join(csv_row_headers) + '\n')
    if campaign_link_click_objects:
        for campaign_link_click_object in campaign_link_click_objects:
            data.append(
                str(campaign_link_click_object.contact.email) + ',' +
                str(campaign_link_click_object.contact.company_name) + ',' +
                str(campaign_link_click_object.contact.name) + ',' +
                str(campaign_link_click_object.contact.last_name) + ',' +
                str(campaign_link_click_object.contact.city) + ',' +
                str(campaign_link_click_object.contact.state) + ',' +
                str(campaign_link_click_object.link.original) + ',' +
                str(campaign_link_click_object.link.unique) + ',' +
                str(campaign_link_click_object.link.clicks) + ',' +
                str(campaign_link_click_object.link.campaign.title) + '\n'
            )
        response = HttpResponse(data, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename={}'.format('data_downloads.csv')
        return response


@login_required(login_url='/login')
@marketing_access_required
def delete_multiple_contacts(request):
    contacts_list = Contact.objects.filter(id__in=request.POST.getlist('selected_list[]'))
    shared_contact_lists = request.user.marketing_contactlist.all().values_list('contacts', flat=True)
    cannot_be_deleted = []
    error = False
    for contact_obj in contacts_list:
        if not (request.user.role == 'ADMIN' or request.user.is_superuser or contact_obj.created_by == request.user or (contact_obj.id in shared_contact_lists)):
            cannot_be_deleted.append(contact_obj.email)
            error = True
    if len(cannot_be_deleted) == 0:
        error = False
        for contact_obj in contacts_list:
            if request.POST.get('from_contact'):
                if contact_obj.contact_list.count() == 1:
                    contact_obj.delete()
                else:
                    if request.POST.get('duplicate_contacts', None) == 'true':
                        contact_list_obj = get_object_or_404(ContactList, pk=request.POST.get('from_contact'))
                        contact_obj.contact_list.remove(contact_list_obj)

                        contact_list_duplicates = contact_list_obj.duplicate_contact_contact_list.all()
                        contacts_list_ids = contacts_list.values_list('id', flat=True)
                        contact_list_duplicates.filter(contacts__id__in=contacts_list_ids).delete()
                    else:
                        contact_list_obj = get_object_or_404(ContactList, pk=request.POST.get('from_contact'))
                        contact_obj.contact_list.remove(contact_list_obj)

        return JsonResponse({'error':False, 'refresh': True})
    else:
        message = "You don't have permission to delete {}".format(', '.join(cannot_be_deleted))
        return JsonResponse({'error': True, 'message' : message })



@login_required(login_url='/login')
@marketing_access_required
def delete_all_contacts(request, contact_list_id):

    contacts_list_obj = get_object_or_404(ContactList, pk=contact_list_id)
    if not (request.user.role == 'ADMIN' or request.user.is_superuser or contacts_list_obj.created_by == request.user):
        raise PermissionDenied
    if request.GET.get('bounced','') == 'true':
        bounced = True
    else:
        bounced = False
    if request.GET.get('duplicate_contacts', '') == 'true':
        contact_list_duplicates = contacts_list_obj.duplicate_contact_contact_list.all()
        if contact_list_duplicates:
            for dup_contact_obj in contact_list_duplicates:
                if dup_contact_obj.contacts.contact_list.count() > 1:
                    contact = dup_contact_obj.contacts
                    contact.contact_list.remove(contacts_list_obj)
                    dup_contact_obj.delete()
                    # dup_contact_obj.contacts.contact_list.remove(contacts_list_obj)
                # else:
                #     dup_contact_obj.contacts.delete()
    else:
        contacts_objs = contacts_list_obj.contacts.filter(is_bounced=bounced)
        if contacts_objs:
            for contact_obj in contacts_objs:
                if contact_obj.contact_list.count() > 1:
                    contact_obj.contact_list.remove(contacts_list_obj)
                else:
                    contact_obj.delete()

    # delete_multiple_contacts_tasks.delay(contact_list_id, bounced)
    redirect_to = reverse('marketing:contact_list_detail', args=(contact_list_id,))
    return HttpResponseRedirect(redirect_to)


@login_required
@marketing_access_required
def download_failed_contacts(request, contact_list_id):

    contact_list_obj = get_object_or_404(ContactList, pk=contact_list_id)
    if not (request.user.role == 'ADMIN' or request.user.is_superuser or contact_list_obj.created_by == request.user):
        raise PermissionDenied

    failed_contacts = contact_list_obj.failed_contacts.values('company_name', 'email', 'name', 'last_name', 'city', 'state')
    if failed_contacts:
        data = [
            'company name,email,first name,last name,city,state\n',
        ]
        for contact in failed_contacts:
            data.append(
                str(contact.get('company_name')) + ',' +
                str(contact.get('email')) + ',' +
                str(contact.get('name')) + ',' +
                str(contact.get('last_name')) + ',' +
                str(contact.get('city')) + ',' +
                str(contact.get('state')) + '\n'
            )
        response = HttpResponse(
            data, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename={}'.format(
            'failed_contacts.csv')
        return response

    else:
        return HttpResponse('No Data')


@login_required
@admin_login_required
def list_all_emails_for_campaigns(request):
    context = {}
    if request.method == 'GET':
        queryset = ContactEmailCampaign.objects.all()
        context['contacts'] = queryset
        return render(request, 'email_for_campaigns_list.html', context)


@login_required
@admin_login_required
def add_email_for_campaigns(request):
    context = {}
    if request.method == 'GET':
        form = EmailCampaignForm()
        context['form'] = form
        return render(request, 'add_email_for_campaign.html', context)
    if request.method == 'POST':
        form = EmailCampaignForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.created_by = request.user
            obj.save()
            return JsonResponse({'error':False, 'success_url':reverse('common:api_settings')})
        else:
            return JsonResponse({'error':True, 'errors':form.errors})


@login_required
@admin_login_required
def edit_email_for_campaigns(request, pk):
    edit_contact_obj = get_object_or_404(ContactEmailCampaign, pk=pk)
    context = {}
    if request.method == 'GET':
        form = EmailCampaignForm(instance=edit_contact_obj)
        context['form'] = form
        context['edit_obj'] = edit_contact_obj
        return render(request, 'add_email_for_campaign.html', context)
    if request.method == 'POST':
        form = EmailCampaignForm(request.POST, instance=edit_contact_obj)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.save()
            return JsonResponse({'error':False, 'success_url':reverse('common:api_settings')})
        else:
            return JsonResponse({'error':True, 'errors':form.errors})


@login_required
@admin_login_required
def delete_email_for_campaigns(request, pk):
    contact_obj = get_object_or_404(ContactEmailCampaign, pk=pk)
    context = {}
    if request.method == 'GET':
        contact_obj.delete()
        return HttpResponseRedirect(reverse('common:api_settings'))

# the below views should be in settings page

@login_required
@admin_login_required
def add_blocked_domain(request):
    if request.method == 'GET':
        form = BlockedDomainsForm()
        return render(request, 'add_blocked_domain.html', {'form': form})
    if request.method == 'POST':
        form = BlockedDomainsForm(request.POST)
        if form.is_valid():
            domain = form.save(commit=False)
            domain.created_by = request.user
            domain.save()
            return JsonResponse({'error':False, 'success_url':reverse('common:api_settings')})
        else:
            return JsonResponse({'error':True, 'errors':form.errors})

@login_required
@admin_login_required
def blocked_domain_list(request):
    if request.method == 'GET':
        blocked_domains = BlockedDomain.objects.all()
        return render(request, 'blocked_domain_list.html', {'blocked_domains': blocked_domains})
    if request.method == 'POST':
        blocked_domains = BlockedDomain.objects.all()
        if request.POST.get('domain', ''):
            blocked_domains = blocked_domains.filter(domain__icontains=request.POST.get('domain', ''))
        if request.POST.get('created_by', ''):
            blocked_domains = blocked_domains.filter(created_by_id=request.POST.get('created_by', ''))
        return render(request, 'blocked_domain_list.html', {'blocked_domains': blocked_domains})

@login_required
@admin_login_required
def edit_blocked_domain(request, blocked_domain_id):
    block_domain_obj = get_object_or_404(BlockedDomain, pk=blocked_domain_id)
    if request.method == 'GET':
        form = BlockedDomainsForm(instance=block_domain_obj)
        return render(request, 'add_blocked_domain.html', {'form': form, 'block_domain_obj': block_domain_obj})
    if request.method == 'POST':
        form = BlockedDomainsForm(request.POST, instance=block_domain_obj)
        if form.is_valid():
            form.save()
            return JsonResponse({'error':False, 'success_url':reverse('common:api_settings')})
        else:
            return JsonResponse({'error':True, 'errors':form.errors})

@login_required
@admin_login_required
def delete_blocked_domain(request, blocked_domain_id):
    block_domain_obj = get_object_or_404(BlockedDomain, pk=blocked_domain_id)
    block_domain_obj.delete()
    return redirect(reverse('common:api_settings') + '?blocked_domains')


@login_required
@admin_login_required
def add_blocked_email(request):
    if request.method == 'GET':
        form = BlockedEmailForm()
        return render(request, 'add_blocked_email.html', {'form': form})
    if request.method == 'POST':
        form = BlockedEmailForm(request.POST)
        if form.is_valid():
            email = form.save(commit=False)
            email.created_by = request.user
            email.save()
            return JsonResponse({'error':False, 'success_url':reverse('common:api_settings')})
        else:
            return JsonResponse({'error':True, 'errors':form.errors})

@login_required
@admin_login_required
def blocked_email_list(request):
    if request.method == 'GET':
        blocked_emails = BlockedEmail.objects.all()
        return render(request, 'blocked_email_list.html', {'blocked_emails': blocked_emails})
    if request.method == 'POST':
        blocked_emails = BlockedEmail.objects.all()
        if request.POST.get('email', ''):
            blocked_emails = blocked_emails.filter(email__icontains=request.POST.get('email', ''))
        if request.POST.get('created_by', ''):
            blocked_emails = blocked_emails.filter(created_by_id=request.POST.get('created_by', ''))
        return render(request, 'blocked_email_list.html', {'blocked_emails': blocked_emails})

@login_required
@admin_login_required
def edit_blocked_email(request, blocked_email_id):
    block_email_obj = get_object_or_404(BlockedEmail, pk=blocked_email_id)
    if request.method == 'GET':
        form = BlockedEmailForm(instance=block_email_obj)
        return render(request, 'add_blocked_email.html', {'form': form, 'block_email_obj': block_email_obj})
    if request.method == 'POST':
        form = BlockedEmailForm(request.POST, instance=block_email_obj)
        if form.is_valid():
            form.save()
            return JsonResponse({'error':False, 'success_url':reverse('common:api_settings')})
        else:
            return JsonResponse({'error':True, 'errors':form.errors})

@login_required
@admin_login_required
def delete_blocked_email(request, blocked_email_id):
    block_email_obj = get_object_or_404(BlockedEmail, pk=blocked_email_id)
    block_email_obj.delete()
    return redirect(reverse('common:api_settings') + '?blocked_emails')

@login_required(login_url='/login')
@marketing_access_required
def contacts_list_elastic_search(request):
    if (request.user.role == "ADMIN"):
        # contacts = Contact.objects.filter(is_bounced=False)
        contacts = SearchQuerySet().filter(is_bounced='false').models(Contact)
        bounced_contacts = SearchQuerySet().filter(is_bounced='true').models(Contact)
        failed_contacts = SearchQuerySet().models(FailedContact).filter()
        # bounced_contacts = Contact.objects.filter(is_bounced=True)
        # failed_contacts = FailedContact.objects.all()
        contact_lists = ContactList.objects.all()
    else:
        contact_ids = request.user.marketing_contactlist.all().values_list('contacts',
            flat=True)
        contacts = SearchQuerySet().filter(is_bounced='false', id__in=contact_ids).models(Contact)
        bounced_contacts = SearchQuerySet().filter(is_bounced='true', id__in=contact_ids).models(Contact)
        failed_contacts = SearchQuerySet().models(FailedContact).filter(created_by_id=str(request.user.id))
        # contacts = Contact.objects.filter(id__in=contact_ids).exclude(is_bounced=True)
        # bounced_contacts = Contact.objects.filter(id__in=contact_ids, is_bounced=True)
        # failed_contacts = FailedContact.objects.filter(created_by=request.user)
        contact_lists = ContactList.objects.filter(created_by=request.user)
        # contacts = Contact.objects.filter(created_by=request.user)

    users = User.objects.filter(
        id__in=[_id for _id in contacts.values_list('created_by_id', flat=True) if _id != ''])

    if request.method == 'GET':
        context = {'contacts': contacts, 'users': users, 'contact_lists': contact_lists,
            'bounced_contacts': bounced_contacts, 'failed_contacts': failed_contacts,
        }
        return render(request, 'search_contact_emails.html', context)

    if request.method == 'POST':
        data = request.POST
        if data.get('name'):
            contacts = contacts.filter(
                name__icontains=data.get('name'))
            bounced_contacts = bounced_contacts.filter(
                name__icontains=data.get('name'))
            failed_contacts = failed_contacts.filter(
                name__icontains=data.get('name'))
        if data.get('email'):
            contacts = contacts.filter(email__icontains=data.get('email'))
            bounced_contacts = bounced_contacts.filter(email__icontains=data.get('email'))
            failed_contacts = failed_contacts.filter(email__icontains=data.get('email'))

        if data.get('domain_name'):
            contacts = contacts.filter(email_domain__icontains=data.get('domain_name'))
            bounced_contacts = bounced_contacts.filter(email_domain__icontains=data.get('domain_name'))
            failed_contacts = failed_contacts.filter(email_domain__icontains=data.get('domain_name'))

        if data.get('created_by'):
            contacts = contacts.filter(created_by_id=data.get('created_by'))
            bounced_contacts = bounced_contacts.filter(created_by_id=data.get('created_by'))
            failed_contacts = failed_contacts.filter(created_by_id=data.get('created_by'))

        if data.get('contact_list'):
            contacts = contacts.filter(contact_lists_id=data.get('contact_list'))
            bounced_contacts = bounced_contacts.filter(contact_lists_id=data.get('contact_list'))
            failed_contacts = failed_contacts.filter(contact_lists_id=data.get('contact_list'))

        context = {'contacts': contacts, 'users': users, 'contact_lists': contact_lists,
            'bounced_contacts': bounced_contacts, 'failed_contacts': failed_contacts,
        }
        return render(request, 'search_contact_emails.html', context)


# class MarketingContactEmailSearch(SearchView):
#     form_class = MarketingContactEmailSearchForm

#     def get_query(self):
#         import pdb; pdb.set_trace()
#         if self.form.is_valid():
#             return self.form.cleaned_data["email_domain"]

#         return ""

#     # def get_queryset(self):
#     #     # queryset = super(MarketingContactEmailSearch, self).get_queryset()
#     #     queryset = SearchQuerySet().models(Contact).filter(
#     #         email__icontains=self.request.GET.get('email_domain', None))
#     #     return queryset

#     # def get_context_data(self, *args, **kwargs):
#     #     context = super(MarketingContactEmailSearch, self).get_context_data(*args, **kwargs)
#     #     import pdb; pdb.set_trace()
#     #     return context