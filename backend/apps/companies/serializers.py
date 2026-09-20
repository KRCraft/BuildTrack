from django.utils.text import slugify
from rest_framework import serializers
from apps.accounts.serializers import UserSerializer
from .models import Company, CompanyInvitation, CompanyMembership


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ("id", "name", "slug", "currency_code", "timezone", "country_code", "address", "is_active", "created_at", "updated_at")
        read_only_fields = ("id", "is_active", "created_at", "updated_at")
        extra_kwargs = {"slug": {"required": False}}

    def validate_slug(self, value):
        return slugify(value)

    def create(self, validated_data):
        if not validated_data.get("slug"):
            base = slugify(validated_data["name"])[:70] or "company"
            slug, suffix = base, 2
            while Company.objects.filter(slug=slug).exists():
                slug = f"{base}-{suffix}"
                suffix += 1
            validated_data["slug"] = slug
        return super().create(validated_data)


class MembershipSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = CompanyMembership
        fields = ("id", "user", "role", "status", "joined_at", "deactivated_at")
        read_only_fields = ("id", "user", "joined_at", "deactivated_at")


class MembershipUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyMembership
        fields = ("role", "status")


class InvitationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=CompanyMembership.Role.choices)


class InvitationAcceptSerializer(serializers.Serializer):
    token = serializers.CharField()
