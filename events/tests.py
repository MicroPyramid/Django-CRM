from datetime import datetime, timedelta

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from common.models import Address, Attachments, Comment, User
from contacts.models import Contact
from events.models import Event
from teams.models import Teams


class EventObjectTest(object):

    def setUp(self):
        self.user = User.objects.create(
            first_name="johnEvent", username='johnDoeEvent', email='johnDoeEvent@example.com', role='ADMIN')
        self.user.set_password('password')
        self.user.save()

        self.user1 = User.objects.create(
            first_name="janeEvent",
            username='janeDoeEvent',
            email='janeDoeEvent@example.com',
            role="USER",
            has_sales_access=True)
        self.user1.set_password('password')
        self.user1.save()

        self.user2 = User.objects.create(
            first_name="joeEvent",
            username='joeEvent',
            email='joeEvent@example.com',
            role="USER",
            has_sales_access=True)
        self.user2.set_password('password')
        self.user2.save()

        self.team_dev = Teams.objects.create(name='events teams')
        self.team_dev.users.add(self.user2.id)

        self.contact = Contact.objects.create(
            first_name="contact event",
            email="contact@event.com",
            phone="12345",
            description="contact",
            created_by=self.user1)
        self.contact.assigned_to.add(self.user1)

        self.event = Event.objects.create(
            name='event object test',
            event_type='Non-Recurring',
            start_date=(datetime.now()).strftime('%Y-%m-%d'),
            start_time=(datetime.now()).strftime('%H:%M:%S'),
            end_date=(datetime.now()).strftime('%Y-%m-%d'),
            end_time=(datetime.now() + timedelta(hours=2)
                      ).strftime('%H:%M:%S'),
            description='non recurring event',
            created_by=self.user,
            date_of_meeting=(datetime.now()).strftime('%Y-%m-%d'),
        )
        self.event.contacts.add(self.contact)
        self.event.assigned_to.add(self.user.id, self.user1.id)

        self.event_1 = Event.objects.create(
            name='event object test check',
            event_type='Non-Recurring',
            start_date=(datetime.now()).strftime('%Y-%m-%d'),
            start_time=(datetime.now()).strftime('%H:%M:%S'),
            end_date=(datetime.now()).strftime('%Y-%m-%d'),
            end_time=(datetime.now() + timedelta(hours=2)
                      ).strftime('%H:%M:%S'),
            description='non recurring event',
            created_by=self.user1,
        )
        self.event_1.contacts.add(self.contact)
        self.event_1.assigned_to.add(self.user2.id)

        self.comment = Comment.objects.create(
            comment='test comment', event=self.event,
            commented_by=self.user
        )
        self.attachment = Attachments.objects.create(
            attachment='image.png', event=self.event,
            created_by=self.user
        )


class EventListTestCase(EventObjectTest, TestCase):

    def test_events_list(self):
        self.client.login(email='johnDoeEvent@example.com',
                          password='password')
        response = self.client.get(reverse('events:events_list'))
        self.assertEqual(response.status_code, 200)

        self.client.login(email='janeDoeEvent@example.com',
                          password='password')
        response = self.client.get(reverse('events:events_list'))
        self.assertEqual(response.status_code, 200)

        data = {
            'event_name': 'event name',
            'created_by': self.user.id,
            'assigned_to': self.user1.id,
            'date_of_meeting': (datetime.now()).strftime('%Y-%m-%d'),
        }
        self.client.login(email='johnDoeEvent@example.com',
                          password='password')
        response = self.client.post(reverse('events:events_list'), data)
        self.assertEqual(response.status_code, 200)

        self.client.login(email='janeDoeEvent@example.com',
                          password='password')
        response = self.client.post(reverse('events:events_list'), data)
        self.assertEqual(response.status_code, 200)


