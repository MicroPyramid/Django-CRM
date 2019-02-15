import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.generic import CreateView
from django.views.generic import DetailView
from django.views.generic import TemplateView
from django.views.generic import UpdateView
from django.views.generic import View

from common.forms import BillingAddressForm
from common.models import Attachments
from common.models import Comment
from common.models import User
from common.utils import COUNTRIES
from contacts.forms import ContactAttachmentForm
from contacts.forms import ContactCommentForm
from contacts.forms import ContactForm
from contacts.models import Contact


class ContactsListView(LoginRequiredMixin, TemplateView):
    model = Contact
    context_object_name = 'contact_obj_list'
    template_name = 'contacts.html'

    def get_queryset(self):
        queryset = self.model.objects.all()
        request_post = self.request.POST
        if request_post:
            if request_post.get('first_name'):
                queryset = queryset.filter(
                    first_name__icontains=request_post.get('first_name'),
                )
            if request_post.get('city'):
                queryset = queryset.filter(
                    address__city__icontains=request_post.get('city'),
                )
            if request_post.get('phone'):
                queryset = queryset.filter(
                    phone__icontains=request_post.get('phone'),
                )
            if request_post.get('email'):
                queryset = queryset.filter(
                    email__icontains=request_post.get('email'),
                )
        return queryset

    def get_context_data(self, **kwargs):
        context = super(ContactsListView, self).get_context_data(**kwargs)
        context['contact_obj_list'] = self.get_queryset()
        context['per_page'] = self.request.POST.get('per_page')
        return context

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)


class CreateContactView(LoginRequiredMixin, CreateView):
    model = Contact
    form_class = ContactForm
    template_name = 'create_contact.html'

    def dispatch(self, request, *args, **kwargs):
        self.users = User.objects.filter(is_active=True).order_by('email')
        return super(CreateContactView, self).dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(CreateContactView, self).get_form_kwargs()
        kwargs.update({'assigned_to': self.users})
        return kwargs

    def post(self, request, *args, **kwargs):
        self.object = None
        form = self.get_form()
        address_form = BillingAddressForm(request.POST)
        if form.is_valid() and address_form.is_valid():
            address_obj = address_form.save()
            contact_obj = form.save(commit=False)
            contact_obj.address = address_obj
            contact_obj.created_by = self.request.user
            contact_obj.save()
            return self.form_valid(form)

        return self.form_invalid(form)

    def form_valid(self, form):
        contact_obj = form.save(commit=False)
        if self.request.POST.getlist('assigned_to', []):
            contact_obj.assigned_to.add(
                *self.request.POST.getlist('assigned_to')
            )
            assigned_to_list = self.request.POST.getlist('assigned_to')
            current_site = get_current_site(self.request)
            for assigned_to_user in assigned_to_list:
                user = get_object_or_404(User, pk=assigned_to_user)
                mail_subject = 'Assigned to contact.'
                message = render_to_string(
                    'assigned_to/contact_assigned.html', {
                        'user': user,
                        'domain': current_site.domain,
                        'protocol': self.request.scheme,
                        'contact': contact_obj,
                    },
                )
                email = EmailMessage(mail_subject, message, to=[user.email])
                email.content_subtype = 'html'
                email.send()

        if self.request.FILES.get('contact_attachment'):
            attachment = Attachments()
            attachment.created_by = self.request.user
            attachment.file_name = self.request.FILES.get(
                'contact_attachment',
            ).name
            attachment.contact = contact_obj
            attachment.attachment = self.request.FILES.get(
                'contact_attachment',
            )
            attachment.save()

        if self.request.is_ajax():
            return JsonResponse({'error': False})
        if self.request.POST.get('savenewform'):
            return redirect('contacts:add_contact')

        return redirect('contacts:list')

    def form_invalid(self, form):
        address_form = BillingAddressForm(self.request.POST)
        if self.request.is_ajax():
            return JsonResponse({
                'error': True, 'contact_errors': form.errors,
                'address_errors': address_form.errors,
            })
        return self.render_to_response(
            self.get_context_data(form=form, address_form=address_form),
        )

    def get_context_data(self, **kwargs):
        context = super(CreateContactView, self).get_context_data(**kwargs)
        context['contact_form'] = context['form']
        context['users'] = self.users
        context['countries'] = COUNTRIES
        context['assignedto_list'] = [
            int(i) for i in self.request.POST.getlist('assigned_to', []) if i
        ]
        if 'address_form' in kwargs:
            context['address_form'] = kwargs['address_form']
        else:
            if self.request.POST:
                context['address_form'] = BillingAddressForm(self.request.POST)
            else:
                context['address_form'] = BillingAddressForm()
        return context


