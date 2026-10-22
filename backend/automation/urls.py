from django.urls import path

from automation import views

app_name = "api_automation"

urlpatterns = [
    path("catalogue/", views.CatalogueView.as_view(), name="catalogue"),
    path("rules/", views.RuleListCreateView.as_view(), name="rules"),
    path("rules/reorder/", views.RuleReorderView.as_view(), name="reorder"),
    path("rules/<uid:pk>/", views.RuleDetailView.as_view(), name="rule"),
    path("rules/<uid:pk>/try/", views.RuleTryView.as_view(), name="try"),
    path("rules/<uid:pk>/runs/", views.RuleRunListView.as_view(), name="runs"),
]
