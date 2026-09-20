from django.db import transaction
from django.db.models import Max
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import NotFound,PermissionDenied,ValidationError
from apps.common.tenant import request_company
from apps.companies.models import CompanyMembership
from apps.projects.views import project_or_404,can_manage_project
from apps.audit.services import audit_event
from apps.inventory.models import InventoryLocation,Material,MaterialTransaction
from apps.inventory.services import record_transaction
from .models import DailyReport,DailyReportRevision,DailyReportMaterialUsage,DailyReportAttachment
from .serializers import ReportSerializer,RevisionSerializer,UsageSerializer,NoteSerializer,AttachmentSerializer
def report(r,id):
 x=DailyReport.objects.select_related("project","approved_revision").filter(id=id,company=request_company(r)).first()
 if not x:raise NotFound("Daily report was not found.")
 project_or_404(r,x.project_id);return x
def revision(r,id):
 x=DailyReportRevision.objects.select_related("daily_report__project").filter(id=id,company=request_company(r)).first()
 if not x:raise NotFound("Daily report revision was not found.")
 project_or_404(r,x.daily_report.project_id);return x
def editable(r,x):
 if x.status!=x.Status.DRAFT:raise ValidationError("Only draft revisions can be edited.")
 if not can_manage_project(r,x.daily_report.project):raise PermissionDenied("You cannot edit this report.")
class Reports(APIView):
 def get(self,r,project_id):
  p=project_or_404(r,project_id);return Response(ReportSerializer(DailyReport.objects.filter(project=p),many=True).data)
 @transaction.atomic
 def post(self,r,project_id):
  from datetime import date as date_type
  import datetime
  c=request_company(r);p=project_or_404(r,project_id)
  if not can_manage_project(r,p):raise PermissionDenied("You cannot create reports.")
  date_raw=r.data.get("report_date")
  if not date_raw:raise ValidationError({"report_date":"report_date is required (YYYY-MM-DD)."})
  try:
   date=datetime.date.fromisoformat(str(date_raw))
  except ValueError:raise ValidationError({"report_date":"Invalid date format, use YYYY-MM-DD."})
  if DailyReport.objects.filter(project=p,report_date=date).exists():raise ValidationError("A report already exists for this project and date.")
  report=DailyReport.objects.create(company=c,project=p,report_date=date,created_by=r.user);rev=DailyReportRevision.objects.create(company=c,daily_report=report,revision_number=1,work_completed=r.data.get("work_completed",""),progress_delta=r.data.get("progress_delta",0),worker_count=r.data.get("worker_count",0),issues=r.data.get("issues",""),weather_notes=r.data.get("weather_notes",""));audit_event(r,c,"reports.report_created",report,after_state=RevisionSerializer(rev).data);return Response(ReportSerializer(report).data,status=201)
class ReportDetail(APIView):
 def get(self,r,report_id):return Response(ReportSerializer(report(r,report_id)).data)
class RevisionCreate(APIView):
 @transaction.atomic
 def post(self,r,report_id):
  d=report(r,report_id)
  if not can_manage_project(r,d.project):raise PermissionDenied("You cannot revise this report.")
  reason=r.data.get("revision_reason","")
  if not reason:raise ValidationError({"revision_reason":"A correction reason is required."})
   source=d.approved_revision or d.revisions.order_by("-revision_number").first()
   if not source:raise ValidationError("No source revision exists to create a new revision.")
   num=(d.revisions.aggregate(v=Max("revision_number"))["v"] or 0)+1;new=DailyReportRevision.objects.create(company=d.company,daily_report=d,revision_number=num,work_completed=source.work_completed,progress_delta=source.progress_delta,worker_count=source.worker_count,issues=source.issues,weather_notes=source.weather_notes,revision_reason=reason)
  for u in source.material_usages.all():DailyReportMaterialUsage.objects.create(daily_report_revision=new,material=u.material,inventory_location=u.inventory_location,quantity_used=u.quantity_used)
  audit_event(r,d.company,"reports.revision_created",new,after_state=RevisionSerializer(new).data);return Response(RevisionSerializer(new).data,status=201)
class RevisionDetail(APIView):
 def get(self,r,revision_id):return Response(RevisionSerializer(revision(r,revision_id)).data)
 @transaction.atomic
 def patch(self,r,revision_id):
  x=revision(r,revision_id);editable(r,x);s=RevisionSerializer(x,data=r.data,partial=True);s.is_valid(raise_exception=True)
  delta=s.validated_data.get("progress_delta",x.progress_delta)
  if delta<0 and (r.membership.role not in (CompanyMembership.Role.OWNER,CompanyMembership.Role.PROJECT_MANAGER) or not (s.validated_data.get("revision_reason") or x.revision_reason)):raise PermissionDenied("Negative progress requires PM/owner and a correction reason.")
  x=s.save(version=x.version+1);audit_event(r,r.company,"reports.report_updated",x,after_state=RevisionSerializer(x).data);return Response(RevisionSerializer(x).data)
