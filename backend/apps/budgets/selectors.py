from decimal import Decimal

from django.db.models import DecimalField, Sum, Value
from django.db.models.functions import Coalesce

from .models import BudgetCategory, BudgetVersion

MONEY = DecimalField(max_digits=19, decimal_places=4)
ZERO = Value(Decimal("0"), output_field=MONEY)


def approved_budget_version(project):
    return getattr(getattr(project, "budget", None), "active_version", None)


def actual_spend_queryset(project):
    # Imported here to keep the budget app independent during app initialization.
    from apps.expenses.models import Expense
    return Expense.objects.filter(project=project, status=Expense.Status.APPROVED)


def project_actual_spend(project):
    from apps.expenses.models import Expense
    # Django's conditional aggregate needs Q, keeping the arithmetic explicit avoids floats.
    from django.db.models import Q
    standard = actual_spend_queryset(project).filter(expense_type=Expense.Type.STANDARD).aggregate(total=Coalesce(Sum("amount"), ZERO))["total"]
    reversal = actual_spend_queryset(project).filter(expense_type=Expense.Type.REVERSAL).aggregate(total=Coalesce(Sum("amount"), ZERO))["total"]
    return standard - reversal


def category_spend(version):
    from apps.expenses.models import Expense
    expenses = Expense.objects.filter(project=version.budget.project, status=Expense.Status.APPROVED)
    standard = expenses.filter(expense_type=Expense.Type.STANDARD).values("budget_category").annotate(total=Coalesce(Sum("amount"), ZERO))
    reversal = expenses.filter(expense_type=Expense.Type.REVERSAL).values("budget_category").annotate(total=Coalesce(Sum("amount"), ZERO))
    totals = {row["budget_category"]: row["total"] for row in standard}
    for row in reversal:
        totals[row["budget_category"]] = totals.get(row["budget_category"], Decimal("0")) - row["total"]
    return totals


def project_financial_summary(project):
    active = approved_budget_version(project)
    planned = active.total_planned_amount if active else Decimal("0")
    actual = project_actual_spend(project)
    remaining = planned - actual
    variance = actual - planned
    utilization = (actual / planned * Decimal("100")) if planned else Decimal("0")
    return {"approved_budget": planned, "approved_actual_spend": actual, "remaining_budget": remaining, "variance_amount": variance, "variance_percentage": utilization}


def category_financial_rows(version):
    spend = category_spend(version)
    return [{"category": category, "actual_spend": spend.get(category.id, Decimal("0")), "remaining_amount": category.planned_amount - spend.get(category.id, Decimal("0")), "variance_amount": spend.get(category.id, Decimal("0")) - category.planned_amount} for category in version.categories.all()]
