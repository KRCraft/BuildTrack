import uuid
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q

from apps.common.models import UUIDTimeStampedModel


class Material(UUIDTimeStampedModel):
    class Unit(models.TextChoices):
        PIECE = "PIECE", "Piece"; KG = "KG", "Kilogram"; TON = "TON", "Ton"; METER = "METER", "Meter"; M2 = "M2", "Square meter"; M3 = "M3", "Cubic meter"; LITER = "LITER", "Liter"; BAG = "BAG", "Bag"; BOX = "BOX", "Box"; OTHER = "OTHER", "Other"
    company = models.ForeignKey("companies.Company", on_delete=models.PROTECT, related_name="materials")
    code = models.CharField(max_length=64)
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=128, blank=True)
    unit = models.CharField(max_length=16, choices=Unit.choices)
    minimum_stock_level = models.DecimalField(max_digits=19, decimal_places=4, default=0, validators=[MinValueValidator(Decimal("0"))])
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_materials")
    class Meta:
        ordering = ["name"]
        constraints = [models.UniqueConstraint(fields=["company", "code"], name="inventory_material_company_code"), models.CheckConstraint(condition=Q(minimum_stock_level__gte=0), name="inventory_material_minimum_nonnegative")]
        indexes = [models.Index(fields=["company", "is_active"])]


class InventoryLocation(UUIDTimeStampedModel):
    class Type(models.TextChoices):
        WAREHOUSE = "WAREHOUSE", "Warehouse"; PROJECT_SITE = "PROJECT_SITE", "Project site"; TRANSIT = "TRANSIT", "Transit"
    company = models.ForeignKey("companies.Company", on_delete=models.PROTECT, related_name="inventory_locations")
    project = models.ForeignKey("projects.Project", null=True, blank=True, on_delete=models.PROTECT, related_name="inventory_locations")
    name = models.CharField(max_length=255)
    location_type = models.CharField(max_length=16, choices=Type.choices)
    is_active = models.BooleanField(default=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=["company", "name"], name="inventory_location_company_name")]
        indexes = [models.Index(fields=["company", "location_type", "is_active"]), models.Index(fields=["company", "project"])]


class InventoryTransfer(UUIDTimeStampedModel):
    class Purpose(models.TextChoices):
        TRANSFER = "TRANSFER", "Transfer"; ALLOCATION = "ALLOCATION", "Allocation"; RETURN = "RETURN", "Return"
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"; DISPATCHED = "DISPATCHED", "Dispatched"; PARTIALLY_RECEIVED = "PARTIALLY_RECEIVED", "Partially received"; RECEIVED = "RECEIVED", "Received"; CANCELLED = "CANCELLED", "Cancelled"
    company = models.ForeignKey("companies.Company", on_delete=models.PROTECT, related_name="inventory_transfers")
    source_location = models.ForeignKey(InventoryLocation, on_delete=models.PROTECT, related_name="outgoing_transfers")
    destination_location = models.ForeignKey(InventoryLocation, on_delete=models.PROTECT, related_name="incoming_transfers")
    purpose = models.CharField(max_length=16, choices=Purpose.choices, default=Purpose.TRANSFER)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="requested_inventory_transfers")
    dispatched_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="dispatched_inventory_transfers")
    received_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="received_inventory_transfers")
    dispatched_at = models.DateTimeField(null=True, blank=True); received_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True); version = models.PositiveIntegerField(default=1)
    dispatch_idempotency_key = models.UUIDField(null=True, blank=True); receive_idempotency_key = models.UUIDField(null=True, blank=True)
    class Meta:
        indexes = [models.Index(fields=["company", "status"]), models.Index(fields=["company", "source_location"])]
        constraints = [models.CheckConstraint(condition=~Q(source_location=models.F("destination_location")), name="inventory_transfer_locations_differ")]


