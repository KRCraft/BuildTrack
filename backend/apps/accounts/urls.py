from django.urls import path
from .views import ChangePasswordView, LoginView, LogoutView, MeView, PasswordResetConfirmView, PasswordResetView, RefreshView, RegisterView, ResendVerificationView, VerifyEmailView

urlpatterns = [
    path("register/", RegisterView.as_view()), path("login/", LoginView.as_view()), path("logout/", LogoutView.as_view()),
    path("me/", MeView.as_view()), path("password/change/", ChangePasswordView.as_view()),
    path("refresh/", RefreshView.as_view()), path("password/reset/", PasswordResetView.as_view()),
    path("password/reset/confirm/", PasswordResetConfirmView.as_view()),
    path("verify-email/", VerifyEmailView.as_view()),
    path("resend-verification/", ResendVerificationView.as_view()),
]