class EventCreateTestCase(EventObjectTest, TestCase):

    def test_events_create(self):
        self.client.login(email='janeDoeEvent@example.com',
                          password='password')
        response = self.client.get(reverse('events:event_create'))
        self.assertEqual(response.status_code, 200)

        self.client.login(email='johnDoeEvent@example.com',
                          password='password')
        response = self.client.get(reverse('events:event_create'))
        self.assertEqual(response.status_code, 200)

        data = {
            'event_name': 'event name',
            'event_type': 'Non-Recurring',
            'contacts': self.contact.id,
            'teams': self.team_dev.id,
            'assigned_to': self.user1.id,
            'start_date': (datetime.now()).strftime('%Y-%m-%d'),
            'start_time': (datetime.now()).strftime('%H:%M:%S'),
            'end_date': (datetime.now()).strftime('%Y-%m-%d'),
            'end_time': (datetime.now() + timedelta(hours=2)).strftime('%H:%M:%S'),
        }

        response = self.client.post(reverse('events:event_create'), data)
        self.assertEqual(response.status_code, 200)
        data = {**data, 'name': 'event name'}
        response = self.client.post(reverse('events:event_create'), data)
        self.assertEqual(response.status_code, 200)

        data = {**data, 'event_type': 'Recurring', 'recurring_days': [
            'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']}
        response = self.client.post(reverse('events:event_create'), data)
        self.assertEqual(response.status_code, 200)

        data = {**data, 'name': 'recurring event test', 'end_date': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
                'start_date': (datetime.now()).strftime('%Y-%m-%d'), }
        response = self.client.post(reverse('events:event_create'), data)
        self.assertEqual(response.status_code, 200)

        data = {**data, 'event_type': 'Recurring', 'recurring_days': []}
        response = self.client.post(reverse('events:event_create'), data)
        self.assertEqual(response.status_code, 200)

        data = {**data, 'name': 'recurring event test', 'start_date': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
                'end_date': (datetime.now()).strftime('%Y-%m-%d'), }
        response = self.client.post(reverse('events:event_create'), data)
        self.assertEqual(response.status_code, 200)

        data = {**data, 'event_type': 'Recurring', 'start_date': ''}
        response = self.client.post(reverse('events:event_create'), data)
        self.assertEqual(response.status_code, 200)

        data = {**data, 'event_type': 'Recurring', 'start_time': ''}
        response = self.client.post(reverse('events:event_create'), data)
        self.assertEqual(response.status_code, 200)

        data = {**data, 'event_type': 'Recurring',
                'start_time': (datetime.now() + timedelta(hours=2)).strftime('%H:%M:%S'),
                'end_time': (datetime.now()).strftime('%H:%M:%S'),
                }
        response = self.client.post(reverse('events:event_create'), data)
        self.assertEqual(response.status_code, 200)


class EventDetailTestCase(EventObjectTest, TestCase):

    def test_events_detail(self):
        self.client.login(email='johnDoeEvent@example.com',
                          password='password')
        response = self.client.get(
            reverse('events:detail_view', args=(self.event.id,)))
        self.assertEqual(response.status_code, 200)

        self.client.login(email='janeDoeEvent@example.com',
                          password='password')
        response = self.client.get(
            reverse('events:detail_view', args=(self.event.id,)))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(
            reverse('events:detail_view', args=(self.event_1.id,)))
        self.assertEqual(response.status_code, 200)

        self.client.login(email='joeEvent@example.com',
                          password='password')
        response = self.client.get(
            reverse('events:detail_view', args=(self.event.id,)))
        self.assertEqual(response.status_code, 403)


