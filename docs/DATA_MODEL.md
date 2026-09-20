# BuildTrack — Data Model v1.1

> DB: PostgreSQL (prod) / SQLite (dev USE_SQLITE=True). ORM: Django 5.  
> Source of truth: `backend/apps/*/models.py`. Frontend mirror: `frontend/src/utils/apiTypes.js` (legacy) + `frontend/lib/api.ts` types.

---

## 1. ER overview (live, 2026-09-20)

```
                         ┌─────────┐
                         │ Company │ 1
                         └────┬────┘
                              │ 1:N
              ┌───────────────┼────────────────┐
              │               │                │
       ┌──────▼─────┐   ┌─────▼──────┐   ┌────▼─────┐
       │ Membership │   │  Project   │   │ Material │
       │ (User ↔    │   │ (code,     │   └────┬─────┘
       │  Company)  │   │  status)   │        │
       └─────┬──────┘   └─────┬──────┘        │
             │ 1:N            │ 1:1           │ N:M via balances/transactions
             │          ┌─────▼──────┐        │
             └──────────┤ Assignment │   ┌────▼────────────────┐
                        └────────────┘   │ InventoryLocation   │
                                         │ InventoryBalance    │
                                         │ MaterialTransaction │
                                         │ InventoryTransfer   │
                                         └─────────────────────┘
                              ┌──────────┬──────┴──────┬──────────┐
                              │          │             │          │
                        ┌─────▼─────┐ ┌──▼─────┐ ┌────▼─────┐ ┌──▼────┐
                        │  Budget   │ │Expense │ │  Worker  │ │ Daily │
                        │  Version  │ │ Supplier│ │          │ │ Report│
                        │  Category │ └────────┘ └──────────┘ │Revision│
                        └───────────┘                          └───────┘
                              │
                        ┌─────▼──────┐
                        │  AuditLog  │ (immutable, company-scoped)
                        └────────────┘
```

Relation summary:

| From | To | Type | On delete | Notes |
|------|----|------|-----------|-------|
| Company → User via Membership | M:N | PROTECT/CASCADE | tenant isolation via `X-Company-ID` |
| Project → Company | N:1 | PROTECT | all company-scoped |
| Budget → Project | 1:1 | PROTECT | one budget per project |
| BudgetVersion → Budget | N:1 | CASCADE | `active_version` FK on Budget |
| Expense → Project, BudgetCategory, Supplier | N:1 | PROTECT | must match company+approved budget |
| Material → Company | N:1 | PROTECT | `code` unique per company |
| InventoryBalance → Material+Location | N:1 | CASCADE | quantity_on_hand aggregated |
| MaterialTransaction → Company+Project+Location | N:1 | PROTECT | signed qty, idempotency |
| DailyReport → Project | N:1 | CASCADE | `report_date` unique per project |
| DailyReportRevision → DailyReport | N:1 | CASCADE | `revision_number` monotonic |
| AuditLog → Company, User | N:1 nullable | PROTECT/SET_NULL | immutable |

Legacy tables kept on disk but **not in `INSTALLED_APPS`**: `clients_client`, `quotes_quoterequest`, `contact_contactmessage`, `testimonials_testimonial` — see §7.

---

## 2. Tables (live)

### 2.1 Company (`companies_company`)

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID PK | default uuid4 |  |
| `name` | VARCHAR(255) | NOT NULL |  |
| `slug` | SLUG(80) | UNIQUE | auto from name `-2` suffix on collision |
| `currency_code` | CHAR(3) | regex `^[A-Z]{3}$`, default `UZS` | company accounting currency |
| `timezone` | VARCHAR(64) | default `Asia/Tashkent` |  |
| `country_code` | VARCHAR(2) | blank |  |
| `address` | TEXT | blank |  |
| `is_active` | BOOL | default True, indexed |  |
| `created_at` | TIMESTAMPTZ | auto_now_add |  |
| `updated_at` | TIMESTAMPTZ | auto_now |  |

