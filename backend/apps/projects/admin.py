from django.contrib import admin
from .models import Project, ProjectAssignment


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "company", "status", "progress_percent_cache", "is_archived")
    list_filter = ("status", "is_archived")
    search_fields = ("name", "code", "client_name")


@admin.register(ProjectAssignment)
class ProjectAssignmentAdmin(admin.ModelAdmin):
    list_display = ("project", "membership", "assignment_role", "is_active")
