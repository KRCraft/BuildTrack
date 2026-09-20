from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError


def active_membership(request, company_id):
    from apps.companies.models import CompanyMembership
    try:
        return CompanyMembership.objects.select_related("company").get(company_id=company_id, user=request.user, status=CompanyMembership.Status.ACTIVE, company__is_active=True)
    except CompanyMembership.DoesNotExist as exc:
        raise NotFound("Company was not found.") from exc


def request_company(request):
    company_id = request.headers.get("X-Company-ID")
    if not company_id:
        raise ValidationError({"X-Company-ID": "An active company context is required."})
    membership = active_membership(request, company_id)
    request.company, request.membership = membership.company, membership
    return membership.company


def require_company_role(request, *roles):
    membership = getattr(request, "membership", None) or active_membership(request, request.headers.get("X-Company-ID"))
    if membership.role not in roles:
        raise PermissionDenied("Your company role does not allow this action.")
    return membership
