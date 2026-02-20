# Salesforce Import Feature Design

**Date:** 2026-02-18
**Branch:** sf_import
**Status:** Approved

## Summary

Import Accounts, Contacts, Opportunities, Products, Orders, and Quotes from Salesforce into BottleCRM. Uses OAuth 2.0 for authentication, `simple-salesforce` for API access, and Celery for background processing with progress tracking. Supports re-import with duplicate skipping via Salesforce ID tracking.

## Decisions

- **Auth:** OAuth 2.0 Web Server Flow
- **Library:** `simple-salesforce`
- **Import type:** One-time + re-import (not continuous sync)
- **Duplicate handling:** Skip records with existing SF IDs
- **Object selection:** User picks which object types to import
- **SF Orders:** New dedicated `Order` model (not mapped to Invoice)
- **Processing:** Celery background tasks with progress tracking

## New Django Apps

### `salesforce_imports` app

**SalesforceConnection** - OAuth tokens per org
- `org` (FK Org, unique)
- `instance_url` (CharField)
- `access_token` (encrypted TextField)
- `refresh_token` (encrypted TextField)
- `token_expires_at` (DateTimeField)
- `connected_by` (FK Profile)
- `is_active` (BooleanField)

**ImportJob** - tracks each import run
- `org` (FK Org)
- `status` (PENDING / IN_PROGRESS / COMPLETED / FAILED / CANCELLED)
- `object_types` (JSONField - list like `["Account", "Contact"]`)
- `started_at`, `completed_at` (DateTimeField)
- `started_by` (FK Profile)
- `total_records`, `imported_count`, `skipped_count`, `error_count` (IntegerField)
- `error_log` (JSONField)

**ImportedRecord** - SF ID to CRM ID mapping for dedup
- `org` (FK Org)
- `salesforce_id` (CharField)
- `salesforce_object_type` (CharField)
- `content_type` + `object_id` (GenericFK)
- `import_job` (FK ImportJob)
- Unique constraint: `(org, salesforce_id, salesforce_object_type)`

### `orders` app (or extend `invoices`)

**Order** (BaseOrgModel)
- `name`, `order_number`, `status` (Draft/Activated/Completed/Cancelled)
- `account` (FK Account), `contact` (FK Contact), `opportunity` (FK Opportunity, optional)
- `currency`, `subtotal`, `total_amount`, `discount_amount`, `tax_amount`
- `order_date`, `activated_date`, `shipped_date`
- Billing + shipping address fields
- `description`, `org` (FK Org)

**OrderLineItem** (BaseOrgModel)
- `order` (FK Order), `product` (FK Product)
- `name`, `description`, `quantity`, `unit_price`, `total`, `order` (sort order)

## Field Mapping

### Account -> accounts.Account
| SF Field | CRM Field |
|---|---|
| Name | name |
| Website | website |
| Phone | phone |
| Industry | industry |
| NumberOfEmployees | number_of_employees |
| AnnualRevenue | annual_revenue |
| Description | description |
| BillingStreet/City/State/PostalCode/Country | address_line/city/state/postcode/country |

### Contact -> contacts.Contact
| SF Field | CRM Field |
|---|---|
| FirstName/LastName | first_name/last_name |
| Email | email |
| Phone | phone |
| Title | title |
| Department | department |
| AccountId | account (via ImportedRecord lookup) |
| DoNotCall | do_not_call |
| MailingStreet/City/State/PostalCode/Country | address_line/city/state/postcode/country |
| Description | description |

### Opportunity -> opportunity.Opportunity
| SF Field | CRM Field |
|---|---|
| Name | name |
| AccountId | account (via ImportedRecord) |
| StageName | stage |
| Amount | amount |
| Probability | probability |
| CloseDate | closed_on |
| LeadSource | lead_source |
| Type | opportunity_type |
| Description | description |

### Product2 -> invoices.Product
| SF Field | CRM Field |
|---|---|
| Name | name |
| ProductCode | sku |
| Description | description |
| IsActive | is_active |

### Order -> orders.Order
| SF Field | CRM Field |
|---|---|
| OrderNumber | order_number |
| Status | status |
| AccountId | account (via ImportedRecord) |
| EffectiveDate | order_date |
| TotalAmount | total_amount |
| Description | description |
| Billing/Shipping address fields | billing/shipping address fields |

### Quote -> invoices.Estimate
| SF Field | CRM Field |
|---|---|
| Name | title |
| QuoteNumber | estimate_number |
| Status | status |
| AccountId/ContactId/OpportunityId | account/contact/opportunity (via ImportedRecord) |
| Subtotal/TotalPrice/Discount/Tax | subtotal/total_amount/discount_value/tax_amount |
| ExpirationDate | expiry_date |
| Description | notes |

## Import Order (dependency-based)

1. Products (no dependencies)
2. Accounts (no dependencies)
3. Contacts (depends on Accounts)
4. Opportunities (depends on Accounts)
5. Orders (depends on Accounts, Contacts)
6. Quotes (depends on Accounts, Contacts, Opportunities)

## API Endpoints

```
POST   /api/salesforce/connect/          # Initiate OAuth (returns SF auth URL)
GET    /api/salesforce/callback/          # OAuth callback (exchanges code for tokens)
GET    /api/salesforce/status/            # Connection status
DELETE /api/salesforce/disconnect/        # Revoke + remove connection

POST   /api/salesforce/import/            # Start import job
GET    /api/salesforce/import/<job_id>/   # Import job progress
GET    /api/salesforce/import/history/    # Past import jobs
```

## OAuth 2.0 Flow

1. Frontend calls `POST /api/salesforce/connect/`
2. Backend returns Salesforce authorization URL
3. User logs into SF, grants access
4. SF redirects to `GET /api/salesforce/callback/` with auth code
5. Backend exchanges code for tokens, stores encrypted in SalesforceConnection

## Celery Import Pipeline

```
POST /api/salesforce/import/
  -> Creates ImportJob (PENDING)
  -> Dispatches Celery task

Celery task:
  1. Set RLS context (org_id)
  2. Refresh SF token if expired
  3. For each selected object type (in dependency order):
     a. SOQL query to fetch records
     b. Per record:
        - Check ImportedRecord for existing SF ID -> skip if found
        - Map fields, resolve FKs via ImportedRecord
        - Create CRM record + ImportedRecord entry
        - Increment counters
     c. Update ImportJob progress
  4. Mark ImportJob COMPLETED or FAILED
```

## Error Handling

- Per-record errors logged (don't fail the batch)
- Token refresh on 401
- Rate limit with exponential backoff
- Partial success supported

## Security

- All endpoints require auth + org context
- SF tokens encrypted at rest
- Only org admins can connect/disconnect
- RLS applies automatically to imported records

## Frontend Pages

### `/settings/salesforce` - Connection
- Connection status display
- "Connect to Salesforce" button -> OAuth flow
- Connected: instance URL, connected by, date
- "Disconnect" with confirmation

### `/settings/salesforce/import` - Import
- Object type checkboxes with dependency hints
- "Start Import" button
- Progress: overall bar + per-object status + counts
- Completion summary with expandable error details

### `/settings/salesforce/import/history` - History
- Table of past jobs (status, date, counts)
- Click for details/error log

## Tech Stack Additions

- `simple-salesforce` - Salesforce REST API client
- `cryptography` (Fernet) - token encryption at rest
