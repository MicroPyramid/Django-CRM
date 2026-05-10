"""URL patterns mounted at ``/api/time-entries/`` (entry-scoped + timesheet).

Case-scoped patterns live in ``cases/urls.py``.
"""

from django.urls import path

from cases import time_views

app_name = "api_time_entries"

urlpatterns = [
    # Timesheet must come before <str:pk>/ to avoid the catchall.
    path(
        "timesheet/",
        time_views.TimesheetView.as_view(),
        name="time_entries_timesheet",
    ),
    path(
        "unbilled/",
        time_views.UnbilledEntriesView.as_view(),
        name="time_entries_unbilled",
    ),
    path(
        "<str:pk>/stop/",
        time_views.TimeEntryStopView.as_view(),
        name="time_entry_stop",
    ),
    path(
        "<str:pk>/",
        time_views.TimeEntryDetailView.as_view(),
        name="time_entry_detail",
    ),
]
