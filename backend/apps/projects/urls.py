from django.urls import path
from .views import ProjectArchiveView, ProjectAssignmentListCreateView, ProjectDetailView, ProjectListCreateView

urlpatterns = [
    path("", ProjectListCreateView.as_view()), path("<uuid:project_id>/", ProjectDetailView.as_view()),
    path("<uuid:project_id>/archive/", ProjectArchiveView.as_view()), path("<uuid:project_id>/assignments/", ProjectAssignmentListCreateView.as_view()),
]
