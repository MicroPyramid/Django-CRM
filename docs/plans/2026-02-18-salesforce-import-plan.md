# Salesforce Import Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Import Accounts, Contacts, Opportunities, Products, Orders, and Quotes from Salesforce into BottleCRM via OAuth 2.0, with background processing and progress tracking.

**Architecture:** New `salesforce_imports` Django app handles OAuth + import pipeline. New `orders` app for Order model. Celery tasks process imports in dependency order. Frontend pages under `/settings/salesforce/` for connection management and import UI.

**Tech Stack:** `simple-salesforce` (SF API), `cryptography` (token encryption), Celery (background tasks), SvelteKit + shadcn-svelte (frontend)

---

### Task 1: Add Python Dependencies

**Files:**
- Modify: `backend/requirements.txt`

**Step 1: Add simple-salesforce and cryptography to requirements**

Add these lines to `backend/requirements.txt`:
```
simple-salesforce==1.12.6
cryptography==44.0.0
```

**Step 2: Install dependencies**

Run: `cd backend && source venv/bin/activate && pip install -r requirements.txt`
Expected: Successfully installed simple-salesforce and cryptography

**Step 3: Commit**

```bash
git add backend/requirements.txt
git commit -m "feat(sf-import): add simple-salesforce and cryptography dependencies"
```

---

### Task 2: Create the `orders` Django App with Order Model

**Files:**
- Create: `backend/orders/__init__.py`
- Create: `backend/orders/models.py`
- Create: `backend/orders/admin.py`
- Create: `backend/orders/apps.py`
- Modify: `backend/crm/settings.py` (add to INSTALLED_APPS)
- Modify: `backend/common/rls/__init__.py` (add to ORG_SCOPED_TABLES)

**Step 1: Write the failing test**

Create `backend/orders/tests/__init__.py` (empty) and `backend/orders/tests/test_models.py`:

```python
import pytest
from django.db import connection
from orders.models import Order, OrderLineItem
from invoices.models import Product
from accounts.models import Account


@pytest.fixture
def setup_rls(org_a):
    with connection.cursor() as cursor:
        cursor.execute("SELECT set_config('app.current_org', %s, false)", [str(org_a.id)])
    yield
    with connection.cursor() as cursor:
        cursor.execute("SELECT set_config('app.current_org', '', false)")


@pytest.mark.django_db
class TestOrderModel:
    def test_create_order(self, org_a, setup_rls):
        account = Account.objects.create(name="Test Account", org=org_a)
        order = Order.objects.create(
            name="Test Order",
            order_number="ORD-001",
            status="DRAFT",
            account=account,
            org=org_a,
        )
        assert order.id is not None
        assert order.name == "Test Order"
        assert order.order_number == "ORD-001"

    def test_create_order_line_item(self, org_a, setup_rls):
        account = Account.objects.create(name="Test Account", org=org_a)
        product = Product.objects.create(name="Widget", sku="W-001", price=10.00, org=org_a)
        order = Order.objects.create(
            name="Test Order",
            order_number="ORD-002",
            status="DRAFT",
            account=account,
            org=org_a,
        )
        line = OrderLineItem.objects.create(
            order=order,
            product=product,
            name="Widget",
            quantity=5,
            unit_price=10.00,
            total=50.00,
            org=org_a,
        )
        assert line.id is not None
        assert line.quantity == 5
```

**Step 2: Run test to verify it fails**

Run: `cd backend && source venv/bin/activate && pytest orders/tests/test_models.py -v`
Expected: FAIL (module not found)

**Step 3: Create the orders app**

Create `backend/orders/__init__.py` (empty).

Create `backend/orders/apps.py`:
```python
from django.apps import AppConfig


class OrdersConfig(AppConfig):
    default_auto_field = "django.db.models.AutoField"
    name = "orders"
```

Create `backend/orders/admin.py`:
```python
from django.contrib import admin
from orders.models import Order, OrderLineItem

admin.site.register(Order)
admin.site.register(OrderLineItem)
```

Create `backend/orders/models.py`:
```python
from django.db import models
from common.base import BaseOrgModel

ORDER_STATUS = (
    ("DRAFT", "Draft"),
    ("ACTIVATED", "Activated"),
    ("COMPLETED", "Completed"),
    ("CANCELLED", "Cancelled"),
)


class Order(BaseOrgModel):
    name = models.CharField(max_length=255)
    order_number = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default="DRAFT")
    account = models.ForeignKey(
        "accounts.Account",
        on_delete=models.CASCADE,
        related_name="orders",
    )
    contact = models.ForeignKey(
        "contacts.Contact",
        on_delete=models.SET_NULL,
        related_name="orders",
        null=True,
        blank=True,
    )
    opportunity = models.ForeignKey(
        "opportunity.Opportunity",
        on_delete=models.SET_NULL,
        related_name="orders",
        null=True,
        blank=True,
    )
    currency = models.CharField(max_length=3, blank=True, null=True)
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    order_date = models.DateField(null=True, blank=True)
    activated_date = models.DateField(null=True, blank=True)
    shipped_date = models.DateField(null=True, blank=True)
    billing_address_line = models.CharField(max_length=255, blank=True, null=True)
    billing_city = models.CharField(max_length=255, blank=True, null=True)
    billing_state = models.CharField(max_length=255, blank=True, null=True)
    billing_postcode = models.CharField(max_length=64, blank=True, null=True)
    billing_country = models.CharField(max_length=3, blank=True, null=True)
    shipping_address_line = models.CharField(max_length=255, blank=True, null=True)
    shipping_city = models.CharField(max_length=255, blank=True, null=True)
    shipping_state = models.CharField(max_length=255, blank=True, null=True)
    shipping_postcode = models.CharField(max_length=64, blank=True, null=True)
    shipping_country = models.CharField(max_length=3, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "orders"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["org", "-created_at"]),
            models.Index(fields=["order_number"]),
        ]

    def __str__(self):
        return self.name


class OrderLineItem(BaseOrgModel):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="line_items",
    )
    product = models.ForeignKey(
        "invoices.Product",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_line_items",
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    sort_order = models.IntegerField(default=0)

    class Meta:
        db_table = "order_line_item"
        ordering = ("sort_order",)
        indexes = [
            models.Index(fields=["org", "-created_at"]),
        ]

    def __str__(self):
        return self.name
```

**Step 4: Register the app and update RLS tables**

Add `"orders"` to `INSTALLED_APPS` in `backend/crm/settings.py`.

Add `"orders"` and `"order_line_item"` to `ORG_SCOPED_TABLES` in `backend/common/rls/__init__.py`.

**Step 5: Create and run migration**

Run:
```bash
cd backend && source venv/bin/activate
python manage.py makemigrations orders
python manage.py migrate
```

**Step 6: Run tests**

Run: `cd backend && pytest orders/tests/test_models.py -v`
Expected: PASS

**Step 7: Commit**

```bash
git add orders/ backend/crm/settings.py backend/common/rls/__init__.py
git commit -m "feat(orders): add Order and OrderLineItem models"
```

---

### Task 3: Create `salesforce_imports` Django App with Models

**Files:**
- Create: `backend/salesforce_imports/__init__.py`
- Create: `backend/salesforce_imports/apps.py`
- Create: `backend/salesforce_imports/admin.py`
- Create: `backend/salesforce_imports/models.py`
- Modify: `backend/crm/settings.py` (add to INSTALLED_APPS)
- Modify: `backend/common/rls/__init__.py` (add tables)

**Step 1: Write the failing test**

Create `backend/salesforce_imports/tests/__init__.py` and `backend/salesforce_imports/tests/test_models.py`:

