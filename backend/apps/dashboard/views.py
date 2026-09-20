from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Sum
from django.db.models.functions import Coalesce
from decimal import Decimal
from apps.audit.models import AuditLog
from apps.audit.serializers import AuditLogSerializer
from apps.projects.models import Project
from apps.projects.serializers import ProjectSerializer
from apps.projects.views import company_projects
from apps.companies.models import CompanyMembership
from apps.projects.views import project_or_404
from apps.budgets.selectors import project_financial_summary, category_financial_rows
from apps.expenses.models import Expense
from apps.expenses.serializers import ExpenseSerializer
from apps.inventory.models import InventoryBalance, InventoryTransfer, Material, MaterialTransaction
from apps.inventory.selectors import project_usage


class CompanyDashboardView(APIView):
    def get(self, request):
        projects = company_projects(request)
        company = request.company
        audit_logs = AuditLog.objects.filter(company=company).order_by("-created_at")[:10] if request.membership.role == CompanyMembership.Role.OWNER else AuditLog.objects.none()
        financial = [project_financial_summary(project) for project in projects.select_related("budget__active_version")]
        pending_expenses = Expense.objects.filter(company=company, project__in=projects, status=Expense.Status.PENDING_APPROVAL)
        material_totals = {row["material_id"]: row["total"] for row in InventoryBalance.objects.filter(company=company).values("material_id").annotate(total=Coalesce(Sum("quantity_on_hand"), Decimal("0")))}
        low_stock_items = []
        for material in Material.objects.filter(company=company, is_active=True):
            raw_total = material_totals.get(material.id, Decimal("0"))
            total = raw_total if isinstance(raw_total, Decimal) else Decimal(str(raw_total))
            minimum = material.minimum_stock_level
            if not isinstance(minimum, Decimal):
                minimum = Decimal(str(minimum))
            if total <= minimum:
                low_stock_items.append({
                    "id": str(material.id),
                    "name": material.name,
                    "code": material.code,
                    "total": str(total),
                    "minimum": str(minimum),
                })
        low_stock = len(low_stock_items)
        return Response({
            "company": {"id": str(company.id), "name": company.name, "currency_code": company.currency_code},
            "total_projects": projects.count(),
            "active_projects": projects.filter(status=Project.Status.ACTIVE).count(),
            "completed_projects": projects.filter(status=Project.Status.COMPLETED).count(),
            "archived_projects": projects.filter(status=Project.Status.ARCHIVED).count(),
            "recent_projects": ProjectSerializer(projects.order_by("-updated_at")[:6], many=True).data,
            "recent_audit_actions": AuditLogSerializer(audit_logs, many=True).data,
            "total_approved_budget": str(sum((item["approved_budget"] for item in financial), start=0)),
            "total_approved_spend": str(sum((item["approved_actual_spend"] for item in financial), start=0)),
            "projects_near_budget_threshold": sum(1 for item in financial if item["approved_budget"] and item["variance_percentage"] >= 80 and item["variance_percentage"] <= 100),
            "projects_over_budget": sum(1 for item in financial if item["approved_budget"] and item["approved_actual_spend"] > item["approved_budget"]),
            "pending_expense_approvals": pending_expenses.count(),
            "total_materials": Material.objects.filter(company=company, is_active=True).count(),
            "low_stock_count": low_stock,
            "low_stock_items": low_stock_items,
            "active_transfers": InventoryTransfer.objects.filter(company=company, status__in=[InventoryTransfer.Status.DISPATCHED, InventoryTransfer.Status.PARTIALLY_RECEIVED]).count(),
            "recent_stock_movements": MaterialTransaction.objects.filter(company=company).order_by("-occurred_at").values("id", "transaction_type", "quantity", "occurred_at")[:6],
        })


class ProjectDashboardView(APIView):
    def get(self, request, project_id):
        project = project_or_404(request, project_id)
        summary = project_financial_summary(project)
        active = getattr(getattr(project, "budget", None), "active_version", None)
        rows = category_financial_rows(active) if active else []
        pending = Expense.objects.filter(project=project, status=Expense.Status.PENDING_APPROVAL)
        recent = Expense.objects.filter(project=project).select_related("supplier", "budget_category", "project")[:8]
        site_balances = InventoryBalance.objects.filter(company=request.company, location__project=project)
        usage = project_usage(project)
        return Response({
            "project": ProjectSerializer(project).data,
            "financial_summary": {key: str(value) for key, value in summary.items()},
            "category_spend": [{"category_id": str(row["category"].id), "category_name": row["category"].name, "planned_amount": str(row["category"].planned_amount), "actual_spend": str(row["actual_spend"]), "remaining_amount": str(row["remaining_amount"]), "variance_amount": str(row["variance_amount"])} for row in rows],
            "pending_expenses": pending.count(),
            "recent_expenses": ExpenseSerializer(recent, many=True).data,
            "project_inventory_count": site_balances.count(),
            "project_low_stock_count": sum(1 for balance in site_balances if balance.quantity_on_hand <= balance.material.minimum_stock_level),
            "recent_material_usage": list(usage.values("id", "material__name", "quantity", "occurred_at")[:6]),
            "incoming_transfers": InventoryTransfer.objects.filter(company=request.company, destination_location__project=project, status__in=[InventoryTransfer.Status.DISPATCHED, InventoryTransfer.Status.PARTIALLY_RECEIVED]).count(),
        })
