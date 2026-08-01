"""
Tests for organization management views: OrgProfileCreateView, OrgUpdateView,
ProfileView, ProfileDetailView, OrgSettingsView.

Run with: pytest common/tests/test_organizations.py -v
"""

import pytest
from rest_framework import status

from common.models import Profile, Teams


@pytest.mark.django_db
class TestOrgProfileCreateView:
    """Tests for GET/POST /api/org/"""

    url = "/api/org/"

    def test_create_org(self, admin_client, admin_user):
        """Create a new organization."""
        response = admin_client.post(
            self.url,
            {"name": "New Organization"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["error"] is False
        assert "org" in response.data
        # User should be an admin of the new org
        assert Profile.objects.filter(
            user=admin_user, org__name="New Organization", role="ADMIN"
        ).exists()

    def test_create_org_special_chars(self, admin_client):
        """Organization name with special characters should fail."""
        response = admin_client.post(
            self.url,
            {"name": "Bad@Name!"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_org_duplicate_name(self, admin_client, org_a):
        """Creating org with duplicate name should fail."""
        response = admin_client.post(
            self.url,
            {"name": org_a.name},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_orgs(self, admin_client, admin_user, admin_profile, org_a):
        """List organizations the user belongs to."""
        response = admin_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["error"] is False
        assert "profile_org_list" in response.data
        org_names = [p["org"]["name"] for p in response.data["profile_org_list"]]
        assert org_a.name in org_names

    def test_list_orgs_unauthenticated(self, unauthenticated_client):
        """Unauthenticated user gets 401."""
        response = unauthenticated_client.get(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestOrgUpdateView:
    """Tests for GET/PUT/PATCH /api/org/<pk>/"""

    def _url(self, pk):
        return f"/api/org/{pk}/"

    def test_get_org(self, admin_client, org_a):
        """Get organization details."""
        response = admin_client.get(self._url(org_a.id))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["error"] is False
        assert "org" in response.data

    def test_update_org(self, admin_client, org_a):
        """Admin can update organization."""
        response = admin_client.put(
            self._url(org_a.id),
            {"name": "Updated Org Name"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["error"] is False
        org_a.refresh_from_db()
        assert org_a.name == "Updated Org Name"

    def test_update_org_non_admin_forbidden(self, user_client, org_a, user_profile):
        """Non-admin user cannot update organization."""
        response = user_client.put(
            self._url(org_a.id),
            {"name": "Nope"},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_different_org_forbidden(self, admin_client, org_b):
        """Cannot update a different organization."""
        response = admin_client.put(
            self._url(org_b.id),
            {"name": "Cross Org Update"},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_patch_org(self, admin_client, org_a):
        """Partial update of organization via PATCH."""
        response = admin_client.patch(
            self._url(org_a.id),
            {"name": "Patched Org"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["error"] is False

    def test_patch_org_non_admin_forbidden(self, user_client, org_a, user_profile):
        """Non-admin cannot PATCH organization."""
        response = user_client.patch(
            self._url(org_a.id),
            {"name": "No Patch"},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_different_org_forbidden(self, admin_client, org_b):
        """Cannot get a different organization's details."""
        response = admin_client.get(self._url(org_b.id))
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestProfileView:
    """Tests for GET/PATCH /api/profile/"""

    url = "/api/profile/"

    def test_get_profile(self, admin_client, admin_profile):
        """Get current user's profile."""
        response = admin_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert "user_obj" in response.data

    def test_patch_profile_phone(self, admin_client, admin_profile):
        """Update phone via PATCH."""
        response = admin_client.patch(
            self.url,
            {"phone": "+9876543210"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert "user_obj" in response.data
        admin_profile.refresh_from_db()
        assert admin_profile.phone == "+9876543210"

    def test_patch_profile_name(self, admin_client, admin_profile):
        """Update name on User via PATCH /api/profile/."""
        response = admin_client.patch(
            self.url,
            {"name": "Alex Carter"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        admin_profile.user.refresh_from_db()
        assert admin_profile.user.name == "Alex Carter"

    def test_patch_profile_name_trims_whitespace(self, admin_client, admin_profile):
        """Name input is trimmed before save."""
        response = admin_client.patch(
            self.url,
            {"name": "  Alex Carter  "},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        admin_profile.user.refresh_from_db()
        assert admin_profile.user.name == "Alex Carter"

    def test_patch_profile_name_and_phone_together(self, admin_client, admin_profile):
        """Both fields update in a single PATCH."""
        response = admin_client.patch(
            self.url,
            {"name": "Alex Carter", "phone": "+1234567890"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        admin_profile.refresh_from_db()
        admin_profile.user.refresh_from_db()
        assert admin_profile.user.name == "Alex Carter"
        assert admin_profile.phone == "+1234567890"

    def test_patch_profile_rejects_invalid_phone(self, admin_client, admin_profile):
        """A phone with letters is a clean 400, not written to the column.

        The view used to write request.data straight onto the model, so any
        string landed. It now runs through flexible_phone_validator.
        """
        Profile.objects.filter(pk=admin_profile.pk).update(phone="+1234567890")
        response = admin_client.patch(
            self.url,
            {"phone": "not a phone ext 5"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "phone" in response.data
        admin_profile.refresh_from_db()
        assert admin_profile.phone == "+1234567890"  # unchanged

    def test_patch_profile_allows_blank_phone_to_clear(
        self, admin_client, admin_profile
    ):
        """A blank phone is allowed and clears the field (allow_blank path)."""
        Profile.objects.filter(pk=admin_profile.pk).update(phone="+1234567890")
        response = admin_client.patch(self.url, {"phone": ""}, format="json")
        assert response.status_code == status.HTTP_200_OK
        admin_profile.refresh_from_db()
        assert admin_profile.phone == ""

    def test_patch_profile_rejects_overlong_name(self, admin_client, admin_profile):
        """A name past the 255 max is a clean 400, not a silent truncation."""
        response = admin_client.patch(
            self.url,
            {"name": "x" * 256},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "name" in response.data

    def test_patch_profile_cannot_escalate_role(self, user_client, user_profile):
        """A plain USER cannot set role/admin flags on their own profile here.

        The self-edit serializer names only phone and name, so a role or
        is_organization_admin in the body is ignored (not 400'd) — the request
        succeeds, the privileged fields do not move. This is the /api/profile/
        counterpart to the CreateProfileSerializer escalation that was closed on
        /api/user/<id>/; the door has to be shut on every self-edit path.
        """
        response = user_client.patch(
            self.url,
            {
                "role": "ADMIN",
                "is_organization_admin": True,
                "has_sales_access": True,
                "phone": "+1234567890",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        user_profile.refresh_from_db()
        assert user_profile.role == "USER"
        assert user_profile.is_organization_admin is False
        assert user_profile.has_sales_access is False
        assert user_profile.phone == "+1234567890"  # the legit field did change

    def test_get_profile_includes_teams(self, admin_client, admin_profile):
        """GET surfaces the current user's team names for the profile page."""
        team = Teams.objects.create(name="New business", org=admin_profile.org)
        team.users.add(admin_profile)
        response = admin_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["user_obj"]["teams"] == ["New business"]


@pytest.mark.django_db
class TestOrgSettingsView:
    """Tests for GET/PATCH /api/org/settings/"""

    url = "/api/org/settings/"

    def test_get_org_settings(self, admin_client, org_a):
        """Get organization settings."""
        response = admin_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert "default_currency" in response.data
        assert "currency_symbol" in response.data

    def test_patch_org_settings(self, admin_client, org_a):
        """Admin can update organization settings."""
        response = admin_client.patch(
            self.url,
            {"default_currency": "EUR"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        org_a.refresh_from_db()
        assert org_a.default_currency == "EUR"

    def test_patch_org_settings_non_admin_forbidden(
        self, user_client, org_a, user_profile
    ):
        """Non-admin cannot update organization settings."""
        response = user_client.patch(
            self.url,
            {"default_currency": "GBP"},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_patch_org_settings_company_name(self, admin_client, org_a):
        """Update company name in org settings."""
        response = admin_client.patch(
            self.url,
            {"company_name": "ACME Corp"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        org_a.refresh_from_db()
        assert org_a.company_name == "ACME Corp"

    # ── Reads: what the settings page shows, and what it must never show ──────

    def test_get_org_settings_member_can_read(self, user_client, org_a, user_profile):
        """A non-admin member can READ org settings (the page is read-only for
        them). Editing is gated; reading the company profile is not."""
        response = user_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert "company_name" in response.data

    def test_get_org_settings_never_exposes_api_key(self, admin_client, org_a):
        """The org API key authenticates as the org's first admin. It must never
        appear in the settings payload -- not even for an admin, who reads/rotates
        it through the dedicated OrgApiKeyView instead."""
        response = admin_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert "api_key" not in response.data
        # And the value itself is nowhere in the serialized body.
        org_a.refresh_from_db()
        assert org_a.api_key not in str(response.data)

    def test_get_org_settings_includes_behaviour_and_header_fields(
        self, admin_client, org_a
    ):
        """The two behaviour switches and the read-only header context are part
        of the payload the page renders."""
        response = admin_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        for key in (
            "csat_enabled",
            "auto_close_children_on_parent_close",
            "member_count",
            "created_at",
        ):
            assert key in response.data

    def test_get_org_settings_member_count(
        self, admin_client, org_a, admin_profile, user_profile
    ):
        """member_count reflects the active profiles in this org."""
        response = admin_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        # admin_profile + user_profile are both active in org_a.
        assert response.data["member_count"] == 2

    # ── Writes: the behaviour toggles that had no API write path before ──────

    def test_patch_org_settings_behaviour_toggles(self, admin_client, org_a):
        """Admin can flip csat_enabled and the cascade-close default -- the only
        write path these columns have."""
        assert org_a.csat_enabled is True
        assert org_a.auto_close_children_on_parent_close is False
        response = admin_client.patch(
            self.url,
            {
                "csat_enabled": False,
                "auto_close_children_on_parent_close": True,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        org_a.refresh_from_db()
        assert org_a.csat_enabled is False
        assert org_a.auto_close_children_on_parent_close is True

    def test_patch_org_settings_toggle_non_admin_forbidden(
        self, user_client, org_a, user_profile
    ):
        """A member cannot silence org-wide CSAT (or any switch)."""
        response = user_client.patch(
            self.url,
            {"csat_enabled": False},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        org_a.refresh_from_db()
        assert org_a.csat_enabled is True

    # ── Mass assignment: the allow-list holds ────────────────────────────────

    def test_patch_org_settings_cannot_change_api_key(self, admin_client, org_a):
        """api_key is not a writable field. A PATCH naming it is ignored, not
        honoured -- the credential is only rotated via OrgApiKeyView."""
        original_key = org_a.api_key
        response = admin_client.patch(
            self.url,
            {"api_key": "attacker-chosen-key", "company_name": "Legit Co"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        org_a.refresh_from_db()
        assert org_a.api_key == original_key
        # The legitimate field in the same request still applied.
        assert org_a.company_name == "Legit Co"

    def test_patch_org_settings_cannot_deactivate_org(self, admin_client, org_a):
        """is_active (the org kill switch) is not editable through the settings
        form -- an org cannot deactivate itself here."""
        response = admin_client.patch(
            self.url,
            {"is_active": False},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        org_a.refresh_from_db()
        assert org_a.is_active is True

    # ── Validation: bad input is a clean 400, not a 500 ──────────────────────

    def test_patch_org_settings_invalid_currency_400(self, admin_client, org_a):
        """A currency outside the supported list is rejected with a 400."""
        response = admin_client.patch(
            self.url,
            {"default_currency": "ZZZ"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        org_a.refresh_from_db()
        assert org_a.default_currency != "ZZZ"

    def test_patch_org_settings_invalid_country_400(self, admin_client, org_a):
        """An unknown country code is rejected with a 400."""
        response = admin_client.patch(
            self.url,
            {"country": "QQ"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_patch_org_settings_invalid_email_400(self, admin_client, org_a):
        """A malformed email is rejected with a 400, not stored raw."""
        response = admin_client.patch(
            self.url,
            {"email": "not-an-email"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    # ── Tenant isolation: the endpoint edits the CALLER's org, never another ─

    def test_patch_org_settings_edits_only_callers_org(
        self, org_b_client, org_a, org_b, admin_profile
    ):
        """org/settings/ takes the org from request.profile, never a client id, so
        an admin of org B editing settings can only ever touch org B."""
        org_a_name_before = org_a.company_name
        response = org_b_client.patch(
            self.url,
            {"company_name": "Org B Trading Ltd"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        org_a.refresh_from_db()
        org_b.refresh_from_db()
        assert org_b.company_name == "Org B Trading Ltd"
        assert org_a.company_name == org_a_name_before

    def test_get_org_settings_unauthenticated_rejected(self, unauthenticated_client):
        """No token, no settings. (Asserts rejection without pinning the exact
        401-vs-403 code, which is inconsistent across this app's endpoints.)"""
        response = unauthenticated_client.get(self.url)
        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )
