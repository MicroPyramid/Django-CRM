# import datetime
# from django.utils import timezone
# from django.test import TestCase
# from planner.models import Event
# from django.contrib.auth.models import User


# class EventObjects(object):
#     def setUp(self):
#         self.user = User.objects.create_superuser(
#             'user@micropyramid.com', 'username', 'password')

#         user_login = self.client.login(username='user@micropyramid.com', password='password')

#         self.meeting = Event.objects.create(event_type='Meeting', name='llll', status='Not Held',
#                                             description='addsdasda', start_date=timezone.now(),
#                                             close_date=timezone.now() + datetime.timedelta(days=5), created_user=self.user)
#         self.task = Event.objects.create(event_type='Task', name='dddl', status='Not Held',
#                                          description='addsdasda', start_date=timezone.now(),
#                                          close_date=timezone.now() + datetime.timedelta(days=1), created_user=self.user)
#         self.call = Event.objects.create(event_type='Call', name='asdfjkas dfasdfa 555',
#                                          status='Held',
#                                          description='addsdasda', start_date=timezone.now(),
#                                          close_date=timezone.now() + datetime.timedelta(days=2), created_user=self.user)


# class EventCreateTestCase(EventObjects, TestCase):
#     '''
#     Test for creating Events Through Models
#     '''

#     def test_create_meetings(self):
#         self.assertEqual(self.meeting.id, 1)

#     def test_create_task(self):
#         self.assertEqual(self.task.id, 2)

#     def test_create_call(self):
#         self.assertEqual(self.call.id, 3)


# class EventListViewsTestCase(EventObjects, TestCase):
#     '''Tests for events lists'''

#     def test_load_meetings(self):
#         self.meetings = Event.objects.filter(event_type='Meeting').order_by('-id')
#         response = self.client.get('/planner/meetings/list/')
#         self.assertEqual(response.status_code, 200)
#         self.assertTrue(response.context['meetings'])
#         self.assertEqual(response.context['meetings'][0].id, self.meeting.id)
#         self.assertTrue(response.context['reminder_form_set'])

#     def test_load_tasks(self):
#         self.tasks = Event.objects.filter(event_type='Task').order_by('-id')
#         response = self.client.get('/planner/tasks/list/')
#         self.assertEqual(response.status_code, 200)
#         self.assertEqual(response.context['tasks'][0].id, self.task.id)
#         self.assertTrue(response.context['tasks'])

#     def test_load_calls(self):
#         self.calls = Event.objects.filter(event_type='Call').order_by('-id')
#         response = self.client.get('/planner/calls/list/')
#         self.assertEqual(response.status_code, 200)
#         self.assertTrue(response.context['calls'])
#         self.assertEqual(response.context['calls'][0].id, self.call.id)
#         self.assertTrue(response.context['reminder_form_set'])


# class EventCreateUsingURLsTestCase(EventObjects, TestCase):
#     '''
#     Tests for testing Views using URLs and POST data
#     '''

#     def test_create_meeting(self):
#         response = self.client.post('/planner/meeting/create/', {'name': 'dfasdf',
#                                                                  'parent_type': 'Case',
#                                                                  'parent_id': '',
#                                                                  'status': 'Held',
#                                                                  'event_type': 'Meeting',
#                                                                  'duration': '7200',
#                                                                  'start_date': str(timezone.now().strftime(
#                                                                      '%m/%d/%Y %H:%M:%S')),
#                                                                  'close_date': str(
#                                                                      (timezone.now() + datetime.timedelta(
#                                                                          days=6)).strftime('%m/%d/%Y %H:%M:%S')),
#                                                                  'form-TOTAL_FORMS': '1',
#                                                                  'form-INITIAL_FORMS': '0',
#                                                                  'form-MAX_NUM_FORMS': '10',
#                                                                  'form-0-reminder_type': 'Email',
#                                                                  'form-0-reminder_time': '120',
#                                                                  'form-0-DELETE': '',
#                                                                  'form-0-id': ''
#                                                                  })

#         self.assertEqual(response.status_code, 200)
#         self.assertEqual('Meeting Created', response.json()['success'])

#     def test_create_meeting_with_empty_data(self):
#         response = self.client.post('/planner/meeting/create/', {'name': '',
#                                                                  'parent_type': '',
#                                                                  'status': '',
#                                                                  'event_type': '',
#                                                                  'parent_id': '',
#                                                                  'duration': '',
#                                                                  'start_date': '',
#                                                                  'close_date': '',
#                                                                  'form-TOTAL_FORMS': '',
#                                                                  'form-INITIAL_FORMS': '',
#                                                                  'form-MAX_NUM_FORMS': '',
#                                                                  'form-0-reminder_type': '',
#                                                                  'form-0-reminder_time': '',
#                                                                  'form-0-DELETE': '',
#                                                                  'form-0-id': ''
#                                                                  })

#         self.assertEqual(response.status_code, 200)
#         self.assertIn('name', response.json().keys())
#         self.assertIn('duration', response.json().keys())
#         self.assertEqual(['This field is required.'], response.json()['name'])
#         self.assertEqual(['This field is required.'], response.json()['event_type'])
#         self.assertEqual(['This field is required.'], response.json()['start_date'])
#         self.assertEqual(['This field is required.'], response.json()['close_date'])

#     def test_create_meeting_with_invalid_data(self):
#         response = self.client.post('/planner/meeting/create/', {'name': '',
#                                                                  'parent_type': 'qqqweq',
#                                                                  'parent_id': '22',
#                                                                  'status': 'qweqw#e',
#                                                                  'event_type': 'eq##we',
#                                                                  'duration': 'qw66e',
#                                                                  'start_date': '654sad654',
#                                                                  'close_date': '65sda',
#                                                                  'form-TOTAL_FORMS': '',
#                                                                  'form-INITIAL_FORMS': '',
#                                                                  'form-MAX_NUM_FORMS': '',
#                                                                  'form-0-reminder_type': '',
#                                                                  'form-0-reminder_time': '',
#                                                                  'form-0-DELETE': '',
#                                                                  'form-0-id': ''
#                                                                  })

#         self.assertEqual(response.status_code, 200)
#         self.assertEqual(['This field is required.'], response.json()['name'])
#         self.assertEqual(['Enter a valid date/time.'], response.json()['close_date'])
#         self.assertEqual(['Invalid Startdate'], response.json()['start_date'])
#         self.assertEqual(['Select a valid choice. qw66e is not one of the available choices.'],
#                          response.json()['duration'])
#         self.assertEqual(['Select a valid choice. qweqw#e is not one of the available choices.'],
#                          response.json()['status'])
#         self.assertEqual(['Select a valid choice. qqqweq is not one of the available choices.'],
#                          response.json()['parent_type'])

#     def test_create_task(self):
#         data = {'name': 'dfasdf',
#                 'parent_type': 'Account',
#                 'status': 'Held',
#                 'event_type': 'Task',
#                 'duration': '1800',
#                 'priority': 'High',
#                 'start_date': str(timezone.now().strftime('%m/%d/%Y %H:%M:%S')),
#                 'close_date': str((timezone.now() + datetime.timedelta(
#                     days=6)).strftime('%m/%d/%Y %H:%M:%S')),
#                 }
#         response = self.client.post('/planner/task/create/', data)
#         self.assertEqual(response.status_code, 200)
#         self.assertEqual('Task Created', response.json()['success'])

#     def test_create_call(self):
#         response = self.client.post('/planner/call/create/', {'name': 'dfasdf',
#                                                               'parent_type': 'Account',
#                                                               'event_type': 'Call',
#                                                               'duration': '3600',
#                                                               'direction': 'Outbound',
#                                                               'start_date': str(timezone.now().strftime(
#                                                                   '%m/%d/%Y %H:%M:%S')),
#                                                               'form-TOTAL_FORMS': '1',
#                                                               'form-INITIAL_FORMS': '0',
#                                                               'form-MAX_NUM_FORMS': '10',
#                                                               'form-0-reminder_type': 'Email',
#                                                               'form-0-reminder_time': '120',
#                                                               'form-0-DELETE': '',
#                                                               'form-0-id': ''
#                                                               })

