from django.http import HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from emails.models import Email
from emails.forms import EmailForm
from django.core.mail import EmailMessage
from datetime import datetime
from datetime import timedelta


def emails_list(request):
    filter_list = Email.objects.all()
    if request.GET.get('from_date', ''):
        from_date = request.GET.get('from_date', '')
        fd = datetime.strptime(from_date, "%Y-%m-%d").date()
        filter_list = filter_list.filter(send_time__gte=fd)
    if request.GET.get('to_date', ''):
        to_date = request.GET.get('to_date', '')
        td = datetime.strptime(to_date, "%Y-%m-%d")
        td = td + timedelta(seconds=(24 * 60 * 60 - 1))
        filter_list = filter_list.filter(send_time__lte=td)
    if request.GET.get('name', ''):
        name = request.GET.get('name', '')
        filter_list = filter_list.filter(to_email__startswith=name)
    return render(request, 'mail_all.html', {
        'filter_list': filter_list})


def email(request):
    if request.method == "POST":
        form = EmailForm(request.POST, request.FILES)
        if form.is_valid():
            subject = request.POST.get('subject', '')
            message = request.POST.get('message', '')
            from_email = request.POST.get('from_email', '')
            to_email = request.POST.get('to_email', '')
            file = request.FILES.get('files', None)
            status = request.POST.get('email_draft', '')
            email = EmailMessage(subject, message, from_email, [to_email])
            email.content_subtype = "html"
            f = form.save()
            if file is not None:
                email.attach(file.name, file.read(), file.content_type)
                f.file = file
            if status:
                f.status = "draft"
            else:
                email.send(fail_silently=False)
            f.save()
            return HttpResponseRedirect(reverse('emails:list'))
        else:
            return render(request, 'create_mail.html', {'form': form})
    else:
        form = EmailForm()
        return render(request, 'create_mail.html', {'form': form})


def email_sent(request):
    filter_list = Email.objects.filter(status="sent")
    if request.GET.get('from_date', ''):
        from_date = request.GET.get('from_date', '')
        fd = datetime.strptime(from_date, "%Y-%m-%d").date()
        filter_list = filter_list.filter(send_time__gte=fd)
    if request.GET.get('to_date', ''):
        to_date = request.GET.get('to_date', '')
        td = datetime.strptime(to_date, "%Y-%m-%d")
        td = td + timedelta(seconds=(24 * 60 * 60 - 1))
        filter_list = filter_list.filter(send_time__lte=td)
    if request.GET.get('name', ''):
        name = request.GET.get('name', '')
        filter_list = filter_list.filter(to_email__startswith=name)
    return render(request, 'mail_sent.html',
                  {'filter_list': filter_list})


def email_trash(request):
    filter_list = Email.objects.filter(status="trash")
    if request.GET.get('from_date', ''):
        from_date = request.GET.get('from_date', '')
        fd = datetime.strptime(from_date, "%Y-%m-%d").date()
        filter_list = filter_list.filter(send_time__gte=fd)
    if request.GET.get('to_date', ''):
        to_date = request.GET.get('to_date', '')
        td = datetime.strptime(to_date, "%Y-%m-%d")
        td = td + timedelta(seconds=(24 * 60 * 60 - 1))
        filter_list = filter_list.filter(send_time__lte=td)
    if request.GET.get('name', ''):
        name = request.GET.get('name', '')
        filter_list = filter_list.filter(to_email__startswith=name)
    return render(request, 'mail_trash.html',
                  {'filter_list': filter_list})


def email_trash_delete(request, pk):
    get_object_or_404(Email, id=pk).delete()
    return HttpResponseRedirect(reverse('emails:email_trash'))


def email_draft(request):
    filter_list = Email.objects.filter(status="draft")
    if request.GET.get('from_date', ''):
        from_date = request.GET.get('from_date', '')
        fd = datetime.strptime(from_date, "%Y-%m-%d").date()
        filter_list = filter_list.filter(send_time__gte=fd)
    if request.GET.get('to_date', ''):
        to_date = request.GET.get('to_date', '')
        td = datetime.strptime(to_date, "%Y-%m-%d")
        td = td + timedelta(seconds=(24 * 60 * 60 - 1))
        filter_list = filter_list.filter(send_time__lte=td)
    if request.GET.get('name', ''):
        name = request.GET.get('name', '')
        filter_list = filter_list.filter(to_email__startswith=name)
    return render(request, 'mail_drafts.html',
                  {'filter_list': filter_list})


def email_draft_delete(request, pk):
    get_object_or_404(Email, id=pk).delete()
    return HttpResponseRedirect(reverse('emails:email_draft'))


def email_delete(request, pk):
    get_object_or_404(Email, id=pk).delete()
    return HttpResponseRedirect(reverse('emails:email_sent'))


def email_move_to_trash(request, pk):
    trashitem = get_object_or_404(Email, id=pk)
    trashitem.status = "trash"
    trashitem.save()
    return HttpResponseRedirect(request.META['HTTP_REFERER'])


def email_imp(request, pk):
    impitem = get_object_or_404(Email, id=pk)
    impitem.important = True
    impitem.save()
    return HttpResponseRedirect(request.META['HTTP_REFERER'])


def email_imp_list(request):
    filter_list = Email.objects.filter(important="True")
    if request.GET.get('from_date', ''):
        from_date = request.GET.get('from_date', '')
        fd = datetime.strptime(from_date, "%Y-%m-%d").date()
        filter_list = filter_list.filter(send_time__gte=fd)

    if request.GET.get('to_date', ''):
        to_date = request.GET.get('to_date', '')
        td = datetime.strptime(to_date, "%Y-%m-%d")
        td = td + timedelta(seconds=(24 * 60 * 60 - 1))
        filter_list = filter_list.filter(send_time__lte=td)
    if request.GET.get('name', ''):
        name = request.GET.get('name', '')
        filter_list = filter_list.filter(to_email__startswith=name)
    return render(request, 'mail_important.html', {'filter_list': filter_list})


def email_sent_edit(request, pk):
    em = get_object_or_404(Email, pk=pk)
    if request.method == 'POST':
        form = EmailForm(request.POST, instance=em)
        if form.is_valid():
            subject = request.POST.get('subject', '')
            message = request.POST.get('message', '')
            from_email = request.POST.get('from_email', '')
            to_email = request.POST.get('to_email', '')
            file = request.FILES.get('files', None)
            status = request.POST.get('email_draft', '')
            email = EmailMessage(subject, message, from_email, [to_email])
            email.content_subtype = "html"
            f = form.save()
            if file is not None:
                email.attach(file.name, file.read(), file.content_type)
                f.file = file
            if status:
                f.status = "draft"
            else:
                email.send(fail_silently=False)
                f.status = "sent"
            f.save()
            return HttpResponseRedirect(reverse('emails:list'))
        else:
            return render(request, 'create_mail.html',
                          {'form': form, 'em': em})
    else:
        form = EmailForm()
    return render(request, 'create_mail.html',
                  {'form': form, 'em': em})


def email_unimp(request, pk):
    unimpitem = get_object_or_404(Email, id=pk)
    unimpitem.important = False
    unimpitem.save()
    return HttpResponseRedirect(request.META['HTTP_REFERER'])


def email_view(request, pk):
    email_view = get_object_or_404(Email, pk=pk)
    x = EmailForm(instance=email_view)
    return render(request, 'create_mail.html', {'x': x})
