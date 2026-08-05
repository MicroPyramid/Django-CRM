"""Tenant-scoped object lookup that answers 404 instead of 500.

The `get_object(self, pk)` helper on a detail view is written the same way in a
dozen places:

    return self.model.objects.get(pk=pk, org=self.request.profile.org)

which fails two ways a caller can trigger without doing anything wrong.

* A record that has been deleted, or belongs to another tenant, raises
  ``DoesNotExist``. Nothing catches it, so it leaves the view as a 500.
* ``id`` is a UUID column, so an id that is not a well-formed UUID raises
  ``django.core.exceptions.ValidationError`` (or ``ValueError``) while the query
  is being built, before any row is looked at. DRF's exception handler does not
  translate that class either, so it is a 500 too. A stale bookmark or a
  hand-edited URL takes the endpoint down.

Both are the same answer: the caller asked for something that is not there, and
that is a 404. Returning 404 rather than 403 for a record in another tenant is
also the right disclosure: a 403 would confirm the id exists somewhere.

This mirrors ``cases.access.get_case_or_404``, which solved it for one model. It
is generic so the next detail view can use it without a fourteenth copy.
"""

from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404


def get_scoped_or_404(model, pk, org, **extra):
    """Return the ``model`` row with this pk inside ``org``, or raise ``Http404``.

    ``extra`` adds further filters (``profile=``, ``is_active=True``) for views
    whose scope is narrower than the org.
    """
    try:
        obj = model.objects.filter(pk=pk, org=org, **extra).first()
    except (DjangoValidationError, ValueError, TypeError):
        raise Http404(f"No such {model._meta.verbose_name}.") from None
    if obj is None:
        raise Http404(f"No such {model._meta.verbose_name}.")
    return obj
