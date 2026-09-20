from rest_framework import status
from rest_framework.test import APITestCase
from apps.accounts.models import User
from .models import Company, CompanyMembership


class CompanyTenancyTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="owner@example.com", first_name="Owner", password="StrongPass123!")
        self.other = User.objects.create_user(email="other@example.com", first_name="Other", password="StrongPass123!")
        self.company = Company.objects.create(name="Alpha", slug="alpha")
        self.other_company = Company.objects.create(name="Beta", slug="beta")
        CompanyMembership.objects.create(company=self.company, user=self.user, role=CompanyMembership.Role.OWNER)
        CompanyMembership.objects.create(company=self.other_company, user=self.other, role=CompanyMembership.Role.OWNER)
        self.client.force_authenticate(self.user)

    def test_user_only_sees_own_company(self):
        response = self.client.get("/api/v1/companies/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([item["id"] for item in response.data], [str(self.company.id)])

    def test_user_cannot_retrieve_other_company(self):
        response = self.client.get(f"/api/v1/companies/{self.other_company.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
