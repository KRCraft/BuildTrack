from django.conf import settings
from django.db import models
from django.db.models import Q
from apps.common.models import UUIDTimeStampedModel
class Worker(UUIDTimeStampedModel):
 class Status(models.TextChoices): ACTIVE="ACTIVE","Active"; INACTIVE="INACTIVE","Inactive"
 company=models.ForeignKey("companies.Company",on_delete=models.PROTECT,related_name="workers");full_name=models.CharField(max_length=255);phone=models.CharField(max_length=64,blank=True);trade=models.CharField(max_length=128,blank=True);status=models.CharField(max_length=16,choices=Status.choices,default=Status.ACTIVE);notes=models.TextField(blank=True);created_by=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name="created_workers")
 class Meta: indexes=[models.Index(fields=["company","status"]),models.Index(fields=["company","trade"])]
class WorkerAssignment(UUIDTimeStampedModel):
 company=models.ForeignKey("companies.Company",on_delete=models.PROTECT,related_name="worker_assignments");worker=models.ForeignKey(Worker,on_delete=models.PROTECT,related_name="assignments");project=models.ForeignKey("projects.Project",on_delete=models.PROTECT,related_name="worker_assignments");role_on_project=models.CharField(max_length=128,blank=True);start_date=models.DateField();end_date=models.DateField(null=True,blank=True);is_active=models.BooleanField(default=True)
 class Meta:
  constraints=[models.UniqueConstraint(fields=["worker","project"],condition=Q(is_active=True),name="workforce_one_active_assignment")]
  indexes=[models.Index(fields=["company","project","is_active"])]
