import uuid

from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.services import audit_event
from apps.common.tenant import request_company
from apps.companies.models import CompanyMembership
from apps.projects.models import ProjectAssignment
from apps.projects.views import company_projects, project_or_404

from .models import Expense, ExpenseApproval, ExpenseAttachment, Supplier
from .serializers import (ApprovalInputSerializer, ExpenseAttachmentSerializer, ExpenseAttachmentUploadSerializer, ExpenseSerializer, SupplierSerializer)


def may_create_expense(request, project):
    role = request.membership.role
    if role in (CompanyMembership.Role.OWNER, CompanyMembership.Role.ACCOUNTANT):
        return True
    return ProjectAssignment.objects.filter(project=project, membership=request.membership, is_active=True, assignment_role__in=[ProjectAssignment.AssignmentRole.PROJECT_MANAGER, ProjectAssignment.AssignmentRole.SITE_MANAGER]).exists()


def expense_or_404(request, expense_id):
    company = request_company(request)
    expense = Expense.objects.select_related("project", "budget_category__budget_version__budget", "supplier").filter(id=expense_id, company=company, project__in=company_projects(request)).first()
    if not expense:
        raise NotFound("Expense was not found.")
    return expense


class SupplierListCreateView(APIView):
    def get(self, request):
        company = request_company(request)
        return Response(SupplierSerializer(Supplier.objects.filter(company=company), many=True).data)

    @transaction.atomic
    def post(self, request):
        company = request_company(request)
        if request.membership.role not in (CompanyMembership.Role.OWNER, CompanyMembership.Role.ACCOUNTANT):
            raise PermissionDenied("Only owners and accountants can manage suppliers.")
        serializer = SupplierSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        supplier = serializer.save(company=company)
        audit_event(request, company, "supplier.created", supplier, after_state=SupplierSerializer(supplier).data)
        return Response(SupplierSerializer(supplier).data, status=status.HTTP_201_CREATED)


