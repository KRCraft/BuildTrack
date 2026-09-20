from rest_framework.throttling import AnonRateThrottle, UserRateThrottle, ScopedRateThrottle


class LoginRateThrottle(AnonRateThrottle):
    scope = "login"


class RegisterRateThrottle(AnonRateThrottle):
    scope = "register"


class PasswordResetRateThrottle(AnonRateThrottle):
    scope = "password_reset"


class BurstAnonThrottle(AnonRateThrottle):
    scope = "anon"


class BurstUserThrottle(UserRateThrottle):
    scope = "user"
