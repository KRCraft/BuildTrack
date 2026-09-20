from django.urls import path

from .views import (BudgetCategoryCreateView, BudgetCategoryDetailView, BudgetVersionApproveView, BudgetVersionDetailView, BudgetVersionRejectView, BudgetVersionSubmitView, ProjectBudgetVersionCreateView, ProjectBudgetView)

urlpatterns = [
    path("projects/<uuid:project_id>/budget/", ProjectBudgetView.as_view()),
    path("projects/<uuid:project_id>/budget/versions/", ProjectBudgetVersionCreateView.as_view()),
    path("budget-versions/<uuid:version_id>/", BudgetVersionDetailView.as_view()),
    path("budget-versions/<uuid:version_id>/submit/", BudgetVersionSubmitView.as_view()),
    path("budget-versions/<uuid:version_id>/approve/", BudgetVersionApproveView.as_view()),
    path("budget-versions/<uuid:version_id>/reject/", BudgetVersionRejectView.as_view()),
    path("budget-versions/<uuid:version_id>/categories/", BudgetCategoryCreateView.as_view()),
    path("budget-categories/<uuid:category_id>/", BudgetCategoryDetailView.as_view()),
]
