from django.urls import path

from .views import (ExpenseApproveView, ExpenseAttachmentCreateView, ExpenseDetailView, ExpenseListCreateView, ExpenseRejectView, ExpenseReverseView, ExpenseSubmitView, SupplierDetailView, SupplierListCreateView)

urlpatterns = [
    path("suppliers/", SupplierListCreateView.as_view()), path("suppliers/<uuid:supplier_id>/", SupplierDetailView.as_view()),
    path("expenses/", ExpenseListCreateView.as_view()), path("expenses/<uuid:expense_id>/", ExpenseDetailView.as_view()),
    path("expenses/<uuid:expense_id>/submit/", ExpenseSubmitView.as_view()), path("expenses/<uuid:expense_id>/approve/", ExpenseApproveView.as_view()),
    path("expenses/<uuid:expense_id>/reject/", ExpenseRejectView.as_view()), path("expenses/<uuid:expense_id>/reverse/", ExpenseReverseView.as_view()),
    path("expenses/<uuid:expense_id>/attachments/", ExpenseAttachmentCreateView.as_view()),
]
