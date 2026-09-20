import uuid
import json
from django.core.serializers.json import DjangoJSONEncoder
from .models import AuditLog


def audit_event(request, company, action, entity, before_state=None, after_state=None):
    actor = getattr(request, "user", None)
    if not getattr(actor, "is_authenticated", False):
        actor = None
    actor_snapshot = {} if not actor else {"id": str(actor.id), "email": actor.email, "name": f"{actor.first_name} {actor.last_name}".strip()}
    raw_request_id = request.headers.get("X-Request-ID") if request else None
    try:
        request_id = uuid.UUID(raw_request_id) if raw_request_id else uuid.uuid4()
    except (ValueError, TypeError):
        request_id = uuid.uuid4()
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "") if request else ""
    ip = (forwarded.split(",")[0].strip() if forwarded else request.META.get("REMOTE_ADDR")) if request else None
    normalize = lambda value: json.loads(json.dumps(value, cls=DjangoJSONEncoder)) if value is not None else None
    AuditLog.objects.create(company=company, actor=actor, actor_snapshot=actor_snapshot, action=action, entity_type=entity.__class__._meta.label_lower, entity_id=getattr(entity, "id", None), before_state=normalize(before_state), after_state=normalize(after_state), request_id=request_id, ip_address=ip, user_agent=(request.META.get("HTTP_USER_AGENT", "") if request else ""))
