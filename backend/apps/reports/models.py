import uuid
from decimal import Decimal
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from apps.common.models import UUIDTimeStampedModel
class DailyReport(UUIDTimeStampedModel):
 company=models.ForeignKey("companies.Company",on_delete=models.PROTECT,related_name="daily_reports");project=models.ForeignKey("projects.Project",on_delete=models.PROTECT,related_name="daily_reports");report_date=models.DateField();approved_revision=models.ForeignKey("DailyReportRevision",null=True,blank=True,on_delete=models.SET_NULL,related_name="approved_for_reports");created_by=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name="created_daily_reports")
 class Meta: constraints=[models.UniqueConstraint(fields=["project","report_date"],name="reports_one_per_project_date")]
class DailyReportRevision(UUIDTimeStampedModel):
 class Status(models.TextChoices): DRAFT="DRAFT","Draft";SUBMITTED="SUBMITTED","Submitted";APPROVED="APPROVED","Approved";REJECTED="REJECTED","Rejected";SUPERSEDED="SUPERSEDED","Superseded"
 company=models.ForeignKey("companies.Company",on_delete=models.PROTECT,related_name="daily_report_revisions");daily_report=models.ForeignKey(DailyReport,on_delete=models.PROTECT,related_name="revisions");revision_number=models.PositiveIntegerField();status=models.CharField(max_length=16,choices=Status.choices,default=Status.DRAFT);work_completed=models.TextField(blank=True);progress_delta=models.DecimalField(max_digits=7,decimal_places=2,default=0);worker_count=models.PositiveIntegerField(default=0);issues=models.TextField(blank=True);weather_notes=models.TextField(blank=True);submitted_by=models.ForeignKey(settings.AUTH_USER_MODEL,null=True,blank=True,on_delete=models.PROTECT,related_name="submitted_daily_revisions");approved_by=models.ForeignKey(settings.AUTH_USER_MODEL,null=True,blank=True,on_delete=models.PROTECT,related_name="approved_daily_revisions");submitted_at=models.DateTimeField(null=True,blank=True);approved_at=models.DateTimeField(null=True,blank=True);revision_reason=models.TextField(blank=True);version=models.PositiveIntegerField(default=1)
 class Meta: constraints=[models.UniqueConstraint(fields=["daily_report","revision_number"],name="reports_unique_revision_number")];indexes=[models.Index(fields=["company","status"])]
class DailyReportMaterialUsage(UUIDTimeStampedModel):
 daily_report_revision=models.ForeignKey(DailyReportRevision,on_delete=models.PROTECT,related_name="material_usages");material=models.ForeignKey("inventory.Material",on_delete=models.PROTECT);inventory_location=models.ForeignKey("inventory.InventoryLocation",on_delete=models.PROTECT);quantity_used=models.DecimalField(max_digits=19,decimal_places=4,validators=[MinValueValidator(Decimal("0.0001"))]);material_transaction=models.OneToOneField("inventory.MaterialTransaction",null=True,blank=True,on_delete=models.PROTECT,related_name="daily_report_usage")
 class Meta: constraints=[models.UniqueConstraint(fields=["daily_report_revision","material","inventory_location"],name="reports_unique_usage")]
class DailyReportAttachment(models.Model):
 id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False);daily_report_revision=models.ForeignKey(DailyReportRevision,on_delete=models.PROTECT,related_name="attachments");storage_key=models.FileField(upload_to="daily_report_attachments/");original_filename=models.CharField(max_length=255);content_type=models.CharField(max_length=127);size_bytes=models.PositiveBigIntegerField();uploaded_by=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT);uploaded_at=models.DateTimeField(auto_now_add=True)