```python
import pytest
from django.db import connection
from django.contrib.contenttypes.models import ContentType
from salesforce_imports.models import SalesforceConnection, ImportJob, ImportedRecord
from accounts.models import Account


@pytest.fixture
def setup_rls(org_a):
    with connection.cursor() as cursor:
        cursor.execute("SELECT set_config('app.current_org', %s, false)", [str(org_a.id)])
    yield
    with connection.cursor() as cursor:
        cursor.execute("SELECT set_config('app.current_org', '', false)")


@pytest.mark.django_db
class TestSalesforceModels:
    def test_create_sf_connection(self, org_a, admin_profile, setup_rls):
        conn = SalesforceConnection.objects.create(
            org=org_a,
            instance_url="https://na1.salesforce.com",
            access_token="test_access",
            refresh_token="test_refresh",
            connected_by=admin_profile,
        )
        assert conn.id is not None
        assert conn.is_active is True

    def test_create_import_job(self, org_a, admin_profile, setup_rls):
        job = ImportJob.objects.create(
            org=org_a,
            object_types=["Account", "Contact"],
            started_by=admin_profile,
        )
        assert job.status == "PENDING"
        assert "Account" in job.object_types

    def test_create_imported_record(self, org_a, setup_rls, admin_profile):
        account = Account.objects.create(name="SF Account", org=org_a)
        job = ImportJob.objects.create(
            org=org_a,
            object_types=["Account"],
            started_by=admin_profile,
        )
        ct = ContentType.objects.get_for_model(Account)
        rec = ImportedRecord.objects.create(
            org=org_a,
            salesforce_id="001XXXXXXXXXXXXXXX",
            salesforce_object_type="Account",
            content_type=ct,
            object_id=account.id,
            import_job=job,
        )
        assert rec.content_object == account

    def test_imported_record_unique_constraint(self, org_a, setup_rls, admin_profile):
        account = Account.objects.create(name="SF Account", org=org_a)
        job = ImportJob.objects.create(
            org=org_a,
            object_types=["Account"],
            started_by=admin_profile,
        )
        ct = ContentType.objects.get_for_model(Account)
        ImportedRecord.objects.create(
            org=org_a,
            salesforce_id="001XXXXXXXXXXXXXXX",
            salesforce_object_type="Account",
            content_type=ct,
            object_id=account.id,
            import_job=job,
        )
        with pytest.raises(Exception):
            ImportedRecord.objects.create(
                org=org_a,
                salesforce_id="001XXXXXXXXXXXXXXX",
                salesforce_object_type="Account",
                content_type=ct,
                object_id=account.id,
                import_job=job,
            )
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest salesforce_imports/tests/test_models.py -v`
Expected: FAIL

**Step 3: Create the salesforce_imports app**

Create `backend/salesforce_imports/__init__.py` (empty).

Create `backend/salesforce_imports/apps.py`:
```python
from django.apps import AppConfig


class SalesforceImportsConfig(AppConfig):
    default_auto_field = "django.db.models.AutoField"
    name = "salesforce_imports"
```

Create `backend/salesforce_imports/models.py`:
```python
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from common.base import BaseOrgModel

IMPORT_STATUS = (
    ("PENDING", "Pending"),
    ("IN_PROGRESS", "In Progress"),
    ("COMPLETED", "Completed"),
    ("FAILED", "Failed"),
    ("CANCELLED", "Cancelled"),
)

SF_OBJECT_TYPES = (
    ("Account", "Account"),
    ("Contact", "Contact"),
    ("Opportunity", "Opportunity"),
    ("Product2", "Product"),
    ("Order", "Order"),
    ("Quote", "Quote"),
)


class SalesforceConnection(BaseOrgModel):
    instance_url = models.URLField(help_text="Salesforce instance URL")
    access_token = models.TextField(help_text="Encrypted OAuth access token")
    refresh_token = models.TextField(help_text="Encrypted OAuth refresh token")
    token_expires_at = models.DateTimeField(null=True, blank=True)
    connected_by = models.ForeignKey(
        "common.Profile",
        on_delete=models.SET_NULL,
        null=True,
        related_name="sf_connections",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "salesforce_connection"
        constraints = [
            models.UniqueConstraint(fields=["org"], name="one_sf_connection_per_org"),
        ]
        indexes = [
            models.Index(fields=["org", "-created_at"]),
        ]

    def __str__(self):
        return f"SF Connection for {self.org}"


class ImportJob(BaseOrgModel):
    status = models.CharField(max_length=20, choices=IMPORT_STATUS, default="PENDING")
    object_types = models.JSONField(
        default=list,
        help_text="List of SF object types to import",
    )
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    started_by = models.ForeignKey(
        "common.Profile",
        on_delete=models.SET_NULL,
        null=True,
        related_name="sf_import_jobs",
    )
    total_records = models.IntegerField(default=0)
    imported_count = models.IntegerField(default=0)
    skipped_count = models.IntegerField(default=0)
    error_count = models.IntegerField(default=0)
    error_log = models.JSONField(default=list)
    progress_detail = models.JSONField(
        default=dict,
        help_text="Per-object-type progress: {'Account': {'status': 'done', 'imported': 10}}",
    )

    class Meta:
        db_table = "salesforce_import_job"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["org", "-created_at"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"Import Job {self.id} ({self.status})"


class ImportedRecord(BaseOrgModel):
    salesforce_id = models.CharField(max_length=18, db_index=True)
    salesforce_object_type = models.CharField(max_length=50)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    content_object = GenericForeignKey("content_type", "object_id")
    import_job = models.ForeignKey(
        ImportJob,
        on_delete=models.CASCADE,
        related_name="imported_records",
    )

    class Meta:
        db_table = "salesforce_imported_record"
        constraints = [
            models.UniqueConstraint(
                fields=["org", "salesforce_id", "salesforce_object_type"],
                name="unique_sf_record_per_org",
            ),
        ]
        indexes = [
            models.Index(fields=["org", "salesforce_id"]),
            models.Index(fields=["content_type", "object_id"]),
        ]

    def __str__(self):
        return f"{self.salesforce_object_type}:{self.salesforce_id}"
```

Create `backend/salesforce_imports/admin.py`:
```python
from django.contrib import admin
from salesforce_imports.models import SalesforceConnection, ImportJob, ImportedRecord

admin.site.register(SalesforceConnection)
admin.site.register(ImportJob)
admin.site.register(ImportedRecord)
```

**Step 4: Register app and RLS tables**

Add `"salesforce_imports"` to `INSTALLED_APPS` in `backend/crm/settings.py`.

Add these to `ORG_SCOPED_TABLES` in `backend/common/rls/__init__.py`:
- `"salesforce_connection"`
- `"salesforce_import_job"`
- `"salesforce_imported_record"`

**Step 5: Create and run migrations**

Run:
```bash
cd backend && source venv/bin/activate
python manage.py makemigrations salesforce_imports
python manage.py migrate
```

**Step 6: Run tests**

Run: `cd backend && pytest salesforce_imports/tests/test_models.py -v`
Expected: PASS

**Step 7: Commit**

```bash
git add salesforce_imports/ backend/crm/settings.py backend/common/rls/__init__.py
git commit -m "feat(sf-import): add SalesforceConnection, ImportJob, ImportedRecord models"
```

---

### Task 4: Token Encryption Utility

**Files:**
- Create: `backend/salesforce_imports/encryption.py`
- Create: `backend/salesforce_imports/tests/test_encryption.py`
- Modify: `backend/crm/settings.py` (add FIELD_ENCRYPTION_KEY setting)

**Step 1: Write the failing test**

