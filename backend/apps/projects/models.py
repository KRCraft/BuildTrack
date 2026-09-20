from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from apps.common.models import UUIDTimeStampedModel


class Project(UUIDTimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        ACTIVE = "ACTIVE", "Active"
        ON_HOLD = "ON_HOLD", "On hold"
        COMPLETED = "COMPLETED", "Completed"
        ARCHIVED = "ARCHIVED", "Archived"

    company = models.ForeignKey("companies.Company", on_delete=models.PROTECT, related_name="projects")
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=64)
    client_name = models.CharField(max_length=255, blank=True)
    client_contact = models.JSONField(default=dict, blank=True)
    location = models.TextField(blank=True)
    planned_start_date = models.DateField(null=True, blank=True)
    planned_end_date = models.DateField(null=True, blank=True)
    actual_start_date = models.DateField(null=True, blank=True)
    actual_end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT)
    progress_percent_cache = models.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    is_archived = models.BooleanField(default=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_projects")
    version = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["company", "code"], name="unique_company_project_code"),
            models.CheckConstraint(condition=Q(planned_end_date__isnull=True) | Q(planned_start_date__isnull=True) | Q(planned_end_date__gte=models.F("planned_start_date")), name="project_planned_dates_valid"),
            models.CheckConstraint(condition=Q(actual_end_date__isnull=True) | Q(actual_start_date__isnull=True) | Q(actual_end_date__gte=models.F("actual_start_date")), name="project_actual_dates_valid"),
        ]
        indexes = [models.Index(fields=["company", "status"]), models.Index(fields=["company", "is_archived"]), models.Index(fields=["company", "planned_start_date"])]


class ProjectAssignment(UUIDTimeStampedModel):
    class AssignmentRole(models.TextChoices):
        PROJECT_MANAGER = "PROJECT_MANAGER", "Project manager"
        SITE_MANAGER = "SITE_MANAGER", "Site manager"
        ACCOUNTANT = "ACCOUNTANT", "Accountant"
        VIEWER = "VIEWER", "Viewer"

    project = models.ForeignKey(Project, on_delete=models.PROTECT, related_name="assignments")
    membership = models.ForeignKey("companies.CompanyMembership", on_delete=models.PROTECT, related_name="project_assignments")
    assignment_role = models.CharField(max_length=32, choices=AssignmentRole.choices)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["project", "membership", "assignment_role"], condition=Q(is_active=True), name="unique_active_project_assignment"),
            models.CheckConstraint(condition=Q(end_date__isnull=True) | Q(start_date__isnull=True) | Q(end_date__gte=models.F("start_date")), name="project_assignment_dates_valid"),
        ]
        indexes = [models.Index(fields=["project", "is_active"]), models.Index(fields=["membership", "is_active"])]
