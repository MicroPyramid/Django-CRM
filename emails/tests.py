from django.test import TestCase
from django.test import Client
from common.models import User
from emails.models import Email
from emails.forms import EmailForm


class UserCreation(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create(
            first_name="navaneetha", username='navaneetha', email="n@mp.com", role="ADMIN")
        self.user.set_password('navi123')
        self.user.save()
        self.email = Email.objects.create(
            from_email="admin@micropyramid.com", to_email="meghana@micropyramid.com", subject="wish", message="haii",
            important=False)
        self.client.login(username='n@mp.com', password='navi123')


class EmailSentEdit(UserCreation, TestCase):
    def test_edit_form_valid(self):
        form = EmailForm(data={'from_email': "abc@mp.com",
                               'to_email': "xyz@mp.com",
                               'subject': "hello hi",
                               'message': 'simple mail'})
        print('yes')
        self.assertTrue(form.is_valid())

    def test_edit_form_invalid(self):
        form = EmailForm(data={'from_email': "abc@mp.com",
                               'to_email': "",
                               'subject': "hello hi",
                               'message': 'simple mail'})
        print('yes2')
        self.assertFalse(form.is_valid())


class EmailListTestCase(UserCreation, TestCase):
    def test_email_list(self):
        url = "/emails/list/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


class EmailTestCase(UserCreation, TestCase):
    def test_email_send(self):
        url = "/emails/compose/"
        data = {
            'from_email': "abc@micropyramid.com", 'to_email': "meg@gmail.com",
            'subject': 'act', 'message': "Hello"
        }
        response = self.client.post(url, data)
        get_email = Email.objects.get(subject="wish")
        # boo = Email.objects.get(important=True)
        # print('yes')
        self.assertFalse(get_email.important)
        self.assertEqual(get_email.subject, get_email.__unicode__())

        self.assertEqual(response.status_code, 302)

    def test_email_sent(self):
        url = "/emails/email_sent/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_email_trash(self):
        url = "/emails/email_trash/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    # def test_email_trash_del(self):
    #     url = "/emails/trash_delete/"+str(self.email.pk)+"/$"
    #     print(url)
    #     response = self.client.get(url)
    #     self.assertEqual(response.status_code,200)
