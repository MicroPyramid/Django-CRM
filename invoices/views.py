import io
import os

import pdfkit
from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http.response import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.template.loader import render_to_string
from django.views.generic import (CreateView, DeleteView, DetailView, FormView,
                                  TemplateView, UpdateView, View)

from common.models import Address, Attachments, Comment, User
from common.tasks import send_email_user_mentions
from invoices.forms import (InvoiceAddressForm, InvoiceAttachmentForm,
                            InvoiceCommentForm, InvoiceForm)
from invoices.models import Invoice
from invoices.tasks import send_email, send_invoice_email, send_invoice_email_cancel, create_invoice_history
from common.access_decorators_mixins import (
    sales_access_required, marketing_access_required, SalesAccessRequiredMixin, MarketingAccessRequiredMixin)
from teams.models import Teams


@login_required
@sales_access_required
def invoices_list(request):

    if request.user.role == 'ADMIN' or request.user.is_superuser:
        users = User.objects.all()
    # elif request.user.google.all():
    #     # users = User.objects.none()
    #     # users = User.objects.filter(id=request.user.id)
    #     users = User.objects.filter(Q(role='ADMIN') | Q(id=request.user.id))
    elif request.user.role == 'USER':
        users = User.objects.filter(Q(role='ADMIN') | Q(id=request.user.id))
    status = (
        ('Draft', 'Draft'),
        ('Sent', 'Sent'),
        ('Paid', 'Paid'),
        ('Pending', 'Pending'),
        ('Cancel', 'Cancel'),
    )

    if request.method == 'GET':
        context = {}
        if request.user.role == 'ADMIN' or request.user.is_superuser:
            invoices = Invoice.objects.all().distinct()
        else:
            invoices = Invoice.objects.filter(
                Q(created_by=request.user) | Q(assigned_to=request.user)).distinct()
        context['invoices'] = invoices.order_by('id')
        context['status'] = status
        context['users'] = users
        user_ids = list(invoices.values_list('created_by', flat=True))
        user_ids.append(request.user.id)
        context['created_by_users'] = users.filter(is_active=True, id__in=user_ids)
        today = datetime.today().date()
        context['today'] = today
        return render(request, 'invoices_list.html', context)

    if request.method == 'POST':
        context = {}
        context['status'] = status
        context['users'] = users
        invoices = Invoice.objects.filter()
        if request.user.role == 'ADMIN' or request.user.is_superuser:
            invoices = invoices
        else:
            invoices = invoices.filter(
                Q(created_by=request.user) | Q(assigned_to=request.user)).distinct()

        if request.POST.get('invoice_title_number', None):
            invoices = invoices.filter(
                Q(invoice_title__icontains=request.POST.get('invoice_title_number')) |
                Q(invoice_number__icontains=request.POST.get('invoice_title_number')))

        if request.POST.get('created_by', None):
            invoices = invoices.filter(
                created_by__id=request.POST.get('created_by'))

        if request.POST.getlist('assigned_to', None):
            invoices = invoices.filter(
                assigned_to__in=request.POST.getlist('assigned_to'))
            context['assigned_to'] = request.POST.getlist('assigned_to')

        if request.POST.get('status', None):
            invoices = invoices.filter(status=request.POST.get('status'))

        if request.POST.get('total_amount', None):
            invoices = invoices.filter(
                total_amount=request.POST.get('total_amount'))

        user_ids = list(invoices.values_list('created_by', flat=True))
        user_ids.append(request.user.id)
        context['created_by_users'] = users.filter(is_active=True, id__in=user_ids)
        context['invoices'] = invoices.distinct().order_by('id')
        today = datetime.today().date()
        context['today'] = today
        return render(request, 'invoices_list.html', context)


