"""Where an org came from: what POST /api/org/ stores in `Org.signup_source`."""

import pytest
from rest_framework import status

from common.models import Org
from common.signup_source import MAX_TAG_LENGTH, clean_signup_source

URL = "/api/org/"


class TestClean:
    def test_keeps_tags_and_a_host(self):
        raw = {
            "utm_source": "newsletter",
            "utm_medium": "email",
            "utm_campaign": "october",
            "referrer": "news.example.com",
        }
        assert clean_signup_source(raw, "axios/1.20.0") == {"client": "web", **raw}

    def test_the_phone_app_is_recognised_by_its_user_agent(self):
        assert clean_signup_source({}, "Dart/3.12 (dart:io)") == {"client": "phone"}

    def test_a_missing_user_agent_is_web(self):
        assert clean_signup_source(None, None) == {"client": "web"}

    @pytest.mark.parametrize("raw", [None, "utm_source=x", ["x"], 42])
    def test_anything_but_a_dict_records_only_the_client(self, raw):
        assert clean_signup_source(raw, "") == {"client": "web"}

    def test_unknown_keys_are_dropped(self):
        source = clean_signup_source(
            {"utm_source": "x", "email": "a@b.com", "org": "1"}, ""
        )
        assert source == {"client": "web", "utm_source": "x"}

    @pytest.mark.parametrize("value", [None, 7, ["x"], {"a": 1}, "   ", "\x00\x01"])
    def test_a_tag_that_is_not_text_or_is_blank_is_dropped(self, value):
        assert "utm_source" not in clean_signup_source({"utm_source": value}, "")

    def test_a_long_tag_is_cut_and_control_characters_removed(self):
        source = clean_signup_source({"utm_campaign": "a\nb" + "c" * 500}, "")
        assert source["utm_campaign"].startswith("abc")
        assert len(source["utm_campaign"]) == MAX_TAG_LENGTH

    @pytest.mark.parametrize(
        "referrer",
        [
            "https://news.example.com/",
            "news.example.com/path?token=secret",
            "user@news.example.com",
            "-bad.example.com",
            "a" * 254,
            "",
            7,
        ],
    )
    def test_a_referrer_that_is_not_a_bare_host_is_dropped(self, referrer):
        # A full URL can carry a path, a query or a token, so only a host name
        # is ever stored.
        assert "referrer" not in clean_signup_source({"referrer": referrer}, "")

    def test_a_host_is_stored_lower_case(self):
        assert clean_signup_source({"referrer": " News.Example.COM "}, "")[
            "referrer"
        ] == ("news.example.com")


@pytest.mark.django_db
class TestCreate:
    def test_the_source_is_stored_on_the_new_org(self, admin_client):
        response = admin_client.post(
            URL,
            {
                "name": "Sourced Org",
                "signup_source": {"utm_source": "site", "referrer": "example.org"},
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        org = Org.objects.get(name="Sourced Org")
        assert org.signup_source == {
            "client": "web",
            "utm_source": "site",
            "referrer": "example.org",
        }
        # Analytics only: the response does not echo it.
        assert "signup_source" not in response.data["org"]

    def test_an_org_created_without_one_still_records_the_client(self, admin_client):
        response = admin_client.post(
            URL,
            {"name": "Plain Org"},
            format="json",
            HTTP_USER_AGENT="Dart/3.12 (dart:io)",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert Org.objects.get(name="Plain Org").signup_source == {"client": "phone"}

    def test_a_malformed_source_never_blocks_the_create(self, admin_client):
        response = admin_client.post(
            URL,
            {
                "name": "Junk Org",
                "signup_source": {"referrer": "https://x.example/?t=1", "x": 1},
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert Org.objects.get(name="Junk Org").signup_source == {"client": "web"}

    def test_a_refused_create_stores_nothing(self, admin_client):
        before = Org.objects.count()
        response = admin_client.post(
            URL,
            {"name": "Bad & Name", "signup_source": {"utm_source": "x"}},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert Org.objects.count() == before