Create `backend/salesforce_imports/tests/test_encryption.py`:
```python
from salesforce_imports.encryption import encrypt_token, decrypt_token


def test_encrypt_decrypt_roundtrip():
    token = "00D000000000001!AQEAQBxyz123_test_token"
    encrypted = encrypt_token(token)
    assert encrypted != token
    decrypted = decrypt_token(encrypted)
    assert decrypted == token


def test_encrypt_produces_different_output():
    token = "test_token_123"
    enc1 = encrypt_token(token)
    enc2 = encrypt_token(token)
    # Fernet uses random IV, so each encryption is different
    assert enc1 != enc2


def test_decrypt_empty_returns_none():
    assert decrypt_token("") is None
    assert decrypt_token(None) is None
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest salesforce_imports/tests/test_encryption.py -v`
Expected: FAIL

**Step 3: Add encryption key to settings**

Add to `backend/crm/settings.py`:
```python
# Salesforce token encryption
FIELD_ENCRYPTION_KEY = os.environ.get("FIELD_ENCRYPTION_KEY", "")
```

**Step 4: Implement encryption utility**

Create `backend/salesforce_imports/encryption.py`:
```python
import base64
from cryptography.fernet import Fernet
from django.conf import settings


def _get_fernet():
    key = settings.FIELD_ENCRYPTION_KEY
    if not key:
        # Generate a deterministic key from SECRET_KEY for dev convenience
        import hashlib

        key = base64.urlsafe_b64encode(
            hashlib.sha256(settings.SECRET_KEY.encode()).digest()
        ).decode()
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt_token(plaintext):
    """Encrypt a token string. Returns base64-encoded ciphertext."""
    if not plaintext:
        return ""
    f = _get_fernet()
    return f.encrypt(plaintext.encode()).decode()


def decrypt_token(ciphertext):
    """Decrypt a token string. Returns plaintext."""
    if not ciphertext:
        return None
    f = _get_fernet()
    return f.decrypt(ciphertext.encode()).decode()
```

**Step 5: Run tests**

Run: `cd backend && pytest salesforce_imports/tests/test_encryption.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add salesforce_imports/encryption.py salesforce_imports/tests/test_encryption.py backend/crm/settings.py
git commit -m "feat(sf-import): add token encryption utility"
```

---

### Task 5: Salesforce OAuth 2.0 Flow (Connect/Callback/Status/Disconnect)

**Files:**
- Create: `backend/salesforce_imports/serializers.py`
- Create: `backend/salesforce_imports/views.py`
- Create: `backend/salesforce_imports/urls.py`
- Modify: `backend/common/urls.py` (include sf urls)
- Modify: `backend/crm/settings.py` (add SF_* settings)
- Create: `backend/salesforce_imports/tests/test_oauth.py`

**Step 1: Add Salesforce settings**

Add to `backend/crm/settings.py`:
```python
# Salesforce OAuth 2.0
SF_CLIENT_ID = os.environ.get("SF_CLIENT_ID", "")
SF_CLIENT_SECRET = os.environ.get("SF_CLIENT_SECRET", "")
SF_REDIRECT_URI = os.environ.get("SF_REDIRECT_URI", "http://localhost:8000/api/salesforce/callback/")
SF_AUTH_URL = "https://login.salesforce.com/services/oauth2/authorize"
SF_TOKEN_URL = "https://login.salesforce.com/services/oauth2/token"
SF_REVOKE_URL = "https://login.salesforce.com/services/oauth2/revoke"
```

**Step 2: Write the failing test**

Create `backend/salesforce_imports/tests/test_oauth.py`:
```python
import pytest
from unittest.mock import patch, MagicMock
from django.db import connection
from salesforce_imports.models import SalesforceConnection


@pytest.fixture
def setup_rls(org_a):
    with connection.cursor() as cursor:
        cursor.execute("SELECT set_config('app.current_org', %s, false)", [str(org_a.id)])
    yield
    with connection.cursor() as cursor:
        cursor.execute("SELECT set_config('app.current_org', '', false)")


@pytest.mark.django_db
class TestSalesforceOAuth:
    def test_connect_returns_auth_url(self, admin_client):
        response = admin_client.post("/api/salesforce/connect/")
        assert response.status_code == 200
        data = response.json()
        assert "auth_url" in data
        assert "login.salesforce.com" in data["auth_url"]

    def test_status_not_connected(self, admin_client):
        response = admin_client.get("/api/salesforce/status/")
        assert response.status_code == 200
        data = response.json()
        assert data["connected"] is False

    def test_status_connected(self, admin_client, org_a, admin_profile, setup_rls):
        SalesforceConnection.objects.create(
            org=org_a,
            instance_url="https://na1.salesforce.com",
            access_token="encrypted_token",
            refresh_token="encrypted_refresh",
            connected_by=admin_profile,
            is_active=True,
        )
        response = admin_client.get("/api/salesforce/status/")
        assert response.status_code == 200
        data = response.json()
        assert data["connected"] is True
        assert data["instance_url"] == "https://na1.salesforce.com"

    @patch("salesforce_imports.views.requests.post")
    def test_disconnect(self, mock_post, admin_client, org_a, admin_profile, setup_rls):
        mock_post.return_value = MagicMock(status_code=200)
        SalesforceConnection.objects.create(
            org=org_a,
            instance_url="https://na1.salesforce.com",
            access_token="encrypted_token",
            refresh_token="encrypted_refresh",
            connected_by=admin_profile,
            is_active=True,
        )
        response = admin_client.delete("/api/salesforce/disconnect/")
        assert response.status_code == 200
        assert not SalesforceConnection.objects.filter(org=org_a, is_active=True).exists()
```

**Step 3: Run test to verify it fails**

Run: `cd backend && pytest salesforce_imports/tests/test_oauth.py -v`
Expected: FAIL

**Step 4: Implement serializers**

Create `backend/salesforce_imports/serializers.py`:
```python
from rest_framework import serializers
from salesforce_imports.models import SalesforceConnection, ImportJob, ImportedRecord


class SalesforceConnectionSerializer(serializers.ModelSerializer):
    connected_by_email = serializers.SerializerMethodField()

    class Meta:
        model = SalesforceConnection
        fields = (
            "id",
            "instance_url",
            "is_active",
            "connected_by",
            "connected_by_email",
            "created_at",
        )

    def get_connected_by_email(self, obj):
        if obj.connected_by and obj.connected_by.user:
            return obj.connected_by.user.email
        return None


class ImportJobSerializer(serializers.ModelSerializer):
    started_by_email = serializers.SerializerMethodField()

    class Meta:
        model = ImportJob
        fields = (
            "id",
            "status",
            "object_types",
            "started_at",
            "completed_at",
            "started_by",
            "started_by_email",
            "total_records",
            "imported_count",
            "skipped_count",
            "error_count",
            "error_log",
            "progress_detail",
            "created_at",
        )

    def get_started_by_email(self, obj):
        if obj.started_by and obj.started_by.user:
            return obj.started_by.user.email
        return None


class StartImportSerializer(serializers.Serializer):
    object_types = serializers.ListField(
        child=serializers.ChoiceField(
            choices=["Account", "Contact", "Opportunity", "Product2", "Order", "Quote"]
        ),
        min_length=1,
    )
```

**Step 5: Implement views**

