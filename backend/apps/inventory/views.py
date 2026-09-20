import uuid
from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.services import audit_event
from apps.common.tenant import request_company
from apps.companies.models import CompanyMembership
from apps.projects.views import company_projects, project_or_404

from .models import InventoryBalance, InventoryLocation, InventoryTransfer, InventoryTransferItem, Material, MaterialTransaction
from .selectors import balances, project_usage
from .serializers import AdjustmentSerializer, LocationSerializer, MaterialSerializer, ReceiptSerializer, ReceiveTransferSerializer, ReversalSerializer, TransactionSerializer, TransferSerializer, UsageSerializer
from .services import record_transaction, transfer_types


def uuid_header(request):
    raw=request.headers.get("Idempotency-Key")
    if not raw:return None
    try:return uuid.UUID(raw)
    except ValueError as exc: raise ValidationError({"Idempotency-Key":"Must be a UUID."}) from exc


def location_or_404(request, location_id):
    company=request_company(request); location=InventoryLocation.objects.select_related("project").filter(id=location_id,company=company).first()
    if not location: raise NotFound("Inventory location was not found.")
    if location.project_id and not company_projects(request).filter(id=location.project_id).exists(): raise NotFound("Inventory location was not found.")
    return location


def material_or_404(request, material_id):
    company=request_company(request); material=Material.objects.filter(id=material_id,company=company).first()
    if not material: raise NotFound("Material was not found.")
    return material


def inventory_operator(request, location=None, project=None):
    role=request.membership.role
    if role == CompanyMembership.Role.OWNER:return True
    target_project=project or getattr(location,"project",None)
    if not target_project:return False
    return company_projects(request).filter(id=target_project.id).exists() and role in (CompanyMembership.Role.PROJECT_MANAGER,CompanyMembership.Role.SITE_MANAGER)


class MaterialListCreateView(APIView):
    def get(self,request):
        from django.db.models import Q
        company=request_company(request); queryset=Material.objects.filter(company=company)
        if request.query_params.get("search"): queryset=queryset.filter(Q(name__icontains=request.query_params["search"]) | Q(code__icontains=request.query_params["search"]))
        if request.query_params.get("category"): queryset=queryset.filter(category__iexact=request.query_params["category"])
        queryset=queryset.order_by("name")
        return Response(MaterialSerializer(queryset,many=True,context={"company":company}).data)
    @transaction.atomic
    def post(self,request):
        company=request_company(request)
        if request.membership.role!=CompanyMembership.Role.OWNER: raise PermissionDenied("Only owners can manage materials.")
        serializer=MaterialSerializer(data=request.data,context={"company":company});serializer.is_valid(raise_exception=True); material=serializer.save(company=company,created_by=request.user)
        audit_event(request,company,"inventory.material_created",material,after_state=MaterialSerializer(material,context={"company":company}).data)
        return Response(MaterialSerializer(material,context={"company":company}).data,status=status.HTTP_201_CREATED)


class MaterialDetailView(APIView):
    def get(self,request,material_id): return Response(MaterialSerializer(material_or_404(request,material_id),context={"company":request.company}).data)
    @transaction.atomic
    def patch(self,request,material_id):
        material=material_or_404(request,material_id)
        if request.membership.role!=CompanyMembership.Role.OWNER: raise PermissionDenied("Only owners can manage materials.")
        before=MaterialSerializer(material,context={"company":request.company}).data; serializer=MaterialSerializer(material,data=request.data,partial=True,context={"company":request.company});serializer.is_valid(raise_exception=True);material=serializer.save()
        audit_event(request,request.company,"inventory.material_updated" if material.is_active else "inventory.material_deactivated",material,before_state=before,after_state=MaterialSerializer(material,context={"company":request.company}).data)
        return Response(MaterialSerializer(material,context={"company":request.company}).data)