class ContactDetailView(LoginRequiredMixin, DetailView):
    model = Contact
    context_object_name = 'contact_record'
    template_name = 'view_contact.html'

    def get_queryset(self):
        queryset = super(ContactDetailView, self).get_queryset()
        return queryset.select_related('address')

    def get_context_data(self, **kwargs):
        context = super(ContactDetailView, self).get_context_data(**kwargs)

        assigned_data = []
        for each in context['contact_record'].assigned_to.all():
            assigned_dict = {}
            assigned_dict['id'] = each.id
            assigned_dict['name'] = each.email
            assigned_data.append(assigned_dict)

        context.update({
            'comments': context['contact_record'].contact_comments.all(),
            'attachments': context['contact_record'].contact_attachment.all(),
            'assigned_data': json.dumps(assigned_data),
        })
        return context


class UpdateContactView(LoginRequiredMixin, UpdateView):
    model = Contact
    form_class = ContactForm
    template_name = 'create_contact.html'

    def dispatch(self, request, *args, **kwargs):
        self.users = User.objects.filter(is_active=True).order_by('email')
        return super(UpdateContactView, self).dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(UpdateContactView, self).get_form_kwargs()
        kwargs.update({'assigned_to': self.users})
        return kwargs

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        address_obj = self.object.address
        form = self.get_form()
        address_form = BillingAddressForm(request.POST, instance=address_obj)
        if form.is_valid() and address_form.is_valid():
            addres_obj = address_form.save()
            contact_obj = form.save(commit=False)
            contact_obj.address = addres_obj
            contact_obj.save()
            return self.form_valid(form)
        return self.form_invalid(form)

    def form_valid(self, form):
        assigned_to_ids = self.get_object().assigned_to.all().values_list('id', flat=True)

        contact_obj = form.save(commit=False)
        all_members_list = []
        if self.request.POST.getlist('assigned_to', []):
            current_site = get_current_site(self.request)
            assigned_form_users = form.cleaned_data.get(
                'assigned_to',
            ).values_list('id', flat=True)
            all_members_list = list(
                set(list(assigned_form_users)) - set(list(assigned_to_ids)),
            )
            if len(all_members_list):
                for assigned_to_user in all_members_list:
                    user = get_object_or_404(User, pk=assigned_to_user)
                    mail_subject = 'Assigned to contact.'
                    message = render_to_string(
                        'assigned_to/contact_assigned.html', {
                            'user': user,
                            'domain': current_site.domain,
                            'protocol': self.request.scheme,
                            'contact': contact_obj,
                        },
                    )
                    email = EmailMessage(
                        mail_subject, message, to=[user.email],
                    )
                    email.content_subtype = 'html'
                    email.send()

            contact_obj.assigned_to.clear()
            contact_obj.assigned_to.add(
                *self.request.POST.getlist('assigned_to')
            )
        else:
            contact_obj.assigned_to.clear()

        if self.request.FILES.get('contact_attachment'):
            attachment = Attachments()
            attachment.created_by = self.request.user
            attachment.file_name = self.request.FILES.get(
                'contact_attachment',
            ).name
            attachment.contact = contact_obj
            attachment.attachment = self.request.FILES.get(
                'contact_attachment',
            )
            attachment.save()
        if self.request.POST.get('from_account'):
            from_account = self.request.POST.get('from_account')
            return redirect('accounts:view_account', pk=from_account)
        if self.request.is_ajax():
            return JsonResponse({'error': False})
        return redirect('contacts:list')

    def form_invalid(self, form):
        address_obj = self.object.address
        address_form = BillingAddressForm(
            self.request.POST, instance=address_obj,
        )
        if self.request.is_ajax():
            return JsonResponse({
                'error': True, 'contact_errors': form.errors,
                'address_errors': address_form.errors,
            })
        return self.render_to_response(
            self.get_context_data(form=form, address_form=address_form),
        )

    def get_context_data(self, **kwargs):
        context = super(UpdateContactView, self).get_context_data(**kwargs)
        context['contact_obj'] = self.object
        context['address_obj'] = self.object.address
        context['contact_form'] = context['form']
        context['users'] = self.users
        context['countries'] = COUNTRIES
        context['assignedto_list'] = [
            int(i) for i in self.request.POST.getlist('assigned_to', []) if i
        ]
        if 'address_form' in kwargs:
            context['address_form'] = kwargs['address_form']
        else:
            if self.request.POST:
                context['address_form'] = BillingAddressForm(
                    self.request.POST, instance=context['address_obj'],
                )
            else:
                context['address_form'] = BillingAddressForm(
                    instance=context['address_obj'],
                )
        return context


