"""Import endpoints are throttled per user, and Sentry never carries an upload."""

import copy

import pytest
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile

from common.public_tokens import scrub_public_tokens
from common.sentry_scrub import before_send, scrub_import_data
from common.throttles import ImportThrottle

CONTACT_PREVIEW = "/api/contacts/import/preview/"
LEAD_PREVIEW = "/api/leads/import/preview/"
CONTACT_COMMIT = "/api/contacts/import/commit/"
LEAD_COMMIT = "/api/leads/import/commit/"
TOKEN = "SECRETsecretSECRETsecret0123456789"


@pytest.fixture(autouse=True)
def _fresh_throttle():
    cache.clear()
    yield
    cache.clear()


def _file():
    return SimpleUploadedFile(
        "c.csv",
        b"first_name,last_name,email\nAl,Smith,al@example.com\n",
        content_type="text/csv",
    )


def _lead_file():
    return SimpleUploadedFile(
        "l.csv",
        b"title,first_name,last_name,email\nT,Al,Smith,al@example.com\n",
        content_type="text/csv",
    )


def _post(client, url):
    f = _lead_file() if "leads" in url else _file()
    return client.post(url, {"file": f}, format="multipart")


@pytest.fixture
def three_per_minute(monkeypatch):
    monkeypatch.setattr(ImportThrottle, "THROTTLE_RATES", {"csv_import": "3/minute"})


@pytest.mark.django_db
class TestImportThrottle:
    def test_import_throttle_refuses_over_rate(
        self, admin_client, admin_profile, three_per_minute
    ):
        codes = [_post(admin_client, CONTACT_PREVIEW).status_code for _ in range(4)]
        assert codes[:3] == [200, 200, 200]
        assert codes[3] == 429

    def test_throttle_is_per_user(
        self, admin_client, org_b_client, admin_profile, profile_b, three_per_minute
    ):
        for _ in range(4):
            _post(admin_client, CONTACT_PREVIEW)
        assert _post(admin_client, CONTACT_PREVIEW).status_code == 429
        assert _post(org_b_client, CONTACT_PREVIEW).status_code == 200

    @pytest.mark.parametrize(
        "url", [CONTACT_PREVIEW, LEAD_PREVIEW, CONTACT_COMMIT, LEAD_COMMIT]
    )
    def test_every_import_view_is_throttled(
        self, admin_client, admin_profile, three_per_minute, url
    ):
        codes = [_post(admin_client, url).status_code for _ in range(4)]
        assert 429 not in codes[:3]
        assert codes[3] == 429

    def test_mapped_mode_is_throttled_too(
        self, admin_client, admin_profile, three_per_minute
    ):
        def mapped():
            return admin_client.post(
                CONTACT_PREVIEW,
                {"file": _file(), "mapping": "{}"},
                format="multipart",
            )

        codes = [mapped().status_code for _ in range(4)]
        assert 429 not in codes[:3]
        assert codes[3] == 429

    def test_throttle_is_shared_across_the_four_views(
        self, admin_client, admin_profile, three_per_minute
    ):
        for url in (CONTACT_PREVIEW, LEAD_PREVIEW, CONTACT_COMMIT):
            _post(admin_client, url)
        assert _post(admin_client, LEAD_COMMIT).status_code == 429


def _event(path="/api/contacts/import/commit/"):
    return {
        "request": {
            "url": f"https://api.x{path}",
            "data": {"file": "name,email\nAl,al@example.com"},
            "method": "POST",
        },
        "exception": {
            "values": [
                {
                    "stacktrace": {
                        "frames": [
                            {
                                "module": "contacts.services.csv_import",
                                "vars": {"row": "al@example.com"},
                            },
                            {
                                "module": "django.core.handlers.base",
                                "vars": {"request": "<WSGIRequest>"},
                            },
                        ]
                    }
                }
            ]
        },
        "threads": {
            "values": [
                {
                    "stacktrace": {
                        "frames": [
                            {"module": "common.spreadsheet", "vars": {"x": "secret"}},
                            {"module": "django.db", "vars": {"y": 1}},
                        ]
                    }
                }
            ]
        },
    }