Create `backend/salesforce_imports/views.py`:
```python
import logging
import urllib.parse

import requests
from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions import HasOrgContext, IsOrgAdmin
from salesforce_imports.encryption import encrypt_token, decrypt_token
from salesforce_imports.models import SalesforceConnection, ImportJob
from salesforce_imports.serializers import (
    ImportJobSerializer,
    SalesforceConnectionSerializer,
    StartImportSerializer,
)

logger = logging.getLogger(__name__)


class SalesforceConnectView(APIView):
    """Initiate Salesforce OAuth 2.0 flow. Returns the authorization URL."""

    permission_classes = (IsAuthenticated, HasOrgContext, IsOrgAdmin)

    def post(self, request):
        params = {
            "response_type": "code",
            "client_id": settings.SF_CLIENT_ID,
            "redirect_uri": settings.SF_REDIRECT_URI,
            "scope": "api refresh_token",
            "state": str(request.profile.org.id),
        }
        auth_url = f"{settings.SF_AUTH_URL}?{urllib.parse.urlencode(params)}"
        return Response({"auth_url": auth_url})


class SalesforceCallbackView(APIView):
    """
    OAuth 2.0 callback. Exchanges auth code for tokens.
    This is called by the frontend after SF redirects back.
    """

    permission_classes = (IsAuthenticated, HasOrgContext)

    def post(self, request):
        code = request.data.get("code")
        if not code:
            return Response(
                {"error": True, "message": "Authorization code is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Exchange code for tokens
        token_data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": settings.SF_CLIENT_ID,
            "client_secret": settings.SF_CLIENT_SECRET,
            "redirect_uri": settings.SF_REDIRECT_URI,
        }

        try:
            resp = requests.post(settings.SF_TOKEN_URL, data=token_data, timeout=30)
            resp.raise_for_status()
            tokens = resp.json()
        except requests.RequestException as e:
            logger.error("Salesforce token exchange failed: %s", e)
            return Response(
                {"error": True, "message": "Failed to connect to Salesforce"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        # Store connection (upsert)
        SalesforceConnection.objects.update_or_create(
            org=request.profile.org,
            defaults={
                "instance_url": tokens["instance_url"],
                "access_token": encrypt_token(tokens["access_token"]),
                "refresh_token": encrypt_token(tokens["refresh_token"]),
                "token_expires_at": timezone.now() + timezone.timedelta(hours=1),
                "connected_by": request.profile,
                "is_active": True,
            },
        )

        return Response({"error": False, "message": "Salesforce connected successfully"})


class SalesforceStatusView(APIView):
    """Check current Salesforce connection status."""

    permission_classes = (IsAuthenticated, HasOrgContext)

    def get(self, request):
        conn = SalesforceConnection.objects.filter(
            org=request.profile.org, is_active=True
        ).first()

        if not conn:
            return Response({"connected": False})

        return Response(
            {
                "connected": True,
                "instance_url": conn.instance_url,
                "connection": SalesforceConnectionSerializer(conn).data,
            }
        )


class SalesforceDisconnectView(APIView):
    """Revoke Salesforce tokens and remove connection."""

    permission_classes = (IsAuthenticated, HasOrgContext, IsOrgAdmin)

    def delete(self, request):
        conn = SalesforceConnection.objects.filter(
            org=request.profile.org, is_active=True
        ).first()

        if not conn:
            return Response(
                {"error": True, "message": "No active Salesforce connection"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Attempt to revoke token at Salesforce
        try:
            token = decrypt_token(conn.access_token)
            if token:
                requests.post(
                    settings.SF_REVOKE_URL,
                    data={"token": token},
                    timeout=10,
                )
        except Exception:
            pass  # Best effort revocation

        conn.is_active = False
        conn.save()

        return Response({"error": False, "message": "Salesforce disconnected"})


class StartImportView(APIView):
    """Start a new Salesforce import job."""

    permission_classes = (IsAuthenticated, HasOrgContext, IsOrgAdmin)

    def post(self, request):
        serializer = StartImportSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": True, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check SF connection
        conn = SalesforceConnection.objects.filter(
            org=request.profile.org, is_active=True
        ).first()
        if not conn:
            return Response(
                {"error": True, "message": "No active Salesforce connection"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check no import already running
        running = ImportJob.objects.filter(
            org=request.profile.org, status__in=["PENDING", "IN_PROGRESS"]
        ).exists()
        if running:
            return Response(
                {"error": True, "message": "An import is already in progress"},
                status=status.HTTP_409_CONFLICT,
            )

        job = ImportJob.objects.create(
            org=request.profile.org,
            object_types=serializer.validated_data["object_types"],
            started_by=request.profile,
        )

        # Dispatch Celery task
        from salesforce_imports.tasks import run_import

        run_import.delay(str(job.id), str(request.profile.org.id))

        return Response(
            {
                "error": False,
                "message": "Import started",
                "job": ImportJobSerializer(job).data,
            }
        )


class ImportJobDetailView(APIView):
    """Get import job status and progress."""

    permission_classes = (IsAuthenticated, HasOrgContext)

    def get(self, request, pk):
        try:
            job = ImportJob.objects.get(id=pk, org=request.profile.org)
        except ImportJob.DoesNotExist:
            return Response(
                {"error": True, "message": "Import job not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response({"job": ImportJobSerializer(job).data})


class ImportHistoryView(APIView):
    """List past import jobs."""

    permission_classes = (IsAuthenticated, HasOrgContext)

    def get(self, request):
        jobs = ImportJob.objects.filter(org=request.profile.org).order_by("-created_at")[:50]
        return Response({"jobs": ImportJobSerializer(jobs, many=True).data})
```

**Step 6: Create URL configuration**

Create `backend/salesforce_imports/urls.py`:
```python
from django.urls import path
from salesforce_imports import views

app_name = "api_salesforce"

urlpatterns = [
    path("connect/", views.SalesforceConnectView.as_view()),
    path("callback/", views.SalesforceCallbackView.as_view()),
    path("status/", views.SalesforceStatusView.as_view()),
    path("disconnect/", views.SalesforceDisconnectView.as_view()),
    path("import/", views.StartImportView.as_view()),
    path("import/history/", views.ImportHistoryView.as_view()),
    path("import/<str:pk>/", views.ImportJobDetailView.as_view()),
]
```

**Step 7: Register URLs**

Add to `backend/common/urls.py` (in the `common_urls` urlpatterns, alongside existing app includes):
```python
path("salesforce/", include("salesforce_imports.urls", namespace="api_salesforce")),
```

Note: Find where other app URLs are included (like `path("accounts/", include("accounts.urls"))`) and add the salesforce path there. Check `backend/common/app_urls.py` - it may be `app_urls.py` instead of `urls.py`.

**Step 8: Run tests**

Run: `cd backend && pytest salesforce_imports/tests/test_oauth.py -v`
Expected: PASS

**Step 9: Commit**

```bash
git add salesforce_imports/serializers.py salesforce_imports/views.py salesforce_imports/urls.py backend/common/app_urls.py backend/crm/settings.py
git commit -m "feat(sf-import): add OAuth 2.0 connect/callback/status/disconnect endpoints"
```

---

### Task 6: Salesforce Field Mappers

**Files:**
- Create: `backend/salesforce_imports/mappers.py`
- Create: `backend/salesforce_imports/tests/test_mappers.py`

**Step 1: Write the failing test**

