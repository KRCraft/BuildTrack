from decimal import Decimal
from django.db.models import Sum
from django.db.models.functions import Coalesce

from .models import InventoryBalance, MaterialTransaction


def balances(company, *, material=None, location=None, project=None, low_stock=False):
    queryset = InventoryBalance.objects.select_related("material", "location__project").filter(company=company)
    if material: queryset = queryset.filter(material_id=material)
    if location: queryset = queryset.filter(location_id=location)
    if project: queryset = queryset.filter(location__project_id=project)
    if low_stock:
        # MVP definition: total stock across all company locations compared with material.minimum_stock_level.
        totals = {row["material_id"]: row["total"] for row in InventoryBalance.objects.filter(company=company).values("material_id").annotate(total=Coalesce(Sum("quantity_on_hand"), Decimal("0")))}
        queryset = [balance for balance in queryset if totals.get(balance.material_id, Decimal("0")) <= balance.material.minimum_stock_level]
    return queryset


def material_total(company, material):
    return InventoryBalance.objects.filter(company=company, material=material).aggregate(total=Coalesce(Sum("quantity_on_hand"), Decimal("0")))["total"]


def project_usage(project):
    return MaterialTransaction.objects.filter(company=project.company, project=project, transaction_type=MaterialTransaction.Type.USE).select_related("material", "location", "recorded_by")
