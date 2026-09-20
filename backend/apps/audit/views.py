from rest_framework import generics
from rest_framework.exceptions import PermissionDenied
from apps.common.tenant import request_company
from apps.companies.models import CompanyMembership
from .models import AuditLog
from .serializers import AuditLogSerializer


class AuditLogListView(generics.ListAPIView):
    serializer_class = AuditLogSerializer

    def get_queryset(self):
        company = request_company(self.request)
        if self.request.membership.role != CompanyMembership.Role.OWNER:
            raise PermissionDenied("Only company owners can view company audit logs.")
        queryset = AuditLog.objects.filter(company=company)
        entity_type = self.request.query_params.get("entity_type")
        entity_id = self.request.query_params.get("entity_id")
        if entity_type:
            queryset = queryset.filter(entity_type=entity_type)
        if entity_id:
            queryset = queryset.filter(entity_id=entity_id)
        return queryset
