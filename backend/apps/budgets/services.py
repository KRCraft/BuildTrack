from django.db import transaction
from django.db.models import F, Max, Sum
from django.utils import timezone

from .models import Budget, BudgetCategory, BudgetVersion


def refresh_total(version):
    total = version.categories.aggregate(value=Sum("planned_amount"))["value"] or 0
    BudgetVersion.objects.filter(id=version.id).update(total_planned_amount=total)
    version.total_planned_amount = total
    return version


@transaction.atomic
def create_revision(budget, actor):
    budget = Budget.objects.select_for_update().get(id=budget.id)
    source = budget.active_version or budget.versions.order_by("-version_number").first()
    if not source:
        raise ValueError("A budget needs a source version before it can be revised.")
    next_number = (budget.versions.aggregate(maximum=Max("version_number"))["maximum"] or 0) + 1
    revision = BudgetVersion.objects.create(company=budget.company, budget=budget, version_number=next_number, currency_code=source.currency_code)
    category_map = {}
    for category in source.categories.order_by("sort_order", "code"):
        category_map[category.id] = BudgetCategory.objects.create(company=budget.company, budget_version=revision, lineage_key=category.lineage_key, code=category.code, name=category.name, planned_amount=category.planned_amount, sort_order=category.sort_order, is_active=category.is_active)
    for category in source.categories.exclude(parent=None):
        clone = category_map[category.id]
        clone.parent = category_map[category.parent_id]
        clone.save(update_fields=["parent", "updated_at"])
    return refresh_total(revision)


@transaction.atomic
def approve_version(version, actor, note=""):
    version = BudgetVersion.objects.select_for_update().select_related("budget").get(id=version.id)
    budget = Budget.objects.select_for_update().get(id=version.budget_id)
    if version.status != BudgetVersion.Status.PENDING_APPROVAL:
        raise ValueError("Only submitted budget versions can be approved.")
    previous = budget.active_version
    now = timezone.now()
    if previous and previous.id != version.id and previous.status == BudgetVersion.Status.APPROVED:
        BudgetVersion.objects.filter(id=previous.id).update(status=BudgetVersion.Status.SUPERSEDED, superseded_at=now, version=F("version") + 1)
    version.status = BudgetVersion.Status.APPROVED
    version.approved_by, version.approved_at, version.approval_note, version.version = actor, now, note, version.version + 1
    version.save(update_fields=["status", "approved_by", "approved_at", "approval_note", "version", "updated_at"])
    budget.active_version = version
    budget.save(update_fields=["active_version", "updated_at"])
    return version
