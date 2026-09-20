from django.urls import path
from .views import (AdjustmentView, BalanceListView, LocationDetailView, LocationListCreateView, MaterialDetailView, MaterialListCreateView, ReceiptView, TransactionListView, TransactionReverseView, TransferCancelView, TransferDetailView, TransferDispatchView, TransferListCreateView, TransferReceiveView, UsageView)

urlpatterns = [
    path("materials/", MaterialListCreateView.as_view()), path("materials/<uuid:material_id>/", MaterialDetailView.as_view()),
    path("inventory/locations/", LocationListCreateView.as_view()), path("inventory/locations/<uuid:location_id>/", LocationDetailView.as_view()),
    path("inventory/balances/", BalanceListView.as_view()), path("inventory/transactions/", TransactionListView.as_view()),
    path("inventory/receipts/", ReceiptView.as_view()), path("inventory/usage/", UsageView.as_view()), path("inventory/adjustments/", AdjustmentView.as_view()),
    path("inventory/transactions/<uuid:transaction_id>/reverse/", TransactionReverseView.as_view()),
    path("inventory/transfers/", TransferListCreateView.as_view()), path("inventory/transfers/<uuid:transfer_id>/", TransferDetailView.as_view()),
    path("inventory/transfers/<uuid:transfer_id>/dispatch/", TransferDispatchView.as_view()), path("inventory/transfers/<uuid:transfer_id>/receive/", TransferReceiveView.as_view()), path("inventory/transfers/<uuid:transfer_id>/cancel/", TransferCancelView.as_view()),
]