class LocationListCreateView(APIView):
    def get(self,request):
        company=request_company(request); return Response(LocationSerializer(InventoryLocation.objects.filter(company=company,project__in=company_projects(request)) | InventoryLocation.objects.filter(company=company,project=None),many=True,context={"company":company}).data)
    @transaction.atomic
    def post(self,request):
        company=request_company(request)
        if request.membership.role!=CompanyMembership.Role.OWNER: raise PermissionDenied("Only owners can manage inventory locations.")
        serializer=LocationSerializer(data=request.data,context={"company":company});serializer.is_valid(raise_exception=True);location=serializer.save(company=company);audit_event(request,company,"inventory.location_created",location,after_state=LocationSerializer(location,context={"company":company}).data);return Response(LocationSerializer(location,context={"company":company}).data,status=status.HTTP_201_CREATED)


class LocationDetailView(APIView):
    def get(self,request,location_id):return Response(LocationSerializer(location_or_404(request,location_id),context={"company":request.company}).data)
    @transaction.atomic
    def patch(self,request,location_id):
        location=location_or_404(request,location_id)
        if request.membership.role!=CompanyMembership.Role.OWNER:raise PermissionDenied("Only owners can manage inventory locations.")
        before=LocationSerializer(location,context={"company":request.company}).data;serializer=LocationSerializer(location,data=request.data,partial=True,context={"company":request.company});serializer.is_valid(raise_exception=True);location=serializer.save();audit_event(request,request.company,"inventory.location_updated",location,before_state=before,after_state=LocationSerializer(location,context={"company":request.company}).data);return Response(LocationSerializer(location,context={"company":request.company}).data)


class BalanceListView(APIView):
    def get(self,request):
        company=request_company(request); project_id=request.query_params.get("project")
        if project_id: project_or_404(request,project_id)
        query=balances(company,material=request.query_params.get("material"),location=request.query_params.get("location"),project=project_id,low_stock=request.query_params.get("low_stock","").lower()=="true")
        if request.membership.role not in (CompanyMembership.Role.OWNER,CompanyMembership.Role.ACCOUNTANT): query=query.filter(location__project__in=company_projects(request)) if hasattr(query,"filter") else [b for b in query if b.location.project_id and company_projects(request).filter(id=b.location.project_id).exists()]
        # Precompute total per material to avoid N+1 string bool bug
        totals={}
        balances_list = list(query) if not hasattr(query, "filter") else list(query)
        # compute totals once per material if needed
        from collections import defaultdict
        mat_totals=defaultdict(Decimal)
        for b in InventoryBalance.objects.filter(company=company).select_related("material"):
            mat_totals[b.material_id]+=b.quantity_on_hand
        data=[{"id":str(b.id),"material":str(b.material_id),"material_name":b.material.name,"unit":b.material.unit,"location":str(b.location_id),"location_name":b.location.name,"project":str(b.location.project_id) if b.location.project_id else None,"project_name":b.location.project.name if b.location.project_id else None,"quantity_on_hand":str(b.quantity_on_hand),"minimum_stock_level":str(b.material.minimum_stock_level),"low_stock": bool(b.material.minimum_stock_level >= mat_totals.get(b.material_id, Decimal("0")))} for b in balances_list]
        return Response(data)


class TransactionListView(APIView):
    def get(self,request):
        company=request_company(request);query=MaterialTransaction.objects.select_related("material","location","project").filter(company=company)
        if request.membership.role not in (CompanyMembership.Role.OWNER,CompanyMembership.Role.ACCOUNTANT): query=query.filter(project__in=company_projects(request))
        for param,field in (("material","material_id"),("location","location_id"),("project","project_id"),("transaction_type","transaction_type")):
            if request.query_params.get(param):query=query.filter(**{field:request.query_params[param]})
        if request.query_params.get("date_from"):query=query.filter(occurred_at__date__gte=request.query_params["date_from"])
        if request.query_params.get("date_to"):query=query.filter(occurred_at__date__lte=request.query_params["date_to"])
        page=PageNumberPagination();page.page_size=25;result=page.paginate_queryset(query,request);return page.get_paginated_response(TransactionSerializer(result,many=True).data)


