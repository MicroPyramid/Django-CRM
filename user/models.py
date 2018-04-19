from django.db import models
from django.urls import reverse
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, UserManager
# Create your models here.

class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=100, unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    email = models.EmailField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(('date joined'), auto_now_add=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', ]

    objects = UserManager()

    def get_view_url(self):
        """
        returns a reverse url for user view
        """
        return reverse('user:view', kwargs={'user_id': self.pk})

    def get_update_url(self):
        """
        returns a reverse url for updating user pk
        """
        return reverse('user:update', kwargs={'user_id': self.pk})

    def get_short_name(self):
        return self.username

    def __unicode__(self):
        return self.email