#         self.assertEqual(response.status_code, 200)
#         self.assertEqual('Call Created', response.json()['success'])


# class EventsGetViewsTestCase(EventObjects, TestCase):
#     '''
#     Tests for getting a meeting with ID
#     '''

#     def test_get_meeting_validID(self):
#         response = self.client.post('/planner/get/meeting/', {
#             'meetingID': self.meeting.id
#         })
#         self.assertEqual(response.status_code, 200)
#         self.assertEqual('Meeting', response.json()['meeting']['event_type'])

#     def test_get_meeting_invalidID(self):
#         response = self.client.post('/planner/get/meeting/', {
#             'meetingID': 6
#         })
#         self.assertEqual(response.status_code, 200)
#         self.assertEqual({'Event': 'DoesNotExist'}, response.json())

#     def test_get_task_validID(self):
#         response = self.client.post('/planner/get/task/', {
#             'taskID': self.task.id
#         })
#         self.assertEqual(response.status_code, 200)
#         self.assertEqual('Task', response.json()['task']['event_type'])

#     def test_get_task_invalidID(self):
#         response = self.client.post('/planner/get/task/', {
#             'taskID': 6
#         })
#         self.assertEqual(response.status_code, 200)
#         self.assertEqual({'Event': 'DoesNotExist'}, response.json())

#     def test_get_call_validID(self):
#         response = self.client.post('/planner/get/call/', {
#             'callID': self.call.id
#         })
#         self.assertEqual(response.status_code, 200)
#         self.assertEqual('Call', response.json()['call']['event_type'])

#     def test_get_call_invalidID(self):
#         response = self.client.post('/planner/get/call/', {
#             'callID': 67
#         })
#         self.assertEqual(response.status_code, 200)
#         self.assertEqual({'Event': 'DoesNotExist'}, response.json())


# class EventsDeleteViewsTestCase(EventObjects, TestCase):
#     '''
#     Tests for getting a meeting with ID
#     '''

#     def test_delete_meeting_valid_ID(self):
#         response = self.client.post('/planner/meeting/delete/', {
#             'meetingID': self.meeting.id
#         })
#         self.assertEqual(response.status_code, 200)
#         self.assertEqual({'success': 'Meeting Deleted'}, response.json())

#     def test_delete_meeting_InvalidID(self):
#         response = self.client.post('/planner/meeting/delete/', {
#             'meetingID': '5'
#         })
#         self.assertEqual(response.status_code, 200)
#         self.assertEqual({'Event': 'DoesNotExist'}, response.json())

#     def test_delete_task_valid_ID(self):
#         response = self.client.post('/planner/task/delete/', {
#             'taskID': self.task.id
#         })
#         self.assertEqual(response.status_code, 200)
#         self.assertEqual({'success': 'Task Deleted'}, response.json())

#     def test_delete_task_InvalidID(self):
#         response = self.client.post('/planner/task/delete/', {
#             'taskID': '5'
#         })
#         self.assertEqual(response.status_code, 200)
#         self.assertEqual({'Event': 'DoesNotExist'}, response.json())

#     def test_delete_call_valid_ID(self):
#         response = self.client.post('/planner/call/delete/', {
#             'callID': self.call.id
#         })
#         self.assertEqual(response.status_code, 200)
#         self.assertEqual({'success': 'Call Deleted'}, response.json())

#     def test_call_task_InvalidID(self):
#         response = self.client.post('/planner/call/delete/', {
#             'callID': '55'
#         })
#         self.assertEqual(response.status_code, 200)
#         self.assertEqual({'Event': 'DoesNotExist'}, response.json())