Create `backend/salesforce_imports/tests/test_mappers.py`:
```python
import pytest
from salesforce_imports.mappers import (
    map_sf_account,
    map_sf_contact,
    map_sf_opportunity,
    map_sf_product,
    map_sf_order,
    map_sf_quote,
)


class TestAccountMapper:
    def test_maps_basic_fields(self):
        sf_record = {
            "Id": "001XXXXXXXXXXXXXXX",
            "Name": "Acme Corp",
            "Website": "https://acme.com",
            "Phone": "555-1234",
            "Industry": "Technology",
            "NumberOfEmployees": 100,
            "AnnualRevenue": 1000000.50,
            "Description": "A test account",
            "BillingStreet": "123 Main St",
            "BillingCity": "San Francisco",
            "BillingState": "CA",
            "BillingPostalCode": "94105",
            "BillingCountry": "US",
        }
        result = map_sf_account(sf_record)
        assert result["name"] == "Acme Corp"
        assert result["website"] == "https://acme.com"
        assert result["phone"] == "555-1234"
        assert result["city"] == "San Francisco"
        assert result["postcode"] == "94105"

    def test_handles_none_fields(self):
        sf_record = {"Id": "001XXXXXXXXXXXXXXX", "Name": "Minimal"}
        result = map_sf_account(sf_record)
        assert result["name"] == "Minimal"
        assert result["phone"] is None


class TestContactMapper:
    def test_maps_basic_fields(self):
        sf_record = {
            "Id": "003XXXXXXXXXXXXXXX",
            "FirstName": "John",
            "LastName": "Doe",
            "Email": "john@example.com",
            "Phone": "555-5678",
            "Title": "VP Sales",
            "Department": "Sales",
            "AccountId": "001XXXXXXXXXXXXXXX",
            "DoNotCall": True,
        }
        result = map_sf_contact(sf_record)
        assert result["first_name"] == "John"
        assert result["last_name"] == "Doe"
        assert result["do_not_call"] is True
        assert result["_sf_account_id"] == "001XXXXXXXXXXXXXXX"


class TestProductMapper:
    def test_maps_basic_fields(self):
        sf_record = {
            "Id": "01tXXXXXXXXXXXXXXX",
            "Name": "Widget Pro",
            "ProductCode": "WP-001",
            "Description": "A premium widget",
            "IsActive": True,
        }
        result = map_sf_product(sf_record)
        assert result["name"] == "Widget Pro"
        assert result["sku"] == "WP-001"
        assert result["is_active"] is True
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest salesforce_imports/tests/test_mappers.py -v`
Expected: FAIL

**Step 3: Implement mappers**

Create `backend/salesforce_imports/mappers.py`:
```python
"""
Field mappers that convert Salesforce records to BottleCRM model kwargs.

Each mapper returns a dict of model field names -> values.
Foreign key references (e.g. AccountId) are returned as _sf_<field>
for the import pipeline to resolve via ImportedRecord lookups.
"""


def _get(record, key, default=None):
    """Safely get a value from a SF record."""
    val = record.get(key)
    return val if val is not None else default


def map_sf_account(record):
    return {
        "name": record["Name"],
        "website": _get(record, "Website"),
        "phone": _get(record, "Phone"),
        "industry": _get(record, "Industry"),
        "number_of_employees": _get(record, "NumberOfEmployees"),
        "annual_revenue": _get(record, "AnnualRevenue"),
        "description": _get(record, "Description"),
        "address_line": _get(record, "BillingStreet"),
        "city": _get(record, "BillingCity"),
        "state": _get(record, "BillingState"),
        "postcode": _get(record, "BillingPostalCode"),
        "country": _get(record, "BillingCountry"),
    }


def map_sf_contact(record):
    return {
        "first_name": _get(record, "FirstName", ""),
        "last_name": record.get("LastName", ""),
        "email": _get(record, "Email"),
        "phone": _get(record, "Phone"),
        "title": _get(record, "Title"),
        "department": _get(record, "Department"),
        "do_not_call": bool(_get(record, "DoNotCall", False)),
        "address_line": _get(record, "MailingStreet"),
        "city": _get(record, "MailingCity"),
        "state": _get(record, "MailingState"),
        "postcode": _get(record, "MailingPostalCode"),
        "country": _get(record, "MailingCountry"),
        "description": _get(record, "Description"),
        # FK references for pipeline to resolve
        "_sf_account_id": _get(record, "AccountId"),
    }


def map_sf_opportunity(record):
    return {
        "name": record["Name"],
        "stage": _get(record, "StageName", "QUALIFICATION"),
        "amount": _get(record, "Amount"),
        "probability": _get(record, "Probability"),
        "closed_on": _get(record, "CloseDate"),
        "lead_source": _get(record, "LeadSource"),
        "opportunity_type": _get(record, "Type"),
        "description": _get(record, "Description"),
        # FK references
        "_sf_account_id": _get(record, "AccountId"),
    }


def map_sf_product(record):
    return {
        "name": record["Name"],
        "sku": _get(record, "ProductCode", ""),
        "description": _get(record, "Description"),
        "is_active": bool(_get(record, "IsActive", True)),
    }


def map_sf_order(record):
    return {
        "name": _get(record, "OrderNumber", f"Order {record['Id'][:8]}"),
        "order_number": _get(record, "OrderNumber"),
        "status": _map_order_status(_get(record, "Status", "Draft")),
        "order_date": _get(record, "EffectiveDate"),
        "activated_date": _get(record, "ActivatedDate"),
        "total_amount": _get(record, "TotalAmount", 0),
        "description": _get(record, "Description"),
        "billing_address_line": _get(record, "BillingStreet"),
        "billing_city": _get(record, "BillingCity"),
        "billing_state": _get(record, "BillingState"),
        "billing_postcode": _get(record, "BillingPostalCode"),
        "billing_country": _get(record, "BillingCountry"),
        "shipping_address_line": _get(record, "ShippingStreet"),
        "shipping_city": _get(record, "ShippingCity"),
        "shipping_state": _get(record, "ShippingState"),
        "shipping_postcode": _get(record, "ShippingPostalCode"),
        "shipping_country": _get(record, "ShippingCountry"),
        # FK references
        "_sf_account_id": _get(record, "AccountId"),
    }


def map_sf_quote(record):
    return {
        "title": _get(record, "Name", ""),
        "estimate_number": _get(record, "QuoteNumber"),
        "status": _map_quote_status(_get(record, "Status", "Draft")),
        "subtotal": _get(record, "Subtotal", 0),
        "total_amount": _get(record, "TotalPrice", 0),
        "discount_value": _get(record, "Discount", 0),
        "tax_amount": _get(record, "Tax", 0),
        "expiry_date": _get(record, "ExpirationDate"),
        "notes": _get(record, "Description"),
        # FK references
        "_sf_account_id": _get(record, "AccountId"),
        "_sf_contact_id": _get(record, "ContactId"),
        "_sf_opportunity_id": _get(record, "OpportunityId"),
    }


def _map_order_status(sf_status):
    mapping = {
        "Draft": "DRAFT",
        "Activated": "ACTIVATED",
        "Completed": "COMPLETED",
        "Cancelled": "CANCELLED",
    }
    return mapping.get(sf_status, "DRAFT")


def _map_quote_status(sf_status):
    mapping = {
        "Draft": "DRAFT",
        "Needs Review": "DRAFT",
        "In Review": "SENT",
        "Approved": "ACCEPTED",
        "Rejected": "DECLINED",
        "Presented": "SENT",
        "Accepted": "ACCEPTED",
        "Denied": "DECLINED",
    }
    return mapping.get(sf_status, "DRAFT")
```

**Step 4: Run tests**

Run: `cd backend && pytest salesforce_imports/tests/test_mappers.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add salesforce_imports/mappers.py salesforce_imports/tests/test_mappers.py
git commit -m "feat(sf-import): add Salesforce field mappers for all 6 object types"
```

---

### Task 7: Celery Import Pipeline

**Files:**
- Create: `backend/salesforce_imports/tasks.py`
- Create: `backend/salesforce_imports/sf_client.py`
- Create: `backend/salesforce_imports/tests/test_tasks.py`

**Step 1: Create SF client wrapper**

