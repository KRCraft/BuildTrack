from decimal import Decimal

from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.companies.models import Company, CompanyMembership
from apps.projects.models import Project, ProjectAssignment

from .models import InventoryBalance, Material, MaterialTransaction


class InventoryTests(APITestCase):
    def setUp(self):
        self.owner=User.objects.create_user(email="owner@alpha.test",password="Pass12345!");self.manager=User.objects.create_user(email="manager@alpha.test",password="Pass12345!");self.other=User.objects.create_user(email="owner@beta.test",password="Pass12345!")
        self.company=Company.objects.create(name="Alpha",slug="alpha");self.other_company=Company.objects.create(name="Beta",slug="beta")
        self.owner_m=CompanyMembership.objects.create(company=self.company,user=self.owner,role=CompanyMembership.Role.OWNER);self.manager_m=CompanyMembership.objects.create(company=self.company,user=self.manager,role=CompanyMembership.Role.PROJECT_MANAGER);CompanyMembership.objects.create(company=self.other_company,user=self.other,role=CompanyMembership.Role.OWNER)
        self.project=Project.objects.create(company=self.company,name="Tower",code="T-1",created_by=self.owner);ProjectAssignment.objects.create(project=self.project,membership=self.manager_m,assignment_role=ProjectAssignment.AssignmentRole.PROJECT_MANAGER)
        self.client.force_authenticate(self.owner);self.headers={"HTTP_X_COMPANY_ID":str(self.company.id)}
        self.material=self.create_material();self.warehouse=self.create_location("Central","WAREHOUSE");self.site=self.create_location("Tower site","PROJECT_SITE",self.project.id)

    def create_material(self):
        response=self.client.post("/api/v1/materials/",{"code":"CEMENT","name":"Cement","unit":"BAG","minimum_stock_level":"10"},format="json",**self.headers);self.assertEqual(response.status_code,status.HTTP_201_CREATED);return Material.objects.get(id=response.data["id"])
    def create_location(self,name,kind,project=None):
        payload={"name":name,"location_type":kind};
        if project:payload["project"]=str(project)
        response=self.client.post("/api/v1/inventory/locations/",payload,format="json",**self.headers);self.assertEqual(response.status_code,status.HTTP_201_CREATED);return response.data
    def receive(self,location,qty,key=None):
        headers=self.headers.copy();
        if key:headers["HTTP_IDEMPOTENCY_KEY"]=key
        return self.client.post("/api/v1/inventory/receipts/",{"location":location["id"],"material":str(self.material.id),"quantity":str(qty),"reason":"delivery"},format="json",**headers)

    def test_receipt_idempotency_and_material_unit_immutability(self):
        key="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa";self.assertEqual(self.receive(self.warehouse,100,key).status_code,status.HTTP_201_CREATED);self.assertEqual(self.receive(self.warehouse,100,key).status_code,status.HTTP_200_OK)
        self.assertEqual(InventoryBalance.objects.get(material=self.material,location_id=self.warehouse["id"]).quantity_on_hand,Decimal("100"))
        response=self.client.patch(f"/api/v1/materials/{self.material.id}/",{"unit":"KG"},format="json",**self.headers);self.assertEqual(response.status_code,status.HTTP_400_BAD_REQUEST)

    def test_transfer_partial_receive_and_no_over_receive(self):
        self.receive(self.warehouse,100)
        payload={"source_location":self.warehouse["id"],"destination_location":self.site["id"],"purpose":"ALLOCATION","items":[{"material":str(self.material.id),"quantity_requested":"100"}]}
        response=self.client.post("/api/v1/inventory/transfers/",payload,format="json",**self.headers);self.assertEqual(response.status_code,status.HTTP_201_CREATED);transfer=response.data["id"]
        self.assertEqual(self.client.post(f"/api/v1/inventory/transfers/{transfer}/dispatch/",{},format="json",**self.headers).status_code,status.HTTP_200_OK)
        item=response.data["items"][0]["id"]
        response=self.client.post(f"/api/v1/inventory/transfers/{transfer}/receive/",{"items":[{"id":item,"quantity":"60"}]},format="json",**self.headers);self.assertEqual(response.data["status"],"PARTIALLY_RECEIVED")
        self.assertEqual(self.client.post(f"/api/v1/inventory/transfers/{transfer}/receive/",{"items":[{"id":item,"quantity":"41"}]},format="json",**self.headers).status_code,status.HTTP_400_BAD_REQUEST)
        response=self.client.post(f"/api/v1/inventory/transfers/{transfer}/receive/",{"items":[{"id":item,"quantity":"40"}]},format="json",**self.headers);self.assertEqual(response.data["status"],"RECEIVED")
        self.assertEqual(InventoryBalance.objects.get(material=self.material,location_id=self.site["id"]).quantity_on_hand,Decimal("100"))

    def test_usage_negative_protection_adjustment_and_reversal(self):
        self.receive(self.site,10)
        payload={"project":str(self.project.id),"location":self.site["id"],"material":str(self.material.id),"quantity":"4","reason":"pour"}
        response=self.client.post("/api/v1/inventory/usage/",payload,format="json",**self.headers);self.assertEqual(response.status_code,status.HTTP_201_CREATED);usage=response.data["id"]
        payload["quantity"]="7";self.assertEqual(self.client.post("/api/v1/inventory/usage/",payload,format="json",**self.headers).status_code,status.HTTP_400_BAD_REQUEST)
        response=self.client.post(f"/api/v1/inventory/transactions/{usage}/reverse/",{"reason":"wrong entry"},format="json",**self.headers);self.assertEqual(response.status_code,status.HTTP_201_CREATED);self.assertEqual(InventoryBalance.objects.get(material=self.material,location_id=self.site["id"]).quantity_on_hand,Decimal("10"))
        self.client.force_authenticate(self.manager);response=self.client.post("/api/v1/inventory/adjustments/",{"location":self.site["id"],"material":str(self.material.id),"quantity":"1","direction":"IN","reason":"count"},format="json",**self.headers);self.assertEqual(response.status_code,status.HTTP_403_FORBIDDEN)

    def test_tenant_isolation_and_wrong_project_location(self):
        self.client.force_authenticate(self.other);self.assertEqual(self.client.get(f"/api/v1/materials/{self.material.id}/",HTTP_X_COMPANY_ID=str(self.other_company.id)).status_code,status.HTTP_404_NOT_FOUND)
        self.client.force_authenticate(self.owner);wrong=Project.objects.create(company=self.company,name="Other",code="T-2",created_by=self.owner);self.receive(self.site,10)
        response=self.client.post("/api/v1/inventory/usage/",{"project":str(wrong.id),"location":self.site["id"],"material":str(self.material.id),"quantity":"1"},format="json",**self.headers);self.assertEqual(response.status_code,status.HTTP_400_BAD_REQUEST)
