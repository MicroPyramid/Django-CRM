# from django.shortcuts import render
# from planner.forms import ReminderForm, MeetingEventForm, CallEventForm, TaskEventForm
# from django.http import HttpResponse, JsonResponse
# from django.contrib.auth.decorators import login_required
# from django.forms import modelformset_factory
# from planner.models import Reminder, Event
# from planner import models
# from django.contrib.auth.models import User
# from accounts.models import Account
# from cases.models import Case
# from opportunity.models import Opportunity
# from contacts.models import Contact
# from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
# from django.db.models import Q
# from leads.models import Lead
# from django.contrib.contenttypes.models import ContentType
# import datetime


# @login_required
# def load_meetings(request):
#     if request.method == 'GET':
#         RemindersFormSet = modelformset_factory(Reminder, form=ReminderForm, can_delete=True)
#         data = {
#             'form-TOTAL_FORMS': '1',
#             'form-INITIAL_FORMS': '0',
#             'form-MAX_NUM_FORMS': '10',
#         }
#         reminder_form_set = RemindersFormSet(data)
#         meetings = Event.objects.filter(Q(created_user=request.user) | Q(updated_user=request.user),
#                                         event_type='Meeting').order_by('-id')
#         paginator = Paginator(meetings, 5)
#         try:
#             meetings = paginator.page(request.GET.get('page'))
#             return render(request, 'meetings_list.html',
#                           {'meetings': meetings})
#         except PageNotAnInteger:
#             meetings = paginator.page(1)
#         except EmptyPage:
#             meetings = paginator.page(paginator.num_pages)
#         return render(request, 'meetings.html',
#                       {'meetings': meetings, 'reminder_form_set': reminder_form_set})
#     else:
#         return HttpResponse('Invalid Method or Not Authanticated in load_meetings')


# @login_required
# def load_tasks(request):
#     if request.method == 'GET':
#         tasks = Event.objects.filter(Q(created_user=request.user) | Q(updated_user=request.user),
#                                      event_type='Task').order_by('-id')
#         paginator = Paginator(tasks, 3)
#         try:
#             tasks = paginator.page(request.GET.get('page'))
#             return render(request, 'tasks_list.html',
#                           {'tasks': tasks})
#         except PageNotAnInteger:
#             tasks = paginator.page(1)
#         except EmptyPage:
#             tasks = paginator.page(paginator.num_pages)
#         return render(request, 'tasks.html', {'tasks': tasks})
#     else:
#         return HttpResponse('Invalid Method or Not Authanticated in load_tasks')


# @login_required
# def load_calls(request):
#     if request.method == 'GET':
#         RemindersFormSet = modelformset_factory(Reminder, form=ReminderForm, can_delete=True)
#         data = {
#             'form-TOTAL_FORMS': '1',
#             'form-INITIAL_FORMS': '0',
#             'form-MAX_NUM_FORMS': '10',
#         }
#         reminder_form_set = RemindersFormSet(data)
#         calls = Event.objects.filter(Q(created_user=request.user) | Q(updated_user=request.user),
#                                      event_type='Call').order_by('-id')
#         paginator = Paginator(calls, 3)
#         try:
#             calls = paginator.page(request.GET.get('page'))
#             return render(request, 'calls_list.html',
#                           {'calls': calls})
#         except PageNotAnInteger:
#             calls = paginator.page(1)
#         except EmptyPage:
#             calls = paginator.page(paginator.num_pages)
#         return render(request, 'calls.html', {'calls': calls, 'reminder_form_set': reminder_form_set})
#     else:
#         return HttpResponse('Invalid Method or Not Authanticated in load_calls')


