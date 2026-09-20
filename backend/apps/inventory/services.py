from decimal import Decimal

from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .models import InventoryBalance, MaterialTransaction

NEGATIVE_TYPES = {MaterialTransaction.Type.TRANSFER_OUT, MaterialTransaction.Type.ALLOCATE_OUT, MaterialTransaction.Type.USE, MaterialTransaction.Type.RETURN_OUT, MaterialTransaction.Type.ADJUSTMENT_OUT}


def signed_quantity(transaction_type, quantity):
    return -quantity if transaction_type in NEGATIVE_TYPES else quantity


def locked_balance(company, material, location):
    balance = InventoryBalance.objects.select_for_update().filter(company=company, material=material, location=location).first()
    if balance:
        return balance
    try:
        return InventoryBalance.objects.create(company=company, material=material, location=location, quantity_on_hand=Decimal("0"))
    except IntegrityError:
        return InventoryBalance.objects.select_for_update().get(company=company, material=material, location=location)


@transaction.atomic
def record_transaction(*, company, material, location, transaction_type, quantity, actor, project=None, transfer=None, transfer_item=None, occurred_at=None, reason="", reference_type="", reference_id=None, idempotency_key=None, reversal_of=None):
    if quantity <= 0:
        raise ValidationError("Quantity must be greater than zero.")
    if idempotency_key:
        existing = MaterialTransaction.objects.filter(company=company, idempotency_key=idempotency_key).first()
        if existing:
            return existing, False
    balance = locked_balance(company, material, location)
    signed = signed_quantity(transaction_type, quantity)
    if balance.quantity_on_hand + signed < 0:
        raise ValidationError({"quantity": f"Insufficient stock at {location.name}. Available: {balance.quantity_on_hand}."})
    transaction_record = MaterialTransaction.objects.create(company=company, material=material, location=location, transaction_type=transaction_type, quantity=quantity, signed_quantity=signed, project=project, transfer=transfer, transfer_item=transfer_item, occurred_at=occurred_at or timezone.now(), recorded_by=actor, reason=reason, reference_type=reference_type, reference_id=reference_id, idempotency_key=idempotency_key, reversal_of=reversal_of)
    balance.quantity_on_hand += signed
    balance.save(update_fields=["quantity_on_hand", "updated_at"])
    return transaction_record, True


def transfer_types(transfer):
    if transfer.purpose == transfer.Purpose.ALLOCATION:
        return MaterialTransaction.Type.ALLOCATE_OUT, MaterialTransaction.Type.ALLOCATE_IN
    if transfer.purpose == transfer.Purpose.RETURN:
        return MaterialTransaction.Type.RETURN_OUT, MaterialTransaction.Type.RETURN_IN
    return MaterialTransaction.Type.TRANSFER_OUT, MaterialTransaction.Type.TRANSFER_IN
