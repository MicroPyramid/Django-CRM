from django.urls import path

from django_ses.views import DashboardView


urlpatterns = [
    path('', DashboardView.as_view(), name='django_ses_stats'),
]