# @login_required
# def create_meeting(request):
#     if request.method == 'POST':
#         eventForm = MeetingEventForm(request.POST)
#         ReminderFormSet = modelformset_factory(Reminder, ReminderForm, can_delete=True)
#         reminder_form_set = ReminderFormSet(request.POST)
#         if eventForm.is_valid() and reminder_form_set.is_valid():
#             parent_name = None
#             if eventForm.cleaned_data.get('parent_type') and eventForm.cleaned_data.get('parent_id'):
#                 meeting_object = add_parent(eventForm.cleaned_data.get('parent_type'),
#                                             eventForm.cleaned_data.get('parent_id'), eventForm, request.user)
#                 meeting = meeting_object[0]
#                 parent_name = meeting_object[1]
#             else:
#                 meeting = eventForm.save(commit=False)
#                 meeting.created_user = request.user
#                 meeting.save()
#             eventForm.save_m2m()
#             reminders = reminder_form_set.save()
#             meeting.reminders.add(*reminders)
#             return JsonResponse({'success': 'Meeting Created',
#                                  'id': meeting.id,
#                                  'name': meeting.name,
#                                  'parent': parent_name,
#                                  'status': meeting.status,
#                                  'startdate': meeting.start_date
#                                  })
#         else:
#             return JsonResponse(dict(eventForm.errors))
#     else:
#         return JsonResponse({'METHOD': 'INVALID'})


# @login_required
# def create_task(request):
#     if request.method == 'POST':
#         taskForm = TaskEventForm(request.POST)
#         if taskForm.is_valid():
#             if taskForm.cleaned_data.get('parent_type') and taskForm.cleaned_data.get('parent_id'):
#                 task_object = add_parent(taskForm.cleaned_data.get('parent_type'),
#                                          taskForm.cleaned_data.get('parent_id'), taskForm, request.user)
#                 task = task_object[0]
#             else:
#                 task = taskForm.save(commit=False)
#                 task.created_user = request.user
#                 task.save()
#             return JsonResponse({'success': 'Task Created',
#                                  'id': task.id,
#                                  'name': task.name,
#                                  'status': task.status,
#                                  'priority': task.priority,
#                                  'startdate': task.start_date})
#         else:
#             return JsonResponse(dict(taskForm.errors))
#     else:
#         return JsonResponse({'METHOD': 'INVALID'})


# @login_required
# def create_call(request):
#     if request.method == 'POST':
#         callsForm = CallEventForm(request.POST)
#         ReminderFormSet = modelformset_factory(Reminder, ReminderForm, can_delete=True)
#         reminder_form_set = ReminderFormSet(request.POST)
#         if callsForm.is_valid() and reminder_form_set.is_valid():
#             parent_name = None
#             if callsForm.cleaned_data.get('parent_type') and callsForm.cleaned_data.get('parent_id'):
#                 call_object = add_parent(callsForm.cleaned_data.get('parent_type'),
#                                          callsForm.cleaned_data.get('parent_id'), callsForm, request.user)
#                 call = call_object[0]
#                 parent_name = call_object[1]
#             else:
#                 call = callsForm.save(commit=False)
#                 call.created_user = request.user
#                 call.save()
#             callsForm.save_m2m()
#             reminders = reminder_form_set.save()
#             call.reminders.add(*reminders)
#             return JsonResponse({'success': 'Call Created',
#                                  'id': call.id,
#                                  'name': call.name,
#                                  'parent': parent_name,
#                                  'status': call.status,
#                                  'start_date': call.start_date})
#         else:
#             return JsonResponse(dict(callsForm.errors))
#     else:
#         return JsonResponse({'METHOD': 'INVALID'})


# @login_required
# def delete_meeting(request):
#     if request.method == 'POST':
#         try:
#             Event.objects.get(id=int(request.POST.get('meetingID')), created_user=request.user).delete()
#             return JsonResponse({'success': 'Meeting Deleted'})
#         except models.Event.DoesNotExist:
#             return JsonResponse({'Event': 'DoesNotExist'})
#     else:
#         return JsonResponse({'METHOD': 'INVALID'})


# @login_required
# def delete_task(request):
#     if request.method == 'POST':
#         try:
#             Event.objects.get(id=int(request.POST.get('taskID')), created_user=request.user).delete()
#             return JsonResponse({'success': 'Task Deleted'})
#         except models.Event.DoesNotExist:
#             return JsonResponse({'Event': 'DoesNotExist'})
#     else:
#         return JsonResponse({'METHOD': 'INVALID'})


