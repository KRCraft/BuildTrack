from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.audit.services import audit_event
from apps.common.tenant import request_company
from apps.companies.models import CompanyMembership
from .models import Project, ProjectAssignment
from .serializers import ProjectAssignmentSerializer, ProjectSerializer


def company_projects(request):
    company = request_company(request)
    if request.membership.role in (CompanyMembership.Role.OWNER, CompanyMembership.Role.ACCOUNTANT):
        return Project.objects.filter(company=company)
    return Project.objects.filter(company=company, assignments__membership=request.membership, assignments__is_active=True).distinct()


def project_or_404(request, project_id):
    project = company_projects(request).filter(id=project_id).first()
    if not project:
        raise NotFound("Project was not found.")
    return project


def can_manage_project(request, project):
    if request.membership.role == CompanyMembership.Role.OWNER:
        return True
    return ProjectAssignment.objects.filter(project=project, membership=request.membership, assignment_role=ProjectAssignment.AssignmentRole.PROJECT_MANAGER, is_active=True).exists()


class ProjectListCreateView(APIView):
    def get(self, request):
        queryset = company_projects(request)
        status_filter = request.query_params.get("status")
        search = request.query_params.get("search")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if search:
            queryset = queryset.filter(Q(name__icontains=search) | Q(code__icontains=search) | Q(client_name__icontains=search))
        queryset = queryset.distinct().order_by("-created_at")
        # Paginated (keeps bare array for backwards compat if ?paginate=false)
        if request.query_params.get("paginate") == "false":
            return Response(ProjectSerializer(queryset, many=True).data)
        page = PageNumberPagination()
        page.page_size = 25
        result = page.paginate_queryset(queryset, request)
        if result is not None:
            return page.get_paginated_response(ProjectSerializer(result, many=True).data)
        return Response(ProjectSerializer(queryset, many=True).data)

    @transaction.atomic
    def post(self, request):
        company = request_company(request)
        if request.membership.role not in (CompanyMembership.Role.OWNER, CompanyMembership.Role.PROJECT_MANAGER):
            raise PermissionDenied("Only owners and project managers can create projects.")
        serializer = ProjectSerializer(data=request.data, context={"company": company})
        serializer.is_valid(raise_exception=True)
        project = serializer.save(company=company, created_by=request.user)
        if request.membership.role == CompanyMembership.Role.PROJECT_MANAGER:
            ProjectAssignment.objects.get_or_create(project=project, membership=request.membership, assignment_role=ProjectAssignment.AssignmentRole.PROJECT_MANAGER)
        audit_event(request, company, "project.created", project, after_state=ProjectSerializer(project).data)
        return Response(ProjectSerializer(project).data, status=status.HTTP_201_CREATED)


class ProjectDetailView(APIView):
    def get(self, request, project_id):
        return Response(ProjectSerializer(project_or_404(request, project_id)).data)

    @transaction.atomic
    def patch(self, request, project_id):
        project = project_or_404(request, project_id)
        if not can_manage_project(request, project):
            raise PermissionDenied("You cannot update this project.")
        before = ProjectSerializer(project).data
        serializer = ProjectSerializer(project, data=request.data, partial=True, context={"company": project.company})
        serializer.is_valid(raise_exception=True)
        project = serializer.save()
        audit_event(request, project.company, "project.updated", project, before_state=before, after_state=ProjectSerializer(project).data)
        return Response(ProjectSerializer(project).data)


class ProjectArchiveView(APIView):
    @transaction.atomic
    def post(self, request, project_id):
        project = project_or_404(request, project_id)
        if not can_manage_project(request, project):
            raise PermissionDenied("You cannot archive this project.")
        before = ProjectSerializer(project).data
        project.status, project.is_archived, project.version = Project.Status.ARCHIVED, True, project.version + 1
        project.save(update_fields=["status", "is_archived", "version", "updated_at"])
        audit_event(request, project.company, "project.archived", project, before_state=before, after_state=ProjectSerializer(project).data)
        return Response(ProjectSerializer(project).data)


class ProjectAssignmentListCreateView(APIView):
    def get(self, request, project_id):
        project = project_or_404(request, project_id)
        return Response(ProjectAssignmentSerializer(project.assignments.select_related("membership__user").all(), many=True, context={"project": project}).data)

    @transaction.atomic
    def post(self, request, project_id):
        project = project_or_404(request, project_id)
        if not can_manage_project(request, project):
            raise PermissionDenied("You cannot manage project assignments.")
        serializer = ProjectAssignmentSerializer(data=request.data, context={"project": project})
        serializer.is_valid(raise_exception=True)
        assignment = serializer.save(project=project)
        audit_event(request, project.company, "project.assignment_created", assignment, after_state=ProjectAssignmentSerializer(assignment, context={"project": project}).data)
        return Response(ProjectAssignmentSerializer(assignment, context={"project": project}).data, status=status.HTTP_201_CREATED)
