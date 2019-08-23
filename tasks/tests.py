from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from accounts.models import Account
from common.models import Attachments, Comment, User
from tasks.models import Task
from teams.models import Teams


class TaskCreateTest(object):

    def setUp(self):
        self.user = User.objects.create(
            first_name="johnTask", username='johnDoeTask', email='johnTask@example.com', role='ADMIN')
        self.user.set_password('password')
        self.user.save()

        self.user1 = User.objects.create(
            first_name="janeTask",
            username='janeDoeTask',
            email='janeDoeTask@example.com',
            role="USER",
            has_sales_access=True)
        self.user1.set_password('password')
        self.user1.save()

        self.user2 = User.objects.create(
            first_name="joeTask",
            username='joeTask',
            email='joeTask@example.com',
            role="USER",
            has_sales_access=True)
        self.user2.set_password('password')
        self.user2.save()

        self.team_dev = Teams.objects.create(name='task teams')
        self.team_dev.users.add(self.user2.id)

        self.account = Account.objects.create(
            name="john task", email="johntasks@example.com", phone="123456789",
            billing_address_line="", billing_street="street name",
            billing_city="city name",
            billing_state="state", billing_postcode="1234",
            billing_country="US",
            website="www.example.como", created_by=self.user, status="open",
            industry="SOFTWARE", description="Testing")

        self.task = Task.objects.create(
            title='first task', status='New', priority='Medium')
        self.task.created_by = self.user
        self.task.assigned_to.add(self.user1)
        self.task.account = self.account
        self.task.save()

        self.account.assigned_to.add(self.user1)

        self.task_1 = Task.objects.create(
            title='second task', status='New', priority='Medium')
        self.task_1.created_by = self.user
        self.task_1.assigned_to.add(self.user1)
        self.task_1.save()

        self.task_2 = Task.objects.create(
            title='second task', status='New', priority='Medium')
        self.task_2.created_by = self.user1
        self.task_2.save()

        self.comment = Comment.objects.create(
            comment='test comment', task=self.task,
            commented_by=self.user
        )
        self.attachment = Attachments.objects.create(
            attachment='image.png', task=self.task,
            created_by=self.user
        )


class TaskListTestCase(TaskCreateTest, TestCase):

    def test_tasks_list(self):
        self.client.login(email='johnTask@example.com', password='password')
        response = self.client.get(reverse('tasks:tasks_list'))
        self.assertEqual(response.status_code, 200)

        data = {
            'task_title': 'title',
            'status': 'New',
            'priority': 'Medium'
        }
        response = self.client.post(reverse('tasks:tasks_list'), data)
        self.assertEqual(response.status_code, 200)

        self.client.login(email='janeDoeTask@example.com', password='password')
        response = self.client.get(reverse('tasks:tasks_list'))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse('tasks:tasks_list'), data)
        self.assertEqual(response.status_code, 200)


class TaskCreateTestCase(TaskCreateTest, TestCase):

    def test_task_create(self):
        self.client.login(email='johnTask@example.com', password='password')
        response = self.client.get(reverse('tasks:task_create'))
        self.assertEqual(response.status_code, 200)

        self.client.login(email='janeDoeTask@example.com', password='password')
        response = self.client.get(reverse('tasks:task_create'))
        self.assertEqual(response.status_code, 200)

        self.client.login(email='johnTask@example.com', password='password')
        data = {
            'title': '',
            'status': 'New',
            'priority': 'Medium'
        }
        response = self.client.post(reverse('tasks:task_create'), data)
        self.assertEqual(response.status_code, 200)

        data = {
            'title': 'task title',
            'status': 'New',
            'priority': 'Medium',
            'teams': self.team_dev.id,
            'from_account': self.account.id,
        }
        response = self.client.post(reverse('tasks:task_create'), data)
        self.assertEqual(response.status_code, 200)


class TaskDetailTestCase(TaskCreateTest, TestCase):

    def test_task_detail(self):
        self.client.login(email='johnTask@example.com', password='password')
        response = self.client.get(
            reverse('tasks:task_detail', args=(self.task.id,)))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(
            reverse('tasks:task_detail', args=(self.task_1.id,)))
        self.assertEqual(response.status_code, 200)

        self.client.login(email='janeDoeTask@example.com', password='password')
        response = self.client.get(
            reverse('tasks:task_detail', args=(self.task.id,)))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(
            reverse('tasks:task_detail', args=(self.task_2.id,)))
        self.assertEqual(response.status_code, 200)

        self.client.login(email='joeTask@example.com', password='password')
        response = self.client.get(
            reverse('tasks:task_detail', args=(self.task.id,)))
        self.assertEqual(response.status_code, 403)

        self.assertEqual(str(self.task), 'first task')