class Submit(APIView):
 @transaction.atomic
 def post(self,r,revision_id):
  x=revision(r,revision_id);editable(r,x);x.status=x.Status.SUBMITTED;x.submitted_by=r.user;x.submitted_at=timezone.now();x.version+=1;x.save();audit_event(r,r.company,"reports.report_submitted",x,after_state=RevisionSerializer(x).data);return Response(RevisionSerializer(x).data)
class Approve(APIView):
 @transaction.atomic
 def post(self,r,revision_id):
  from apps.projects.models import Project as _Project
  x=revision(r,revision_id);x=DailyReportRevision.objects.select_for_update().select_related("daily_report__project").get(id=x.id);d=DailyReport.objects.select_for_update().get(id=x.daily_report_id);p=_Project.objects.select_for_update().get(id=x.daily_report.project_id)
  if r.membership.role not in (CompanyMembership.Role.OWNER,CompanyMembership.Role.PROJECT_MANAGER) or not can_manage_project(r,p):raise PermissionDenied("You cannot approve reports.")
  if x.status!=x.Status.SUBMITTED:raise ValidationError("Only submitted revisions can be approved.")
  old=d.approved_revision;old_delta=old.progress_delta if old else 0;new_progress=p.progress_percent_cache-old_delta+x.progress_delta
  if new_progress<0 or new_progress>100:raise ValidationError("Approved progress must remain between 0 and 100.")
  if old:
   for u in old.material_usages.select_related("material","inventory_location").all():
    if u.material_transaction_id:record_transaction(company=d.company,material=u.material,location=u.inventory_location,transaction_type=MaterialTransaction.Type.ADJUSTMENT_IN,quantity=u.quantity_used,actor=r.user,project=p,reason="Superseded daily report revision",reversal_of=u.material_transaction)
   old.status=old.Status.SUPERSEDED;old.save(update_fields=["status","updated_at"])
  for u in x.material_usages.select_related("material","inventory_location").all():
   txn,_=record_transaction(company=d.company,material=u.material,location=u.inventory_location,transaction_type=MaterialTransaction.Type.USE,quantity=u.quantity_used,actor=r.user,project=p,reason=f"Daily report {d.report_date}");u.material_transaction=txn;u.save(update_fields=["material_transaction","updated_at"])
  p.progress_percent_cache=new_progress;p.save(update_fields=["progress_percent_cache","updated_at"]);x.status=x.Status.APPROVED;x.approved_by=r.user;x.approved_at=timezone.now();x.save();d.approved_revision=x;d.save(update_fields=["approved_revision","updated_at"]);audit_event(r,d.company,"reports.report_approved",x,after_state=RevisionSerializer(x).data);return Response(RevisionSerializer(x).data)
class Reject(APIView):
 @transaction.atomic
 def post(self,r,revision_id):
  x=revision(r,revision_id)
  if r.membership.role not in (CompanyMembership.Role.OWNER,CompanyMembership.Role.PROJECT_MANAGER) or x.status!=x.Status.SUBMITTED:raise PermissionDenied("You cannot reject this revision.")
  x.status=x.Status.REJECTED;x.save(update_fields=["status","updated_at"]);audit_event(r,r.company,"reports.report_rejected",x,after_state=RevisionSerializer(x).data);return Response(RevisionSerializer(x).data)
class Usage(APIView):
 @transaction.atomic
 def post(self,r,revision_id):
  x=revision(r,revision_id);editable(r,x);s=UsageSerializer(data=r.data);s.is_valid(raise_exception=True);d=s.validated_data;mat=Material.objects.filter(id=d["material"].id,company=r.company).first();loc=InventoryLocation.objects.filter(id=d["inventory_location"].id,company=r.company,project=x.daily_report.project,location_type=InventoryLocation.Type.PROJECT_SITE).first()
  if not mat or not loc:raise ValidationError("Material usage must use this project's site location.")
  u=s.save(daily_report_revision=x);audit_event(r,r.company,"reports.material_usage_added",u,after_state=UsageSerializer(u).data);return Response(UsageSerializer(u).data,status=201)
class UsageDetail(APIView):
 def obj(self,r,id):
  u=DailyReportMaterialUsage.objects.select_related("daily_report_revision__daily_report__project").filter(id=id,daily_report_revision__company=request_company(r)).first()
  if not u:raise NotFound("Report material usage was not found.")
  editable(r,u.daily_report_revision);return u
 def patch(self,r,usage_id):
  u=self.obj(r,usage_id);s=UsageSerializer(u,data=r.data,partial=True);s.is_valid(raise_exception=True);return Response(UsageSerializer(s.save()).data)
 def delete(self,r,usage_id):self.obj(r,usage_id).delete();return Response(status=204)