### 2.2 User (`accounts_user` — custom, email as USERNAME_FIELD)

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID PK |  |  |
| `username` | VARCHAR(150) | UNIQUE, editable=False, auto uuid hex | internal, not used |
| `email` | EMAIL | UNIQUE, NOT NULL | login identifier |
| `first_name` | VARCHAR(150) | NOT NULL |  |
| `last_name` | VARCHAR(150) | blank |  |
| `password` | VARCHAR(128) | hashed | Django validators (4) |
| `is_staff` | BOOL |  |  |
| `is_active` | BOOL |  |  |
| `created_at` | TIMESTAMPTZ | via UUIDTimeStampedModel? actually AbstractUser |  |

### 2.3 CompanyMembership (`companies_companymembership`)

| Field | Type | Constraints |
|-------|------|-------------|
| `id` | UUID PK |  |
| `company` | FK Company | PROTECT |
| `user` | FK User | CASCADE |
| `role` | VARCHAR | choices `OWNER, PROJECT_MANAGER, SITE_MANAGER, ACCOUNTANT, VIEWER` |
| `status` | VARCHAR | choices `ACTIVE, INACTIVE`, default `ACTIVE` |
| `created_at`/`updated_at` | TIMESTAMPTZ |  |

Unique: `(company, user)`. `is_active` helper filters `status=ACTIVE` + `company.is_active`.

### 2.4 CompanyInvitation (`companies_companyinvitation`)

| Field | Type |
|-------|------|
| `company` FK | PROTECT |
| `email` | invited email, lower-cased match |
| `role` | requested role |
| `token_hash` | SHA256 of `secrets.token_urlsafe(32)`, UNIQUE |
| `status` | `PENDING, ACCEPTED, REVOKED, EXPIRED` |
| `expires_at` | `now+7d` |
| `created_by` FK User | PROTECT |

Flow: pending → revoked on re-invite, expired if `expires_at <= now`.

### 2.5 Project (`projects_project`)

| Field | Type | Constraints |
|-------|------|-------------|
| `id` | UUID PK |  |
| `company` | FK Company | PROTECT |
| `code` | VARCHAR(50) | UNIQUE per company, `code__iexact` validated |
| `name` | VARCHAR(200) |  |
| `client_name` | VARCHAR(200) | denormalized |
| `status` | VARCHAR | `DRAFT, ACTIVE, ON_HOLD, COMPLETED, ARCHIVED` |
| `budget_planned` | DECIMAL(12,2) | nullable |
| `progress_percent_cache` | DECIMAL(5,2) | 0–100, from approved reports |
| `is_archived` | BOOL |  |
| `version` | INT | optimistic lock |
| `created_by` FK User | PROTECT |

Indexes: `(company, code)`, `(company, status)`.

### 2.6 ProjectAssignment (`projects_projectassignment`)

| Field | Type |
|-------|------|
| `project` FK | CASCADE |
| `membership` FK CompanyMembership | CASCADE |
| `assignment_role` | `PROJECT_MANAGER, SITE_MANAGER, VIEWER` etc |
| `is_active` BOOL |  |

Company-scoped: `project.company == membership.company`.

### 2.7 Budget (`budgets_budget`)

| Field | Type |
|-------|------|
| `company` FK | PROTECT |
| `project` OneToOne Project | PROTECT |
| `active_version` FK BudgetVersion nullable | SET_NULL |
| `created_by` FK User | PROTECT |

### 2.8 BudgetVersion (`budgets_budgetversion`)

| Field | Type |
|-------|------|
| `company` FK | PROTECT |
| `budget` FK Budget | CASCADE |
| `version_number` INT | monotonic |
| `status` | `DRAFT, PENDING_APPROVAL, APPROVED, REJECTED, SUPERSEDED` |
| `currency_code` | copies `company.currency_code` |
| `total_planned_amount` DECIMAL | `SUM categories.planned_amount` via `refresh_total()` |
| `version` INT | lock |
| `submitted_by/approved_by` FK User nullable | SET_NULL |