# @login_required
# def delete_call(request):
#     if request.method == 'POST':
#         try:
#             Event.objects.get(id=int(request.POST.get('callID')), created_user=request.user).delete()
#             return JsonResponse({'success': 'Call Deleted'})
#         except models.Event.DoesNotExist:
#             return JsonResponse({'Event': 'DoesNotExist'})
#     else:
#         return JsonResponse({'METHOD': 'INVALID'})


# @login_required
# def get_meeting(request):
#     if request.method == 'POST':
#         try:
#             meeting = Event.objects.get(id=int(request.POST.get('meetingID')), created_user=request.user)
#             ReminderFormSet = modelformset_factory(Reminder, ReminderForm, can_delete=True, extra=0)
#             reminder_form_set = ReminderFormSet(queryset=meeting.reminders.all())
#             remindersHtML = render(request, 'reminder.html', {'reminder_form_set': reminder_form_set})
#             data = {}
#             if meeting.parent:
#                 data['parent_type'] = meeting.parent.__class__.__name__
#                 data['parent_name'] = meeting.parent.__str__()
#                 data['parent_id'] = meeting.object_id
#             else:
#                 data['parent_name'] = ''
#                 data['parent_id'] = ''
#             if meeting.assigned_users: data['assigned_users'] = {
#                 meeting.assigned_users.id: meeting.assigned_users.username}
#             if meeting.attendees_user: data['attendees_user'] = {key.id: key.username for key in
#                                                                  meeting.attendees_user.all()}
#             if meeting.attendees_contacts: data['attendees_contacts'] = {key.id: key.name for key in
#                                                                          meeting.attendees_contacts.all()}
#             if meeting.attendees_leads: data['attendees_leads'] = {key.id: key.first_name for key in
#                                                                    meeting.attendees_leads.all()}
#             del meeting._state
#             del meeting._parent_cache
#             del meeting._assigned_users_cache
#             meeting.__dict__['close_date'] = meeting.__dict__['close_date'].strftime('%m/%d/%Y %H:%M:%S')
#             meeting.__dict__['start_date'] = meeting.__dict__['start_date'].strftime('%m/%d/%Y %H:%M:%S')
#             data['meeting'] = meeting.__dict__
#             data['remindersHTML'] = str(remindersHtML.content)
#             if meeting:
#                 return JsonResponse(data)
#             else:
#                 return JsonResponse({'failed': 'ERROR'})
#         except models.Event.DoesNotExist:
#             return JsonResponse({'Event': 'DoesNotExist'})
#     else:
#         return JsonResponse({'METHOD': 'INVALID'})


# @login_required
# def get_task(request):
#     if request.method == 'POST':
#         try:
#             task = Event.objects.get(id=int(request.POST.get('taskID')), created_user=request.user)
#             data = {}
#             if task.parent:
#                 data['parent_type'] = task.parent.__class__.__name__
#                 data['parent_name'] = task.parent.__str__()
#                 data['parent_id'] = task.object_id
#             else:
#                 data['parent_name'] = ''
#                 data['parent_id'] = ''
#             if task.assigned_users: data['assigned_users'] = {
#                 task.assigned_users.id: task.assigned_users.username}
#             del task._state
#             del task._parent_cache
#             del task._assigned_users_cache
#             task.__dict__['close_date'] = task.__dict__['close_date'].strftime('%m/%d/%Y %H:%M:%S')
#             task.__dict__['start_date'] = task.__dict__['start_date'].strftime('%m/%d/%Y %H:%M:%S')
#             data['task'] = task.__dict__
#             if task:
#                 return JsonResponse(data)
#             else:
#                 return JsonResponse({'failed': 'ERROR'})
#         except models.Event.DoesNotExist:
#             return JsonResponse({'Event': 'DoesNotExist'})
#     else:
#         return JsonResponse({'METHOD': 'INVALID'})