@login_required
@sales_access_required
def invoices_create(request):
    if request.method == 'GET':
        context = {}
        context["form"] = InvoiceForm(request_user=request.user)
        context["users"] = User.objects.all()
        # "prefix" use case in form, both from address and to address use the
        # same model and same model form, so the name attribute in the form will
        #  be same for the both forms and the address will be same for both
        # shipping and to address, so use prefix parameter to distinguish the
        # forms, don't remove this comment
        context["from_address_form"] = InvoiceAddressForm(
            prefix='from')
        context["to_address_form"] = InvoiceAddressForm(prefix='to')
        if request.user.role == 'ADMIN' or request.user.is_superuser:
            context['teams'] = Teams.objects.all()

        return render(request, 'invoice_create_1.html', context)

    if request.method == 'POST':
        form = InvoiceForm(request.POST, request_user=request.user)
        from_address_form = InvoiceAddressForm(
            request.POST, prefix='from')
        to_address_form = InvoiceAddressForm(request.POST, prefix='to')
        if form.is_valid() and from_address_form.is_valid() and to_address_form.is_valid():
            from_address_obj = from_address_form.save()
            to_address_obj = to_address_form.save()
            invoice_obj = form.save(commit=False)
            invoice_obj.created_by = request.user
            invoice_obj.from_address = from_address_obj
            invoice_obj.to_address = to_address_obj
            invoice_obj.save()
            form.save_m2m()

            if request.POST.getlist('teams', []):
                user_ids = Teams.objects.filter(id__in=request.POST.getlist('teams')).values_list('users', flat=True)
                assinged_to_users_ids = invoice_obj.assigned_to.all().values_list('id', flat=True)
                for user_id in user_ids:
                    if user_id not in assinged_to_users_ids:
                        invoice_obj.assigned_to.add(user_id)

            if request.POST.getlist('teams', []):
                invoice_obj.teams.add(*request.POST.getlist('teams'))

            create_invoice_history(invoice_obj.id, request.user.id, [])
            kwargs = {'domain': request.get_host(), 'protocol': request.scheme}
            assigned_to_list = list(invoice_obj.assigned_to.all().values_list('id', flat=True))
            send_email.delay(invoice_obj.id, assigned_to_list, **kwargs)
            if request.POST.get('from_account'):
                return JsonResponse({'error': False, 'success_url': reverse('accounts:view_account',
                    args=(request.POST.get('from_account'),))})
            return JsonResponse({'error': False, 'success_url': reverse('invoices:invoices_list')})
        else:
            return JsonResponse({'error': True, 'errors': form.errors,
                                 'from_address_errors': from_address_form.errors,
                                 'to_address_errors': to_address_form.errors})


@login_required
@sales_access_required
def invoice_details(request, invoice_id):
    invoice = get_object_or_404(Invoice.objects.select_related(
        'from_address', 'to_address'), pk=invoice_id)

    user_assigned_account = False
    user_assigned_accounts = set(request.user.account_assigned_users.values_list('id', flat=True))
    invoice_accounts = set(invoice.accounts.values_list('id', flat=True))
    if user_assigned_accounts.intersection(invoice_accounts):
        user_assigned_account = True

    if not ((request.user.role == 'ADMIN') or
        (request.user.is_superuser) or
        (invoice.created_by == request.user) or
        (request.user in invoice.assigned_to.all()) or
        user_assigned_account):
        raise PermissionDenied

    if request.method == 'GET':
        context = {}
        context['invoice'] = invoice
        context['attachments'] = invoice.invoice_attachment.all()
        context['comments'] = invoice.invoice_comments.all()
        context['invoice_history'] = invoice.invoice_history.all()
        if request.user.is_superuser or request.user.role == 'ADMIN':
            context['users_mention'] = list(
                User.objects.filter(is_active=True).values('username'))
        elif request.user != invoice.created_by:
            context['users_mention'] = [
                {'username': invoice.created_by.username}]
        else:
            context['users_mention'] = list(
                invoice.assigned_to.all().values('username'))
        return render(request, 'invoices_detail_1.html', context)


