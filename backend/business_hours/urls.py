from django.urls import path

from business_hours import views

app_name = "api_business_hours"

urlpatterns = [
    path("calendar/", views.BusinessCalendarView.as_view(), name="calendar_default"),
    path(
        "calendar/<uid:pk>/",
        views.BusinessCalendarView.as_view(),
        name="calendar_detail",
    ),
    path(
        "calendar/<uid:pk>/holidays/",
        views.BusinessHolidayListView.as_view(),
        name="holiday_list",
    ),
    path(
        "calendar/<uid:pk>/holidays/<uid:hid>/",
        views.BusinessHolidayDetailView.as_view(),
        name="holiday_detail",
    ),
]
