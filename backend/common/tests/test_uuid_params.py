"""Tests for the UUID query-parameter validators in ``common.validators``.

Every list endpoint takes id-valued filters (``tags``, ``assigned_to``,
``account``, ...) straight from the query string and feeds them to an ``id``
lookup. Django's ``UUIDField`` raises ``django.core.exceptions.ValidationError``
while the query is still being built when a value is not a UUID, and DRF's
exception handler does not translate that class, so the request answered 500.

These helpers turn that into a clean 400. The tests below pin both directions:
a well-formed value passes through untouched, a malformed one raises DRF's
``ValidationError``.
"""

import pytest
from django.http import QueryDict
from rest_framework.exceptions import ValidationError

from common.validators import (
    payload_id_list,
    uuid_list_param,
    uuid_param,
    validate_uuid,
    validate_uuid_list,
)

GOOD = "3f2504e0-4f89-41d3-9a0c-0305e82c3301"
OTHER = "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d"


class TestValidateUuid:
    def test_returns_a_well_formed_value_unchanged(self):
        assert validate_uuid(GOOD, "tags") == GOOD

    def test_accepts_uppercase(self):
        assert validate_uuid(GOOD.upper(), "tags") == GOOD.upper()

    @pytest.mark.parametrize(
        "bad", ["notauuid", "p1", "1", "abc-123", "profile-1", GOOD[:-1], GOOD + "0"]
    )
    def test_rejects_a_malformed_value(self, bad):
        with pytest.raises(ValidationError) as exc:
            validate_uuid(bad, "tags")
        # The field name has to reach the client, otherwise a page with six
        # filters gives no clue which one is wrong.
        assert "tags" in str(exc.value)

    @pytest.mark.parametrize(
        "spelling",
        [
            GOOD.replace("-", ""),
            "{" + GOOD + "}",
            f"urn:uuid:{GOOD}",
        ],
    )
    def test_accepts_every_spelling_the_orm_accepts(self, spelling):
        """Acceptance must match ``UUIDField``, not a narrower idea of it.

        ``Lead.objects.filter(tags__id__in=[v])`` builds fine for the plain,
        upper-case, unhyphenated, braced and URN forms alike, because Django
        parses with ``uuid.UUID``. A validator that took only the hyphenated
        form would start rejecting requests that work today, turning a crash
        fix into a behaviour change. This helper parses the same way for that
        reason, so the two cannot drift apart.
        """
        assert validate_uuid(spelling, "tags") == spelling


class TestValidateUuidList:
    def test_accepts_a_list(self):
        assert validate_uuid_list([GOOD, OTHER], "tags") == [GOOD, OTHER]

    def test_accepts_a_bare_string_as_a_single_value(self):
        """A body may send one id unwrapped.

        ``common/views/team_views.py`` used to pass such a string to
        ``users__id__in=``, which iterates it character by character and
        silently matches nothing. Normalising here removes that trap.
        """
        assert validate_uuid_list(GOOD, "assigned_users") == [GOOD]

    def test_drops_nothing_and_rejects_the_whole_list_on_one_bad_entry(self):
        with pytest.raises(ValidationError) as exc:
            validate_uuid_list([GOOD, "notauuid"], "tags")
        assert "notauuid" in str(exc.value)

    def test_empty_input_is_an_empty_list(self):
        assert validate_uuid_list(None, "tags") == []
        assert validate_uuid_list([], "tags") == []
        assert validate_uuid_list("", "tags") == []

    def test_ignores_empty_entries_inside_a_list(self):
        """``?tags=&tags=<id>`` is a browser artefact, not a malformed id.

        A `<select>` with a blank first option submits the empty string. That
        should mean "no filter", not a 400.
        """
        assert validate_uuid_list([GOOD, ""], "tags") == [GOOD]


class TestPayloadIdList:
    """The write paths take M2M ids three different shapes."""

    def test_accepts_a_plain_list(self):
        assert payload_id_list([GOOD, OTHER], "tags") == [GOOD, OTHER]

    def test_accepts_a_json_encoded_list(self):
        """Multipart bodies send the list as JSON text."""
        assert payload_id_list(f'["{GOOD}", "{OTHER}"]', "tags") == [GOOD, OTHER]

    def test_accepts_a_list_of_objects_and_takes_their_ids(self):
        value = [{"id": GOOD, "name": "urgent"}, {"id": OTHER, "name": "vip"}]
        assert payload_id_list(value, "tags") == [GOOD, OTHER]

    def test_accepts_a_bare_id_string(self):
        """Previously this either crashed or matched nothing.

        The update paths ran ``json.loads`` on it, which raises
        ``JSONDecodeError`` and answered 500. The create paths skipped the
        decode and passed the string straight to ``id__in``, which iterates it
        character by character and quietly matched no rows.
        """
        assert payload_id_list(GOOD, "tags") == [GOOD]

    def test_malformed_json_is_a_400_not_a_500(self):
        with pytest.raises(ValidationError) as exc:
            payload_id_list("[not json", "tags")
        assert "tags" in str(exc.value)

    def test_a_malformed_id_inside_the_list_is_a_400(self):
        with pytest.raises(ValidationError):
            payload_id_list([GOOD, "notauuid"], "tags")

    def test_a_malformed_id_inside_an_object_is_a_400(self):
        with pytest.raises(ValidationError):
            payload_id_list([{"id": "notauuid"}], "tags")

    def test_empty_input_is_an_empty_list(self):
        for empty in (None, "", [], "[]"):
            assert payload_id_list(empty, "tags") == []

    def test_a_scalar_that_is_not_a_string_is_a_400(self):
        with pytest.raises(ValidationError):
            payload_id_list({"id": GOOD}, "tags")


class TestQueryDictHelpers:
    def test_uuid_param_reads_a_single_value(self):
        params = QueryDict(f"account={GOOD}")
        assert uuid_param(params, "account") == GOOD

    def test_uuid_param_is_none_when_absent_or_blank(self):
        assert uuid_param(QueryDict(""), "account") is None
        assert uuid_param(QueryDict("account="), "account") is None

    def test_uuid_param_rejects_a_malformed_value(self):
        with pytest.raises(ValidationError):
            uuid_param(QueryDict("account=notauuid"), "account")

    def test_uuid_list_param_reads_every_repeat(self):
        params = QueryDict(f"tags={GOOD}&tags={OTHER}")
        assert uuid_list_param(params, "tags") == [GOOD, OTHER]

    def test_uuid_list_param_is_empty_when_absent(self):
        assert uuid_list_param(QueryDict(""), "tags") == []

    def test_uuid_list_param_rejects_a_malformed_repeat(self):
        params = QueryDict(f"tags={GOOD}&tags=notauuid")
        with pytest.raises(ValidationError):
            uuid_list_param(params, "tags")

    def test_uuid_list_param_accepts_a_plain_dict(self):
        """Some callers hold ``request.data``, which is a dict, not a QueryDict."""
        assert uuid_list_param({"tags": [GOOD]}, "tags") == [GOOD]