class TestSentryScrub:
    def test_scrub_drops_request_body_and_frame_vars(self):
        out = scrub_import_data(_event())
        assert "data" not in out["request"]
        frames = out["exception"]["values"][0]["stacktrace"]["frames"]
        assert "vars" not in frames[0]
        # On an import URL every frame loses its vars, Django's included.
        assert "vars" not in frames[1]
        tframes = out["threads"]["values"][0]["stacktrace"]["frames"]
        assert "vars" not in tframes[0]
        assert "vars" not in tframes[1]

    def test_module_scrub_applies_off_the_import_path(self):
        event = _event("/api/contacts/")
        out = scrub_import_data(event)
        frames = out["exception"]["values"][0]["stacktrace"]["frames"]
        assert "vars" not in frames[0]
        assert frames[1]["vars"] == {"request": "<WSGIRequest>"}
        assert "data" in out["request"]
        tframes = out["threads"]["values"][0]["stacktrace"]["frames"]
        assert "vars" not in tframes[0]
        assert tframes[1]["vars"] == {"y": 1}

    def test_scrub_drops_all_frame_vars_on_import_path(self):
        event = _event()
        event["exception"]["values"][0]["stacktrace"]["frames"] = [
            {"module": "csv", "vars": {"row": "al@example.com"}},
            {"module": "openpyxl.reader.excel", "vars": {"cell": "secret"}},
        ]
        out = scrub_import_data(event)
        for frame in out["exception"]["values"][0]["stacktrace"]["frames"]:
            assert "vars" not in frame

    def test_scrub_clears_breadcrumbs_and_extra_on_import_path(self):
        event = _event()
        event["breadcrumbs"] = {"values": [{"message": "al@example.com"}]}
        event["extra"] = {"row": "al@example.com"}
        out = scrub_import_data(event)
        assert not out.get("breadcrumbs")
        assert not out.get("extra")

    def test_query_string_does_not_trigger_the_path_match(self):
        event = _event("/api/contacts/")
        event["request"]["url"] += "?next=/api/contacts/import/"
        event["extra"] = {"k": "v"}
        out = scrub_import_data(event)
        assert out["extra"] == {"k": "v"}
        assert "data" in out["request"]

    def test_scrub_covers_lead_url_and_prefix_only_modules(self):
        event = _event("/api/leads/import/preview/")
        event["exception"]["values"][0]["stacktrace"]["frames"][0]["module"] = (
            "leads.views.import_views"
        )
        out = scrub_import_data(event)
        assert "data" not in out["request"]
        assert "vars" not in out["exception"]["values"][0]["stacktrace"]["frames"][0]

    def test_scrub_leaves_other_requests(self):
        event = _event("/api/contacts/")
        event["exception"]["values"][0]["stacktrace"]["frames"][0]["module"] = (
            "contacts.views"
        )
        event["threads"]["values"][0]["stacktrace"]["frames"][0]["module"] = "tasks.x"
        event["breadcrumbs"] = {"values": [{"message": "m"}]}
        event["extra"] = {"k": "v"}
        before = copy.deepcopy(event)
        assert scrub_import_data(event) == before

    @pytest.mark.parametrize(
        "event",
        [
            {},
            {"request": None},
            {"request": {"url": None, "data": "x"}},
            {"request": "oops"},
            {"exception": None},
            {"exception": {"values": None}},
            {"exception": {"values": [None, "x", {"stacktrace": None}]}},
            {"exception": {"values": [{"stacktrace": {"frames": None}}]}},
            {"exception": {"values": [{"stacktrace": {"frames": [None, 3]}}]}},
            {"threads": [1, 2]},
            {"threads": {"values": [{"stacktrace": {"frames": [{"module": None}]}}]}},
        ],
    )
    def test_malformed_events_pass_through_unchanged(self, event):
        before = copy.deepcopy(event)
        assert scrub_import_data(event) == before

    def test_non_dict_event_is_returned(self):
        assert scrub_import_data(None) is None

    def test_before_send_still_scrubs_public_tokens(self):
        event = _event()
        event["request"]["url"] = f"https://api.x/api/public/invoice/{TOKEN}/"
        out = before_send(event, {})
        assert TOKEN not in str(out)
        assert out == scrub_import_data(scrub_public_tokens(event, {}))
