from rest_framework import viewsets, mixins, permissions, filters
from .models import ContactMessage, Testimonial
from .serializers import ContactMessageSerializer, TestimonialSerializer


class ContactMessageViewSet(mixins.CreateModelMixin,
                            mixins.ListModelMixin,
                            mixins.RetrieveModelMixin,
                            viewsets.GenericViewSet):
    queryset = ContactMessage.objects.all()
    serializer_class = ContactMessageSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]


class TestimonialViewSet(viewsets.ModelViewSet):
    serializer_class = TestimonialSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'rating']

    def get_queryset(self):
        qs = Testimonial.objects.all()
        if self.action == 'list':
            qs = qs.filter(is_approved=True)
        return qs

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticatedOrReadOnly()]
