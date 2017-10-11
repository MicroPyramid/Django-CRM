from django.shortcuts import render, get_object_or_404, redirect, HttpResponseRedirect, reverse
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Q

from cases.models import Case
from cases.forms import CaseForm, CaseCommentForm
from common.models import Team, User, Comment
from accounts.models import Account
from contacts.models import Contact
from common.utils import PRIORITY_CHOICE, STATUS_CHOICE, CASE_TYPE

# CRUD Operations Start


@login_required
def cases_list(request):
    cases = Case.objects.all().select_related("account")
    accounts = Account.objects.all()
    page = request.POST.get('per_page')
    name = request.POST.get('name')
    status = request.POST.get('status')
    priority = request.POST.get('priority')
    account = request.POST.get('account')
    if not account:
        account = 0
    if name:
        cases = Case.objects.filter(name__contains=name)
    if account:
        cases = cases.filter(account=account)
    if status:
        cases = cases.filter(status=status)
    if priority:
        cases = cases.filter(priority=priority)
    return render(request, "cases/cases.html", {
        'cases': cases,
        'accounts': accounts,
        'acc': int(account),
        'per_page': page,
        'case_priority': PRIORITY_CHOICE,
        'case_status': STATUS_CHOICE
    })


@login_required
def add_case(request):
    accounts = Account.objects.all()
    contacts = Contact.objects.all()
    users = User.objects.filter(is_active=True).order_by('email')
    form = CaseForm(assigned_to=users, account=accounts, contacts=contacts)
    teams = Team.objects.all()
    teams_list = request.POST.getlist("teams")
    assignedto_list = request.POST.getlist("assigned_to")
    contacts_list = request.POST.getlist("contacts")
    if request.method == 'POST':
        form = CaseForm(request.POST, assigned_to=users, account=accounts, contacts=contacts)
        if form.is_valid():
            case = form.save(commit=False)
            case.created_by = request.user
            case.save()
            case.assigned_to.add(*assignedto_list)
            case.teams.add(*teams_list)
            case.contacts.add(*contacts_list)
            if request.is_ajax():
                return JsonResponse({'error': False})
            if request.POST.get("savenewform"):
                return redirect("cases:case_add")
            else:
                return HttpResponseRedirect(reverse('cases:list'))
        else:
            if request.is_ajax():
                return JsonResponse({'error': True, 'case_errors': form.errors})
            return render(request, "cases/create_cases.html", {
                'case_form': form,
                'accounts': accounts,
                'users': users,
                'teams': teams,
                'case_types': CASE_TYPE,
                'case_priority': PRIORITY_CHOICE,
                'case_status': STATUS_CHOICE,
                'teams_list': teams_list,
                'assignedto_list': assignedto_list,
                'contacts_list': contacts_list
            })
    return render(request, "cases/create_cases.html", {
        'case_form': form,
        'accounts': accounts,
        'users': users,
        'teams': teams,
        'teams_list': teams_list,
        'assignedto_list': assignedto_list,
        'contacts_list': contacts_list,
        'case_types': CASE_TYPE,
        'case_priority': PRIORITY_CHOICE,
        'case_status': STATUS_CHOICE
    })


@login_required
def view_case(request, case_id):
    case_record = get_object_or_404(
        Case.objects.prefetch_related("contacts", "account"), id=case_id)
    comments = case_record.cases.all()
    return render(request, "cases/view_case.html", {
        'case_record': case_record,
        'comments': comments
    })


