from rest_framework import serializers
from .models import Worker,WorkerAssignment
class WorkerSerializer(serializers.ModelSerializer):
 assignments=serializers.SerializerMethodField()
 class Meta: model=Worker;fields=("id","full_name","phone","trade","status","notes","assignments","created_at","updated_at");read_only_fields=("id","assignments","created_at","updated_at")
 def get_assignments(self,o):return [{"id":str(a.id),"project":str(a.project_id),"project_name":a.project.name,"role_on_project":a.role_on_project,"is_active":a.is_active,"start_date":a.start_date,"end_date":a.end_date} for a in o.assignments.select_related("project").all()]
class WorkerAssignmentSerializer(serializers.ModelSerializer):
 class Meta: model=WorkerAssignment;fields=("id","worker","project","role_on_project","start_date","end_date","is_active","created_at","updated_at");read_only_fields=("id","worker","created_at","updated_at")