Create `backend/salesforce_imports/sf_client.py`:
```python
"""
Wrapper around simple_salesforce that handles token refresh and SOQL queries.
"""
import logging

from django.utils import timezone
from simple_salesforce import Salesforce, SalesforceExpiredSession

from salesforce_imports.encryption import decrypt_token, encrypt_token
from salesforce_imports.models import SalesforceConnection

logger = logging.getLogger(__name__)

# SOQL queries for each object type
SOQL_QUERIES = {
    "Account": (
        "SELECT Id, Name, Website, Phone, Industry, NumberOfEmployees, "
        "AnnualRevenue, Description, BillingStreet, BillingCity, BillingState, "
        "BillingPostalCode, BillingCountry FROM Account"
    ),
    "Contact": (
        "SELECT Id, FirstName, LastName, Email, Phone, Title, Department, "
        "AccountId, DoNotCall, MailingStreet, MailingCity, MailingState, "
        "MailingPostalCode, MailingCountry, Description FROM Contact"
    ),
    "Opportunity": (
        "SELECT Id, Name, AccountId, StageName, Amount, Probability, "
        "CloseDate, LeadSource, Type, Description FROM Opportunity"
    ),
    "Product2": (
        "SELECT Id, Name, ProductCode, Description, IsActive FROM Product2"
    ),
    "Order": (
        "SELECT Id, OrderNumber, Status, AccountId, EffectiveDate, ActivatedDate, "
        "TotalAmount, Description, BillingStreet, BillingCity, BillingState, "
        "BillingPostalCode, BillingCountry, ShippingStreet, ShippingCity, "
        "ShippingState, ShippingPostalCode, ShippingCountry FROM Order"
    ),
    "Quote": (
        "SELECT Id, Name, QuoteNumber, Status, AccountId, ContactId, "
        "OpportunityId, Subtotal, TotalPrice, Discount, Tax, "
        "ExpirationDate, Description FROM Quote"
    ),
}


def get_sf_client(connection):
    """Create a Salesforce client from a SalesforceConnection."""
    access_token = decrypt_token(connection.access_token)
    return Salesforce(
        instance_url=connection.instance_url,
        session_id=access_token,
    )


def refresh_sf_token(connection):
    """Refresh the access token using the refresh token."""
    import requests
    from django.conf import settings

    refresh_token = decrypt_token(connection.refresh_token)
    resp = requests.post(
        settings.SF_TOKEN_URL,
        data={
            "grant_type": "refresh_token",
            "client_id": settings.SF_CLIENT_ID,
            "client_secret": settings.SF_CLIENT_SECRET,
            "refresh_token": refresh_token,
        },
        timeout=30,
    )
    resp.raise_for_status()
    tokens = resp.json()

    connection.access_token = encrypt_token(tokens["access_token"])
    connection.token_expires_at = timezone.now() + timezone.timedelta(hours=1)
    connection.save(update_fields=["access_token", "token_expires_at", "updated_at"])

    return get_sf_client(connection)


def query_sf_objects(sf_client, object_type, connection):
    """Query all records of a given object type. Handles token refresh on expiry."""
    soql = SOQL_QUERIES.get(object_type)
    if not soql:
        raise ValueError(f"Unknown SF object type: {object_type}")

    try:
        result = sf_client.query_all(soql)
    except SalesforceExpiredSession:
        logger.info("SF token expired, refreshing...")
        sf_client = refresh_sf_token(connection)
        result = sf_client.query_all(soql)

    return result.get("records", [])
```

**Step 2: Write the failing test for the import task**

Create `backend/salesforce_imports/tests/test_tasks.py`:
```python
import pytest
from unittest.mock import patch, MagicMock
from django.db import connection as db_connection
from salesforce_imports.models import ImportJob, ImportedRecord, SalesforceConnection
from salesforce_imports.tasks import run_import
from accounts.models import Account


@pytest.fixture
def setup_rls(org_a):
    with db_connection.cursor() as cursor:
        cursor.execute("SELECT set_config('app.current_org', %s, false)", [str(org_a.id)])
    yield
    with db_connection.cursor() as cursor:
        cursor.execute("SELECT set_config('app.current_org', '', false)")


@pytest.fixture
def sf_connection(org_a, admin_profile, setup_rls):
    return SalesforceConnection.objects.create(
        org=org_a,
        instance_url="https://test.salesforce.com",
        access_token="encrypted_access",
        refresh_token="encrypted_refresh",
        connected_by=admin_profile,
        is_active=True,
    )


@pytest.mark.django_db
class TestRunImport:
    @patch("salesforce_imports.tasks.get_sf_client")
    @patch("salesforce_imports.tasks.query_sf_objects")
    def test_import_accounts(
        self, mock_query, mock_client, org_a, admin_profile, sf_connection, setup_rls
    ):
        mock_client.return_value = MagicMock()
        mock_query.return_value = [
            {
                "Id": "001000000000001",
                "Name": "Acme Corp",
                "Website": "https://acme.com",
                "Phone": None,
                "Industry": None,
                "NumberOfEmployees": None,
                "AnnualRevenue": None,
                "Description": None,
                "BillingStreet": None,
                "BillingCity": None,
                "BillingState": None,
                "BillingPostalCode": None,
                "BillingCountry": None,
            }
        ]

        job = ImportJob.objects.create(
            org=org_a,
            object_types=["Account"],
            started_by=admin_profile,
        )

        run_import(str(job.id), str(org_a.id))

        job.refresh_from_db()
        assert job.status == "COMPLETED"
        assert job.imported_count == 1
        assert Account.objects.filter(name="Acme Corp", org=org_a).exists()
        assert ImportedRecord.objects.filter(
            salesforce_id="001000000000001", org=org_a
        ).exists()

    @patch("salesforce_imports.tasks.get_sf_client")
    @patch("salesforce_imports.tasks.query_sf_objects")
    def test_skip_duplicate(
        self, mock_query, mock_client, org_a, admin_profile, sf_connection, setup_rls
    ):
        mock_client.return_value = MagicMock()
        mock_query.return_value = [
            {
                "Id": "001000000000002",
                "Name": "Existing Corp",
                "Website": None,
                "Phone": None,
                "Industry": None,
                "NumberOfEmployees": None,
                "AnnualRevenue": None,
                "Description": None,
                "BillingStreet": None,
                "BillingCity": None,
                "BillingState": None,
                "BillingPostalCode": None,
                "BillingCountry": None,
            }
        ]

        # Pre-create an imported record to simulate previous import
        from django.contrib.contenttypes.models import ContentType

        account = Account.objects.create(name="Existing Corp", org=org_a)
        first_job = ImportJob.objects.create(
            org=org_a, object_types=["Account"], started_by=admin_profile
        )
        ct = ContentType.objects.get_for_model(Account)
        ImportedRecord.objects.create(
            org=org_a,
            salesforce_id="001000000000002",
            salesforce_object_type="Account",
            content_type=ct,
            object_id=account.id,
            import_job=first_job,
        )

        job = ImportJob.objects.create(
            org=org_a,
            object_types=["Account"],
            started_by=admin_profile,
        )

        run_import(str(job.id), str(org_a.id))

        job.refresh_from_db()
        assert job.status == "COMPLETED"
        assert job.skipped_count == 1
        assert job.imported_count == 0
```

**Step 3: Run test to verify it fails**

Run: `cd backend && pytest salesforce_imports/tests/test_tasks.py -v`
Expected: FAIL

**Step 4: Implement the import task**

