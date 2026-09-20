from django.contrib import admin
from .models import QuoteRequest


@admin.register(QuoteRequest)
class QuoteRequestAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'project_type', 'budget_range', 'status', 'created_at')
    list_filter = ('status', 'project_type')
    search_fields = ('name', 'email', 'project_type', 'message')
    list_editable = ('status',)
