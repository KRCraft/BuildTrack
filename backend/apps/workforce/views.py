from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import NotFound,PermissionDenied,ValidationError
from apps.common.tenant import request_company
from apps.companies.models import CompanyMembership
from apps.projects.views import project_or_404,can_manage_project
from apps.audit.services import audit_event
from .models import Worker,WorkerAssignment
from .serializers import WorkerSerializer,WorkerAssignmentSerializer
def worker(request,id):
 w=Worker.objects.filter(id=id,company=request_company(request)).first()
 if not w:raise NotFound("Worker was not found.")
 return w
class WorkerList(APIView):
 def get(self,r):
  c=request_company(r);q=Worker.objects.filter(company=c)
  for p,f in (("trade","trade"),("status","status")):
   if r.query_params.get(p):q=q.filter(**{f:r.query_params[p]})
  if r.query_params.get("project"):q=q.filter(assignments__project_id=r.query_params["project"],assignments__is_active=True)
  return Response(WorkerSerializer(q.distinct(),many=True).data)
 @transaction.atomic
 def post(self,r):
  c=request_company(r)
  if r.membership.role not in (CompanyMembership.Role.OWNER,CompanyMembership.Role.PROJECT_MANAGER):raise PermissionDenied("You cannot manage workers.")
  s=WorkerSerializer(data=r.data);s.is_valid(raise_exception=True);w=s.save(company=c,created_by=r.user);audit_event(r,c,"workforce.worker_created",w,after_state=WorkerSerializer(w).data);return Response(WorkerSerializer(w).data,status=201)
class WorkerDetail(APIView):
 def get(self,r,worker_id):return Response(WorkerSerializer(worker(r,worker_id)).data)
 @transaction.atomic
 def patch(self,r,worker_id):
  w=worker(r,worker_id)
  if r.membership.role not in (CompanyMembership.Role.OWNER,CompanyMembership.Role.PROJECT_MANAGER):raise PermissionDenied("You cannot manage workers.")
  before=WorkerSerializer(w).data;s=WorkerSerializer(w,data=r.data,partial=True);s.is_valid(raise_exception=True);w=s.save();audit_event(r,r.company,"workforce.worker_deactivated" if w.status==Worker.Status.INACTIVE else "workforce.worker_updated",w,before_state=before,after_state=WorkerSerializer(w).data);return Response(WorkerSerializer(w).data)
class AssignmentList(APIView):
 def get(self,r,worker_id):return Response(WorkerAssignmentSerializer(worker(r,worker_id).assignments.all(),many=True).data)
 @transaction.atomic
 def post(self,r,worker_id):
  w=worker(r,worker_id);s=WorkerAssignmentSerializer(data=r.data);s.is_valid(raise_exception=True);p=project_or_404(r,s.validated_data["project"].id)
  if not can_manage_project(r,p) or w.status!=Worker.Status.ACTIVE:raise PermissionDenied("You cannot make this assignment.")
  if p.company_id!=w.company_id:raise ValidationError("Worker and project must be in the same company.")
  a=s.save(worker=w,company=r.company);audit_event(r,r.company,"workforce.worker_assigned",a,after_state=WorkerAssignmentSerializer(a).data);return Response(WorkerAssignmentSerializer(a).data,status=201)
class ProjectWorkers(APIView):
 def get(self,r,project_id):
  p=project_or_404(r,project_id);return Response(WorkerAssignmentSerializer(WorkerAssignment.objects.filter(project=p,is_active=True),many=True).data)