# @login_required
# def get_call(request):
#     if request.method == 'POST':
#         try:
#             call = Event.objects.get(id=int(request.POST.get('callID')), created_user=request.user)
#             ReminderFormSet = modelformset_factory(Reminder, ReminderForm, can_delete=True, extra=0)
#             reminder_form_set = ReminderFormSet(queryset=call.reminders.all())
#             remindersHtML = render(request, 'planner/reminder.html', {'reminder_form_set': reminder_form_set})
#             data = {}
#             if call.parent:
#                 data['parent_type'] = call.parent.__class__.__name__
#                 data['parent_name'] = call.parent.__str__()
#                 data['parent_id'] = call.object_id
#             else:
#                 data['parent_name'] = ''
#                 data['parent_id'] = ''
#             if call.assigned_users: data['assigned_users'] = {
#                 call.assigned_users.id: call.assigned_users.username}
#             if call.attendees_user: data['attendees_user'] = {key.id: key.username for key in
#                                                               call.attendees_user.all()}
#             if call.attendees_contacts: data['attendees_contacts'] = {key.id: key.name for key in
#                                                                       call.attendees_contacts.all()}
#             if call.attendees_leads: data['attendees_leads'] = {key.id: key.first_name for key in
#                                                                 call.attendees_leads.all()}
#             del call._state
#             del call._parent_cache
#             del call._assigned_users_cache
#             call.__dict__['start_date'] = call.__dict__['start_date'].strftime('%m/%d/%Y %H:%M:%S')
#             data['call'] = call.__dict__
#             data['remindersHTML'] = str(remindersHtML.content)
#             if call:
#                 return JsonResponse(data)
#             else:
#                 return JsonResponse({'failed': 'ERROR'})
#         except models.Event.DoesNotExist:
#             return JsonResponse({'Event': 'DoesNotExist'})
#     else:
#         return JsonResponse({'METHOD': 'INVALID'})


# @login_required
# def update_meeting(request):
#     if request.method == 'POST':
#         try:
#             meeting = Event.objects.get(Q(created_user=request.user) | Q(updated_user=request.user),
#                                         id=int(request.POST.get('meetingID')))
#             eventForm = MeetingEventForm(request.POST, instance=meeting)
#             ReminderFormSet = modelformset_factory(Reminder, ReminderForm, can_delete=True)
#             reminder_form_set = ReminderFormSet(request.POST)
#             if eventForm.is_valid() and reminder_form_set.is_valid():
#                 meeting = None
#                 parent_name = None
#                 if eventForm.cleaned_data.get('parent_type') and eventForm.cleaned_data.get('parent_id'):
#                     meeting_object = add_parent(eventForm.cleaned_data.get('parent_type'),
#                                                 eventForm.cleaned_data.get('parent_id'), eventForm, None)
#                     meeting = meeting_object[0]
#                     parent_name = meeting_object[1]
#                 else:
#                     meeting = eventForm.save(commit=False)
#                     meeting.updated_user = request.user
#                     meeting.save()
#                 eventForm.save_m2m()
#                 reminders = reminder_form_set.save()
#                 meeting.reminders.add(*reminders)
#                 return JsonResponse({'success': 'Meeting Updated',
#                                      'id': meeting.id,
#                                      'name': meeting.name,
#                                      'parent': parent_name or None,
#                                      'status': meeting.status,
#                                      'startdate': meeting.start_date
#                                      })
#             else:
#                 if reminder_form_set.errors:
#                     return JsonResponse({'reminder': reminder_form_set.errors[-1]['__all__'][0]})
#                 elif eventForm.errors:
#                     return JsonResponse(dict(eventForm.errors))
#         except models.Event.DoesNotExist:
#             return JsonResponse({'Event': 'DoesNotExist'})
#     else:
#         return JsonResponse({'METHOD': 'INVALID'})


