from django.urls import path
from .views import CompanyDashboardView, ProjectDashboardView

urlpatterns = [path("company/", CompanyDashboardView.as_view()), path("projects/<uuid:project_id>/", ProjectDashboardView.as_view())]