class TaskEditTestCase(TaskCreateTest, TestCase):

    def test_task_Edit(self):
        self.client.login(email='johnTask@example.com', password='password')
        response = self.client.get(
            reverse('tasks:task_edit', args=(self.task.id,)))
        self.assertEqual(response.status_code, 200)

        self.client.login(email='janeDoeTask@example.com', password='password')
        response = self.client.get(
            reverse('tasks:task_edit', args=(self.task.id,)))
        self.assertEqual(response.status_code, 403)

        response = self.client.get(
            reverse('tasks:task_edit', args=(self.task_2.id,)))
        self.assertEqual(response.status_code, 200)

        self.client.login(email='johnTask@example.com', password='password')
        data = {
            'title': '',
            'status': 'New',
            'priority': 'Medium'
        }
        response = self.client.post(
            reverse('tasks:task_edit', args=(self.task.id,)), data)
        self.assertEqual(response.status_code, 200)

        data = {
            'title': 'task title',
            'status': 'New',
            'priority': 'High',
            'teams': self.team_dev.id,
            'from_account': self.account.id,
        }
        response = self.client.post(
            reverse('tasks:task_edit', args=(self.task.id,)), data)
        self.assertEqual(response.status_code, 200)

        data = {
            'title': 'second task',
            'status': 'New',
            'priority': 'High',
            'teams': self.team_dev.id,
            'from_account': self.account.id,
        }

        response = self.client.post(
            reverse('tasks:task_edit', args=(self.task.id,)), data)
        self.assertEqual(response.status_code, 200)


class TaskDeleteTestCase(TaskCreateTest, TestCase):

    def test_task_delete(self):
        self.client.login(email='janeDoeTask@example.com', password='password')
        response = self.client.get(
            reverse('tasks:task_delete', args=(self.task.id,)))
        self.assertEqual(response.status_code, 403)

        self.client.login(email='johnTask@example.com', password='password')
        response = self.client.get(
            reverse('tasks:task_delete', args=(self.task.id,)))
        self.assertEqual(response.status_code, 302)

        response = self.client.get(
            reverse('tasks:task_delete', args=(self.task_1.id,)) + '?view_account={}'.format(self.account.id))
        self.assertEqual(response.status_code, 302)



class AddCommentTestCase(TaskCreateTest, TestCase):

    def test_task_add_comment(self):

        self.client.login(email='johnTask@example.com', password='password')
        data = {
            'comment': '',
            'task_id': self.task.id,
        }
        response = self.client.post(
            reverse('tasks:add_comment'), data)
        self.assertEqual(response.status_code, 200)

        data = {
            'comment': 'test comment',
            'task_id': self.task.id,
        }
        response = self.client.post(
            reverse('tasks:add_comment'), data)
        self.assertEqual(response.status_code, 200)

        self.client.login(email='janeDoeTask@example.com', password='password')
        response = self.client.post(
            reverse('tasks:add_comment'), data)
        self.assertEqual(response.status_code, 200)


class UpdateCommentTestCase(TaskCreateTest, TestCase):

    def test_task_update_comment(self):

        self.client.login(email='johnTask@example.com', password='password')
        data = {
            'commentid': self.comment.id,
            'task_id': self.task.id,
            'comment':''
        }
        response = self.client.post(
            reverse('tasks:edit_comment'), data)
        self.assertEqual(response.status_code, 200)

        data = {
            'comment': 'test comment',
            'commentid': self.comment.id,
            'task_id': self.task.id,
        }
        response = self.client.post(
            reverse('tasks:edit_comment'), data)
        self.assertEqual(response.status_code, 200)

        self.client.login(email='janeDoeTask@example.com', password='password')
        response = self.client.post(
            reverse('tasks:edit_comment'), data)
        self.assertEqual(response.status_code, 200)


class DeleteCommentTestCase(TaskCreateTest, TestCase):

    def test_task_delete_comment(self):

        data = {
            'comment_id': self.comment.id,
        }
        self.client.login(email='janeDoeTask@example.com', password='password')
        response = self.client.post(
            reverse('tasks:remove_comment'), data)
        self.assertEqual(response.status_code, 200)

        self.client.login(email='johnTask@example.com', password='password')
        response = self.client.post(
            reverse('tasks:remove_comment'), data)
        self.assertEqual(response.status_code, 200)


class AddAttachmentTestCase(TaskCreateTest, TestCase):

    def test_task_add_attachment(self):

        data = {
            'attachment': SimpleUploadedFile('file_name.txt', bytes('file contents.', 'utf-8')),
            'task_id':self.task.id
        }
        self.client.login(email='johnTask@example.com', password='password')
        response = self.client.post(
            reverse('tasks:add_attachment'), data)
        self.assertEqual(response.status_code, 200)

        self.client.login(email='johnTask@example.com', password='password')
        response = self.client.post(
            reverse('tasks:add_attachment'), data)
        self.assertEqual(response.status_code, 200)

        data = {
            'attachment': '',
            'task_id':self.task.id
        }
        self.client.login(email='janeDoeTask@example.com', password='password')
        response = self.client.post(
            reverse('tasks:add_attachment'), data)
        self.assertEqual(response.status_code, 200)


class DeleteAttachmentTestCase(TaskCreateTest, TestCase):

    def test_task_delete_attachment(self):

        data = {
            'attachment_id': self.attachment.id,
        }
        self.client.login(email='janeDoeTask@example.com', password='password')
        response = self.client.post(
            reverse('tasks:remove_attachment'), data)
        self.assertEqual(response.status_code, 200)

        self.client.login(email='johnTask@example.com', password='password')
        response = self.client.post(
            reverse('tasks:remove_attachment'), data)
        self.assertEqual(response.status_code, 200)
