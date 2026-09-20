from django.conf import settings
from django.core.cache import cache


def _key(email: str, ip: str) -> str:
    return f"auth:lockout:{email.lower().strip()}:{ip}"


def is_locked(email: str, ip: str) -> bool:
    return cache.get(_key(email, ip), 0) >= getattr(settings, "AUTH_LOCKOUT_MAX_ATTEMPTS", 5)


def record_failed(email: str, ip: str):
    k = _key(email, ip)
    attempts = cache.get(k, 0) + 1
    cache.set(k, attempts, timeout=getattr(settings, "AUTH_LOCKOUT_WINDOW_SECONDS", 900))
    return attempts


def clear_lockout(email: str, ip: str):
    cache.delete(_key(email, ip))


def get_client_ip(request) -> str:
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")
