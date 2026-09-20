from rest_framework.test import APITestCase
from rest_framework import status
from .models import User


class AuthenticationTests(APITestCase):
    def test_registration_and_login(self):
        registration = self.client.post("/api/v1/auth/register/", {"email": "owner@example.com", "first_name": "Owner", "last_name": "One", "password": "StrongPass123!"}, format="json")
        self.assertEqual(registration.status_code, status.HTTP_201_CREATED)
        self.assertIn("access", registration.data)
        login = self.client.post("/api/v1/auth/login/", {"email": "owner@example.com", "password": "StrongPass123!"}, format="json")
        self.assertEqual(login.status_code, status.HTTP_200_OK)
        self.assertIn("buildtrack_refresh", login.cookies)

    def test_invalid_credentials_are_rejected(self):
        User.objects.create_user(email="owner@example.com", first_name="Owner", password="StrongPass123!")
        response = self.client.post("/api/v1/auth/login/", {"email": "owner@example.com", "password": "wrong"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
