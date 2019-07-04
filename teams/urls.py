from django.urls import path
from teams.views import (
    teams_list, team_create, team_edit, team_delete, team_detail
)


app_name = 'teams'


urlpatterns = [
    path('', teams_list, name='teams_list'),
    path('create/', team_create, name='team_create'),
    path('edit/<int:team_id>/', team_edit, name='team_edit'),
    path('delete/<int:team_id>/', team_delete, name='team_delete'),
    path('detail/<int:team_id>/', team_detail, name='team_detail'),

]