# @login_required
# def update_task(request):
#     if request.method == 'POST':
#         try:
#             task = Event.objects.get(Q(created_user=request.user) | Q(updated_user=request.user),
#                                      id=int(request.POST.get('taskID')))
#             eventForm = TaskEventForm(request.POST, instance=task)
#             if eventForm.is_valid():
#                 task = None
#                 if eventForm.cleaned_data.get('parent_type') and eventForm.cleaned_data.get('parent_id'):
#                     task_object = add_parent(eventForm.cleaned_data.get('parent_type'),
#                                              eventForm.cleaned_data.get('parent_id'), eventForm, None)
#                     task = task_object[0]
#                 else:
#                     task = eventForm.save(commit=False)
#                     task.updated_user = request.user
#                     task.save()
#                 return JsonResponse({'success': 'Task Updated',
#                                      'name': task.name,
#                                      'id': task.id,
#                                      'status': task.status,
#                                      'priority': task.priority,
#                                      'startdate': task.start_date})
#             else:
#                 return JsonResponse(dict(eventForm.errors))
#         except models.Event.DoesNotExist:
#             return JsonResponse({'Event': 'DoesNotExist'})
#     else:
#         return JsonResponse({'METHOD': 'INVALID'})


# @login_required
# def update_call(request):
#     if request.method == 'POST':
#         try:
#             call = Event.objects.get(Q(created_user=request.user) | Q(updated_user=request.user),
#                                      id=int(request.POST.get('callID')))
#             callsForm = CallEventForm(request.POST, instance=call)
#             ReminderFormSet = modelformset_factory(Reminder, ReminderForm, can_delete=True)
#             reminder_form_set = ReminderFormSet(request.POST)
#             if callsForm.is_valid() and reminder_form_set.is_valid():
#                 parent_name = None
#                 if callsForm.cleaned_data.get('parent_type') and callsForm.cleaned_data.get('parent_id'):
#                     call_object = add_parent(callsForm.cleaned_data.get('parent_type'),
#                                              callsForm.cleaned_data.get('parent_id'), callsForm, None)
#                     call = call_object[0]
#                     parent_name = call_object[1]
#                 else:
#                     call = callsForm.save(commit=False)
#                     call.updated_user = request.user
#                     call.save()
#                 callsForm.save_m2m()
#                 reminders = reminder_form_set.save()
#                 call.reminders.add(*reminders)
#                 return JsonResponse({'success': 'Call Updated',
#                                      'id': call.id,
#                                      'name': call.name,
#                                      'parent': parent_name or None,
#                                      'status': call.status,
#                                      'startdate': call.start_date
#                                      })
#             else:
#                 return JsonResponse(dict(callsForm.errors))
#         except models.Event.DoesNotExist:
#             return JsonResponse({'Event': 'DoesNotExist'})
#     else:
#         return JsonResponse({'METHOD': 'INVALID'})


# @login_required
# def update_event_status(request):
#     if request.method == 'POST':
#         try:
#             event = Event.objects.get(Q(created_user=request.user) | Q(updated_user=request.user),
#                                       Q(assigned_users=request.user), Q(attendees_user=request.user),
#                                       id=int(request.POST.get('id')))
#             if request.POST.get('status') == 'Held':
#                 event.status = request.POST.get('status')
#                 event.updated_user = request.user
#                 event.save()
#                 return JsonResponse({'success': 'Event Updated',
#                                      'status': event.status,
#                                      'id': event.id,
#                                      })
#             elif request.POST.get('status') == 'Not Held':
#                 event.status = request.POST.get('status')
#                 event.save()
#                 return JsonResponse({'success': 'Event Updated',
#                                      'id': event.id,
#                                      'status': event.status,
#                                      })
#             else:
#                 return JsonResponse({'INVALID': 'DATA'})
#         except models.Event.DoesNotExist:
#             return JsonResponse({'Event': 'DoesNotExist'})
#     else:
#         return JsonResponse({'METHOD': 'INVALID'})


# @login_required
# def search_meetings(request):
#     if request.method == 'GET':
#         try:
#             event = Event.objects.filter(Q(created_user=request.user) | Q(updated_user=request.user) |
#                                          Q(assigned_users=request.user) | Q(attendees_user=request.user)).distinct()
#             if request.GET.get('event_type'):
#                 event = event.filter(event_type=request.GET.get('event_type'))
#             if request.GET.get('event_name'):
#                 event = event.filter(name=request.GET.get('event_name')) or event
#             if request.GET.get('parent_type') and request.GET.get('parent_id'):
#                 parent = get_parent(request.GET.get('parent_type'), request.GET.get('parent_id'))
#                 if parent is not None:
#                     parent_content_type = ContentType.objects.get_for_model(parent)
#                     event = event.filter(content_type__pk=parent_content_type.id, object_id=parent.id) or event

