"""Tests for the User.name auto-fill on creation."""

import pytest

from common.models import User


@pytest.mark.django_db
class TestUserNameAutoFill:
    """User.save() / UserManager.create_user() set name from email-local-part."""

    def test_create_user_without_name_falls_back_to_email_prefix(self):
        user = User.objects.create(email="aswin.1231@example.com")
        assert user.name == "aswin.1231"

    def test_create_user_with_explicit_name_is_preserved(self):
        user = User.objects.create(email="x@example.com", name="Alex Carter")
        assert user.name == "Alex Carter"

    def test_get_or_create_falls_back_when_creating(self):
        user, created = User.objects.get_or_create(email="foo.bar@example.com")
        assert created is True
        assert user.name == "foo.bar"

    def test_manager_create_user_sets_name_when_missing(self):
        user = User.objects.create_user(email="manager@example.com")
        assert user.name == "manager"

    def test_subsequent_save_does_not_overwrite_cleared_name(self):
        """If a user PATCHes name to "", the next save() must keep it empty."""
        user = User.objects.create(email="keep.empty@example.com")
        assert user.name == "keep.empty"  # auto-filled on creation
        user.name = ""
        user.save()
        user.refresh_from_db()
        assert user.name == ""

    def test_longest_storable_email_fills_name_within_limit(self):
        """The longest email the column can hold still yields a valid `name`.

        `save()` caps the fallback at `[:255]` to match `name`'s max_length, but
        that slice is unreachable through the database: `email` is an
        EmailField (varchar(254)), so its local part tops out at 254 - len("@…")
        and can never exceed 255. Building a 300-char local part therefore never
        tested truncation — it just overflowed `email`, which SQLite silently
        allows and PostgreSQL rejects with DataError.

        So assert the property that is actually reachable: the longest storable
        email fills `name` with its full local part, still within the limit.
        """
        domain = "@example.com"
        local = "a" * (254 - len(domain))  # -> email is exactly 254 chars
        user = User.objects.create(email=f"{local}{domain}")
        assert user.name == local
        assert len(user.name) <= 255