class ReceiptView(APIView):
    @transaction.atomic
    def post(self,request):
        company=request_company(request);serializer=ReceiptSerializer(data=request.data);serializer.is_valid(raise_exception=True);d=serializer.validated_data;location=location_or_404(request,d["location"].id);material=material_or_404(request,d["material"].id)
        if not inventory_operator(request,location):raise PermissionDenied("You cannot receive stock into this location.")
        transaction_record,created=record_transaction(company=company,material=material,location=location,transaction_type=MaterialTransaction.Type.RECEIVE,quantity=d["quantity"],actor=request.user,project=location.project,occurred_at=d.get("occurred_at"),reason=d.get("reason",""),idempotency_key=uuid_header(request))
        if created:audit_event(request,company,"inventory.receipt_recorded",transaction_record,after_state=TransactionSerializer(transaction_record).data)
        return Response(TransactionSerializer(transaction_record).data,status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class TransferListCreateView(APIView):
    def get(self,request):
        company=request_company(request);query=InventoryTransfer.objects.select_related("source_location","destination_location").filter(company=company)
        return Response(TransferSerializer(query,many=True,context={"company":company}).data)
    @transaction.atomic
    def post(self,request):
        company=request_company(request);serializer=TransferSerializer(data=request.data,context={"company":company});serializer.is_valid(raise_exception=True);d=serializer.validated_data;source=location_or_404(request,d["source_location"].id);destination=location_or_404(request,d["destination_location"].id)
        if not (inventory_operator(request,source) or inventory_operator(request,destination)):raise PermissionDenied("You cannot create this transfer.")
        transfer=InventoryTransfer.objects.create(company=company,source_location=source,destination_location=destination,purpose=d["purpose"],notes=d.get("notes",""),requested_by=request.user)
        for item in d["items"]:InventoryTransferItem.objects.create(transfer=transfer,material=material_or_404(request,item["material"].id),quantity_requested=item["quantity_requested"])
        audit_event(request,company,"inventory.transfer_created",transfer,after_state=TransferSerializer(transfer,context={"company":company}).data);return Response(TransferSerializer(transfer,context={"company":company}).data,status=status.HTTP_201_CREATED)


def transfer_or_404(request,transfer_id):
    company=request_company(request);transfer=InventoryTransfer.objects.select_related("source_location__project","destination_location__project").filter(id=transfer_id,company=company).first()
    if not transfer:raise NotFound("Inventory transfer was not found.")
    if not(inventory_operator(request,transfer.source_location) or inventory_operator(request,transfer.destination_location)):raise NotFound("Inventory transfer was not found.")
    return transfer


class TransferDetailView(APIView):
    def get(self,request,transfer_id):return Response(TransferSerializer(transfer_or_404(request,transfer_id),context={"company":request.company}).data)
    @transaction.atomic
    def patch(self,request,transfer_id):
        transfer=transfer_or_404(request,transfer_id)
        if transfer.status!=transfer.Status.DRAFT:raise ValidationError("Dispatched transfers cannot be edited.")
        if not inventory_operator(request,transfer.source_location):raise PermissionDenied("You cannot edit this transfer.")
        serializer=TransferSerializer(transfer,data=request.data,partial=True,context={"company":request.company});serializer.is_valid(raise_exception=True);d=serializer.validated_data
        if "items" in d:raise ValidationError("Transfer items cannot be replaced; create a new draft transfer.")
        transfer=serializer.save(version=transfer.version+1);return Response(TransferSerializer(transfer,context={"company":request.company}).data)


class TransferDispatchView(APIView):
    @transaction.atomic
    def post(self,request,transfer_id):
        transfer=transfer_or_404(request,transfer_id);transfer=InventoryTransfer.objects.select_for_update().get(id=transfer.id);key=uuid_header(request)
        if transfer.status!=transfer.Status.DRAFT:
            if key and key==transfer.dispatch_idempotency_key:return Response(TransferSerializer(transfer,context={"company":request.company}).data)
            raise ValidationError("Only draft transfers can be dispatched.")
        if not inventory_operator(request,transfer.source_location):raise PermissionDenied("You cannot dispatch this transfer.")
        out_type,_=transfer_types(transfer)
        for item in transfer.items.select_for_update().select_related("material"):
            if item.quantity_requested<=0:raise ValidationError("Transfer quantities must be greater than zero.")
            record_transaction(company=transfer.company,material=item.material,location=transfer.source_location,transaction_type=out_type,quantity=item.quantity_requested,actor=request.user,project=transfer.source_location.project,transfer=transfer,transfer_item=item,reason=transfer.notes)
            item.quantity_dispatched=item.quantity_requested;item.save(update_fields=["quantity_dispatched","updated_at"])
        transfer.status=transfer.Status.DISPATCHED;transfer.dispatched_by=request.user;transfer.dispatched_at=timezone.now();transfer.dispatch_idempotency_key=key;transfer.version+=1;transfer.save();audit_event(request,transfer.company,"inventory.transfer_dispatched",transfer,after_state=TransferSerializer(transfer,context={"company":transfer.company}).data);return Response(TransferSerializer(transfer,context={"company":transfer.company}).data)


class TransferReceiveView(APIView):
    @transaction.atomic
    def post(self,request,transfer_id):
        transfer=transfer_or_404(request,transfer_id);transfer=InventoryTransfer.objects.select_for_update().get(id=transfer.id);key=uuid_header(request)
        if transfer.status not in (transfer.Status.DISPATCHED,transfer.Status.PARTIALLY_RECEIVED):
            if key and key==transfer.receive_idempotency_key:return Response(TransferSerializer(transfer,context={"company":request.company}).data)
            raise ValidationError("Only dispatched transfers can be received.")
        if not inventory_operator(request,transfer.destination_location):raise PermissionDenied("You cannot receive this transfer.")
        serializer=ReceiveTransferSerializer(data=request.data);serializer.is_valid(raise_exception=True);item_map={str(i.id):i for i in transfer.items.select_for_update().select_related("material")};_,in_type=transfer_types(transfer)
        for row in serializer.validated_data["items"]:
            item=item_map.get(str(row["id"]));qty=Decimal(str(row["quantity"]))
            if not item:raise ValidationError("Receipt item does not belong to this transfer.")
            if item.quantity_received+qty>item.quantity_dispatched:raise ValidationError("Cannot receive more than dispatched.")
            record_transaction(company=transfer.company,material=item.material,location=transfer.destination_location,transaction_type=in_type,quantity=qty,actor=request.user,project=transfer.destination_location.project,transfer=transfer,transfer_item=item,reason=transfer.notes)
            item.quantity_received+=qty;item.save(update_fields=["quantity_received","updated_at"])
        items=list(transfer.items.all());complete=all(i.quantity_received==i.quantity_dispatched for i in items);transfer.status=transfer.Status.RECEIVED if complete else transfer.Status.PARTIALLY_RECEIVED;transfer.received_by=request.user;transfer.received_at=timezone.now() if complete else None;transfer.receive_idempotency_key=key;transfer.version+=1;transfer.save();audit_event(request,transfer.company,"inventory.transfer_completed" if complete else "inventory.transfer_partially_received",transfer,after_state=TransferSerializer(transfer,context={"company":transfer.company}).data);return Response(TransferSerializer(transfer,context={"company":transfer.company}).data)


class TransferCancelView(APIView):
    @transaction.atomic
    def post(self,request,transfer_id):
        transfer=transfer_or_404(request,transfer_id)
        if transfer.status!=transfer.Status.DRAFT:raise ValidationError("Only draft transfers can be cancelled.")
        if not inventory_operator(request,transfer.source_location):raise PermissionDenied("You cannot cancel this transfer.")
        transfer.status=transfer.Status.CANCELLED;transfer.version+=1;transfer.save(update_fields=["status","version","updated_at"]);audit_event(request,transfer.company,"inventory.transfer_cancelled",transfer,after_state=TransferSerializer(transfer,context={"company":transfer.company}).data);return Response(TransferSerializer(transfer,context={"company":transfer.company}).data)


class UsageView(APIView):
    @transaction.atomic
    def post(self,request):
        company=request_company(request);serializer=UsageSerializer(data=request.data);serializer.is_valid(raise_exception=True);d=serializer.validated_data;project=project_or_404(request,d["project"].id);location=location_or_404(request,d["location"].id);material=material_or_404(request,d["material"].id)
        if location.project_id!=project.id or location.location_type!=InventoryLocation.Type.PROJECT_SITE:raise ValidationError("Usage must be recorded against the project's site location.")
        if not inventory_operator(request,location,project):raise PermissionDenied("You cannot record project material usage.")
        txn,created=record_transaction(company=company,material=material,location=location,transaction_type=MaterialTransaction.Type.USE,quantity=d["quantity"],actor=request.user,project=project,occurred_at=d.get("occurred_at"),reason=d.get("reason",""),idempotency_key=uuid_header(request))
        if created:audit_event(request,company,"inventory.material_used",txn,after_state=TransactionSerializer(txn).data)
        return Response(TransactionSerializer(txn).data,status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class AdjustmentView(APIView):
    @transaction.atomic
    def post(self,request):
        company=request_company(request)
        if request.membership.role!=CompanyMembership.Role.OWNER:raise PermissionDenied("Only owners can adjust inventory.")
        serializer=AdjustmentSerializer(data=request.data);serializer.is_valid(raise_exception=True);d=serializer.validated_data;location=location_or_404(request,d["location"].id);material=material_or_404(request,d["material"].id);kind=MaterialTransaction.Type.ADJUSTMENT_IN if d["direction"]=="IN" else MaterialTransaction.Type.ADJUSTMENT_OUT
        txn,created=record_transaction(company=company,material=material,location=location,transaction_type=kind,quantity=d["quantity"],actor=request.user,project=location.project,occurred_at=d.get("occurred_at"),reason=d["reason"],idempotency_key=uuid_header(request))
        if created:audit_event(request,company,"inventory.adjustment",txn,after_state=TransactionSerializer(txn).data)
        return Response(TransactionSerializer(txn).data,status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class TransactionReverseView(APIView):
    @transaction.atomic
    def post(self,request,transaction_id):
        company=request_company(request)
        if request.membership.role!=CompanyMembership.Role.OWNER:raise PermissionDenied("Only owners can reverse inventory transactions.")
        original=MaterialTransaction.objects.select_for_update().select_related("material","location","project").filter(id=transaction_id,company=company).first()
        if not original:raise NotFound("Material transaction was not found.")
        if MaterialTransaction.objects.filter(reversal_of=original).exists():raise ValidationError("This transaction has already been reversed.")
        serializer=ReversalSerializer(data=request.data);serializer.is_valid(raise_exception=True);reverse_type=MaterialTransaction.Type.ADJUSTMENT_OUT if original.signed_quantity>0 else MaterialTransaction.Type.ADJUSTMENT_IN
        txn,_=record_transaction(company=company,material=original.material,location=original.location,transaction_type=reverse_type,quantity=original.quantity,actor=request.user,project=original.project,reason=serializer.validated_data["reason"],reversal_of=original)
        audit_event(request,company,"inventory.transaction_reversed",txn,after_state=TransactionSerializer(txn).data);return Response(TransactionSerializer(txn).data,status=status.HTTP_201_CREATED)