### 2.9 BudgetCategory (`budgets_budgetcategory`)

| Field | Type |
|-------|------|
| `company` FK | PROTECT |
| `budget_version` FK | CASCADE |
| `parent` FK self nullable | CASCADE |
| `name` VARCHAR |  |
| `planned_amount` DECIMAL |  |
| `lineage_key` UUID | preserves lineage across revisions |

### 2.10 Supplier (`expenses_supplier`)

| Field | Type |
|-------|------|
| `company` FK | PROTECT |
| `name` VARCHAR |  |
| `tax_id`, `phone`, `email`, `address` | nullable |
| `is_active` BOOL |  |

### 2.11 Expense (`expenses_expense`)

| Field | Type |
|-------|------|
| `id` UUID PK |  |
| `company` FK | PROTECT |
| `project` FK | PROTECT, must match company |
| `budget_category` FK | PROTECT, must be in `project.budget.active_version` |
| `supplier` FK nullable | PROTECT |
| `expense_type` | `STANDARD, REVERSAL` |
| `reverses_expense` FK self nullable | PROTECT |
| `amount` DECIMAL(12,2) |  |
| `currency_code` CHAR(3) | must == `company.currency_code` |
| `expense_date` DATE |  |
| `status` | `DRAFT, PENDING_APPROVAL, APPROVED, REJECTED, CANCELLED` |
| `idempotency_key` UUID nullable | UNIQUE per company |
| `correction_group_id` UUID | uuid4, shared with reversal |
| `version` INT |  |

Approvals: `ExpenseApproval` (`action` SUBMITTED/APPROVED/REJECTED/REVERSED) + `ExpenseAttachment` (FileField, 10MB, PDF/JPG/PNG).

### 2.12 Material (`inventory_material`)

| Field | Type |
|-------|------|
| `company` FK | PROTECT |
| `name` VARCHAR |  |
| `code` VARCHAR | UNIQUE per company |
| `unit` VARCHAR | `kg, m, pcs` etc |
| `category` VARCHAR nullable | filter |
| `minimum_stock_level` DECIMAL | validator >=0 |
| `is_active` BOOL |  |

### 2.13 InventoryLocation (`inventory_inventorylocation`)

| Field | Type |
|-------|------|
| `company` FK | PROTECT |
| `name` VARCHAR |  |
| `project` FK nullable | PROTECT, if set must be in `company_projects` |
| `location_type` | `WAREHOUSE, PROJECT_SITE` |
| `address` TEXT blank |  |

### 2.14 InventoryBalance (`inventory_inventorybalance`)

| Field | Type |
|-------|------|
| `company` FK | PROTECT |
| `material` FK | CASCADE |
| `location` FK | CASCADE |
| `quantity_on_hand` DECIMAL | signed aggregation via `record_transaction()` |

Unique: `(material, location)`.

### 2.15 MaterialTransaction (`inventory_materialtransaction`)

| Field | Type |
|-------|------|
| `company` FK | PROTECT |
| `material` FK | PROTECT |
| `location` FK | PROTECT |
| `project` FK nullable | PROTECT |
| `transaction_type` | `RECEIVE, USE, TRANSFER_OUT, TRANSFER_IN, ADJUSTMENT_IN, ADJUSTMENT_OUT` |
| `quantity` DECIMAL | always positive, signed via `signed_quantity` property |
| `occurred_at` TIMESTAMPTZ |  |
| `idempotency_key` UUID nullable | UNIQUE |
| `reversal_of` FK self nullable | PROTECT |

Blocks negative stock: `quantity_on_hand + signed < 0` → `ValidationError`.

### 2.16 InventoryTransfer (`inventory_inventorytransfer`)

| Field | Type |
|-------|------|
| `company` FK | PROTECT |
| `source_location` FK | PROTECT |
| `destination_location` FK | PROTECT |
| `status` | `DRAFT, DISPATCHED, PARTIALLY_RECEIVED, RECEIVED, CANCELLED` |
| `purpose` VARCHAR | `SITE_TRANSFER` etc |
| `dispatch_idempotency_key`, `receive_idempotency_key` UUID nullable |  |

