from django.shortcuts import render, get_object_or_404, redirect
from cases.forms import caseForm
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from cases.models import Case
from common.models import Comment, Comment_Files
from accounts.models import Account
from contacts.models import Contact
from django.contrib.auth.models import User
from cases.forms import CommentForm
from django.db.models import Q
import json
from django.conf import settings


@login_required
def cases(request):
    accounts = Account.objects.all()
    page = request.POST.get('per_page')
    name = request.POST.get('name')
    status = request.POST.get('status')
    priority = request.POST.get('priority')
    account = request.POST.get('account')
    if not account:
        account = 0
    cases = Case.objects.filter(Q(userid=request.user) | Q(assigned_user=request.user)).order_by("-id")
    if name:
        cases = Case.objects.filter(name__contains=name)
    if account:
        cases = cases.filter(account=account)
    if status:
        cases = cases.filter(status=status)
    if priority:
        cases = cases.filter(priority=priority)
    return render(request, "cases/cases.html", {"cases": cases, "accounts": accounts, "acc": int(account), "per_page": page})


@login_required
def edit_case(request, case_id):
    edata = get_object_or_404(Case, id=case_id)
    selcon = edata.contacts.all()
    con = Contact.objects.filter(account=edata.account)
    edit2 = "edit from home"
    accounts = Account.objects.all()
    if request.method == 'POST':
        eid = get_object_or_404(Case, id=case_id)
        form = caseForm(request.POST, instance=eid)
        if form.is_valid():
            form.save()
            if request.is_ajax():
                return HttpResponse(json.dumps({'error': False}))
            return redirect("/cases/list")
        else:
            if request.is_ajax():
                return JsonResponse({'error': True, 'errors_case': form.errors})
            return render(request, "cases/show_case.html", {"case": edata, "con": con, "accounts": accounts, "selcon": selcon, "edit2": edit2})
    assigned_user = "None"
    if edata.assigned_user:
        assigned_user = edata.get_assigned_user
    users = User.objects.filter(is_active=True)
    return render(request, "cases/show_case.html", {"case": edata, "con": con, "accounts": accounts, "selcon": selcon, "edit2": edit2,
                                                    "users": users, "a_user": assigned_user})


def selectContacts(request):
        ac = request.GET["acc"]
        company = Account.objects.filter(id=ac)
        contacts = Contact.objects.filter(account=company)
        data = {}
        for i in contacts:
            new = {i.pk: i.name}
            data.update(new)
        return JsonResponse(data)


@login_required
def editdetails(request):
    eid = request.POST["tid"]
    edata = get_object_or_404(Case, id=eid)
    account = 0
    if edata.account:
        account = edata.account.id
    con = Contact.objects.filter(account=account)
    selcon = edata.contacts.all()
    contactsHtml = render(request, "cases/sel_contacts.html", {"selcon": selcon, "con": con})
    data = {"name": edata.name, "status": edata.status, "priority": edata.priority,
            "case-type": edata.case_type, "description": edata.description, "account": account, "eid": eid, }
    data['contacts'] = str(contactsHtml.content)
    return JsonResponse(data)


@login_required
def case_add(request):
    accounts = Account.objects.all()
    users = User.objects.filter(is_active=True)
    if request.method == 'POST':
        form = caseForm(request.POST)
        if form.is_valid():
            case = form.save()
            case_new = get_object_or_404(Case, id=case.id)
            case_new.userid = request.user
            case_new.save()
            if request.is_ajax():
                return HttpResponse(json.dumps({'error': False}))
            accounts = Account.objects.all()
            return redirect("/cases/list")
        else:
            if request.is_ajax():
                return HttpResponse(json.dumps({'error': True, 'errors': form.errors}))
            return render(request, "cases/create_cases.html", {"form": form, "accounts": accounts})
    return render(request, "cases/create_cases.html", {"accounts": accounts, "users": users})


@login_required
def remove_case(request, case_id):
    if request.method == 'POST':
        cid = request.POST.get('case_id')
        get_object_or_404(Case, id=cid).delete()
        count = Case.objects.filter(Q(userid=request.user) | Q(assigned_user=request.user)).count()
        data = {"case_id": cid, "count": count}
        return JsonResponse(data)
    else:
        Case.objects.filter(id=case_id).delete()
        return redirect("/cases/list")


