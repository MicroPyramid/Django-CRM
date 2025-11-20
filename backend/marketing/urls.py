"""
Marketing App URLs
"""

from django.urls import path
from marketing import views

app_name = "marketing"

urlpatterns = [
    # Newsletter endpoints
    path(
        "newsletter/subscribers/",
        views.NewsletterSubscriberListView.as_view(),
        name="newsletter_subscribers"
    ),
    path(
        "newsletter/subscribe/",
        views.NewsletterSubscribeView.as_view(),
        name="newsletter_subscribe"
    ),
    path(
        "newsletter/unsubscribe/",
        views.NewsletterUnsubscribeView.as_view(),
        name="newsletter_unsubscribe"
    ),
    path(
        "newsletter/confirm/",
        views.NewsletterConfirmView.as_view(),
        name="newsletter_confirm"
    ),

    # Contact form endpoints
    path(
        "contact/submissions/",
        views.ContactFormSubmissionListView.as_view(),
        name="contact_submissions"
    ),
    path(
        "contact/submissions/<str:pk>/",
        views.ContactFormSubmissionDetailView.as_view(),
        name="contact_submission_detail"
    ),
    path(
        "contact/submit/",
        views.ContactFormSubmitView.as_view(),
        name="contact_submit"
    ),
]
