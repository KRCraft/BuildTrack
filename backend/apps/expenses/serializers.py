from rest_framework import serializers

from apps.budgets.models import BudgetCategory

from .models import Expense, ExpenseApproval, ExpenseAttachment, Supplier


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ("id", "name", "tax_id", "phone", "email", "address", "is_active", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")


class ExpenseApprovalSerializer(serializers.ModelSerializer):
    actor_name = serializers.SerializerMethodField()

    class Meta:
        model = ExpenseApproval
        fields = ("id", "action", "actor", "actor_name", "comment", "created_at")

    def get_actor_name(self, obj):
        return obj.actor.get_full_name() or obj.actor.email if obj.actor else "System"


class ExpenseAttachmentSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = ExpenseAttachment
        fields = ("id", "storage_key", "url", "original_filename", "content_type", "size_bytes", "uploaded_by", "uploaded_at")
        read_only_fields = fields

    def get_url(self, obj):
        return obj.storage_key.url if obj.storage_key else None


class ExpenseSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source="supplier.name", read_only=True)
    category_name = serializers.CharField(source="budget_category.name", read_only=True)
    project_name = serializers.CharField(source="project.name", read_only=True)
    approval_history = ExpenseApprovalSerializer(many=True, read_only=True)
    attachments = ExpenseAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = Expense
        fields = ("id", "project", "project_name", "budget_category", "category_name", "supplier", "supplier_name", "expense_type", "reverses_expense", "amount", "currency_code", "expense_date", "payment_method", "description", "status", "submitted_by", "approved_by", "approved_at", "idempotency_key", "correction_group_id", "version", "approval_history", "attachments", "created_at", "updated_at")
        read_only_fields = ("id", "expense_type", "reverses_expense", "status", "submitted_by", "approved_by", "approved_at", "correction_group_id", "version", "approval_history", "attachments", "created_at", "updated_at")

    def validate(self, attrs):
        request = self.context.get("request")
        company = self.context.get("company") or getattr(self.instance, "company", None)
        project = attrs.get("project", getattr(self.instance, "project", None))
        category = attrs.get("budget_category", getattr(self.instance, "budget_category", None))
        supplier = attrs.get("supplier", getattr(self.instance, "supplier", None))
        currency = attrs.get("currency_code", getattr(self.instance, "currency_code", None))
        if project and project.company_id != company.id:
            raise serializers.ValidationError({"project": "Project belongs to another company."})
        if category:
            try:
                active_version_id = project.budget.active_version_id if hasattr(project, "budget") else None
            except Exception:
                active_version_id = None
            if not active_version_id:
                raise serializers.ValidationError({"budget_category": "This project's budget is not yet approved."})
            if category.company_id != company.id or category.budget_version.budget.project_id != project.id or category.budget_version_id != active_version_id:
                raise serializers.ValidationError({"budget_category": "Category must belong to this project's approved budget."})
        if supplier and supplier.company_id != company.id:
            raise serializers.ValidationError({"supplier": "Supplier belongs to another company."})
        if currency and currency != company.currency_code:
            raise serializers.ValidationError({"currency_code": "Expenses must use the company accounting currency."})
        return attrs


class ApprovalInputSerializer(serializers.Serializer):
    comment = serializers.CharField(required=False, allow_blank=True, max_length=2000)


class ExpenseAttachmentUploadSerializer(serializers.Serializer):
    file = serializers.FileField()

    def validate_file(self, value):
        allowed = {"application/pdf", "image/jpeg", "image/png"}
        if value.content_type not in allowed:
            raise serializers.ValidationError("Only PDF, JPG, JPEG, and PNG files are allowed.")
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("Attachments must be 10 MB or smaller.")
        return value
