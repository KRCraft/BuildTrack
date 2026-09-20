from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from apps.audit.services import audit_event
from .models import User
from .serializers import LoginSerializer, PasswordResetConfirmSerializer, PasswordResetSerializer, RegisterSerializer, UserSerializer


def set_refresh_cookie(response, refresh):
    response.set_cookie(settings.REFRESH_COOKIE_NAME, str(refresh), httponly=True, secure=settings.REFRESH_COOKIE_SECURE, samesite=settings.REFRESH_COOKIE_SAMESITE, max_age=int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds()), path="/api/v1/auth/")


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        response = Response({"user": UserSerializer(user).data, "access": str(refresh.access_token)}, status=status.HTTP_201_CREATED)
        set_refresh_cookie(response, refresh)
        return response


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        refresh = RefreshToken.for_user(user)
        audit_event(request, None, "auth.login", user, after_state={"email": user.email})
        response = Response({"user": UserSerializer(user).data, "access": str(refresh.access_token)})
        set_refresh_cookie(response, refresh)
        return response


class LogoutView(APIView):
    def post(self, request):
        raw_token = request.COOKIES.get(settings.REFRESH_COOKIE_NAME)
        if raw_token:
            try:
                token = RefreshToken(raw_token)
                token.blacklist()
            except Exception:
                pass
        audit_event(request, None, "auth.logout", request.user)
        response = Response(status=status.HTTP_204_NO_CONTENT)
        response.delete_cookie(settings.REFRESH_COOKIE_NAME, path="/api/v1/auth/")
        return response


class MeView(APIView):
    def get(self, request):
        return Response(UserSerializer(request.user).data)


class RefreshView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        raw_token = request.COOKIES.get(settings.REFRESH_COOKIE_NAME)
        if not raw_token:
            return Response({"detail": "Refresh token missing."}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            refresh = RefreshToken(raw_token)
            access = str(refresh.access_token)
            if settings.SIMPLE_JWT["ROTATE_REFRESH_TOKENS"]:
                refresh.blacklist()
                refresh = RefreshToken.for_user(User.objects.get(id=refresh["user_id"]))
        except Exception:
            return Response({"detail": "Refresh token is invalid."}, status=status.HTTP_401_UNAUTHORIZED)
        response = Response({"access": access})
        set_refresh_cookie(response, refresh)
        return response


class PasswordResetView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.filter(email__iexact=serializer.validated_data["email"], is_active=True).first()
        if user:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            send_mail("Reset your BuildTrack password", f"Use this reset payload in the app: uid={uid}&token={token}", settings.DEFAULT_FROM_EMAIL, [user.email])
        return Response({"detail": "If an account exists, a reset email has been sent."})


class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = User.objects.get(pk=force_str(urlsafe_base64_decode(serializer.validated_data["uid"])))
        except Exception:
            return Response({"detail": "Reset link is invalid."}, status=status.HTTP_400_BAD_REQUEST)
        if not default_token_generator.check_token(user, serializer.validated_data["token"]):
            return Response({"detail": "Reset link is invalid or expired."}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(serializer.validated_data["password"])
        user.save(update_fields=["password"])
        return Response({"detail": "Password updated."})