@login_required
@sales_access_required
def invoice_edit(request, invoice_id):
    invoice_obj = get_object_or_404(Invoice, pk=invoice_id)

    if not (request.user.role == 'ADMIN' or request.user.is_superuser or invoice_obj.created_by == request.user or request.user in invoice_obj.assigned_to.all()):
        raise PermissionDenied

    if request.method == 'GET':
        context = {}
        context['invoice_obj'] = invoice_obj
        context['teams'] = Teams.objects.all()
        context['users'] = User.objects.all()
        context['form'] = InvoiceForm(
            instance=invoice_obj, request_user=request.user)
        context['from_address_form'] = InvoiceAddressForm(prefix='from',
                                                          instance=invoice_obj.from_address)
        context['to_address_form'] = InvoiceAddressForm(prefix='to',
                                                        instance=invoice_obj.to_address)
        return render(request, 'invoice_create_1.html', context)

    if request.method == 'POST':
        form = InvoiceForm(request.POST, instance=invoice_obj,
                           request_user=request.user)
        from_address_form = InvoiceAddressForm(
            request.POST, instance=invoice_obj.from_address, prefix='from')
        to_address_form = InvoiceAddressForm(
            request.POST, instance=invoice_obj.to_address, prefix='to')
        previous_assigned_to_users = list(invoice_obj.assigned_to.all().values_list('id', flat=True))
        if form.is_valid() and from_address_form.is_valid() and to_address_form.is_valid():
            form_changed_data = form.changed_data
            form_changed_data.remove('from_address')
            form_changed_data.remove('to_address')
            form_changed_data = form_changed_data + ['from_' + field for field in from_address_form.changed_data]
            form_changed_data = form_changed_data + ['to_' + field for field in to_address_form.changed_data]
            # if form_changed_data:
            #     create_invoice_history(invoice_obj.id, request.user.id, form_changed_data)
            from_address_obj = from_address_form.save()
            to_address_obj = to_address_form.save()
            invoice_obj = form.save(commit=False)
            invoice_obj.created_by = request.user
            invoice_obj.from_address = from_address_obj
            invoice_obj.to_address = to_address_obj
            invoice_obj.save()
            form.save_m2m()
            if form_changed_data:
                create_invoice_history(invoice_obj.id, request.user.id, form_changed_data)

            if request.POST.getlist('teams', []):
                user_ids = Teams.objects.filter(id__in=request.POST.getlist('teams')).values_list('users', flat=True)
                assinged_to_users_ids = invoice_obj.assigned_to.all().values_list('id', flat=True)
                for user_id in user_ids:
                    if user_id not in assinged_to_users_ids:
                        invoice_obj.assigned_to.add(user_id)

            if request.POST.getlist('teams', []):
                invoice_obj.teams.clear()
                invoice_obj.teams.add(*request.POST.getlist('teams'))
            else:
                invoice_obj.teams.clear()

            kwargs = {'domain': request.get_host(), 'protocol': request.scheme}

            assigned_to_list = list(invoice_obj.assigned_to.all().values_list('id', flat=True))
            recipients = list(set(assigned_to_list) - set(previous_assigned_to_users))
            # send_email_to_assigned_user.delay(recipients, account_object.id, domain=current_site.domain,
            #     protocol=self.request.scheme)

            send_email.delay(invoice_obj.id, recipients, **kwargs)
            if request.POST.get('from_account'):
                return JsonResponse({'error': False, 'success_url': reverse('accounts:view_account',
                    args=(request.POST.get('from_account'),))})
            return JsonResponse({'error': False, 'success_url': reverse('invoices:invoices_list')})
        else:
            return JsonResponse({'error': True, 'errors': form.errors,
                                 'from_address_errors': from_address_form.errors,
                                 'to_address_errors': to_address_form.errors})


@login_required
@sales_access_required
def invoice_delete(request, invoice_id):
    invoice = get_object_or_404(Invoice, pk=invoice_id)
    if not (request.user.role == 'ADMIN' or request.user.is_superuser or invoice.created_by == request.user):
        raise PermissionDenied

    if request.method == 'GET':
        invoice.delete()
        if request.GET.get('view_account'):
            return redirect(reverse('accounts:view_account', args=(request.GET.get('view_account'),)))
        return redirect('invoices:invoices_list')


@login_required
@sales_access_required
def invoice_send_mail(request, invoice_id):
    invoice = get_object_or_404(Invoice, pk=invoice_id)
    if not (request.user.role == 'ADMIN' or request.user.is_superuser or invoice.created_by == request.user):
        raise PermissionDenied

    if request.method == 'GET':
        Invoice.objects.filter(id=invoice_id).update(
            is_email_sent=True, status='Sent')
        kwargs = {'domain': request.get_host(), 'protocol': request.scheme}
        send_invoice_email.delay(invoice_id, **kwargs)
        return redirect('invoices:invoices_list')


@login_required
@sales_access_required
def invoice_change_status_paid(request, invoice_id):
    invoice = get_object_or_404(Invoice, pk=invoice_id)
    if not (request.user.role == 'ADMIN' or request.user.is_superuser or invoice.created_by == request.user):
        raise PermissionDenied

    if request.method == 'GET':
        Invoice.objects.filter(id=invoice_id).update(status='Paid')
        kwargs = {'domain': request.get_host(), 'protocol': request.scheme}
        # send_invoice_email.delay(invoice_id, **kwargs)
        return redirect('invoices:invoices_list')

@login_required
@sales_access_required
def invoice_change_status_cancelled(request, invoice_id):
    invoice = get_object_or_404(Invoice, pk=invoice_id)
    if not (request.user.role == 'ADMIN' or request.user.is_superuser or invoice.created_by == request.user):
        raise PermissionDenied

    if request.method == 'GET':
        Invoice.objects.filter(id=invoice_id).update(status='Cancelled')
        kwargs = {'domain': request.get_host(), 'protocol': request.scheme}
        send_invoice_email_cancel.delay(invoice_id, **kwargs)
        return redirect('invoices:invoices_list')

