from django.urls import path

from business_hours import views

app_name = "api_business_hours"

urlpatterns = [
    path("calendar/", views.BusinessCalendarView.as_view(), name="calendar_default"),
    path(
        "calendar/<str:pk>/",
        views.BusinessCalendarView.as_view(),
        name="calendar_detail",
    ),
    path(
        "calendar/<str:pk>/holidays/",
        views.BusinessHolidayListView.as_view(),
        name="holiday_list",
    ),
    path(
        "calendar/<str:pk>/holidays/<str:hid>/",
        views.BusinessHolidayDetailView.as_view(),
        name="holiday_detail",
    ),
]
