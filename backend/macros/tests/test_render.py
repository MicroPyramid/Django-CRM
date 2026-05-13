"""Render-helper tests. Pure function — no API/RLS surface here."""

from types import SimpleNamespace

from macros.render import find_unknown_placeholders, render_macro


def _macro(body: str):
    return SimpleNamespace(body=body)


class TestFindUnknownPlaceholders:
    def test_empty_body_returns_empty_list(self):
        assert find_unknown_placeholders("") == []
        assert find_unknown_placeholders(None) == []

    def test_no_placeholders_returns_empty_list(self):
        assert find_unknown_placeholders("Plain text, no tokens.") == []

    def test_only_supported_returns_empty_list(self):
        body = "Hi %customer_name%, I'm %agent_name% from %org_name%."
        assert find_unknown_placeholders(body) == []

    def test_typo_is_flagged(self):
        # The bug we're guarding against: missing 'o' in 'customer'.
        body = "Hi %custmer_name%, how can we help?"
        assert find_unknown_placeholders(body) == ["%custmer_name%"]

    def test_mixed_known_and_unknown(self):
        body = "Hi %customer_name%, your priority %priority% case %case_id%."
        assert find_unknown_placeholders(body) == ["%priority%"]

    def test_dedupes_repeated_unknown(self):
        body = "%foo% then %foo% again"
        assert find_unknown_placeholders(body) == ["%foo%"]

    def test_preserves_first_seen_order(self):
        body = "%bar% comes after %foo%, then %baz%."
        assert find_unknown_placeholders(body) == ["%bar%", "%foo%", "%baz%"]


class TestRenderPlaceholders:
    def test_empty_body(self):
        assert render_macro(_macro(""), case=None, profile=None) == ""

    def test_no_placeholders_pass_through(self):
        assert render_macro(_macro("Hello world"), case=None, profile=None) == (
            "Hello world"
        )

    def test_unknown_token_is_left_literal(self):
        # `%priority%` is not in SUPPORTED_TOKENS — must survive verbatim.
        out = render_macro(_macro("priority=%priority%"), case=None, profile=None)
        assert out == "priority=%priority%"

    def test_customer_name_from_first_contact(
        self, case_factory, contact_factory, user_profile
    ):
        contact = contact_factory(first_name="Mira", last_name="Singh")
        case = case_factory(name="Login broken", contact=contact)
        out = render_macro(
            _macro("Hi %customer_name%!"),
            case=case,
            profile=user_profile,
        )
        assert out == "Hi Mira Singh!"

    def test_customer_email_falls_back_to_email_when_names_missing(
        self, case_factory, contact_factory, user_profile
    ):
        contact = contact_factory(first_name="", last_name="", email="x@y.com")
        case = case_factory(contact=contact)
        out = render_macro(_macro("%customer_name%"), case=case, profile=user_profile)
        assert out == "x@y.com"

    def test_customer_name_empty_when_no_contact(self, case_factory, user_profile):
        case = case_factory(name="No contact case")
        out = render_macro(_macro("Hi %customer_name%."), case=case, profile=user_profile)
        assert out == "Hi ."

    def test_case_id_and_subject(self, case_factory, user_profile):
        case = case_factory(name="Reset password")
        out = render_macro(
            _macro("Case %case_id% (%case_subject%)"),
            case=case,
            profile=user_profile,
        )
        assert str(case.id) in out
        assert "Reset password" in out

    def test_agent_name_and_email(self, case_factory, user_profile):
        # The User model only has `email` — agent_name falls back to the
        # local-part of the email so signatures stay readable.
        case = case_factory()
        out = render_macro(
            _macro("Best, %agent_name% (%agent_email%)"),
            case=case,
            profile=user_profile,
        )
        assert out == "Best, user (user@test.com)"

    def test_org_name(self, case_factory, user_profile):
        case = case_factory()
        out = render_macro(
            _macro("from %org_name%"),
            case=case,
            profile=user_profile,
        )
        assert out == "from Test Organization A"

    def test_multiple_placeholders_in_one_string(
        self, case_factory, contact_factory, user_profile
    ):
        contact = contact_factory(first_name="Lou", last_name="Reed")
        case = case_factory(contact=contact, name="Subject A")
        out = render_macro(
            _macro("Hi %customer_name% on %case_subject%"),
            case=case,
            profile=user_profile,
        )
        assert out == "Hi Lou Reed on Subject A"

    def test_unknown_mixed_with_known(
        self, case_factory, contact_factory, user_profile
    ):
        contact = contact_factory(first_name="A", last_name="B")
        case = case_factory(contact=contact)
        out = render_macro(
            _macro("%customer_name% / %not_a_token% / %org_name%"),
            case=case,
            profile=user_profile,
        )
        assert out == "A B / %not_a_token% / Test Organization A"

    def test_none_macro_returns_empty(self):
        assert render_macro(None, case=None, profile=None) == ""
