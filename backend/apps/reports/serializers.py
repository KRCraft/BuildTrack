from decimal import Decimal
from rest_framework import serializers
from .models import DailyReport,DailyReportRevision,DailyReportMaterialUsage,DailyReportAttachment
class UsageSerializer(serializers.ModelSerializer):
 material_name=serializers.CharField(source="material.name",read_only=True);location_name=serializers.CharField(source="inventory_location.name",read_only=True)
 class Meta:model=DailyReportMaterialUsage;fields=("id","material","material_name","inventory_location","location_name","quantity_used","material_transaction");read_only_fields=("id","material_transaction","material_name","location_name")
class RevisionSerializer(serializers.ModelSerializer):
 material_usages=UsageSerializer(many=True,read_only=True)
 class Meta:model=DailyReportRevision;fields=("id","revision_number","status","work_completed","progress_delta","worker_count","issues","weather_notes","submitted_by","approved_by","submitted_at","approved_at","revision_reason","version","material_usages","created_at","updated_at");read_only_fields=("id","revision_number","status","submitted_by","approved_by","submitted_at","approved_at","version","material_usages","created_at","updated_at")
class ReportSerializer(serializers.ModelSerializer):
 approved_revision=RevisionSerializer(read_only=True);revisions=RevisionSerializer(many=True,read_only=True)
 class Meta:model=DailyReport;fields=("id","project","report_date","approved_revision","revisions","created_at");read_only_fields=fields
class NoteSerializer(serializers.Serializer):reason=serializers.CharField(required=False,allow_blank=True,max_length=2000)
class AttachmentSerializer(serializers.Serializer):
 file=serializers.FileField()
 def validate_file(self,f):
  if f.content_type not in {"application/pdf","image/jpeg","image/png"}:raise serializers.ValidationError("Only PDF, JPG, JPEG, and PNG files are allowed.")
  if f.size>10*1024*1024:raise serializers.ValidationError("Files must be 10 MB or smaller.")
  return f
