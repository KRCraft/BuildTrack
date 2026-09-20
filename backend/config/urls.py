from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/schema/swagger-ui/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/schema/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path("api/v1/auth/", include("apps.accounts.urls")),
    path("api/v1/companies/", include("apps.companies.urls")),
    path("api/v1/projects/", include("apps.projects.urls")),
    path("api/v1/dashboard/", include("apps.dashboard.urls")),
    path("api/v1/audit-logs/", include("apps.audit.urls")),
    path("api/v1/", include("apps.budgets.urls")),
    path("api/v1/", include("apps.expenses.urls")),
    path("api/v1/", include("apps.inventory.urls")),
    path("api/v1/", include("apps.workforce.urls")),
    path("api/v1/", include("apps.reports.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
