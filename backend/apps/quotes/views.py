from rest_framework import viewsets, mixins, permissions, filters
from .models import QuoteRequest
from .serializers import QuoteRequestSerializer


class QuoteRequestViewSet(mixins.CreateModelMixin,
                          mixins.ListModelMixin,
                          mixins.RetrieveModelMixin,
                          viewsets.GenericViewSet):
    """Public create + authenticated list/retrieve for staff."""
    queryset = QuoteRequest.objects.all()
    serializer_class = QuoteRequestSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'email', 'project_type']
    ordering_fields = ['created_at']

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]