Create `backend/salesforce_imports/tasks.py`:
```python
import logging

from celery import shared_task
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

from common.tasks import set_rls_context
from salesforce_imports.mappers import (
    map_sf_account,
    map_sf_contact,
    map_sf_opportunity,
    map_sf_product,
    map_sf_order,
    map_sf_quote,
)
from salesforce_imports.models import ImportJob, ImportedRecord, SalesforceConnection
from salesforce_imports.sf_client import get_sf_client, query_sf_objects

logger = logging.getLogger(__name__)

# Import order: dependencies first
IMPORT_ORDER = ["Product2", "Account", "Contact", "Opportunity", "Order", "Quote"]

# Map SF object type to (CRM model, mapper function, SF object name for display)
OBJECT_CONFIG = {
    "Product2": {
        "model_path": "invoices.models.Product",
        "mapper": map_sf_product,
    },
    "Account": {
        "model_path": "accounts.models.Account",
        "mapper": map_sf_account,
    },
    "Contact": {
        "model_path": "contacts.models.Contact",
        "mapper": map_sf_contact,
    },
    "Opportunity": {
        "model_path": "opportunity.models.Opportunity",
        "mapper": map_sf_opportunity,
    },
    "Order": {
        "model_path": "orders.models.Order",
        "mapper": map_sf_order,
    },
    "Quote": {
        "model_path": "invoices.models.Estimate",
        "mapper": map_sf_quote,
    },
}


def _get_model(model_path):
    """Import and return a Django model class from dotted path."""
    module_path, class_name = model_path.rsplit(".", 1)
    import importlib

    module = importlib.import_module(module_path)
    return getattr(module, class_name)


def _resolve_fk(org, sf_id, sf_object_type):
    """Look up a CRM object by its Salesforce ID."""
    if not sf_id:
        return None
    try:
        rec = ImportedRecord.objects.get(
            org=org, salesforce_id=sf_id, salesforce_object_type=sf_object_type
        )
        return rec.content_object
    except ImportedRecord.DoesNotExist:
        return None


def _import_single_record(sf_record, object_type, org, job):
    """
    Import a single SF record. Returns ('imported', 'skipped', or 'error').
    """
    sf_id = sf_record["Id"]
    config = OBJECT_CONFIG[object_type]
    model_cls = _get_model(config["model_path"])
    mapper = config["mapper"]

    # Check for duplicate
    if ImportedRecord.objects.filter(
        org=org, salesforce_id=sf_id, salesforce_object_type=object_type
    ).exists():
        return "skipped"

    try:
        mapped = mapper(sf_record)

        # Extract FK references (keys starting with _sf_)
        fk_refs = {k: v for k, v in mapped.items() if k.startswith("_sf_")}
        model_data = {k: v for k, v in mapped.items() if not k.startswith("_sf_")}

        # Resolve foreign keys
        if "_sf_account_id" in fk_refs and fk_refs["_sf_account_id"]:
            model_data["account"] = _resolve_fk(org, fk_refs["_sf_account_id"], "Account")
            if model_data["account"] is None and object_type in ("Order",):
                # Account is required for Order - skip if not found
                return "error"

        if "_sf_contact_id" in fk_refs and fk_refs["_sf_contact_id"]:
            model_data["contact"] = _resolve_fk(org, fk_refs["_sf_contact_id"], "Contact")

        if "_sf_opportunity_id" in fk_refs and fk_refs["_sf_opportunity_id"]:
            model_data["opportunity"] = _resolve_fk(
                org, fk_refs["_sf_opportunity_id"], "Opportunity"
            )

        # Create CRM record
        model_data["org"] = org
        obj = model_cls.objects.create(**model_data)

        # Track the mapping
        ct = ContentType.objects.get_for_model(model_cls)
        ImportedRecord.objects.create(
            org=org,
            salesforce_id=sf_id,
            salesforce_object_type=object_type,
            content_type=ct,
            object_id=obj.id,
            import_job=job,
        )

        return "imported"

    except Exception as e:
        logger.error("Failed to import %s %s: %s", object_type, sf_id, e)
        job.error_log.append(
            {"sf_id": sf_id, "object_type": object_type, "error": str(e)}
        )
        job.save(update_fields=["error_log"])
        return "error"


@shared_task
def run_import(job_id, org_id):
    """
    Main import task. Processes all selected object types in dependency order.
    """
    set_rls_context(org_id)

    try:
        job = ImportJob.objects.get(id=job_id)
    except ImportJob.DoesNotExist:
        logger.error("Import job %s not found", job_id)
        return

    job.status = "IN_PROGRESS"
    job.started_at = timezone.now()
    job.save(update_fields=["status", "started_at"])

    try:
        connection = SalesforceConnection.objects.get(org_id=org_id, is_active=True)
    except SalesforceConnection.DoesNotExist:
        job.status = "FAILED"
        job.error_log = [{"error": "No active Salesforce connection"}]
        job.completed_at = timezone.now()
        job.save()
        return

    sf_client = get_sf_client(connection)
    selected_types = job.object_types

    # Process in dependency order, but only selected types
    ordered_types = [t for t in IMPORT_ORDER if t in selected_types]

    for object_type in ordered_types:
        job.progress_detail[object_type] = {"status": "importing", "imported": 0, "skipped": 0, "errors": 0}
        job.save(update_fields=["progress_detail"])

        try:
            records = query_sf_objects(sf_client, object_type, connection)
        except Exception as e:
            logger.error("Failed to query %s from Salesforce: %s", object_type, e)
            job.progress_detail[object_type] = {"status": "failed", "error": str(e)}
            job.error_count += 1
            job.save(update_fields=["progress_detail", "error_count"])
            continue

        job.total_records += len(records)
        job.save(update_fields=["total_records"])

        for sf_record in records:
            result = _import_single_record(sf_record, object_type, job.org, job)

            if result == "imported":
                job.imported_count += 1
                job.progress_detail[object_type]["imported"] += 1
            elif result == "skipped":
                job.skipped_count += 1
                job.progress_detail[object_type]["skipped"] += 1
            elif result == "error":
                job.error_count += 1
                job.progress_detail[object_type]["errors"] += 1

            job.save(update_fields=[
                "imported_count", "skipped_count", "error_count", "progress_detail"
            ])

        job.progress_detail[object_type]["status"] = "done"
        job.save(update_fields=["progress_detail"])

    job.status = "COMPLETED"
    job.completed_at = timezone.now()
    job.save(update_fields=["status", "completed_at"])
```

**Step 5: Run tests**

Run: `cd backend && pytest salesforce_imports/tests/test_tasks.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add salesforce_imports/tasks.py salesforce_imports/sf_client.py salesforce_imports/tests/test_tasks.py
git commit -m "feat(sf-import): add Celery import pipeline with dependency ordering and dedup"
```

---

### Task 8: Frontend - Salesforce Connection Page

**Files:**
- Create: `frontend/src/routes/(app)/settings/salesforce/+page.server.js`
- Create: `frontend/src/routes/(app)/settings/salesforce/+page.svelte`
- Modify: `frontend/src/lib/api.js` (add salesforce API methods)
- Modify: `frontend/src/lib/components/layout/AppSidebar.svelte` (add nav item)

**Step 1: Add Salesforce API methods**

Add to `frontend/src/lib/api.js` (alongside existing API definitions):
```javascript
export const salesforce = {
    async status() {
        return apiRequest('salesforce/status/')
    },
    async connect() {
        return apiRequest('salesforce/connect/', { method: 'POST' })
    },
    async callback(code) {
        return apiRequest('salesforce/callback/', {
            method: 'POST',
            body: { code },
        })
    },
    async disconnect() {
        return apiRequest('salesforce/disconnect/', { method: 'DELETE' })
    },
    async startImport(objectTypes) {
        return apiRequest('salesforce/import/', {
            method: 'POST',
            body: { object_types: objectTypes },
        })
    },
    async getImportJob(jobId) {
        return apiRequest(`salesforce/import/${jobId}/`)
    },
    async importHistory() {
        return apiRequest('salesforce/import/history/')
    },
}
```

**Step 2: Create the server-side load function**

Create `frontend/src/routes/(app)/settings/salesforce/+page.server.js`:
```javascript
import { apiRequest } from '$lib/api-helpers.js'

export async function load({ cookies }) {
    try {
        const status = await apiRequest('salesforce/status/', {}, { cookies })
        return { sfStatus: status }
    } catch {
        return { sfStatus: { connected: false } }
    }
}

export const actions = {
    disconnect: async ({ cookies }) => {
        try {
            await apiRequest('salesforce/disconnect/', { method: 'DELETE' }, { cookies })
            return { success: true }
        } catch (error) {
            return { success: false, error: error.message }
        }
    },
}
```