class SupplierDetailView(APIView):
    def get_object(self, request, supplier_id):
        company = request_company(request)
        supplier = Supplier.objects.filter(id=supplier_id, company=company).first()
        if not supplier:
            raise NotFound("Supplier was not found.")
        return supplier

    def get(self, request, supplier_id):
        return Response(SupplierSerializer(self.get_object(request, supplier_id)).data)

    @transaction.atomic
    def patch(self, request, supplier_id):
        if request.membership.role not in (CompanyMembership.Role.OWNER, CompanyMembership.Role.ACCOUNTANT):
            raise PermissionDenied("Only owners and accountants can manage suppliers.")
        supplier = self.get_object(request, supplier_id)
        before = SupplierSerializer(supplier).data
        serializer = SupplierSerializer(supplier, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        supplier = serializer.save()
        audit_event(request, request.company, "supplier.updated", supplier, before_state=before, after_state=SupplierSerializer(supplier).data)
        return Response(SupplierSerializer(supplier).data)


class ExpenseListCreateView(APIView):
    def get(self, request):
        company = request_company(request)
        queryset = Expense.objects.select_related("project", "budget_category", "supplier").filter(company=company, project__in=company_projects(request))
        filters = {"project_id": "project_id", "status": "status", "category": "budget_category", "supplier": "supplier"}
        for key, field in filters.items():
            if request.query_params.get(key):
                queryset = queryset.filter(**{field: request.query_params[key]})
        if request.query_params.get("date_from"):
            queryset = queryset.filter(expense_date__gte=request.query_params["date_from"])
        if request.query_params.get("date_to"):
            queryset = queryset.filter(expense_date__lte=request.query_params["date_to"])
        page = PageNumberPagination()
        page.page_size = 25
        result = page.paginate_queryset(queryset, request)
        return page.get_paginated_response(ExpenseSerializer(result, many=True).data)

    @transaction.atomic
    def post(self, request):
        company = request_company(request)
        raw_key = request.headers.get("Idempotency-Key")
        if raw_key:
            try:
                key = uuid.UUID(raw_key)
            except ValueError as exc:
                raise ValidationError({"Idempotency-Key": "Must be a UUID."}) from exc
            existing = Expense.objects.filter(company=company, idempotency_key=key).first()
            if existing:
                return Response(ExpenseSerializer(existing).data, status=status.HTTP_200_OK)
        else:
            key = None
        serializer = ExpenseSerializer(data=request.data, context={"company": company, "request": request})
        serializer.is_valid(raise_exception=True)
        project = serializer.validated_data["project"]
        if not may_create_expense(request, project):
            raise PermissionDenied("You cannot create expenses for this project.")
        try:
            expense = serializer.save(company=company, idempotency_key=key)
        except IntegrityError:
            expense = Expense.objects.get(company=company, idempotency_key=key)
        audit_event(request, company, "expense.created", expense, after_state=ExpenseSerializer(expense).data)
        return Response(ExpenseSerializer(expense).data, status=status.HTTP_201_CREATED)


class ExpenseDetailView(APIView):
    def get(self, request, expense_id):
        return Response(ExpenseSerializer(expense_or_404(request, expense_id)).data)

    @transaction.atomic
    def patch(self, request, expense_id):
        expense = expense_or_404(request, expense_id)
        if expense.status != Expense.Status.DRAFT or expense.expense_type != Expense.Type.STANDARD:
            raise ValidationError("Only draft standard expenses can be edited.")
        if not may_create_expense(request, expense.project):
            raise PermissionDenied("You cannot edit this expense.")
        before = ExpenseSerializer(expense).data
        serializer = ExpenseSerializer(expense, data=request.data, partial=True, context={"company": request.company, "request": request})
        serializer.is_valid(raise_exception=True)
        expense = serializer.save(version=expense.version + 1)
        audit_event(request, request.company, "expense.updated", expense, before_state=before, after_state=ExpenseSerializer(expense).data)
        return Response(ExpenseSerializer(expense).data)


class ExpenseWorkflowView(APIView):
    action = None

    @transaction.atomic
    def post(self, request, expense_id):
        expense = expense_or_404(request, expense_id)
        expense = Expense.objects.select_for_update().get(id=expense.id, company=request.company)
        serializer = ApprovalInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = serializer.validated_data.get("comment", "")
        if self.action == "submit":
            if not may_create_expense(request, expense.project) or expense.status != Expense.Status.DRAFT:
                raise ValidationError("Only draft expenses you can manage can be submitted.")
            expense.status, expense.submitted_by, expense.version = Expense.Status.PENDING_APPROVAL, request.user, expense.version + 1
            event, audit_action = ExpenseApproval.Action.SUBMITTED, "expense.submitted"
        elif self.action in ("approve", "reject"):
            if request.membership.role not in (CompanyMembership.Role.OWNER, CompanyMembership.Role.ACCOUNTANT):
                raise PermissionDenied("Only owners and accountants can approve expenses.")
            if expense.status != Expense.Status.PENDING_APPROVAL:
                raise ValidationError("Only submitted expenses can be reviewed.")
            if expense.submitted_by_id == request.user.id:
                raise PermissionDenied("You cannot approve or reject your own expense.")
            if self.action == "approve":
                expense.status, expense.approved_by, expense.approved_at = Expense.Status.APPROVED, request.user, timezone.now()
                event, audit_action = ExpenseApproval.Action.APPROVED, "expense.approved"
            else:
                expense.status = Expense.Status.REJECTED
                event, audit_action = ExpenseApproval.Action.REJECTED, "expense.rejected"
            expense.version += 1
        else:
            raise NotFound()
        expense.save()
        ExpenseApproval.objects.create(expense=expense, action=event, actor=request.user, comment=comment)
        audit_event(request, request.company, audit_action, expense, after_state=ExpenseSerializer(expense).data)
        return Response(ExpenseSerializer(expense).data)


class ExpenseReverseView(APIView):
    @transaction.atomic
    def post(self, request, expense_id):
        expense = expense_or_404(request, expense_id)
        expense = Expense.objects.select_for_update().get(id=expense.id, company=request.company)
        if not may_create_expense(request, expense.project) or expense.status != Expense.Status.APPROVED or expense.expense_type != Expense.Type.STANDARD:
            raise ValidationError("Only approved standard expenses can be reversed.")
        if Expense.objects.select_for_update().filter(reverses_expense=expense).exclude(status=Expense.Status.REJECTED).exclude(status=Expense.Status.CANCELLED).exists():
            raise ValidationError("This expense already has a reversal in progress.")
        reversal = Expense.objects.create(company=expense.company, project=expense.project, budget_category=expense.budget_category, supplier=expense.supplier, expense_type=Expense.Type.REVERSAL, reverses_expense=expense, amount=expense.amount, currency_code=expense.currency_code, expense_date=timezone.localdate(), payment_method=expense.payment_method, description=f"Reversal of expense {expense.id}", correction_group_id=expense.correction_group_id)
        ExpenseApproval.objects.create(expense=expense, action=ExpenseApproval.Action.REVERSED, actor=request.user, comment=f"Reversal request {reversal.id} created.")
        audit_event(request, request.company, "expense.reversed", reversal, after_state=ExpenseSerializer(reversal).data)
        return Response(ExpenseSerializer(reversal).data, status=status.HTTP_201_CREATED)


class ExpenseAttachmentCreateView(APIView):
    @transaction.atomic
    def post(self, request, expense_id):
        expense = expense_or_404(request, expense_id)
        if not may_create_expense(request, expense.project):
            raise PermissionDenied("You cannot attach files to this expense.")
        serializer = ExpenseAttachmentUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        upload = serializer.validated_data["file"]
        attachment = ExpenseAttachment.objects.create(expense=expense, storage_key=upload, original_filename=upload.name, content_type=upload.content_type, size_bytes=upload.size, uploaded_by=request.user)
        return Response(ExpenseAttachmentSerializer(attachment).data, status=status.HTTP_201_CREATED)


class ExpenseSubmitView(ExpenseWorkflowView):
    action = "submit"


class ExpenseApproveView(ExpenseWorkflowView):
    action = "approve"


class ExpenseRejectView(ExpenseWorkflowView):
    action = "reject"
