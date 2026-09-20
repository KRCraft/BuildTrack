from rest_framework import status
from rest_framework.test import APITestCase
from apps.accounts.models import User
from apps.audit.models import AuditLog
from apps.companies.models import Company, CompanyMembership
from .models import Project, ProjectAssignment


class TenantProjectTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email="owner@example.com", first_name="Owner", password="StrongPass123!")
        self.manager = User.objects.create_user(email="manager@example.com", first_name="Manager", password="StrongPass123!")
        self.site = User.objects.create_user(email="site@example.com", first_name="Site", password="StrongPass123!")
        self.accountant = User.objects.create_user(email="accountant@example.com", first_name="Accountant", password="StrongPass123!")
        self.other_owner = User.objects.create_user(email="other@example.com", first_name="Other", password="StrongPass123!")
        self.company = Company.objects.create(name="Alpha Build", slug="alpha-build")
        self.other_company = Company.objects.create(name="Beta Build", slug="beta-build")
        self.owner_membership = CompanyMembership.objects.create(company=self.company, user=self.owner, role="OWNER")
        self.manager_membership = CompanyMembership.objects.create(company=self.company, user=self.manager, role="PROJECT_MANAGER")
        self.site_membership = CompanyMembership.objects.create(company=self.company, user=self.site, role="SITE_MANAGER")
        self.accountant_membership = CompanyMembership.objects.create(company=self.company, user=self.accountant, role="ACCOUNTANT")
        CompanyMembership.objects.create(company=self.other_company, user=self.other_owner, role="OWNER")

    def authenticate(self, user, company):
        self.client.force_authenticate(user=user)
        self.client.credentials(HTTP_X_COMPANY_ID=str(company.id))

    def create_project(self):
        self.authenticate(self.owner, self.company)
        response = self.client.post("/api/v1/projects/", {"name": "Central Tower", "code": "CT-01", "client_name": "KRCraft", "status": "ACTIVE", "progress_percent_cache": "15.00"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return Project.objects.get(id=response.data["id"])

    def test_owner_can_create_update_archive_and_audit_project(self):
        project = self.create_project()
        update = self.client.patch(f"/api/v1/projects/{project.id}/", {"location": "Tashkent"}, format="json")
        self.assertEqual(update.status_code, status.HTTP_200_OK)
        archive = self.client.post(f"/api/v1/projects/{project.id}/archive/", format="json")
        self.assertEqual(archive.status_code, status.HTTP_200_OK)
        project.refresh_from_db()
        self.assertTrue(project.is_archived)
        self.assertTrue(AuditLog.objects.filter(company=self.company, entity_id=project.id, action="project.archived").exists())

    def test_cross_company_project_access_is_not_found(self):
        project = self.create_project()
        self.authenticate(self.other_owner, self.other_company)
        response = self.client.get(f"/api/v1/projects/{project.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_site_manager_and_accountant_cannot_create_projects(self):
        for user in (self.site, self.accountant):
            self.authenticate(user, self.company)
            response = self.client.post("/api/v1/projects/", {"name": "No Access", "code": f"N-{user.id.hex[:4]}"}, format="json")
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_project_assignment_requires_same_company_membership(self):
        project = self.create_project()
        self.authenticate(self.owner, self.company)
        other_membership = CompanyMembership.objects.get(company=self.other_company, user=self.other_owner)
        response = self.client.post(f"/api/v1/projects/{project.id}/assignments/", {"membership": str(other_membership.id), "assignment_role": "SITE_MANAGER"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_project_manager_is_limited_to_assigned_projects(self):
        project = self.create_project()
        self.authenticate(self.manager, self.company)
        self.assertEqual(self.client.get(f"/api/v1/projects/{project.id}/").status_code, status.HTTP_404_NOT_FOUND)
        self.authenticate(self.owner, self.company)
        self.client.post(f"/api/v1/projects/{project.id}/assignments/", {"membership": str(self.manager_membership.id), "assignment_role": "PROJECT_MANAGER"}, format="json")
        self.authenticate(self.manager, self.company)
        self.assertEqual(self.client.get(f"/api/v1/projects/{project.id}/").status_code, status.HTTP_200_OK)
