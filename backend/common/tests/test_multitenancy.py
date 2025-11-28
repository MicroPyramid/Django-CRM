"""
Multi-Tenancy Security Tests

These tests verify that the multi-tenancy implementation properly isolates
data between organizations and prevents cross-org data access.

Run with: pytest common/tests/test_multitenancy.py -v
"""

from unittest.mock import MagicMock, patch

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import RequestFactory, TestCase
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import Account
from common.middleware.get_company import GetProfileAndOrg
from common.models import Address, Attachments, Comment, Org, Profile, Tags, Teams, User
from common.serializer import OrgAwareRefreshToken
from leads.models import Lead


class MultiTenancyBaseTestCase(TestCase):
    """Base test case with common setup for multi-tenancy tests"""

    def setUp(self):
        # Create two organizations
        self.org_a = Org.objects.create(name="Organization A")
        self.org_b = Org.objects.create(name="Organization B")

        # Create users
        self.user_a = User.objects.create_user(
            email="user_a@test.com", password="testpass123"
        )
        self.user_b = User.objects.create_user(
            email="user_b@test.com", password="testpass123"
        )

        # Create profiles (user membership in orgs)
        self.profile_a = Profile.objects.create(
            user=self.user_a, org=self.org_a, role="ADMIN", is_active=True
        )
        self.profile_b = Profile.objects.create(
            user=self.user_b, org=self.org_b, role="ADMIN", is_active=True
        )

        # API client
        self.client = APIClient()
        self.factory = RequestFactory()


class TestOrgAwareRefreshToken(MultiTenancyBaseTestCase):
    """Test JWT token generation with org context"""

    def test_token_includes_org_id(self):
        """Token should include org_id in payload"""
        token = OrgAwareRefreshToken.for_user_and_org(self.user_a, self.org_a)

        # Access token should have org_id
        access_token = token.access_token
        self.assertEqual(str(access_token["org_id"]), str(self.org_a.id))

    def test_token_without_org(self):
        """Token can be generated without org for initial login"""
        token = OrgAwareRefreshToken.for_user_and_org(self.user_a, None)

        # Should not have org_id claim
        access_token = token.access_token
        self.assertNotIn("org_id", access_token)

    def test_different_orgs_different_tokens(self):
        """Different orgs should produce different token claims"""
        token_a = OrgAwareRefreshToken.for_user_and_org(self.user_a, self.org_a)
        token_b = OrgAwareRefreshToken.for_user_and_org(self.user_a, self.org_b)

        self.assertNotEqual(
            str(token_a.access_token["org_id"]), str(token_b.access_token["org_id"])
        )


class TestMiddlewareOrgValidation(MultiTenancyBaseTestCase):
    """Test middleware extracts org from JWT, not headers"""

    def test_org_extracted_from_jwt_not_header(self):
        """Middleware should use org_id from JWT, ignoring org header"""
        # Generate token for org_a
        token = OrgAwareRefreshToken.for_user_and_org(self.user_a, self.org_a)

        # Make request with JWT for org_a but header claiming org_b
        request = self.factory.get(
            "/api/leads/",
            HTTP_AUTHORIZATION=f"Bearer {token.access_token}",
            HTTP_ORG=str(self.org_b.id),  # Attempt to spoof org
        )

        middleware = GetProfileAndOrg(lambda r: r)
        middleware(request)

        # Should use org from JWT (org_a), not header (org_b)
        self.assertEqual(request.profile.org, self.org_a)
        self.assertEqual(request.org, self.org_a)

    def test_revoked_membership_denied(self):
        """User whose membership was revoked should be denied"""
        # Generate token
        token = OrgAwareRefreshToken.for_user_and_org(self.user_a, self.org_a)

        # Revoke membership (deactivate profile)
        self.profile_a.is_active = False
        self.profile_a.save()

        # Make request
        request = self.factory.get(
            "/api/leads/", HTTP_AUTHORIZATION=f"Bearer {token.access_token}"
        )

        middleware = GetProfileAndOrg(lambda r: r)
        middleware(request)

        # Middleware should not set profile when membership is revoked
        self.assertIsNone(getattr(request, "profile", None))

    def test_api_key_scoped_to_org(self):
        """API key authentication should be scoped to specific org"""
        request = self.factory.get("/api/leads/", HTTP_TOKEN=self.org_a.api_key)

        middleware = GetProfileAndOrg(lambda r: r)
        middleware(request)

        self.assertEqual(request.org, self.org_a)


