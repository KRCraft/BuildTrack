from decimal import Decimal
from rest_framework import serializers
from apps.projects.models import Project

from .models import InventoryLocation, InventoryTransfer, InventoryTransferItem, Material, MaterialTransaction
from .selectors import material_total


class MaterialSerializer(serializers.ModelSerializer):
    total_stock = serializers.SerializerMethodField()
    low_stock = serializers.SerializerMethodField()
    class Meta:
        model = Material
        fields = ("id","code","name","category","unit","minimum_stock_level","is_active","total_stock","low_stock","created_at","updated_at")
        read_only_fields = ("id","total_stock","low_stock","created_at","updated_at")
    def get_total_stock(self, obj): return str(material_total(obj.company, obj))
    def get_low_stock(self, obj): return material_total(obj.company, obj) <= obj.minimum_stock_level
    def validate_code(self, value):
        company = self.context.get("company") or self.instance.company
        if Material.objects.filter(company=company, code__iexact=value).exclude(id=getattr(self.instance,"id",None)).exists(): raise serializers.ValidationError("Material code already exists in this company.")
        return value
    def validate(self, attrs):
        if self.instance and "unit" in attrs and attrs["unit"] != self.instance.unit and self.instance.transactions.exists(): raise serializers.ValidationError({"unit":"Unit cannot change after stock has been recorded."})
        return attrs


class LocationSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source="project.name", read_only=True)
    class Meta:
        model = InventoryLocation
        fields = ("id","project","project_name","name","location_type","is_active","created_at","updated_at")
        read_only_fields = ("id","created_at","updated_at","project_name")
    def validate(self, attrs):
        company = self.context["company"]; project = attrs.get("project", getattr(self.instance,"project",None)); kind = attrs.get("location_type",getattr(self.instance,"location_type",None))
        if project and project.company_id != company.id: raise serializers.ValidationError({"project":"Project belongs to another company."})
        if kind == InventoryLocation.Type.PROJECT_SITE and not project: raise serializers.ValidationError({"project":"A project site requires a project."})
        if kind != InventoryLocation.Type.PROJECT_SITE and project: raise serializers.ValidationError({"project":"Only project sites can be tied to a project."})
        return attrs


class TransferItemSerializer(serializers.ModelSerializer):
    material_name = serializers.CharField(source="material.name", read_only=True)
    class Meta:
        model = InventoryTransferItem
        fields = ("id","material","material_name","quantity_requested","quantity_dispatched","quantity_received")
        read_only_fields = ("id","quantity_dispatched","quantity_received","material_name")


class TransferSerializer(serializers.ModelSerializer):
    items = TransferItemSerializer(many=True)
    source_name = serializers.CharField(source="source_location.name", read_only=True); destination_name = serializers.CharField(source="destination_location.name", read_only=True)
    class Meta:
        model = InventoryTransfer
        fields = ("id","source_location","source_name","destination_location","destination_name","purpose","status","notes","requested_by","dispatched_by","received_by","dispatched_at","received_at","version","items","created_at","updated_at")
        read_only_fields = ("id","status","requested_by","dispatched_by","received_by","dispatched_at","received_at","version","source_name","destination_name","created_at","updated_at")
    def validate(self, attrs):
        company=self.context["company"]; source=attrs.get("source_location",getattr(self.instance,"source_location",None)); destination=attrs.get("destination_location",getattr(self.instance,"destination_location",None))
        if source.company_id != company.id or destination.company_id != company.id: raise serializers.ValidationError("Locations must belong to the active company.")
        if source.id == destination.id: raise serializers.ValidationError({"destination_location":"Source and destination must differ."})
        return attrs
    def validate_items(self, items):
        company=self.context["company"]
        if not items: raise serializers.ValidationError("At least one material is required.")
        seen=set()
        for item in items:
            if item["material"].company_id != company.id: raise serializers.ValidationError("Material belongs to another company.")
            if item["material"].id in seen: raise serializers.ValidationError("A material can only appear once.")
            seen.add(item["material"].id)
        return items


class TransactionSerializer(serializers.ModelSerializer):
    material_name=serializers.CharField(source="material.name",read_only=True); location_name=serializers.CharField(source="location.name",read_only=True)
    class Meta:
        model=MaterialTransaction
        fields=("id","material","material_name","location","location_name","transaction_type","quantity","signed_quantity","transfer","project","reversal_of","occurred_at","recorded_by","reason","created_at")
        read_only_fields=fields


class ReceiptSerializer(serializers.Serializer):
    location=serializers.PrimaryKeyRelatedField(queryset=InventoryLocation.objects.all()); material=serializers.PrimaryKeyRelatedField(queryset=Material.objects.all()); quantity=serializers.DecimalField(max_digits=19,decimal_places=4,min_value=Decimal("0.0001")); occurred_at=serializers.DateTimeField(required=False); reason=serializers.CharField(required=False,allow_blank=True)


class UsageSerializer(ReceiptSerializer):
    project=serializers.PrimaryKeyRelatedField(queryset=Project.objects.all())


class AdjustmentSerializer(ReceiptSerializer):
    direction=serializers.ChoiceField(choices=["IN","OUT"]); reason=serializers.CharField(required=True,allow_blank=False)


class ReceiveTransferSerializer(serializers.Serializer):
    items=serializers.ListField(child=serializers.DictField(),allow_empty=False)
    def validate_items(self, items):
        for item in items:
            if set(item) != {"id","quantity"}: raise serializers.ValidationError("Each receipt item needs id and quantity.")
            try:
                if float(item["quantity"]) <= 0: raise ValueError
            except (ValueError,TypeError): raise serializers.ValidationError("Receipt quantity must be positive.")
        return items


class ReversalSerializer(serializers.Serializer):
    reason=serializers.CharField(required=True,allow_blank=False)