class InventoryTransferItem(UUIDTimeStampedModel):
    transfer = models.ForeignKey(InventoryTransfer, on_delete=models.PROTECT, related_name="items")
    material = models.ForeignKey(Material, on_delete=models.PROTECT, related_name="transfer_items")
    quantity_requested = models.DecimalField(max_digits=19, decimal_places=4, validators=[MinValueValidator(Decimal("0"))])
    quantity_dispatched = models.DecimalField(max_digits=19, decimal_places=4, default=0, validators=[MinValueValidator(Decimal("0"))])
    quantity_received = models.DecimalField(max_digits=19, decimal_places=4, default=0, validators=[MinValueValidator(Decimal("0"))])
    class Meta:
        constraints = [models.UniqueConstraint(fields=["transfer", "material"], name="inventory_transfer_one_material"), models.CheckConstraint(condition=Q(quantity_requested__gte=0) & Q(quantity_dispatched__gte=0) & Q(quantity_received__gte=0), name="inventory_transfer_item_nonnegative")]


class InventoryBalance(UUIDTimeStampedModel):
    company = models.ForeignKey("companies.Company", on_delete=models.PROTECT, related_name="inventory_balances")
    material = models.ForeignKey(Material, on_delete=models.PROTECT, related_name="balances")
    location = models.ForeignKey(InventoryLocation, on_delete=models.PROTECT, related_name="balances")
    quantity_on_hand = models.DecimalField(max_digits=19, decimal_places=4, default=0)
    class Meta:
        constraints = [models.UniqueConstraint(fields=["company", "material", "location"], name="inventory_unique_balance")]
        indexes = [models.Index(fields=["company", "location"]), models.Index(fields=["company", "material"])]


class MaterialTransaction(models.Model):
    class Type(models.TextChoices):
        RECEIVE="RECEIVE","Receive"; TRANSFER_OUT="TRANSFER_OUT","Transfer out"; TRANSFER_IN="TRANSFER_IN","Transfer in"; ALLOCATE_OUT="ALLOCATE_OUT","Allocate out"; ALLOCATE_IN="ALLOCATE_IN","Allocate in"; USE="USE","Use"; RETURN_OUT="RETURN_OUT","Return out"; RETURN_IN="RETURN_IN","Return in"; ADJUSTMENT_IN="ADJUSTMENT_IN","Adjustment in"; ADJUSTMENT_OUT="ADJUSTMENT_OUT","Adjustment out"; REVERSAL="REVERSAL","Reversal"
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey("companies.Company", on_delete=models.PROTECT, related_name="material_transactions")
    material = models.ForeignKey(Material, on_delete=models.PROTECT, related_name="transactions")
    location = models.ForeignKey(InventoryLocation, on_delete=models.PROTECT, related_name="transactions")
    transaction_type = models.CharField(max_length=20, choices=Type.choices)
    quantity = models.DecimalField(max_digits=19, decimal_places=4, validators=[MinValueValidator(Decimal("0.0001"))])
    signed_quantity = models.DecimalField(max_digits=19, decimal_places=4)
    transfer = models.ForeignKey(InventoryTransfer, null=True, blank=True, on_delete=models.PROTECT, related_name="transactions")
    transfer_item = models.ForeignKey(InventoryTransferItem, null=True, blank=True, on_delete=models.PROTECT, related_name="transactions")
    project = models.ForeignKey("projects.Project", null=True, blank=True, on_delete=models.PROTECT, related_name="material_transactions")
    reversal_of = models.OneToOneField("self", null=True, blank=True, on_delete=models.PROTECT, related_name="reversal_transaction")
    reference_type = models.CharField(max_length=64, blank=True); reference_id = models.UUIDField(null=True, blank=True)
    idempotency_key = models.UUIDField(null=True, blank=True)
    occurred_at = models.DateTimeField(); recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="recorded_material_transactions")
    reason = models.TextField(blank=True); created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ["-occurred_at", "-created_at"]
        constraints = [models.CheckConstraint(condition=Q(quantity__gt=0), name="inventory_transaction_quantity_positive"), models.UniqueConstraint(fields=["company", "idempotency_key"], condition=Q(idempotency_key__isnull=False), name="inventory_transaction_idempotency")]
        indexes = [models.Index(fields=["company", "material", "location"]), models.Index(fields=["company", "project", "occurred_at"]), models.Index(fields=["company", "transaction_type"])]