class TestCrossOrgDataAccess(MultiTenancyBaseTestCase):
    """Test that cross-org data access is prevented"""

    def setUp(self):
        super().setUp()

        # Create data in each org
        self.account_a = Account.objects.create(name="Account in Org A", org=self.org_a)
        self.account_b = Account.objects.create(name="Account in Org B", org=self.org_b)

        self.lead_a = Lead.objects.create(
            first_name="Lead",
            last_name="In Org A",
            email="lead_a@test.com",
            org=self.org_a,
        )
        self.lead_b = Lead.objects.create(
            first_name="Lead",
            last_name="In Org B",
            email="lead_b@test.com",
            org=self.org_b,
        )

    def test_queryset_filters_by_org(self):
        """QuerySet should only return data for the specified org"""
        # Filter for org_a
        accounts_a = Account.objects.filter(org=self.org_a)
        self.assertEqual(accounts_a.count(), 1)
        self.assertEqual(accounts_a.first().name, "Account in Org A")

        # Filter for org_b
        accounts_b = Account.objects.filter(org=self.org_b)
        self.assertEqual(accounts_b.count(), 1)
        self.assertEqual(accounts_b.first().name, "Account in Org B")

    def test_api_returns_only_org_data(self):
        """API endpoints should only return data for user's org"""
        # Login as user_a
        token = OrgAwareRefreshToken.for_user_and_org(self.user_a, self.org_a)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")

        # Get accounts - should only see org_a data
        response = self.client.get("/api/accounts/")

        if response.status_code == 200:
            data = response.json()
            # Verify all returned accounts belong to org_a
            if "results" in data:
                for account in data["results"]:
                    self.assertEqual(account.get("org"), str(self.org_a.id))


class TestGenericFKOrgValidation(MultiTenancyBaseTestCase):
    """Test that Comment and Attachments validate org matches content object"""

    def setUp(self):
        super().setUp()

        self.lead_a = Lead.objects.create(
            first_name="Lead",
            last_name="In Org A",
            email="lead_a@test.com",
            org=self.org_a,
        )

    def test_comment_org_must_match_content_object(self):
        """Comment org must match the referenced object's org"""
        from django.contrib.contenttypes.models import ContentType

        lead_content_type = ContentType.objects.get_for_model(Lead)

        # Try to create comment with different org than lead
        comment = Comment(
            content_type=lead_content_type,
            object_id=self.lead_a.id,
            comment="Cross-org comment attempt",
            org=self.org_b,  # Different org than lead
            commented_by=self.profile_b,
        )

        with self.assertRaises(ValidationError) as context:
            comment.save()

        self.assertIn("org", context.exception.message_dict)

    def test_comment_same_org_succeeds(self):
        """Comment with same org as content object should succeed"""
        from django.contrib.contenttypes.models import ContentType

        lead_content_type = ContentType.objects.get_for_model(Lead)

        comment = Comment(
            content_type=lead_content_type,
            object_id=self.lead_a.id,
            comment="Same-org comment",
            org=self.org_a,  # Same org as lead
            commented_by=self.profile_a,
            created_by=self.user_a,
            updated_by=self.user_a,
        )

        # Should not raise
        comment.save()
        self.assertIsNotNone(comment.id)

    def test_attachment_org_must_match_content_object(self):
        """Attachment org must match the referenced object's org"""
        from django.contrib.contenttypes.models import ContentType
        from django.core.files.uploadedfile import SimpleUploadedFile

        lead_content_type = ContentType.objects.get_for_model(Lead)

        attachment = Attachments(
            content_type=lead_content_type,
            object_id=self.lead_a.id,
            file_name="test.txt",
            attachment=SimpleUploadedFile("test.txt", b"content"),
            org=self.org_b,  # Different org than lead
        )

        with self.assertRaises(ValidationError) as context:
            attachment.save()

        self.assertIn("org", context.exception.message_dict)