class RemoveContactView(LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        contact_id = kwargs.get('pk')
        self.object = get_object_or_404(Contact, id=contact_id)
        if self.object.address_id:
            self.object.address.delete()
        self.object.delete()
        if self.request.is_ajax():
            return JsonResponse({'error': False})

        return redirect('contacts:list')


class AddCommentView(LoginRequiredMixin, CreateView):
    model = Comment
    form_class = ContactCommentForm
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        self.object = None
        self.contact = get_object_or_404(
            Contact, id=request.POST.get('contactid'),
        )
        if (
            request.user in self.contact.assigned_to.all() or
            request.user == self.contact.created_by or request.user.is_superuser or
            request.user.role == 'ADMIN'
        ):
            form = self.get_form()
            if form.is_valid():
                return self.form_valid(form)

            return self.form_invalid(form)

        data = {'error': "You don't have permission to comment."}
        return JsonResponse(data)

    def form_valid(self, form):
        comment = form.save(commit=False)
        comment.commented_by = self.request.user
        comment.contact = self.contact
        comment.save()
        return JsonResponse({
            'comment_id': comment.id, 'comment': comment.comment,
            'commented_on': comment.commented_on,
            'commented_by': comment.commented_by.email,
        })

    def form_invalid(self, form):
        return JsonResponse({'error': form['comment'].errors})


class UpdateCommentView(LoginRequiredMixin, View):
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        self.comment_obj = get_object_or_404(
            Comment, id=request.POST.get('commentid'),
        )
        if request.user == self.comment_obj.commented_by:
            form = ContactCommentForm(request.POST, instance=self.comment_obj)
            if form.is_valid():
                return self.form_valid(form)

            return self.form_invalid(form)

        data = {'error': "You don't have permission to edit this comment."}
        return JsonResponse(data)

    def form_valid(self, form):
        self.comment_obj.comment = form.cleaned_data.get('comment')
        self.comment_obj.save(update_fields=['comment'])
        return JsonResponse({
            'commentid': self.comment_obj.id,
            'comment': self.comment_obj.comment,
        })

    def form_invalid(self, form):
        return JsonResponse({'error': form['comment'].errors})


class DeleteCommentView(LoginRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        self.object = get_object_or_404(
            Comment, id=request.POST.get('comment_id'),
        )
        if request.user == self.object.commented_by:
            self.object.delete()
            data = {'cid': request.POST.get('comment_id')}
            return JsonResponse(data)

        data = {'error': "You don't have permission to delete this comment."}
        return JsonResponse(data)


class GetContactsView(LoginRequiredMixin, TemplateView):
    model = Contact
    context_object_name = 'contacts'
    template_name = 'contacts_list.html'

    def get_context_data(self, **kwargs):
        context = super(GetContactsView, self).get_context_data(**kwargs)
        context['contacts'] = self.get_queryset()
        return context


class AddAttachmentsView(LoginRequiredMixin, CreateView):
    model = Attachments
    form_class = ContactAttachmentForm
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        self.object = None
        self.contact = get_object_or_404(
            Contact, id=request.POST.get('contactid'),
        )
        if (
                request.user in self.contact.assigned_to.all() or
                request.user == self.contact.created_by or request.user.is_superuser or
                request.user.role == 'ADMIN'
        ):
            form = self.get_form()
            if form.is_valid():
                return self.form_valid(form)

            return self.form_invalid(form)

        data = {'error': "You don't have permission to add attachment."}
        return JsonResponse(data)

    def form_valid(self, form):
        attachment = form.save(commit=False)
        attachment.created_by = self.request.user
        attachment.file_name = attachment.attachment.name
        attachment.contact = self.contact
        attachment.save()
        return JsonResponse({
            'attachment_id': attachment.id,
            'attachment': attachment.file_name,
            'attachment_url': attachment.attachment.url,
            'created_on': attachment.created_on,
            'download_url': reverse('common:download_attachment', kwargs={'pk': attachment.id}),
            'attachment_display': attachment.get_file_type_display(),
            'created_by': attachment.created_by.email,
        })

    def form_invalid(self, form):
        return JsonResponse({'error': form['attachment'].errors})


class DeleteAttachmentsView(LoginRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        self.object = get_object_or_404(
            Attachments, id=request.POST.get('attachment_id'),
        )
        if (
            request.user == self.object.created_by or request.user.is_superuser or
            request.user.role == 'ADMIN'
        ):
            self.object.delete()
            data = {'aid': request.POST.get('attachment_id')}
            return JsonResponse(data)

        data = {'error': "You don't have permission to delete this attachment."}
        return JsonResponse(data)
