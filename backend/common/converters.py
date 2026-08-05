"""A URL path converter for id segments, so a malformed id 404s at the router.

Every model here has a UUID primary key, but the routes captured those ids with
``<str:pk>``. The string reached the view unexamined and went straight into an
``id`` lookup, where Django parses it while *building* the query and raises
``django.core.exceptions.ValidationError``. DRF's exception handler does not
translate that class, so the request answered 500. A stale bookmark, a
hand-edited URL, or a crawler hitting ``/api/leads/undefined/`` took the
endpoint down, and it did so on 114 route/method combinations across roughly 50
views: every detail, move, comment, attachment, watch, merge and approval route
in the product.

Fixing it per view means auditing 50 view bodies and remembering the guard in
every future one. Fixing it at the router is one line per route and cannot be
forgotten, because a view can no longer be reached with an unparseable id.

Django ships a ``uuid`` converter already, and it is deliberately not used here:
its regex accepts only the canonical lowercase hyphenated form, while the ORM
accepts bare hex, braced and URN forms and any case. Swapping in ``<uuid:pk>``
would turn requests that work today into 404s. ``uuid.UUID`` is what
``UUIDField.to_python`` itself calls, so parsing with it accepts exactly what
the ORM accepts and nothing that used to work can break. ``common.validators``
made the same choice for query parameters and says so for the same reason.

Raising ``ValueError`` from ``to_python`` is the documented way to tell the
resolver "this pattern does not match": resolution continues to the next
pattern and ends in a normal 404, rather than the pattern matching and the view
failing later.
"""

import uuid as uuid_module


class UUIDLikeConverter:
    """Match a path segment that ``uuid.UUID`` can parse, in any of its forms."""

    regex = "[^/]+"

    def to_python(self, value):
        try:
            return str(uuid_module.UUID(value))
        except (AttributeError, TypeError, ValueError):
            raise ValueError(f"{value!r} is not a usable id.") from None

    def to_url(self, value):
        return str(value)