@login_required
@sales_access_required
def invoice_download(request, invoice_id):
    invoice = get_object_or_404(Invoice.objects.select_related(
        'from_address', 'to_address'), pk=invoice_id)
    if not (request.user.role == 'ADMIN' or request.user.is_superuser or invoice.created_by == request.user or request.user in invoice.assigned_to.all()):
        raise PermissionDenied

    if request.method == 'GET':
        context = {}
        context['invoice'] = invoice
        html = render_to_string('invoice_download_pdf.html', context=context)
        pdfkit.from_string(html, 'out.pdf', options={'encoding': "UTF-8"})
        pdf = open("out.pdf", 'rb')
        response = HttpResponse(pdf.read(), content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename=Invoice.pdf'
        pdf.close()
        os.remove("out.pdf")
        return response


class AddCommentView(LoginRequiredMixin, CreateView):
    model = Comment
    form_class = InvoiceCommentForm
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        self.object = None
        self.invoice = get_object_or_404(
            Invoice, id=request.POST.get('invoice_id'))
        if (
            request.user == self.invoice.created_by or request.user.is_superuser or
            request.user.role == 'ADMIN'
        ):
            form = self.get_form()
            if form.is_valid():
                return self.form_valid(form)
            return self.form_invalid(form)

        data = {
            'error': "You don't have permission to comment for this account."}
        return JsonResponse(data)

    def form_valid(self, form):
        comment = form.save(commit=False)
        comment.commented_by = self.request.user
        comment.invoice = self.invoice
        comment.save()
        comment_id = comment.id
        current_site = get_current_site(self.request)
        send_email_user_mentions.delay(comment_id, 'invoices', domain=current_site.domain,
                                       protocol=self.request.scheme)
        return JsonResponse({
            "comment_id": comment.id, "comment": comment.comment,
            "commented_on": comment.commented_on,
            "commented_on_arrow": comment.commented_on_arrow,
            "commented_by": comment.commented_by.email
        })

    def form_invalid(self, form):
        return JsonResponse({"error": form['comment'].errors})


class UpdateCommentView(LoginRequiredMixin, View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        self.comment_obj = get_object_or_404(
            Comment, id=request.POST.get("commentid"))
        if request.user == self.comment_obj.commented_by:
            form = InvoiceCommentForm(request.POST, instance=self.comment_obj)
            if form.is_valid():
                return self.form_valid(form)

            return self.form_invalid(form)

        data = {'error': "You don't have permission to edit this comment."}
        return JsonResponse(data)

    def form_valid(self, form):
        self.comment_obj.comment = form.cleaned_data.get("comment")
        self.comment_obj.save(update_fields=["comment"])
        comment_id = self.comment_obj.id
        current_site = get_current_site(self.request)
        send_email_user_mentions.delay(comment_id, 'invoices', domain=current_site.domain,
                                       protocol=self.request.scheme)
        return JsonResponse({
            "comment_id": self.comment_obj.id,
            "comment": self.comment_obj.comment,
        })

    def form_invalid(self, form):
        return JsonResponse({"error": form['comment'].errors})


class DeleteCommentView(LoginRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        self.object = get_object_or_404(
            Comment, id=request.POST.get("comment_id"))
        if request.user == self.object.commented_by:
            self.object.delete()
            data = {"cid": request.POST.get("comment_id")}
            return JsonResponse(data)

        data = {'error': "You don't have permission to delete this comment."}
        return JsonResponse(data)


class AddAttachmentView(LoginRequiredMixin, CreateView):
    model = Attachments
    form_class = InvoiceAttachmentForm
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        self.object = None
        self.invoice = get_object_or_404(
            Invoice, id=request.POST.get('invoice_id'))
        if (
            request.user == self.invoice.created_by or
            request.user.is_superuser or
            request.user.role == 'ADMIN'
        ):
            form = self.get_form()
            if form.is_valid():
                return self.form_valid(form)

            return self.form_invalid(form)

        data = {
            'error': "You don't have permission to add attachment \
            for this account."}
        return JsonResponse(data)

    def form_valid(self, form):
        attachment = form.save(commit=False)
        attachment.created_by = self.request.user
        attachment.file_name = attachment.attachment.name
        attachment.invoice = self.invoice
        attachment.save()
        return JsonResponse({
            "attachment_id": attachment.id,
            "attachment": attachment.file_name,
            "attachment_url": attachment.attachment.url,
            "download_url": reverse('common:download_attachment',
                                    kwargs={'pk': attachment.id}),
            "attachment_display": attachment.get_file_type_display(),
            "created_on": attachment.created_on,
            "created_on_arrow": attachment.created_on_arrow,
            "created_by": attachment.created_by.email,
            "file_type": attachment.file_type()
        })

    def form_invalid(self, form):
        return JsonResponse({"error": form['attachment'].errors})


class DeleteAttachmentsView(LoginRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        self.object = get_object_or_404(
            Attachments, id=request.POST.get("attachment_id"))
        if (
            request.user == self.object.created_by or
            request.user.is_superuser or
            request.user.role == 'ADMIN'
        ):
            self.object.delete()
            data = {"acd": request.POST.get("attachment_id")}
            return JsonResponse(data)

        data = {
            'error': "You don't have permission to delete this attachment."}
        return JsonResponse(data)
