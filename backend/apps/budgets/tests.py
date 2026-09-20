from decimal import Decimal

from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.companies.models import Company, CompanyMembership
from apps.projects.models import Project, ProjectAssignment

from .models import Budget, BudgetCategory, BudgetVersion


class BudgetWorkflowTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email="owner@alpha.test", password="Pass12345!")
        self.manager = User.objects.create_user(email="manager@alpha.test", password="Pass12345!")
        self.other = User.objects.create_user(email="owner@beta.test", password="Pass12345!")
        self.company = Company.objects.create(name="Alpha", slug="alpha", currency_code="UZS")
        self.other_company = Company.objects.create(name="Beta", slug="beta")
        self.owner_member = CompanyMembership.objects.create(company=self.company, user=self.owner, role=CompanyMembership.Role.OWNER)
        self.manager_member = CompanyMembership.objects.create(company=self.company, user=self.manager, role=CompanyMembership.Role.PROJECT_MANAGER)
        CompanyMembership.objects.create(company=self.other_company, user=self.other, role=CompanyMembership.Role.OWNER)
        self.project = Project.objects.create(company=self.company, name="Tower", code="T-1", created_by=self.owner)
        ProjectAssignment.objects.create(project=self.project, membership=self.manager_member, assignment_role=ProjectAssignment.AssignmentRole.PROJECT_MANAGER)
        self.client.force_authenticate(self.owner)
        self.headers = {"HTTP_X_COMPANY_ID": str(self.company.id)}

    def create_budget_and_category(self):
        response = self.client.post(f"/api/v1/projects/{self.project.id}/budget/", {}, format="json", **self.headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        version = Budget.objects.get(project=self.project).versions.get()
        response = self.client.post(f"/api/v1/budget-versions/{version.id}/categories/", {"code": "MAT", "name": "Materials", "planned_amount": "1000.0000"}, format="json", **self.headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return version

    def test_budget_create_submit_approve_and_revision(self):
        version = self.create_budget_and_category()
        response = self.client.post(f"/api/v1/budget-versions/{version.id}/submit/", {}, format="json", **self.headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.post(f"/api/v1/budget-versions/{version.id}/approve/", {}, format="json", **self.headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        budget = Budget.objects.get(project=self.project)
        self.assertEqual(budget.active_version_id, version.id)
        response = self.client.post(f"/api/v1/projects/{self.project.id}/budget/versions/", {}, format="json", **self.headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        revision = BudgetVersion.objects.get(id=response.data["id"])
        self.assertEqual(revision.version_number, 2)
        self.assertEqual(revision.categories.count(), 1)
        lineage = revision.categories.get().lineage_key
        self.assertEqual(lineage, version.categories.get().lineage_key)
        self.client.post(f"/api/v1/budget-versions/{revision.id}/submit/", {}, format="json", **self.headers)
        self.client.post(f"/api/v1/budget-versions/{revision.id}/approve/", {}, format="json", **self.headers)
        version.refresh_from_db(); budget.refresh_from_db()
        self.assertEqual(version.status, BudgetVersion.Status.SUPERSEDED)
        self.assertEqual(budget.active_version_id, revision.id)

    def test_approved_budget_is_immutable_and_tenant_isolated(self):
        version = self.create_budget_and_category()
        category = version.categories.get()
        self.client.post(f"/api/v1/budget-versions/{version.id}/submit/", {}, format="json", **self.headers)
        self.client.post(f"/api/v1/budget-versions/{version.id}/approve/", {}, format="json", **self.headers)
        response = self.client.patch(f"/api/v1/budget-categories/{category.id}/", {"planned_amount": "2"}, format="json", **self.headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.client.force_authenticate(self.other)
        response = self.client.get(f"/api/v1/budget-versions/{version.id}/", HTTP_X_COMPANY_ID=str(self.other_company.id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_parent_and_unique_code_validation(self):
        version = self.create_budget_and_category()
        first = version.categories.get()
        response = self.client.post(f"/api/v1/budget-versions/{version.id}/categories/", {"code": "MAT", "name": "Duplicate", "planned_amount": "0"}, format="json", **self.headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        other_budget = Budget.objects.create(company=self.company, project=Project.objects.create(company=self.company, name="Other", code="T-2", created_by=self.owner), created_by=self.owner)
        other_version = BudgetVersion.objects.create(company=self.company, budget=other_budget, version_number=1, currency_code="UZS")
        response = self.client.post(f"/api/v1/budget-versions/{other_version.id}/categories/", {"code": "X", "name": "Wrong parent", "planned_amount": "0", "parent": str(first.id)}, format="json", **self.headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