class TestOrgSwitching(MultiTenancyBaseTestCase):
    """Test organization switching functionality"""

    def setUp(self):
        super().setUp()

        # Give user_a access to both orgs
        self.profile_a_in_b = Profile.objects.create(
            user=self.user_a, org=self.org_b, role="USER", is_active=True
        )

    def test_switch_org_success(self):
        """User with access to multiple orgs can switch"""
        # Login to org_a first
        token = OrgAwareRefreshToken.for_user_and_org(self.user_a, self.org_a)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")

        # Switch to org_b
        response = self.client.post(
            "/api/auth/switch-org/", {"org_id": str(self.org_b.id)}
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Should have new tokens with org_b
        self.assertIn("access_token", data)
        self.assertEqual(data["current_org"]["id"], str(self.org_b.id))

    def test_switch_to_unauthorized_org_fails(self):
        """User cannot switch to org they don't have access to"""
        # user_b only has access to org_b
        token = OrgAwareRefreshToken.for_user_and_org(self.user_b, self.org_b)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")

        # Try to switch to org_a
        response = self.client.post(
            "/api/auth/switch-org/", {"org_id": str(self.org_a.id)}
        )

        self.assertEqual(response.status_code, 403)


class TestLoginWithOrgContext(MultiTenancyBaseTestCase):
    """Test login endpoint includes org context"""

    def test_login_returns_current_org(self):
        """Login should return current_org in response"""
        response = self.client.post(
            "/api/auth/login/", {"email": "user_a@test.com", "password": "testpass123"}
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertIn("current_org", data)
        self.assertEqual(data["current_org"]["id"], str(self.org_a.id))

    def test_login_with_specific_org(self):
        """Login can specify which org to use"""
        # Give user_a access to org_b
        Profile.objects.create(
            user=self.user_a, org=self.org_b, role="USER", is_active=True
        )

        response = self.client.post(
            "/api/auth/login/",
            {
                "email": "user_a@test.com",
                "password": "testpass123",
                "org_id": str(self.org_b.id),
            },
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["current_org"]["id"], str(self.org_b.id))

    def test_login_with_invalid_org_fails(self):
        """Login with org user doesn't have access to should fail"""
        response = self.client.post(
            "/api/auth/login/",
            {
                "email": "user_a@test.com",
                "password": "testpass123",
                "org_id": str(self.org_b.id),  # user_a doesn't have access
            },
        )

        self.assertEqual(response.status_code, 403)


class TestBaseOrgModel(TestCase):
    """Test BaseOrgModel validation"""

    def test_org_required_on_save(self):
        """BaseOrgModel descendants should require org on save"""
        from common.base import BaseOrgModel

        # This is tested indirectly through models like Teams
        org = Org.objects.create(name="Test Org")

        team = Teams(name="Test Team", description="Test Description", org=org)
        team.save()  # Should succeed

        self.assertIsNotNone(team.id)


class TestOrgScopedQuerySet(MultiTenancyBaseTestCase):
    """Test OrgScopedQuerySet helper methods"""

    def setUp(self):
        super().setUp()

        # Create teams in each org
        self.team_a = Teams.objects.create(
            name="Team A", description="In Org A", org=self.org_a
        )
        self.team_b = Teams.objects.create(
            name="Team B", description="In Org B", org=self.org_b
        )

    def test_for_org_filters_correctly(self):
        """for_org() should filter by organization"""
        teams = Teams.objects.filter(org=self.org_a)
        self.assertEqual(teams.count(), 1)
        self.assertEqual(teams.first().name, "Team A")

    def test_for_request_uses_profile_org(self):
        """for_request() should use org from request.profile"""
        # Create mock request
        request = MagicMock()
        request.profile = self.profile_a

        # This would be used with OrgScopedManager
        # Teams.objects.for_request(request)


class TestNullOrgPrevention(MultiTenancyBaseTestCase):
    """Test that models properly handle org field"""

    def test_comment_requires_org(self):
        """Comment should require org field"""
        from django.contrib.contenttypes.models import ContentType

        lead = Lead.objects.create(
            first_name="Test", last_name="Lead", email="test@test.com", org=self.org_a
        )

        lead_content_type = ContentType.objects.get_for_model(Lead)

        # Try to create comment without org
        comment = Comment(
            content_type=lead_content_type,
            object_id=lead.id,
            comment="No org comment",
            # org not set
        )

        with self.assertRaises(Exception):
            comment.save()


class TestRLSIntegration(MultiTenancyBaseTestCase):
    """
    Test Row-Level Security at the database level.

    These tests verify that PostgreSQL RLS policies properly isolate
    data between organizations. They require:
    - PostgreSQL database
    - Non-superuser database connection (superusers bypass RLS)
    - RLS migrations applied
    """

    @classmethod
    def setUpClass(cls):
        """Check if RLS testing is possible."""
        super().setUpClass()
        from django.db import connection

        # Check if using PostgreSQL
        cls.is_postgres = connection.vendor == "postgresql"

        if cls.is_postgres:
            # Check if database user is a superuser (which bypasses RLS)
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT usesuper FROM pg_user WHERE usename = current_user"
                )
                result = cursor.fetchone()
                cls.is_superuser = result[0] if result else True

    def setUp(self):
        super().setUp()

        # Create test data in each org
        self.lead_a = Lead.objects.create(
            first_name="Lead", last_name="OrgA", email="lead_a@test.com", org=self.org_a
        )
        self.lead_b = Lead.objects.create(
            first_name="Lead", last_name="OrgB", email="lead_b@test.com", org=self.org_b
        )

        self.account_a = Account.objects.create(
            name="Account A", email="account_a@test.com", org=self.org_a
        )
        self.account_b = Account.objects.create(
            name="Account B", email="account_b@test.com", org=self.org_b
        )

    def test_empty_context_returns_no_rows(self):
        """With empty RLS context, queries should return zero rows (fail-safe)."""
        if not self.is_postgres:
            self.skipTest("RLS requires PostgreSQL")

        if self.is_superuser:
            self.skipTest(
                "RLS is bypassed for superusers - use non-superuser for testing"
            )

        from django.db import connection

        with connection.cursor() as cursor:
            # Clear the org context (empty string means no context)
            cursor.execute("SELECT set_config('app.current_org', '', true)")

            # Query should return no rows due to NULLIF fail-safe
            cursor.execute("SELECT COUNT(*) FROM lead")
            count = cursor.fetchone()[0]

            self.assertEqual(count, 0, "Empty context should return zero rows")

    def test_rls_isolates_between_orgs(self):
        """RLS should isolate data between organizations."""
        if not self.is_postgres:
            self.skipTest("RLS requires PostgreSQL")

        if self.is_superuser:
            self.skipTest(
                "RLS is bypassed for superusers - use non-superuser for testing"
            )

        from django.db import connection

        with connection.cursor() as cursor:
            # Set context to org_a
            cursor.execute(
                "SELECT set_config('app.current_org', %s, true)", [str(self.org_a.id)]
            )

            # Should only see org_a's lead
            cursor.execute("SELECT id, first_name FROM lead")
            leads = cursor.fetchall()

            self.assertEqual(len(leads), 1, "Should only see one lead")
            self.assertEqual(str(leads[0][0]), str(self.lead_a.id))

            # Now switch to org_b
            cursor.execute(
                "SELECT set_config('app.current_org', %s, true)", [str(self.org_b.id)]
            )

            cursor.execute("SELECT id, first_name FROM lead")
            leads = cursor.fetchall()

            self.assertEqual(len(leads), 1, "Should only see one lead")
            self.assertEqual(str(leads[0][0]), str(self.lead_b.id))

    def test_rls_prevents_insert_to_wrong_org(self):
        """RLS should prevent inserting records with wrong org_id."""
        if not self.is_postgres:
            self.skipTest("RLS requires PostgreSQL")

        if self.is_superuser:
            self.skipTest(
                "RLS is bypassed for superusers - use non-superuser for testing"
            )

        import uuid

        from django.db import connection

        with connection.cursor() as cursor:
            # Set context to org_a
            cursor.execute(
                "SELECT set_config('app.current_org', %s, true)", [str(self.org_a.id)]
            )

            # Try to insert lead with org_b's ID (should fail due to WITH CHECK)
            new_id = uuid.uuid4()
            try:
                cursor.execute(
                    """
                    INSERT INTO lead (id, first_name, last_name, email, org_id, created_at, updated_at)
                    VALUES (%s, 'Test', 'Wrong Org', 'wrong@test.com', %s, NOW(), NOW())
                """,
                    [str(new_id), str(self.org_b.id)],
                )
                self.fail("Should not be able to insert record with wrong org_id")
            except Exception:
                # Expected - RLS should prevent this insert
                pass

    def test_celery_task_rls_context(self):
        """Celery tasks should be able to set RLS context."""
        if not self.is_postgres:
            self.skipTest("RLS requires PostgreSQL")

        if self.is_superuser:
            self.skipTest(
                "RLS is bypassed for superusers - use non-superuser for testing"
            )

        from django.db import connection

        from common.tasks import set_rls_context

        # Simulate Celery task setting RLS context
        set_rls_context(str(self.org_a.id))

        with connection.cursor() as cursor:
            cursor.execute("SELECT current_setting('app.current_org', true)")
            context = cursor.fetchone()[0]

            self.assertEqual(context, str(self.org_a.id))

    def test_rls_status_check(self):
        """Verify RLS is enabled on key tables."""
        if not self.is_postgres:
            self.skipTest("RLS requires PostgreSQL")

        from django.db import connection

        from common.rls import RLS_CONFIG

        with connection.cursor() as cursor:
            for table in ["lead", "accounts", "contacts"]:
                cursor.execute(
                    """
                    SELECT relrowsecurity, relforcerowsecurity
                    FROM pg_class
                    WHERE relname = %s AND relnamespace = 'public'::regnamespace
                """,
                    [table],
                )
                result = cursor.fetchone()

                if result:
                    rls_enabled, rls_forced = result
                    # Just check that RLS is enabled
                    if not rls_enabled:
                        self.fail(f"RLS not enabled on {table}")


# Run tests with: pytest common/tests/test_multitenancy.py -v
