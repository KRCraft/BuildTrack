import logging
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.throttling import AnonRateThrottle, ScopedRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from rest_framework.exceptions import ValidationError as DRFValidationError
from apps.audit.services import audit_event
from .lockout import clear_lockout, get_client_ip, is_locked, record_failed
from .models import User
from .serializers import ChangePasswordSerializer, LoginSerializer, PasswordResetConfirmSerializer, PasswordResetSerializer, RegisterSerializer, UpdateMeSerializer, UserSerializer

logger = logging.getLogger("apps.accounts")


def set_refresh_cookie(response, refresh):
    response.set_cookie(settings.REFRESH_COOKIE_NAME, str(refresh), httponly=True, secure=settings.REFRESH_COOKIE_SECURE, samesite=settings.REFRESH_COOKIE_SAMESITE, max_age=int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds()), path="/api/v1/auth/")


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = "register"

    def get_throttles(self):
        return [ScopedRateThrottle()]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        audit_event(request, None, "auth.register", user, after_state={"email": user.email})
        logger.info("auth.register email=%s ip=%s", user.email, get_client_ip(request))
        response = Response({"user": UserSerializer(user).data, "access": str(refresh.access_token)}, status=status.HTTP_201_CREATED)
        set_refresh_cookie(response, refresh)
        return response


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = "login"

    def get_throttles(self):
        return [ScopedRateThrottle()]

    def post(self, request):
        email_raw = request.data.get("email", "")
        ip = get_client_ip(request)
        email_key = str(email_raw).lower().strip() or "unknown"
        if is_locked(email_key, ip):
            logger.warning("auth.login.locked email=%s ip=%s", email_key, ip)
            return Response({"detail": "Too many failed attempts. Try again in 15 minutes."}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            record_failed(email_key, ip)
            # Map serializer errors to 401 for login to avoid 400 fingerprinting
            return Response({"detail": "Invalid email or password."}, status=status.HTTP_401_UNAUTHORIZED)
        user = serializer.validated_data["user"]
        clear_lockout(email_key, ip)
        refresh = RefreshToken.for_user(user)
        audit_event(request, None, "auth.login", user, after_state={"email": user.email})
        logger.info("auth.login success email=%s ip=%s", user.email, ip)
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

    def patch(self, request):
        serializer = UpdateMeSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        audit_event(request, None, "auth.me_updated", user, after_state=UserSerializer(user).data)
        return Response(UserSerializer(user).data)


class ChangePasswordView(APIView):
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        if not user.check_password(serializer.validated_data["old_password"]):
            raise DRFValidationError({"old_password": "Current password is incorrect."})
        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])
        # Blacklist all outstanding refresh tokens for this user (force re-login elsewhere)
        for token in OutstandingToken.objects.filter(user=user):
            try:
                BlacklistedToken.objects.get_or_create(token=token)
            except Exception:
                continue
        audit_event(request, None, "auth.password_changed", user)
        logger.info("auth.password_changed email=%s ip=%s", user.email, get_client_ip(request))
        response = Response({"detail": "Password updated. Please log in again."})
        response.delete_cookie(settings.REFRESH_COOKIE_NAME, path="/api/v1/auth/")
        return response


class RefreshView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = "login"

    def get_throttles(self):
        return [ScopedRateThrottle()]

    def post(self, request):
        raw_token = request.COOKIES.get(settings.REFRESH_COOKIE_NAME)
        if not raw_token:
            return Response({"detail": "Refresh token missing."}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            refresh = RefreshToken(raw_token)
            # Validate user still active
            user = User.objects.get(id=refresh["user_id"])
            if not user.is_active:
                raise Exception("User inactive")
            if settings.SIMPLE_JWT["ROTATE_REFRESH_TOKENS"]:
                try:
                    refresh.blacklist()
                except Exception:
                    # Already blacklisted or invalid
                    pass
                new_refresh = RefreshToken.for_user(user)
                access = str(new_refresh.access_token)
                response = Response({"access": access})
                set_refresh_cookie(response, new_refresh)
                return response
            access = str(refresh.access_token)
        except Exception:
            return Response({"detail": "Refresh token is invalid."}, status=status.HTTP_401_UNAUTHORIZED)
        response = Response({"access": access})
        set_refresh_cookie(response, refresh)
        return response


class PasswordResetView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = "password_reset"

    def get_throttles(self):
        return [ScopedRateThrottle()]

    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # Always return same message to avoid enumeration
        user = User.objects.filter(email__iexact=serializer.validated_data["email"].lower().strip(), is_active=True).first()
        if user:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            # In prod this would be a link; for API we send uid+token
            send_mail("Reset your BuildTrack password", f"Use this reset payload in the app: uid={uid}&token={token}", settings.DEFAULT_FROM_EMAIL, [user.email])
            logger.info("auth.password_reset email=%s ip=%s", user.email, get_client_ip(request))
            audit_event(request, None, "auth.password_reset_requested", user, after_state={"email": user.email})
        return Response({"detail": "If an account exists, a reset email has been sent."})


class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = "password_reset"

    def get_throttles(self):
        return [ScopedRateThrottle()]

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
        # Invalidate all refresh tokens
        for token in OutstandingToken.objects.filter(user=user):
            try:
                BlacklistedToken.objects.get_or_create(token=token)
            except Exception:
                continue
        audit_event(request, None, "auth.password_reset_completed", user, after_state={"email": user.email})
        logger.info("auth.password_reset_completed email=%s ip=%s", user.email, get_client_ip(request))
        return Response({"detail": "Password updated."})
