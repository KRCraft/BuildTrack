from rest_framework import serializers

from .models import Budget, BudgetCategory, BudgetVersion
from .selectors import category_financial_rows, project_financial_summary


class BudgetCategorySerializer(serializers.ModelSerializer):
    actual_spend = serializers.DecimalField(max_digits=19, decimal_places=4, read_only=True)
    remaining_amount = serializers.DecimalField(max_digits=19, decimal_places=4, read_only=True)
    variance_amount = serializers.DecimalField(max_digits=19, decimal_places=4, read_only=True)

    class Meta:
        model = BudgetCategory
        fields = ("id", "parent", "lineage_key", "code", "name", "planned_amount", "sort_order", "is_active", "actual_spend", "remaining_amount", "variance_amount", "created_at", "updated_at")
        read_only_fields = ("id", "lineage_key", "created_at", "updated_at")

    def validate_parent(self, value):
        version = self.context.get("budget_version") or getattr(self.instance, "budget_version", None)
        if value and value.budget_version_id != version.id:
            raise serializers.ValidationError("Parent category must belong to this budget version.")
        return value

    def validate_code(self, value):
        version = self.context.get("budget_version") or getattr(self.instance, "budget_version", None)
        if version and BudgetCategory.objects.filter(budget_version=version, code=value).exclude(id=getattr(self.instance, "id", None)).exists():
            raise serializers.ValidationError("A category with this code already exists in this version.")
        return value


class BudgetVersionSerializer(serializers.ModelSerializer):
    categories = serializers.SerializerMethodField()

    class Meta:
        model = BudgetVersion
        fields = ("id", "version_number", "status", "currency_code", "total_planned_amount", "submitted_at", "approved_at", "superseded_at", "submitted_by", "approved_by", "approval_note", "version", "categories", "created_at", "updated_at")
        read_only_fields = ("id", "version_number", "status", "total_planned_amount", "submitted_at", "approved_at", "superseded_at", "submitted_by", "approved_by", "version", "created_at", "updated_at")

    def get_categories(self, version):
        rows = category_financial_rows(version)
        serializer = BudgetCategorySerializer([item["category"] for item in rows], many=True)
        data = serializer.data
        for datum, row in zip(data, rows):
            datum.update({key: str(row[key]) for key in ("actual_spend", "remaining_amount", "variance_amount")})
        return data


class BudgetSerializer(serializers.ModelSerializer):
    active_version = BudgetVersionSerializer(read_only=True)
    financial_summary = serializers.SerializerMethodField()
    versions = serializers.SerializerMethodField()

    class Meta:
        model = Budget
        fields = ("id", "project", "active_version", "financial_summary", "versions", "created_at", "updated_at")
        read_only_fields = fields

    def get_financial_summary(self, budget):
        return {key: str(value) for key, value in project_financial_summary(budget.project).items()}

    def get_versions(self, budget):
        return BudgetVersionSerializer(budget.versions.all(), many=True).data


class ApprovalSerializer(serializers.Serializer):
    approval_note = serializers.CharField(required=False, allow_blank=True, max_length=2000)