Items: `InventoryTransferItem` (`material`, `quantity_requested/dispatched/received`).

### 2.17 Worker (`workforce_worker`)

| Field | Type |
|-------|------|
| `company` FK | PROTECT |
| `full_name` VARCHAR |  |
| `phone` VARCHAR blank |  |
| `specialty` VARCHAR blank |  |
| `status` | `ACTIVE, INACTIVE` |
| `created_by` FK User | PROTECT |

Assignment via `ProjectAssignment` or workforce-specific M2M.

### 2.18 DailyReport (`reports_dailyreport`)

| Field | Type |
|-------|------|
| `company` FK | PROTECT |
| `project` FK | CASCADE |
| `report_date` DATE | UNIQUE per project |
| `approved_revision` FK DailyReportRevision nullable | SET_NULL |
| `created_by` FK User | PROTECT |

### 2.19 DailyReportRevision (`reports_dailyreportrevision`)

| Field | Type |
|-------|------|
| `company` FK | PROTECT |
| `daily_report` FK | CASCADE |
| `revision_number` INT | monotonic |
| `work_completed` TEXT |  |
| `progress_delta` DECIMAL(5,2) | can be negative (requires PM/OWNER + reason) |
| `worker_count` INT |  |
| `issues`, `weather_notes` TEXT |  |
| `revision_reason` TEXT | required if not first |
| `status` | `DRAFT, SUBMITTED, APPROVED, REJECTED, SUPERSEDED` |
| `version` INT | lock |

Material usages: `DailyReportMaterialUsage` (`material`, `inventory_location`, `quantity_used`, `material_transaction` FK nullable — set on APPROVE via `record_transaction USE`).

### 2.20 AuditLog (`audit_auditlog`)

| Field | Type |
|-------|------|
| `company` FK nullable | PROTECT |
| `actor` FK User nullable | SET_NULL |
| `actor_snapshot` JSON |  |
| `action` VARCHAR(120) | e.g. `project.created`, `inventory.transfer_dispatched` |
| `entity_type`, `entity_id` | polymorphic |
| `before_state`, `after_state` JSON | DjangoJSONEncoder |
| `request_id` UUID | `X-Request-ID` or random |
| `ip_address` | `X-Forwarded-For` first hop |
| `user_agent` TEXT |  |

Immutable: `save()` blocks update if PK exists, `delete()` raises. Bulk `QuerySet.delete/update` still bypasses — add DB trigger for hard guarantee (future). Only `OWNER` can list.

---

## 3. Migration order

1. `common` (abstract) → 2. `accounts` (User) → 3. `companies` (Company, Membership, Invitation) → 4. `projects` (Project, Assignment) → 5. `budgets` (Budget, Version, Category) → 6. `expenses` (Supplier, Expense) → 7. `inventory` (Material, Location, Balance, Transaction, Transfer) → 8. `workforce` (Worker) → 9. `reports` (DailyReport, Revision) → 10. `audit` → 11. `dashboard` (views only, no models).

Legacy `clients, quotes, contact` migrations exist on disk but not applied (not in INSTALLED_APPS) — do not run.

---

## 4. Seed / fixture guidance

- 1 owner user, 2 companies (UZS), 3 projects (ACTIVE/COMPLETED), 1 budget per project with 2 versions (DRAFT→APPROVED), 3 suppliers, 5 expenses (DRAFT→APPROVED→reversal), 4 materials + 2 warehouses + 2 project sites, balances via RECEIVE, 2 transfers (DISPATCHED→RECEIVED), 3 workers, 2 daily reports with revisions, audit logs auto.

---

## 5. Non-goals

No payments gateway, no S3, no billing. `gallery` is JSONB/no table, `attachment_url` is FileField `media/` (S3 in prod). Redis optional until Celery.