class EventEditTestCase(EventObjectTest, TestCase):

    def test_events_edit(self):
        self.client.login(email='janeDoeEvent@example.com',
                          password='password')
        response = self.client.get(
            reverse('events:event_update', args=(self.event.id,)))
        self.assertEqual(response.status_code, 200)

        self.client.login(email='joeEvent@example.com',
                          password='password')
        response = self.client.get(
            reverse('events:event_update', args=(self.event.id,)))
        self.assertEqual(response.status_code, 403)

        data = {
            'event_name': 'event name',
            'event_type': 'Non-Recurring',
            'contacts': self.contact.id,
            'teams': self.team_dev.id,
            'assigned_to': self.user1.id,
            'start_date': (datetime.now()).strftime('%Y-%m-%d'),
            'start_time': (datetime.now()).strftime('%H:%M:%S'),
            'end_date': (datetime.now()).strftime('%Y-%m-%d'),
            'end_time': (datetime.now() + timedelta(hours=2)).strftime('%H:%M:%S'),
        }
        self.client.login(email='johnDoeEvent@example.com',
                          password='password')
        response = self.client.post(
            reverse('events:event_update', args=(self.event.id,)), data)
        self.assertEqual(response.status_code, 200)

        data = {**data, 'name': 'event object test edit'}
        response = self.client.post(
            reverse('events:event_update', args=(self.event.id,)), data)
        self.assertEqual(response.status_code, 200)

        self.client.login(email='joeEvent@example.com',
                          password='password')
        response = self.client.post(
            reverse('events:event_update', args=(self.event.id,)), data)
        self.assertEqual(response.status_code, 200)

        self.client.login(email='johnDoeEvent@example.com',
                          password='password')
        new_data = {
            'name': 'event name edit object',
            'event_type': 'Recurring',
            'contacts': self.contact.id,
            'teams': self.team_dev.id,
            'assigned_to': self.user1.id, 'end_date': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
            'end_time': (datetime.now() + timedelta(hours=2)).strftime('%H:%M:%S'),
            'start_time': (datetime.now()).strftime('%H:%M:%S'),
            'start_date': (datetime.now()).strftime('%Y-%m-%d'),
            'recurring_days': [
                'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        }
        response = self.client.post(
            reverse('events:event_update', args=(self.event.id,)), new_data)
        self.assertEqual(response.status_code, 200)


class AddCommentTestCase(EventObjectTest, TestCase):

    def test_event_add_comment(self):

        self.client.login(email='johnDoeEvent@example.com',
                          password='password')
        data = {
            'comment': '',
            'event_id': self.event.id,
        }
        response = self.client.post(
            reverse('events:add_comment'), data)
        self.assertEqual(response.status_code, 200)

        data = {
            'comment': 'test comment event',
            'event_id': self.event.id,
        }
        response = self.client.post(
            reverse('events:add_comment'), data)
        self.assertEqual(response.status_code, 200)

        self.client.login(email='janeDoeEvent@example.com',
                          password='password')
        response = self.client.post(
            reverse('events:add_comment'), data)
        self.assertEqual(response.status_code, 200)


class UpdateCommentTestCase(EventObjectTest, TestCase):

    def test_event_update_comment(self):

        self.client.login(email='johnDoeEvent@example.com',
                          password='password')
        data = {
            'commentid': self.comment.id,
            'event_id': self.event.id,
            'comment': ''
        }
        response = self.client.post(
            reverse('events:edit_comment'), data)
        self.assertEqual(response.status_code, 200)

        data = {
            'comment': 'test comment',
            'commentid': self.comment.id,
            'event_id': self.event.id,
        }
        response = self.client.post(
            reverse('events:edit_comment'), data)
        self.assertEqual(response.status_code, 200)

        self.client.login(email='janeDoeEvent@example.com',
                          password='password')
        response = self.client.post(
            reverse('events:edit_comment'), data)
        self.assertEqual(response.status_code, 200)


class DeleteCommentTestCase(EventObjectTest, TestCase):

    def test_event_delete_comment(self):

        data = {
            'comment_id': self.comment.id,
        }
        self.client.login(email='janeDoeEvent@example.com',
                          password='password')
        response = self.client.post(
            reverse('events:remove_comment'), data)
        self.assertEqual(response.status_code, 200)

        self.client.login(email='johnDoeEvent@example.com',
                          password='password')
        response = self.client.post(
            reverse('events:remove_comment'), data)
        self.assertEqual(response.status_code, 200)


class AddAttachmentTestCase(EventObjectTest, TestCase):

    def test_event_add_attachment(self):

        data = {
            'attachment': SimpleUploadedFile('file_name.txt', bytes('file contents.', 'utf-8')),
            'event_id': self.event.id
        }
        self.client.login(email='johnDoeEvent@example.com',
                          password='password')
        response = self.client.post(
            reverse('events:add_attachment'), data)
        self.assertEqual(response.status_code, 200)

        self.client.login(email='janeDoeEvent@example.com',
                          password='password')
        response = self.client.post(
            reverse('events:add_attachment'), data)
        self.assertEqual(response.status_code, 200)

        data = {
            'attachment': '',
            'event_id': self.event.id
        }
        self.client.login(email='johnDoeEvent@example.com',
                          password='password')
        response = self.client.post(
            reverse('events:add_attachment'), data)
        self.assertEqual(response.status_code, 200)


class DeleteAttachmentTestCase(EventObjectTest, TestCase):

    def test_invoice_delete_attachment(self):

        data = {
            'attachment_id': self.attachment.id,
        }
        self.client.login(email='janeDoeEvent@example.com',
                          password='password')
        response = self.client.post(
            reverse('events:remove_attachment'), data)
        self.assertEqual(response.status_code, 200)

        self.client.login(email='johnDoeEvent@example.com',
                          password='password')
        response = self.client.post(
            reverse('events:remove_attachment'), data)
        self.assertEqual(response.status_code, 200)


class EventDeleteTestCase(EventObjectTest, TestCase):

    def test_events_delete(self):

        self.client.login(email='janeDoeEvent@example.com',
                          password='password')
        response = self.client.get(
            reverse('events:event_delete', args=(self.event.id,)))
        self.assertEqual(response.status_code, 403)

        self.client.login(email='johnDoeEvent@example.com',
                          password='password')
        response = self.client.get(
            reverse('events:event_delete', args=(self.event.id,)))
        self.assertEqual(response.status_code, 302)