#             if request.GET.get('start_date'):
#                 start_date = datetime.datetime.strptime(request.GET.get('start_date'), '%m/%d/%Y %H:%M:%S')
#                 event = event.filter(start_date=start_date) or event
#             if request.GET.get('created_at'):
#                 created_at = datetime.datetime.strptime(request.GET.get('created_at'), '%m/%d/%Y %H:%M:%S')
#                 event = event.filter(created_at=created_at) or event
#             if request.GET.get('updated_at'):
#                 updated_at = datetime.datetime.strptime(request.GET.get('updated_at'), '%m/%d/%Y %H:%M:%S')
#                 event = event.filter(updated_at=updated_at) or event

#             if request.GET.get('status'):
#                 event = event.filter(status=request.GET.get('status')) or event

#             if request.GET.getlist('attendees_contacts'):
#                 event = event.filter(attendees_contacts__in=request.GET.getlist('attendees_contacts')) or event
#             if request.GET.getlist('attendees_user'):
#                 event = event.filter(attendees_user__in=request.GET.getlist('attendees_user')) or event
#             if request.GET.getlist('attendees_leads'):
#                 event = event.filter(attendees_leads__in=request.GET.getlist('attendees_leads')) or event

#             if request.GET.get('assigned_users'):
#                 event = event.filter(assigned_users=request.GET.get('assigned_users')) or event
#             if request.GET.get('created_user'):
#                 event = event.filter(created_user=request.GET.get('created_user')) or event
#             if request.GET.get('updated_user'):
#                 event = event.filter(updated_user=request.GET.get('updated_user')) or event

#             paginator = Paginator(event, 5)
#             if request.GET.get('event_type') == 'Meeting':
#                 try:
#                     event = paginator.page(request.GET.get('page'))
#                     return render(request, 'meetings_list.html',
#                                   {'meetings': event})
#                 except PageNotAnInteger:
#                     event = paginator.page(1)
#                 except EmptyPage:
#                     event = paginator.page(paginator.num_pages)
#                 return render(request, 'meetings_list.html',
#                               {'meetings': event})
#             elif request.GET.get('event_type') == 'Call':
#                 try:
#                     event = paginator.page(request.GET.get('page'))
#                     return render(request, 'calls_list.html',
#                                   {'calls': event})
#                 except PageNotAnInteger:
#                     event = paginator.page(1)
#                 except EmptyPage:
#                     event = paginator.page(paginator.num_pages)
#                 return render(request, 'calls_list.html',
#                               {'calls': event})
#             elif request.GET.get('event_type') == 'Task':
#                 try:
#                     event = paginator.page(request.GET.get('page'))
#                     return render(request, 'tasks_list.html',
#                                   {'tasks': event})
#                 except PageNotAnInteger:
#                     event = paginator.page(1)
#                 except EmptyPage:
#                     event = paginator.page(paginator.num_pages)
#                 return render(request, 'tasks_list.html',
#                               {'tasks': event})
#         except models.Event.DoesNotExist:
#             return JsonResponse({'Event': 'DoesNotExist'})
#     else:
#         return JsonResponse({'METHOD': 'INVALID'})


# @login_required
# def get_reminder_form(request):
#     if request.method == 'GET':
#         RemindersFormSet = modelformset_factory(Reminder, form=ReminderForm, can_delete=True)
#         data = {
#             'form-TOTAL_FORMS': '1',
#             'form-INITIAL_FORMS': '0',
#             'form-MAX_NUM_FORMS': '10',
#         }
#         reminder_form_set = RemindersFormSet(data)
#         return render(request, 'reminder.html', {'reminder_form_set': reminder_form_set})
#     else:
#         return JsonResponse({'METHOD': 'INVALID'})


