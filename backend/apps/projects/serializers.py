from rest_framework import serializers
from apps.companies.models import CompanyMembership
from apps.companies.serializers import MembershipSerializer
from .models import Project, ProjectAssignment


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ("id", "name", "code", "client_name", "client_contact", "location", "planned_start_date", "planned_end_date", "actual_start_date", "actual_end_date", "status", "progress_percent_cache", "is_archived", "version", "created_at", "updated_at")
        read_only_fields = ("id", "is_archived", "version", "created_at", "updated_at")

    def validate(self, attrs):
        instance = self.instance
        start = attrs.get("planned_start_date", getattr(instance, "planned_start_date", None))
        end = attrs.get("planned_end_date", getattr(instance, "planned_end_date", None))
        if start and end and end < start:
            raise serializers.ValidationError({"planned_end_date": "End date cannot precede start date."})
        actual_start = attrs.get("actual_start_date", getattr(instance, "actual_start_date", None))
        actual_end = attrs.get("actual_end_date", getattr(instance, "actual_end_date", None))
        if actual_start and actual_end and actual_end < actual_start:
            raise serializers.ValidationError({"actual_end_date": "End date cannot precede start date."})
        return attrs

    def validate_code(self, value):
        company = self.context.get("company") or getattr(self.instance, "company", None)
        if company and Project.objects.filter(company=company, code__iexact=value).exclude(pk=getattr(self.instance, "pk", None)).exists():
            raise serializers.ValidationError("A project with this code already exists in this company.")
        return value

    def update(self, instance, validated_data):
        instance.version += 1
        return super().update(instance, validated_data)


class ProjectAssignmentSerializer(serializers.ModelSerializer):
    membership = serializers.PrimaryKeyRelatedField(queryset=CompanyMembership.objects.all(), write_only=True)
    member = MembershipSerializer(source="membership", read_only=True)

    class Meta:
        model = ProjectAssignment
        fields = ("id", "membership", "member", "assignment_role", "start_date", "end_date", "is_active", "created_at")
        read_only_fields = ("id", "created_at")

    def validate(self, attrs):
        project = self.context["project"]
        membership = attrs.get("membership", getattr(self.instance, "membership", None))
        if membership.company_id != project.company_id or membership.status != CompanyMembership.Status.ACTIVE:
            raise serializers.ValidationError({"membership": "Member must be active in this company."})
        role = attrs.get("assignment_role", getattr(self.instance, "assignment_role", None))
        if membership.role != CompanyMembership.Role.OWNER and role != membership.role and role != ProjectAssignment.AssignmentRole.VIEWER:
            raise serializers.ValidationError({"assignment_role": "Assignment role exceeds the member's company role."})
        return attrs
