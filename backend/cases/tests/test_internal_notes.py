"""
Tests for the Tier-1 internal-notes feature: Comment.is_internal split,
permission rule, and audit-log on visibility flips.

See docs/cases/tier1/internal-notes.md.
"""

from __future__ import annotations

import pytest
from django.contrib.contenttypes.models import ContentType

from common.models import Activity, Comment


def _make_comment(case, profile, *, text="hi", is_internal=False):
    return Comment.objects.create(
        comment=text,
        content_type=ContentType.objects.get_for_model(case),
        object_id=case.pk,
        commented_by=profile,
        is_internal=is_internal,
        org=case.org,
    )


@pytest.mark.django_db
class TestCommentSplitResponse:
    def test_get_splits_public_and_internal(
        self, admin_client, case_a, admin_profile
    ):
        _make_comment(case_a, admin_profile, text="public reply", is_internal=False)
        _make_comment(case_a, admin_profile, text="agent only", is_internal=True)

        response = admin_client.get(f"/api/cases/{case_a.pk}/")
        assert response.status_code == 200
        body = response.json()
        assert "comments" in body and "internal_notes" in body
        assert {c["comment"] for c in body["comments"]} == {"public reply"}
        assert {c["comment"] for c in body["internal_notes"]} == {"agent only"}
        # Each comment payload exposes is_internal so the frontend can render
        # mixed lists if needed.
        assert all(c["is_internal"] is False for c in body["comments"])
        assert all(c["is_internal"] is True for c in body["internal_notes"])


@pytest.mark.django_db
class TestPostInternalComment:
    def test_admin_can_post_internal_note(self, admin_client, case_a):
        response = admin_client.post(
            f"/api/cases/{case_a.pk}/",
            {"comment": "engineering ack pending", "is_internal": True},
            format="json",
        )
        assert response.status_code == 200, response.content
        body = response.json()
        # Returns split arrays; the new note shows up under internal_notes.
        assert any(
            c["comment"] == "engineering ack pending" and c["is_internal"] is True
            for c in body["internal_notes"]
        )
        # And it's not in the public bucket.
        assert not any(
            c["comment"] == "engineering ack pending" for c in body["comments"]
        )

    def test_default_is_public_when_not_provided(self, admin_client, case_a):
        response = admin_client.post(
            f"/api/cases/{case_a.pk}/",
            {"comment": "default comment"},
            format="json",
        )
        assert response.status_code == 200, response.content
        body = response.json()
        assert any(
            c["comment"] == "default comment" and c["is_internal"] is False
            for c in body["comments"]
        )

    def test_is_internal_string_truthy_coerced(self, admin_client, case_a):
        # The comment-attachment endpoint accepts multipart for file uploads,
        # so flags arrive as strings. Make sure "true" is coerced to bool True.
        response = admin_client.post(
            f"/api/cases/{case_a.pk}/",
            {"comment": "string-truthy", "is_internal": "true"},
            format="multipart",
        )
        assert response.status_code == 200, response.content
        body = response.json()
        assert any(
            c["comment"] == "string-truthy" and c["is_internal"] is True
            for c in body["internal_notes"]
        )


@pytest.mark.django_db
class TestCrossOrgIsolation:
    def test_other_org_cannot_see_internal_notes(
        self, org_b_client, case_a, admin_profile
    ):
        _make_comment(case_a, admin_profile, text="leak?", is_internal=True)
        # Org B should not be able to fetch this case at all.
        response = org_b_client.get(f"/api/cases/{case_a.pk}/")
        assert response.status_code in (403, 404)


@pytest.mark.django_db
class TestVisibilityFlipAuditLogged:
    def test_flip_public_to_internal_emits_comment_activity(
        self, admin_client, case_a, admin_profile
    ):
        comment = _make_comment(
            case_a, admin_profile, text="leaked?", is_internal=False
        )
        # Baseline: one COMMENT activity row for creation.
        baseline_count = Activity.objects.filter(
            entity_type="Case", entity_id=case_a.pk, action="COMMENT"
        ).count()

        response = admin_client.patch(
            f"/api/cases/comment/{comment.pk}/",
            {"is_internal": True},
            format="json",
        )
        assert response.status_code == 200, response.content

        flip_rows = list(
            Activity.objects.filter(
                entity_type="Case",
                entity_id=case_a.pk,
                action="COMMENT",
            )
            .order_by("created_at")
        )
        assert len(flip_rows) == baseline_count + 1
        latest = flip_rows[-1]
        meta = latest.metadata
        assert meta.get("visibility_changed") is True
        assert meta.get("before") is False
        assert meta.get("after") is True
        assert meta.get("comment_id") == str(comment.pk)

    def test_flip_internal_to_public_emits_comment_activity(
        self, admin_client, case_a, admin_profile
    ):
        comment = _make_comment(
            case_a, admin_profile, text="oops private", is_internal=True
        )
        response = admin_client.patch(
            f"/api/cases/comment/{comment.pk}/",
            {"is_internal": False},
            format="json",
        )
        assert response.status_code == 200, response.content

        latest = (
            Activity.objects.filter(
                entity_type="Case",
                entity_id=case_a.pk,
                action="COMMENT",
            )
            .order_by("-created_at")
            .first()
        )
        assert latest is not None
        meta = latest.metadata
        assert meta.get("visibility_changed") is True
        assert meta.get("before") is True
        assert meta.get("after") is False

    def test_text_only_edit_does_not_emit_flip(
        self, admin_client, case_a, admin_profile
    ):
        comment = _make_comment(
            case_a, admin_profile, text="original", is_internal=False
        )
        baseline_count = Activity.objects.filter(
            entity_type="Case", entity_id=case_a.pk, action="COMMENT"
        ).count()

        response = admin_client.patch(
            f"/api/cases/comment/{comment.pk}/",
            {"comment": "edited text"},
            format="json",
        )
        assert response.status_code == 200, response.content
        # No new activity row.
        assert (
            Activity.objects.filter(
                entity_type="Case", entity_id=case_a.pk, action="COMMENT"
            ).count()
            == baseline_count
        )
