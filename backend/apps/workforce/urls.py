from django.urls import path
from .views import WorkerList,WorkerDetail,AssignmentList,ProjectWorkers
urlpatterns=[path("workers/",WorkerList.as_view()),path("workers/<uuid:worker_id>/",WorkerDetail.as_view()),path("workers/<uuid:worker_id>/assignments/",AssignmentList.as_view()),path("projects/<uuid:project_id>/workers/",ProjectWorkers.as_view())]