# def add_parent(parent_type, parent_id, form, request_user):
#     if parent_type == 'Account':
#         account = Account.objects.get(id=int(parent_id))
#         event = form.save(commit=False)
#         event.parent = account
#         if request_user is not None:
#             event.created_user = request_user
#         else:
#             event.updated_user = request_user
#         event.save()
#         return (event, event.parent.name)
#     elif parent_type == 'Case':
#         case = Case.objects.get(id=int(parent_id))
#         event = form.save(commit=False)
#         event.parent = case
#         if request_user is not None:
#             event.created_user = request_user
#         else:
#             event.updated_user = request_user
#         event.save()
#         return (event, event.parent.name)
#     elif parent_type == 'Lead':
#         lead = Lead.objects.get(id=int(parent_id))
#         event = form.save(commit=False)
#         event.parent = lead
#         if request_user is not None:
#             event.created_user = request_user
#         else:
#             event.updated_user = request_user
#         event.save()
#         return (event, event.parent.first_name)

#     elif parent_type == 'Opportunity':
#         opportunity = Opportunity.objects.get(id=int(parent_id))
#         event = form.save(commit=False)
#         event.parent = opportunity
#         if request_user is not None:
#             event.created_user = request_user
#         else:
#             event.updated_user = request_user
#         event.save()
#         return (event, event.parent.name)
#     elif parent_type == 'Contact':
#         contact = Contact.objects.get(id=int(parent_id))
#         event = form.save(commit=False)
#         event.parent = contact
#         if request_user is not None:
#             event.created_user = request_user
#         else:
#             event.updated_user = request_user
#         event.save()
#         return (event, event.parent.name)


# def get_parent(parent_type, parent_id):
#     if parent_type == 'Account':
#         try:
#             account = Account.objects.get(id=parent_id)
#             return account
#         except Account.DoesNotExist:
#             return None
#     elif parent_type == 'Lead':
#         try:
#             lead = Lead.objects.get(id=parent_id)
#             return lead
#         except Lead.DoesNotExist:
#             return None
#     elif parent_type == 'Opportunity':
#         try:
#             opportunity = Opportunity.objects.get(id=parent_id)
#             return opportunity
#         except Opportunity.DoesNotExist:
#             return None
#     elif parent_type == 'Case':
#         try:
#             case = Case.objects.get(id=parent_id)
#             return case
#         except Case.DoesNotExist:
#             return None
#     elif parent_type == 'Contact':
#         try:
#             contact = Contact.objects.get(id=parent_id)
#             return contact
#         except Contact.DoesNotExist:
#             return None


# def get_users(request):
#     if request.method == 'GET':
#         users = User.objects.all()
#         paginator = Paginator(users, 5)
#         try:
#             users = paginator.page(request.GET.get('page'))
#             return render(request, 'users.html',
#                           {'users': users})
#         except PageNotAnInteger:
#             users = paginator.page(1)
#         except EmptyPage:
#             users = paginator.page(paginator.num_pages)
#         return render(request, 'users.html', {'users': users})
#     else:
#         return JsonResponse({'METHOD': 'INVALID'})


# def get_contacts(request):
#     if request.method == 'GET':
#         contacts = Contact.objects.all()
#         paginator = Paginator(contacts, 5)
#         try:
#             contacts = paginator.page(request.GET.get('page'))
#             return render(request, 'contacts.html',
#                           {'contacts': contacts})
#         except PageNotAnInteger:
#             contacts = paginator.page(1)
#         except EmptyPage:
#             contacts = paginator.page(paginator.num_pages)
#         return render(request, 'contacts.html', {'contacts': contacts})
#     else:
#         return JsonResponse({'METHOD': 'INVALID'})


# def get_leads(request):
#     if request.method == 'GET':
#         leads = Lead.objects.all()
#         paginator = Paginator(leads, 5)
#         try:
#             leads = paginator.page(request.GET.get('page'))
#             return render(request, 'leads.html',
#                           {'leads': leads})
#         except PageNotAnInteger:
#             leads = paginator.page(1)
#         except EmptyPage:
#             leads = paginator.page(paginator.num_pages)
#         return render(request, 'leads.html', {'leads': leads})
#     else:
#         return JsonResponse({'METHOD': 'INVALID'})
