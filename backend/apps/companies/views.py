import secrets
from datetime import timedelta
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.audit.services import audit_event
from apps.common.tenant import active_membership
from .models import Company, CompanyInvitation, CompanyMembership
from .serializers import CompanySerializer, InvitationAcceptSerializer, InvitationSerializer, MembershipSerializer, MembershipUpdateSerializer


def owner_membership(request, company_id):
    membership = active_membership(request, company_id)
    if membership.role != CompanyMembership.Role.OWNER:
        raise PermissionDenied("Only company owners can manage members.")
    return membership


class CompanyListCreateView(APIView):
    def get(self, request):
        companies = Company.objects.filter(memberships__user=request.user, memberships__status=CompanyMembership.Status.ACTIVE, is_active=True).distinct()
        return Response(CompanySerializer(companies, many=True).data)

    @transaction.atomic
    def post(self, request):
        serializer = CompanySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        company = serializer.save()
        CompanyMembership.objects.create(company=company, user=request.user, role=CompanyMembership.Role.OWNER)
        audit_event(request, company, "company.created", company, after_state=CompanySerializer(company).data)
        return Response(CompanySerializer(company).data, status=status.HTTP_201_CREATED)


class CompanyDetailView(APIView):
    def get_object(self, request, company_id):
        return active_membership(request, company_id).company

    def get(self, request, company_id):
        return Response(CompanySerializer(self.get_object(request, company_id)).data)

    def patch(self, request, company_id):
        membership = owner_membership(request, company_id)
        company = membership.company
        before = CompanySerializer(company).data
        serializer = CompanySerializer(company, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        company = serializer.save()
        audit_event(request, company, "company.updated", company, before_state=before, after_state=CompanySerializer(company).data)
        return Response(CompanySerializer(company).data)


class MemberListView(APIView):
    def get(self, request, company_id):
        owner_membership(request, company_id)
        members = CompanyMembership.objects.filter(company_id=company_id).select_related("user").order_by("user__first_name", "user__email")
        return Response(MembershipSerializer(members, many=True).data)


class InvitationCreateView(APIView):
    @transaction.atomic
    def post(self, request, company_id):
        membership = owner_membership(request, company_id)
        serializer = InvitationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].lower()
        if CompanyMembership.objects.filter(company=membership.company, user__email__iexact=email).exists():
            raise ValidationError({"email": "This user is already a company member."})
        CompanyInvitation.objects.filter(company=membership.company, email__iexact=email, status=CompanyInvitation.Status.PENDING).update(status=CompanyInvitation.Status.REVOKED)
        raw_token = secrets.token_urlsafe(32)
        invitation = CompanyInvitation.objects.create(company=membership.company, email=email, role=serializer.validated_data["role"], token_hash=CompanyInvitation.hash_token(raw_token), expires_at=timezone.now() + timedelta(days=7), invited_by=request.user)
        send_mail(f"You are invited to {membership.company.name}", f"Use this invitation token after registering: {raw_token}", None, [email])
        audit_event(request, membership.company, "membership.invited", invitation, after_state={"email": email, "role": invitation.role})
        return Response({"id": str(invitation.id), "email": invitation.email, "role": invitation.role, "expires_at": invitation.expires_at}, status=status.HTTP_201_CREATED)


class MemberUpdateView(APIView):
    @transaction.atomic
    def patch(self, request, company_id, membership_id):
        actor_membership = owner_membership(request, company_id)
        target = CompanyMembership.objects.select_for_update().filter(company=actor_membership.company, id=membership_id).first()
        if not target:
            return Response({"detail": "Member was not found."}, status=status.HTTP_404_NOT_FOUND)
        before = MembershipSerializer(target).data
        serializer = MembershipUpdateSerializer(target, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        next_role = serializer.validated_data.get("role", target.role)
        next_status = serializer.validated_data.get("status", target.status)
        removing_owner = target.role == CompanyMembership.Role.OWNER and (next_role != target.role or next_status != CompanyMembership.Status.ACTIVE)
        if removing_owner and CompanyMembership.objects.filter(company=actor_membership.company, role=CompanyMembership.Role.OWNER, status=CompanyMembership.Status.ACTIVE).count() <= 1:
            raise ValidationError("A company must retain at least one active owner.")
        target = serializer.save(deactivated_at=timezone.now() if next_status == CompanyMembership.Status.INACTIVE else None)
        audit_event(request, actor_membership.company, "membership.updated", target, before_state=before, after_state=MembershipSerializer(target).data)
        return Response(MembershipSerializer(target).data)


class InvitationAcceptView(APIView):
    @transaction.atomic
    def post(self, request):
        serializer = InvitationAcceptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        invitation = CompanyInvitation.objects.select_for_update().filter(token_hash=CompanyInvitation.hash_token(serializer.validated_data["token"]), status=CompanyInvitation.Status.PENDING).select_related("company").first()
        if not invitation or invitation.expires_at <= timezone.now() or invitation.email.lower() != request.user.email.lower():
            raise ValidationError("Invitation is invalid or expired.")
        membership, _ = CompanyMembership.objects.update_or_create(company=invitation.company, user=request.user, defaults={"role": invitation.role, "status": CompanyMembership.Status.ACTIVE, "deactivated_at": None})
        invitation.status = CompanyInvitation.Status.ACCEPTED
        invitation.save(update_fields=["status", "updated_at"])
        audit_event(request, invitation.company, "membership.accepted", membership, after_state=MembershipSerializer(membership).data)
        return Response(MembershipSerializer(membership).data)
