from decimal import Decimal

from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.budgets.models import Budget, BudgetCategory, BudgetVersion
from apps.budgets.selectors import project_financial_summary
from apps.companies.models import Company, CompanyMembership
from apps.projects.models import Project, ProjectAssignment

from .models import Expense, Supplier


class ExpenseWorkflowTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email="owner@alpha.test", password="Pass12345!")
        self.accountant = User.objects.create_user(email="accountant@alpha.test", password="Pass12345!")
        self.site = User.objects.create_user(email="site@alpha.test", password="Pass12345!")
        self.other = User.objects.create_user(email="owner@beta.test", password="Pass12345!")
        self.company = Company.objects.create(name="Alpha", slug="alpha", currency_code="UZS")
        self.other_company = Company.objects.create(name="Beta", slug="beta")
        self.owner_m = CompanyMembership.objects.create(company=self.company, user=self.owner, role=CompanyMembership.Role.OWNER)
        self.accountant_m = CompanyMembership.objects.create(company=self.company, user=self.accountant, role=CompanyMembership.Role.ACCOUNTANT)
        self.site_m = CompanyMembership.objects.create(company=self.company, user=self.site, role=CompanyMembership.Role.SITE_MANAGER)
        CompanyMembership.objects.create(company=self.other_company, user=self.other, role=CompanyMembership.Role.OWNER)
        self.project = Project.objects.create(company=self.company, name="Tower", code="T-1", created_by=self.owner)
        ProjectAssignment.objects.create(project=self.project, membership=self.site_m, assignment_role=ProjectAssignment.AssignmentRole.SITE_MANAGER)
        budget = Budget.objects.create(company=self.company, project=self.project, created_by=self.owner)
        self.budget_version = BudgetVersion.objects.create(company=self.company, budget=budget, version_number=1, status=BudgetVersion.Status.APPROVED, currency_code="UZS", total_planned_amount=Decimal("1000"))
        budget.active_version = self.budget_version; budget.save()
        self.category = BudgetCategory.objects.create(company=self.company, budget_version=self.budget_version, code="MAT", name="Materials", planned_amount=Decimal("1000"))
        self.supplier = Supplier.objects.create(company=self.company, name="Concrete Co")
        self.headers = {"HTTP_X_COMPANY_ID": str(self.company.id)}
        self.client.force_authenticate(self.site)

    def payload(self):
        return {"project": str(self.project.id), "budget_category": str(self.category.id), "supplier": str(self.supplier.id), "amount": "250.0000", "currency_code": "UZS", "expense_date": "2026-09-13", "payment_method": "CASH", "description": "Concrete"}

    def test_create_submit_approve_and_reverse_changes_financials(self):
        response = self.client.post("/api/v1/expenses/", self.payload(), format="json", **self.headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        expense_id = response.data["id"]
        self.assertEqual(self.client.post(f"/api/v1/expenses/{expense_id}/submit/", {}, format="json", **self.headers).status_code, status.HTTP_200_OK)
        self.client.force_authenticate(self.accountant)
        response = self.client.post(f"/api/v1/expenses/{expense_id}/approve/", {}, format="json", **self.headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(project_financial_summary(self.project)["approved_actual_spend"], Decimal("250"))
        response = self.client.post(f"/api/v1/expenses/{expense_id}/reverse/", {}, format="json", **self.headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        reversal = response.data["id"]
        self.client.post(f"/api/v1/expenses/{reversal}/submit/", {}, format="json", **self.headers)
        self.client.force_authenticate(self.owner)
        self.client.post(f"/api/v1/expenses/{reversal}/approve/", {}, format="json", **self.headers)
        summary = project_financial_summary(self.project)
        self.assertEqual(summary["approved_actual_spend"], Decimal("0"))
        self.assertEqual(summary["remaining_budget"], Decimal("1000"))

    def test_self_approval_and_approved_edit_are_blocked(self):
        response = self.client.post("/api/v1/expenses/", self.payload(), format="json", **self.headers)
        expense_id = response.data["id"]
        self.client.post(f"/api/v1/expenses/{expense_id}/submit/", {}, format="json", **self.headers)
        self.client.force_authenticate(self.site)
        self.assertEqual(self.client.post(f"/api/v1/expenses/{expense_id}/approve/", {}, format="json", **self.headers).status_code, status.HTTP_403_FORBIDDEN)
        self.client.force_authenticate(self.accountant)
        self.client.post(f"/api/v1/expenses/{expense_id}/approve/", {}, format="json", **self.headers)
        self.assertEqual(self.client.patch(f"/api/v1/expenses/{expense_id}/", {"amount": "1"}, format="json", **self.headers).status_code, status.HTTP_400_BAD_REQUEST)

    def test_cross_company_and_wrong_category_are_blocked(self):
        self.client.force_authenticate(self.other)
        response = self.client.get("/api/v1/expenses/", HTTP_X_COMPANY_ID=str(self.other_company.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.client.force_authenticate(self.site)
        other_project = Project.objects.create(company=self.company, name="Other", code="T-2", created_by=self.owner)
        payload = self.payload(); payload["project"] = str(other_project.id)
        response = self.client.post("/api/v1/expenses/", payload, format="json", **self.headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