@login_required
def edit_case(request, case_id):
    case_object = get_object_or_404(Case, id=case_id)
    users = User.objects.filter(is_active=True).order_by('email')
    accounts = Account.objects.all()
    contacts = Contact.objects.all()
    form = CaseForm(instance=case_object, assigned_to=users, account=accounts, contacts=contacts)
    teams = Team.objects.all()
    teams_list = request.POST.getlist("teams")
    assignedto_list = request.POST.getlist("assigned_to")
    contacts_list = request.POST.getlist("contacts")
    if request.method == 'POST':
        form = CaseForm(
            request.POST, instance=case_object, assigned_to=users, account=accounts,
            contacts=contacts
        )
        if form.is_valid():
            case_obj = form.save(commit=False)
            if request.POST.get("account"):
                case_obj.account = Account.objects.get(id=request.POST.get("account"))
            case_obj.created_by = request.user
            case_obj.save()
            case_obj.assigned_to.clear()
            case_obj.assigned_to.add(*assignedto_list)
            case_obj.teams.clear()
            case_obj.teams.add(*teams_list)
            case_obj.contacts.clear()
            case_obj.contacts.add(*contacts_list)
            if request.is_ajax():
                return JsonResponse({'error': False})
            return HttpResponseRedirect(reverse('cases:list'))
        else:
            if request.is_ajax():
                return JsonResponse({'error': True, 'case_errors': form.errors})
            return render(request, "cases/create_cases.html", {
                'case_obj': case_object,
                'case_form': form,
                'accounts': accounts,
                'users': users,
                'teams': teams,
                'case_types': CASE_TYPE,
                'case_priority': PRIORITY_CHOICE,
                'case_status': STATUS_CHOICE,
                'teams_list': teams_list,
                'assignedto_list': assignedto_list,
                'contacts_list': contacts_list
            })

    return render(request, "cases/create_cases.html", {
        'case_form': form,
        'case_obj': case_object,
        'accounts': accounts,
        'users': users,
        'teams': teams,
        'case_types': CASE_TYPE,
        'case_priority': PRIORITY_CHOICE,
        'case_status': STATUS_CHOICE,
        'assignedto_list': assignedto_list,
        'teams_list': teams_list,
        'contacts_list': contacts_list
    })


@login_required
def remove_case(request, case_id):
    if request.method == 'POST':
        cid = request.POST['case_id']
        get_object_or_404(Case, id=cid).delete()
        count = Case.objects.filter(Q(assigned_to=request.user) | Q(created_by=request.user)).count()
        data = {"case_id": cid, "count": count}
        return JsonResponse(data)
    else:
        Case.objects.filter(id=case_id).delete()
        return HttpResponseRedirect(reverse('cases:list'))


@login_required
def close_case(request):
    cid = request.POST['case_id']
    case = get_object_or_404(Case, id=cid)
    case.status = "Closed"
    case.save()
    data = {'status': "Closed", "cid": cid}
    return JsonResponse(data)


def selectContacts(request):
    contact_account = request.GET.get("account")
    if contact_account:
        account = get_object_or_404(Account, id=contact_account)
        contacts = Contact.objects.filter(account=account)
    else:
        contacts = Contact.objects.all()
    data = {}
    for i in contacts:
        new = {i.pk: i.first_name}
        data.update(new)
    return JsonResponse(data)


# CRUD Operations End
# Comments Section Start


@login_required
def add_comment(request):
    if request.method == 'POST':
        case = get_object_or_404(Case, id=request.POST.get('caseid'))
        if request.user in case.assigned_to.all() or request.user == case.created_by:
            form = CaseCommentForm(request.POST)
            if form.is_valid():
                case_comment = form.save(commit=False)
                case_comment.comment = request.POST.get('comment')
                case_comment.commented_by = request.user
                case_comment.case = case
                case_comment.save()
                data = {"comment_id": case_comment.id, "comment": case_comment.comment,
                        "commented_on": case_comment.commented_on,
                        "commented_by": case_comment.commented_by.email}
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
        comment_obj = get_object_or_404(Comment, id=comment_id)
        form = CaseCommentForm(request.POST)
        if request.user == comment_obj.commented_by:
            if form.is_valid():
                comment_obj.comment = comment
                comment_obj.save()
                data = {"comment": comment_obj.comment, "commentid": comment_id}
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


# Comments Section End
# Other Views


@login_required
def get_cases(request):
    if request.method == 'GET':
        cases = Case.objects.all()
        return render(request, 'cases/cases_list.html', {'cases': cases})
    else:
        return HttpResponse('Oops!! Something Went Wrong..  in load_calls')
