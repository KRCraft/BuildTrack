from rest_framework import serializers
from .models import QuoteRequest


class QuoteRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuoteRequest
        fields = [
            'id', 'name', 'email', 'phone',
            'project_type', 'budget_range', 'message',
            'status', 'created_at',
        ]
        read_only_fields = ['status', 'created_at']