@login_required
def close_case(request):
    cid = request.POST['case_id']
    case = get_object_or_404(Case, id=cid)
    case.status = "Closed"
    case.save()
    data = {'status': "Closed", "cid": cid}
    return JsonResponse(data)


@login_required
def show_case(request, case_id):
    c = get_object_or_404(Case, id=case_id)
    comments = Comments.objects.filter(caseid=case_id).order_by('-id')
    users = User.objects.all()
    con = c.contacts.all()
    a_user = "None"
    if c.assigned_user:
        a_user = c.get_assigned_user
    if not con:
        con = "None"
    accounts = Account.objects.all()
    return render(request, "cases/show_case.html", {"case": c, "accounts": accounts, "contacts": con, "a_user": a_user,
                                                    "users": users, "comments": comments})


@login_required
def get_cases(request):
    if request.method == 'GET':
        cases = Case.objects.all()
        return render(request, 'cases/cases_list.html', {'cases': cases})
    else:
        return HttpResponse('Oops!! Something Went Wrong..  in load_calls')


@login_required
def comment_add(request):
    if request.method == 'POST':
        case = get_object_or_404(Case, id=request.POST.get('caseid'))
        assigned = False
        if case.assigned_user:
            assigned = (int(case.assigned_user) == request.user)
        if request.user == case.userid or assigned:
            form = CommentForm(request.POST)
            if form.is_valid():
                comment = request.POST.get('comment')
                comment_user = request.user
                caseid = request.POST.get('caseid')
                com_file = request.FILES.getlist('comment_file')
                c = Comments.objects.create(comment=comment, caseid=Case.objects.get(id=caseid), comment_user=comment_user)
                for com_file in com_file:
                    Comment_Files.objects.create(comment_id=c, comment_file=com_file)
                data = {"com_id": c.id, "comment": c.comment, "comment_time": c.comment_time,
                        "com_user": c.comment_user.username, "file": {}}
                for cc in Comment_Files.objects.filter(comment_id=c):
                    comfile = cc.comment_file.path.split('/')[-1]
                    fid = cc.id
                    data['file'].update({fid: comfile})
                return JsonResponse(data)
            else:
                return JsonResponse({"error": form['comment'].errors})
        else:
            data = {'error': "You Dont Have permissions to Comment"}
            return JsonResponse(data)


def comment_edit(request):
    if request.method == "POST":
        comment = request.POST.get('comment')
        comment_id = request.POST.get("commentid")
        files = request.FILES.getlist('edit_file')
        com = get_object_or_404(Comments, id=comment_id)
        form = CommentForm(request.POST)
        if request.user == com.comment_user:
            if form.is_valid():
                com.comment = comment
                com.save()
                data = {"comment": com.comment, "commentid": comment_id, "file": {}}
                for file in files:
                    attach = Comment_Files.objects.create(comment_id=com, comment_file=file)
                    data['file'].update({attach.id: attach.comment_file.path.split('/')[-1]})
                return JsonResponse(data)
            else:
                return JsonResponse({"error": form['comment'].errors})
        else:
            return JsonResponse({"error": "You dont have authentication to edit"})
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
        return HttpResponse("Something Went Wrong")


@login_required
def remove_commentfile(request):
    if request.method == 'POST':
        file_id = request.POST.get('file_id')
        file = get_object_or_404(Comment_Files, id=file_id)
        com = get_object_or_404(Comments, id=file.comment_id.id)
        if com.comment_user == request.user:
            file.delete()
            data = {"file_id": file_id}
            return JsonResponse(data)
        else:
            return JsonResponse({"error": "You Dont Have permissions"})
    else:
        return HttpResponse("Something Went Wrong")


def down_file(request, com_id):
    file = get_object_or_404(Comment_Files, pk=com_id)
    file_name = settings.BASE_DIR + '/media/' + str(file.comment_file)
    file_open = open(file_name, 'rb')
    mimetype = "application/octet-stream"
    response = HttpResponse(file_open.read(), content_type=mimetype)
    response["Content-Disposition"] = "attachment; filename=%s" % str(file.comment_file).split('/')[-1]
    return response
