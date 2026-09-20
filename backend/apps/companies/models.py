import hashlib
import uuid
from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Q
from apps.common.models import UUIDTimeStampedModel


class Company(UUIDTimeStampedModel):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=80, unique=True)
    currency_code = models.CharField(max_length=3, default="UZS", validators=[RegexValidator(r"^[A-Z]{3}$")])
    timezone = models.CharField(max_length=64, default="Asia/Tashkent")
    country_code = models.CharField(max_length=2, blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        indexes = [models.Index(fields=["is_active"])]

    def __str__(self):
        return self.name


class CompanyMembership(UUIDTimeStampedModel):
    class Role(models.TextChoices):
        OWNER = "OWNER", "Owner"
        PROJECT_MANAGER = "PROJECT_MANAGER", "Project manager"
        SITE_MANAGER = "SITE_MANAGER", "Site manager"
        ACCOUNTANT = "ACCOUNTANT", "Accountant"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"

    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name="memberships")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="company_memberships")
    role = models.CharField(max_length=32, choices=Role.choices)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)
    joined_at = models.DateTimeField(auto_now_add=True)
    deactivated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["company", "user"], name="unique_company_user_membership")]
        indexes = [models.Index(fields=["company", "status"]), models.Index(fields=["user", "status"])]


class CompanyInvitation(UUIDTimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        ACCEPTED = "ACCEPTED", "Accepted"
        REVOKED = "REVOKED", "Revoked"
        EXPIRED = "EXPIRED", "Expired"

    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name="invitations")
    email = models.EmailField()
    role = models.CharField(max_length=32, choices=CompanyMembership.Role.choices)
    token_hash = models.CharField(max_length=64, unique=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    expires_at = models.DateTimeField()
    invited_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="sent_invitations")

    class Meta:
        constraints = [models.UniqueConstraint(fields=["company", "email"], condition=Q(status="PENDING"), name="one_pending_invitation_per_email")]
        indexes = [models.Index(fields=["company", "status"])]

    @staticmethod
    def hash_token(raw_token):
        return hashlib.sha256(raw_token.encode()).hexdigest()