**Step 3: Create the Salesforce settings page**

Create `frontend/src/routes/(app)/settings/salesforce/+page.svelte`:

This page should:
- Show connection status (connected/not connected)
- "Connect to Salesforce" button that calls the connect API and redirects to SF auth
- When connected: show instance URL, connected by email, connection date
- "Disconnect" button with confirmation
- Link to the Import page when connected

Use existing shadcn-svelte components: `Card`, `Button`, `Badge`, `Separator`.
Use Lucide icons: `Cloud`, `CloudOff`, `ExternalLink`, `Trash2`.

Follow the existing page patterns from accounts/contacts pages (use `$props()` for page data, `$state` for local state, `enhance` for form actions).

**Step 4: Add sidebar navigation**

Add a "Salesforce" item under the Settings section in `AppSidebar.svelte`, using the `Cloud` icon from Lucide.

**Step 5: Test manually**

Run: `cd frontend && pnpm run dev`
Navigate to `/settings/salesforce` and verify the page renders.

**Step 6: Commit**

```bash
git add frontend/src/routes/\(app\)/settings/salesforce/ frontend/src/lib/api.js frontend/src/lib/components/layout/AppSidebar.svelte
git commit -m "feat(sf-import): add Salesforce connection settings page"
```

---

### Task 9: Frontend - Import Page with Progress

**Files:**
- Create: `frontend/src/routes/(app)/settings/salesforce/import/+page.server.js`
- Create: `frontend/src/routes/(app)/settings/salesforce/import/+page.svelte`

**Step 1: Create server-side load**

Create `frontend/src/routes/(app)/settings/salesforce/import/+page.server.js`:
```javascript
import { apiRequest } from '$lib/api-helpers.js'
import { redirect } from '@sveltejs/kit'

export async function load({ cookies }) {
    try {
        const status = await apiRequest('salesforce/status/', {}, { cookies })
        if (!status.connected) {
            redirect(302, '/settings/salesforce')
        }

        const history = await apiRequest('salesforce/import/history/', {}, { cookies })
        return { sfStatus: status, importHistory: history.jobs || [] }
    } catch {
        redirect(302, '/settings/salesforce')
    }
}
```

**Step 2: Create the import page**

Create `frontend/src/routes/(app)/settings/salesforce/import/+page.svelte`:

This page should have:
- **Object type selection:** Checkboxes for Account, Contact, Opportunity, Product, Order, Quote
- Dependency hints shown as help text (e.g. "Contacts depend on Accounts")
- "Start Import" button that calls `salesforce.startImport(selectedTypes)`
- **Active import progress section** (shown when import is running):
  - Poll `salesforce.getImportJob(jobId)` every 2 seconds using `setInterval`
  - Overall progress bar (imported + skipped + errors) / total
  - Per-object-type rows showing: name, status badge (Pending/Importing/Done/Failed), counts
  - Stop polling when status is COMPLETED or FAILED
- **Import history table** at the bottom
  - Date, status badge, object types, imported/skipped/error counts
  - Click to expand error details

Use shadcn-svelte: `Card`, `Button`, `Checkbox`, `Progress`, `Badge`, `Table`, `Separator`, `Collapsible`.
Use Lucide icons: `Download`, `CheckCircle`, `XCircle`, `Clock`, `Loader2`.

Follow Svelte 5 patterns: `$state`, `$effect` for polling, `$derived` for computed values.

**Step 3: Test manually**

Run: `cd frontend && pnpm run dev`
Navigate to `/settings/salesforce/import` and verify the page renders with checkboxes and history table.

**Step 4: Commit**

```bash
git add frontend/src/routes/\(app\)/settings/salesforce/import/
git commit -m "feat(sf-import): add import page with object selection, progress tracking, and history"
```

---

### Task 10: Add RLS Policies for New Tables via Migration

**Files:**
- Create: migration file in `orders/migrations/`
- Create: migration file in `salesforce_imports/migrations/`

**Step 1: Create RLS migration for orders**

Create a new migration in `backend/orders/migrations/` that enables RLS:

```python
from django.db import migrations
from common.rls import get_enable_policy_sql


class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            get_enable_policy_sql("orders"),
            reverse_sql="ALTER TABLE orders DISABLE ROW LEVEL SECURITY;",
        ),
        migrations.RunSQL(
            get_enable_policy_sql("order_line_item"),
            reverse_sql="ALTER TABLE order_line_item DISABLE ROW LEVEL SECURITY;",
        ),
    ]
```

**Step 2: Create RLS migration for salesforce_imports**

Similar migration for `salesforce_connection`, `salesforce_import_job`, `salesforce_imported_record`.

**Step 3: Run migrations**

Run: `cd backend && python manage.py migrate`

**Step 4: Verify RLS**

Run: `cd backend && python manage.py manage_rls --status`
Verify new tables appear as RLS-protected.

**Step 5: Commit**

```bash
git add orders/migrations/ salesforce_imports/migrations/
git commit -m "feat(sf-import): add RLS policies for orders and salesforce_imports tables"
```

---

### Task 11: Integration Testing & OAuth Callback Handler on Frontend

**Files:**
- Create: `frontend/src/routes/(app)/settings/salesforce/callback/+page.server.js`
- Create: `frontend/src/routes/(app)/settings/salesforce/callback/+page.svelte`

**Step 1: Create the OAuth callback page**

After SF authorizes, it redirects to the frontend with a `code` query param. The frontend needs to exchange this code via the backend.

Create `frontend/src/routes/(app)/settings/salesforce/callback/+page.server.js`:
```javascript
import { apiRequest } from '$lib/api-helpers.js'
import { redirect } from '@sveltejs/kit'

export async function load({ url, cookies }) {
    const code = url.searchParams.get('code')
    const error = url.searchParams.get('error')

    if (error) {
        redirect(302, '/settings/salesforce?error=' + encodeURIComponent(error))
    }

    if (!code) {
        redirect(302, '/settings/salesforce')
    }

    try {
        await apiRequest(
            'salesforce/callback/',
            { method: 'POST', body: { code } },
            { cookies }
        )
        redirect(302, '/settings/salesforce?connected=true')
    } catch (err) {
        redirect(302, '/settings/salesforce?error=' + encodeURIComponent(err.message))
    }
}
```

Create a minimal `+page.svelte` that shows "Connecting..." (the server load will redirect before this renders):
```svelte
<p>Connecting to Salesforce...</p>
```

**Step 2: Update SF_REDIRECT_URI**

Update `backend/crm/settings.py` to point to the frontend callback:
```python
SF_REDIRECT_URI = os.environ.get(
    "SF_REDIRECT_URI",
    "http://localhost:5173/settings/salesforce/callback"
)
```

**Step 3: Commit**

```bash
git add frontend/src/routes/\(app\)/settings/salesforce/callback/ backend/crm/settings.py
git commit -m "feat(sf-import): add OAuth callback handler on frontend"
```

---

### Task 12: Run Full Test Suite & Final Verification

**Step 1: Run all backend tests**

Run: `cd backend && pytest -v`
Expected: All tests pass

**Step 2: Run frontend checks**

Run: `cd frontend && pnpm run check && pnpm run lint`
Expected: No errors

**Step 3: Verify the full flow manually**

1. Start backend: `cd backend && python manage.py runserver`
2. Start frontend: `cd frontend && pnpm run dev`
3. Start Celery: `cd backend && celery -A crm worker --loglevel=INFO`
4. Navigate to `/settings/salesforce`
5. Verify connection page renders
6. Navigate to `/settings/salesforce/import`
7. Verify import page renders with checkboxes

**Step 4: Final commit**

```bash
git add -A
git commit -m "feat(sf-import): complete Salesforce import feature"
```
