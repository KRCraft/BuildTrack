import uuid
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.db.models import Q

from apps.common.models import UUIDTimeStampedModel


class Supplier(UUIDTimeStampedModel):
    company = models.ForeignKey("companies.Company", on_delete=models.PROTECT, related_name="suppliers")
    name = models.CharField(max_length=255)
    tax_id = models.CharField(max_length=64, blank=True)
    phone = models.CharField(max_length=64, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["company", "name"], name="supplier_unique_company_name")]
        indexes = [models.Index(fields=["company", "is_active"])]


class Expense(UUIDTimeStampedModel):
    class Type(models.TextChoices):
        STANDARD = "STANDARD", "Standard"
        REVERSAL = "REVERSAL", "Reversal"

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        PENDING_APPROVAL = "PENDING_APPROVAL", "Pending approval"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        CANCELLED = "CANCELLED", "Cancelled"

    class PaymentMethod(models.TextChoices):
        CASH = "CASH", "Cash"
        BANK_TRANSFER = "BANK_TRANSFER", "Bank transfer"
        CARD = "CARD", "Card"
        OTHER = "OTHER", "Other"

    company = models.ForeignKey("companies.Company", on_delete=models.PROTECT, related_name="expenses")
    project = models.ForeignKey("projects.Project", on_delete=models.PROTECT, related_name="expenses")
    budget_category = models.ForeignKey("budgets.BudgetCategory", on_delete=models.PROTECT, related_name="expenses")
    supplier = models.ForeignKey(Supplier, null=True, blank=True, on_delete=models.PROTECT, related_name="expenses")
    expense_type = models.CharField(max_length=16, choices=Type.choices, default=Type.STANDARD)
    reverses_expense = models.ForeignKey("self", null=True, blank=True, on_delete=models.PROTECT, related_name="reversal_expenses")
    amount = models.DecimalField(max_digits=19, decimal_places=4, validators=[MinValueValidator(Decimal("0.0001"))])
    currency_code = models.CharField(max_length=3, validators=[RegexValidator(r"^[A-Z]{3}$")])
    expense_date = models.DateField()
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="submitted_expenses")
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="approved_expenses")
    approved_at = models.DateTimeField(null=True, blank=True)
    idempotency_key = models.UUIDField(null=True, blank=True)
    correction_group_id = models.UUIDField(default=uuid.uuid4, editable=False)
    version = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["-expense_date", "-created_at"]
        constraints = [
            models.CheckConstraint(condition=Q(amount__gt=0), name="expense_amount_positive"),
            models.UniqueConstraint(fields=["company", "idempotency_key"], condition=Q(idempotency_key__isnull=False), name="expense_company_idempotency_key"),
        ]
        indexes = [models.Index(fields=["company", "status"]), models.Index(fields=["company", "project", "expense_date"]), models.Index(fields=["budget_category", "status"])]


class ExpenseApproval(models.Model):
    class Action(models.TextChoices):
        SUBMITTED = "SUBMITTED", "Submitted"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        REVERSED = "REVERSED", "Reversed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    expense = models.ForeignKey(Expense, on_delete=models.PROTECT, related_name="approval_history")
    action = models.CharField(max_length=16, choices=Action.choices)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT, related_name="expense_approval_actions")
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]


def attachment_path(instance, filename):
    return f"expense_attachments/{instance.expense.company_id}/{instance.expense_id}/{filename}"


class ExpenseAttachment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    expense = models.ForeignKey(Expense, on_delete=models.PROTECT, related_name="attachments")
    storage_key = models.FileField(upload_to=attachment_path)
    original_filename = models.CharField(max_length=255)
    content_type = models.CharField(max_length=127)
    size_bytes = models.PositiveBigIntegerField()
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="uploaded_expense_attachments")
    uploaded_at = models.DateTimeField(auto_now_add=True)
