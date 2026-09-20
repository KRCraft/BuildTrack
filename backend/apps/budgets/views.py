from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.services import audit_event
from apps.common.tenant import request_company
from apps.companies.models import CompanyMembership
from apps.projects.views import can_manage_project, project_or_404

from .models import Budget, BudgetCategory, BudgetVersion
from .serializers import ApprovalSerializer, BudgetCategorySerializer, BudgetSerializer, BudgetVersionSerializer
from .services import approve_version, create_revision, refresh_total


def budget_or_404(request, budget_id):
    company = request_company(request)
    budget = Budget.objects.select_related("project", "active_version").filter(id=budget_id, company=company).first()
    if not budget:
        raise NotFound("Budget was not found.")
    project_or_404(request, budget.project_id)
    return budget


def version_or_404(request, version_id):
    company = request_company(request)
    version = BudgetVersion.objects.select_related("budget__project", "budget", "company").filter(id=version_id, company=company).first()
    if not version:
        raise NotFound("Budget version was not found.")
    project_or_404(request, version.budget.project_id)
    return version


def editable(request, version):
    if version.status != BudgetVersion.Status.DRAFT:
        raise ValidationError("Only draft budget versions can be edited.")
    if not can_manage_project(request, version.budget.project):
        raise PermissionDenied("You cannot edit this project budget.")


class ProjectBudgetView(APIView):
     def get(self, request, project_id):
         project = project_or_404(request, project_id)
         budget = Budget.objects.select_related("active_version").filter(project=project, company=request.company).first()
         if not budget:
             raise NotFound("Budget was not found for this project.")
         return Response(BudgetSerializer(budget).data)

    @transaction.atomic
    def post(self, request, project_id):
        company = request_company(request)
        project = project_or_404(request, project_id)
        if not can_manage_project(request, project):
            raise PermissionDenied("You cannot create a budget for this project.")
        if Budget.objects.filter(project=project).exists():
            raise ValidationError("This project already has a budget.")
        budget = Budget.objects.create(company=company, project=project, created_by=request.user)
        version = BudgetVersion.objects.create(company=company, budget=budget, version_number=1, currency_code=company.currency_code)
        audit_event(request, company, "budget.created", budget, after_state=BudgetVersionSerializer(version).data)
        return Response(BudgetSerializer(budget).data, status=status.HTTP_201_CREATED)


class ProjectBudgetVersionCreateView(APIView):
    @transaction.atomic
    def post(self, request, project_id):
        project = project_or_404(request, project_id)
        if not can_manage_project(request, project):
            raise PermissionDenied("You cannot revise this project budget.")
        budget = Budget.objects.filter(project=project, company=request.company).first()
        if not budget:
            raise NotFound("Create the project budget before creating a revision.")
        try:
            version = create_revision(budget, request.user)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        audit_event(request, request.company, "budget.revision_created", version, after_state=BudgetVersionSerializer(version).data)
        return Response(BudgetVersionSerializer(version).data, status=status.HTTP_201_CREATED)


class BudgetVersionDetailView(APIView):
    def get(self, request, version_id):
        return Response(BudgetVersionSerializer(version_or_404(request, version_id)).data)

    @transaction.atomic
    def patch(self, request, version_id):
        version = version_or_404(request, version_id)
        editable(request, version)
        before = BudgetVersionSerializer(version).data
        serializer = BudgetVersionSerializer(version, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        version = serializer.save(version=version.version + 1)
        audit_event(request, request.company, "budget.updated", version, before_state=before, after_state=BudgetVersionSerializer(version).data)
        return Response(BudgetVersionSerializer(version).data)


class BudgetVersionSubmitView(APIView):
    @transaction.atomic
    def post(self, request, version_id):
        version = version_or_404(request, version_id)
        editable(request, version)
        refresh_total(version)
        version.status, version.submitted_at, version.submitted_by, version.version = BudgetVersion.Status.PENDING_APPROVAL, timezone.now(), request.user, version.version + 1
        version.save(update_fields=["status", "submitted_at", "submitted_by", "version", "updated_at"])
        audit_event(request, request.company, "budget.submitted", version, after_state=BudgetVersionSerializer(version).data)
        return Response(BudgetVersionSerializer(version).data)


class BudgetVersionApproveView(APIView):
    @transaction.atomic
    def post(self, request, version_id):
        version = version_or_404(request, version_id)
        if request.membership.role != CompanyMembership.Role.OWNER:
            raise PermissionDenied("Only company owners can approve budgets.")
        serializer = ApprovalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            version = approve_version(version, request.user, serializer.validated_data.get("approval_note", ""))
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        audit_event(request, request.company, "budget.approved", version, after_state=BudgetVersionSerializer(version).data)
        return Response(BudgetVersionSerializer(version).data)


class BudgetVersionRejectView(APIView):
    @transaction.atomic
    def post(self, request, version_id):
        version = version_or_404(request, version_id)
        if request.membership.role != CompanyMembership.Role.OWNER:
            raise PermissionDenied("Only company owners can reject budgets.")
        if version.status != BudgetVersion.Status.PENDING_APPROVAL:
            raise ValidationError("Only submitted budget versions can be rejected.")
        serializer = ApprovalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        version.status, version.approval_note, version.version = BudgetVersion.Status.REJECTED, serializer.validated_data.get("approval_note", ""), version.version + 1
        version.save(update_fields=["status", "approval_note", "version", "updated_at"])
        audit_event(request, request.company, "budget.rejected", version, after_state=BudgetVersionSerializer(version).data)
        return Response(BudgetVersionSerializer(version).data)


class BudgetCategoryCreateView(APIView):
    @transaction.atomic
    def post(self, request, version_id):
        version = version_or_404(request, version_id)
        editable(request, version)
        serializer = BudgetCategorySerializer(data=request.data, context={"budget_version": version})
        serializer.is_valid(raise_exception=True)
        category = serializer.save(company=request.company, budget_version=version)
        refresh_total(version)
        return Response(BudgetCategorySerializer(category).data, status=status.HTTP_201_CREATED)


class BudgetCategoryDetailView(APIView):
    def get_object(self, request, category_id):
        company = request_company(request)
        category = BudgetCategory.objects.select_related("budget_version__budget__project").filter(id=category_id, company=company).first()
        if not category:
            raise NotFound("Budget category was not found.")
        project_or_404(request, category.budget_version.budget.project_id)
        return category

    @transaction.atomic
    def patch(self, request, category_id):
        category = self.get_object(request, category_id)
        editable(request, category.budget_version)
        serializer = BudgetCategorySerializer(category, data=request.data, partial=True, context={"budget_version": category.budget_version})
        serializer.is_valid(raise_exception=True)
        category = serializer.save()
        refresh_total(category.budget_version)
        return Response(BudgetCategorySerializer(category).data)

    @transaction.atomic
    def delete(self, request, category_id):
        category = self.get_object(request, category_id)
        editable(request, category.budget_version)
        if category.children.exists():
            raise ValidationError("Delete child categories before deleting their parent.")
        version = category.budget_version
        category.delete()
        refresh_total(version)
        return Response(status=status.HTTP_204_NO_CONTENT)
