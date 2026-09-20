import uuid

from django.conf import settings
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.db.models import F, Q

from apps.common.models import UUIDTimeStampedModel


class Budget(UUIDTimeStampedModel):
    company = models.ForeignKey("companies.Company", on_delete=models.PROTECT, related_name="budgets")
    project = models.OneToOneField("projects.Project", on_delete=models.PROTECT, related_name="budget")
    active_version = models.ForeignKey("BudgetVersion", null=True, blank=True, on_delete=models.SET_NULL, related_name="active_for_budgets")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_budgets")

    class Meta:
        indexes = [models.Index(fields=["company", "project"])]


class BudgetVersion(UUIDTimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        PENDING_APPROVAL = "PENDING_APPROVAL", "Pending approval"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        SUPERSEDED = "SUPERSEDED", "Superseded"

    company = models.ForeignKey("companies.Company", on_delete=models.PROTECT, related_name="budget_versions")
    budget = models.ForeignKey(Budget, on_delete=models.PROTECT, related_name="versions")
    version_number = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    currency_code = models.CharField(max_length=3, validators=[RegexValidator(r"^[A-Z]{3}$")])
    total_planned_amount = models.DecimalField(max_digits=19, decimal_places=4, default=0, validators=[MinValueValidator(0)])
    submitted_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    superseded_at = models.DateTimeField(null=True, blank=True)
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="submitted_budget_versions")
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="approved_budget_versions")
    approval_note = models.TextField(blank=True)
    version = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["-version_number"]
        constraints = [
            models.UniqueConstraint(fields=["budget", "version_number"], name="budget_unique_version_number"),
            models.CheckConstraint(condition=Q(total_planned_amount__gte=0), name="budget_version_total_nonnegative"),
        ]
        indexes = [models.Index(fields=["company", "status"]), models.Index(fields=["budget", "status"])]

    def clean(self):
        if self.budget_id and self.company_id and self.budget.company_id != self.company_id:
            from django.core.exceptions import ValidationError
            raise ValidationError("Budget version company must match its budget company.")


class BudgetCategory(UUIDTimeStampedModel):
    company = models.ForeignKey("companies.Company", on_delete=models.PROTECT, related_name="budget_categories")
    budget_version = models.ForeignKey(BudgetVersion, on_delete=models.PROTECT, related_name="categories")
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.PROTECT, related_name="children")
    lineage_key = models.UUIDField(default=uuid.uuid4)
    code = models.CharField(max_length=64)
    name = models.CharField(max_length=255)
    planned_amount = models.DecimalField(max_digits=19, decimal_places=4, default=0, validators=[MinValueValidator(0)])
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort_order", "code"]
        constraints = [
            models.UniqueConstraint(fields=["budget_version", "code"], name="budget_category_unique_code"),
            models.UniqueConstraint(fields=["budget_version", "lineage_key"], name="budget_category_unique_lineage"),
            models.CheckConstraint(condition=Q(planned_amount__gte=0), name="budget_category_amount_nonnegative"),
        ]
        indexes = [models.Index(fields=["company", "budget_version"])]

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.company_id and self.budget_version_id and self.budget_version.company_id != self.company_id:
            raise ValidationError("Category company must match its budget version company.")
        if self.parent_id and self.parent.budget_version_id != self.budget_version_id:
            raise ValidationError("Parent category must belong to the same budget version.")
