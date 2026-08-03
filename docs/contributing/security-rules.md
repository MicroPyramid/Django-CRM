# Security rules

BottleCRM is a multi-tenant application where every org's data sits in the same database, the same
tables, next to every other org's. The rules on this page exist because the two ways that goes wrong,
one tenant reading or writing another tenant's data, and a non-admin reaching admin- or
platform-level actions, are the two outcomes every change touching auth, permissions, or
serializers has to rule out before it merges.

## The trust boundary

The backend (`backend/`) is the only trust boundary in this system.
[Architecture overview](../architecture/overview.md#the-three-clients) describes why that has to be
true structurally, not just as policy: a SvelteKit web app, a Flutter mobile app, and any
third-party integration all talk to the *same* Django REST Framework API over the same JSON
endpoints. There is no separate, more-trusted internal API. A rule enforced only in the SvelteKit
UI (disabling a button, hiding a form field, client-side validation) protects none of the three
clients, because a browser DevTools console, a modified mobile build, or a plain `curl` request
reaches the same endpoint directly, skipping whatever the UI would have prevented. Every constraint
that matters has to be enforced in the DRF view or serializer, full stop.

## Identity is server-derived

Who is making a request, which org they're acting in, and what role they hold are facts the server
establishes and re-validates on every request, never values read from the request body, a query
string, or a custom header. [Authentication](../architecture/authentication.md#claims) shows the
concrete mechanism: the `org_id` claim inside a caller's signed JWT is not simply trusted, the
middleware that resolves it re-checks it against an active `Profile` row on every single request:

```python
profile = Profile.objects.select_related("org").get(
    user_id=user_id, org_id=org_id, is_active=True
)
```

If that lookup fails (the membership was revoked, the profile was deactivated) the request gets a
403 asking the caller to sign in again, rather than proceeding on a claim that's gone stale. The
practical rule for any view or serializer you write: identity comes from `request.user` and
`request.profile`, both set by middleware before your code runs (see
[Overview](../architecture/overview.md#request-lifecycle)), never from a field the client sent.
`role`, in particular, is a display convenience when it appears in a JWT payload; every real
permission check reads `request.profile.role` fresh from the database, not from the token.

## Tenant scoping

Pair every permission check with an explicit org filter. The two are independent controls, and
neither substitutes for the other. `HasOrgContext` (`backend/common/permissions.py`) is the standard
permission class on nearly every org-scoped view:

```python
class HasOrgContext(permissions.BasePermission):
    def has_permission(self, request, view):
        if not hasattr(request, "profile") or request.profile is None:
            return False
        if not hasattr(request, "org") or request.org is None:
            return False
        if not request.profile.is_active:
            return False
        return True
```

That establishes "a real, active member of this org is making this request". It does not filter
which rows the view returns. Every queryset still has to add
`Model.objects.filter(org=request.profile.org)` itself, and every `create()` / `serializer.save()`
still has to pass `org=request.profile.org` explicitly, never accept it from the request body. RLS
(PostgreSQL Row-Level Security) backs this up at the database layer, but it's a safety net for when
the filter is missing, not a substitute for writing it. See
[The two-layer contract](../architecture/multi-tenancy-and-rls.md#the-two-layer-contract) for why
both layers are required, and [Adding an org-scoped model](adding-an-org-scoped-model.md) for the
full checklist when the view is for a brand-new model.

## Server-owned fields

Any field the server is supposed to derive: `org`, `created_by`, `profile`, a publish/visibility
flag, must never be settable from `request.data`. There are two real mechanisms in this codebase
for that, not one:

**Declare the field `read_only=True` or list it in `read_only_fields`.** `TeamCreateSerializer` in
`backend/common/serializer.py` declares `read_only_fields = ("created_at", "created_by", "org")`;
`leads/serializer.py` sets `read_only_fields = ("id", "created_at", "updated_at", "org")` on
`LeadStageSerializer` and `LeadPipelineSerializer`; and `TimeEntrySerializer`
(`backend/cases/serializer.py`) declares the field itself read-only; `profile =
ProfileSerializer(read_only=True)`: for exactly the reason this section opens with: `profile` is
who logged the time entry, and it has to be a fact the server sets, not one a client requests.

**Or don't accept it through the serializer at all, and set it explicitly at the call site.**
`TimeEntryCreateSerializer`'s own docstring states this directly: "`case`, `profile`, and `org` are
injected by the view and not accepted from the client", and indeed none of the three appear in its
`Meta.fields`. The view (`backend/cases/time_views.py`) backs that up:

```python
entry = TimeEntry.objects.create(
    org=request.profile.org,
    case=case,
    profile=request.profile,
    **serializer.validated_data,
)
```

`serializer.validated_data` can only ever contain the fields the serializer declared in the first
place, so there's nothing for a client to override here even by guessing field names, the
equivalent of popping a key out of `request.data` before `save()`, but enforced by what the
serializer's `fields` tuple omits rather than by a runtime pop.

The sharpest example of *why* this matters is `is_sample`, a flag shared, via one imported
`SAMPLE_DATA_HELP_TEXT` constant, by six models: `Lead`, `Account`, `Contact`, `Case`, `Opportunity`,
and `Task` (`grep -rl SAMPLE_DATA_HELP_TEXT backend/` finds it in each app's `models.py`, plus
`common/base.py` where it's defined once). `leads/serializer.py` declares
`read_only_fields = ("is_sample",)`. The help text itself, defined once in `backend/common/base.py`
and shared by every model that has the field, states the reasoning as a security invariant rather
than documentation:

```python
SAMPLE_DATA_HELP_TEXT = (
    "True only for demo rows created by common.packs.applier._apply_sample_data. "
    "Server-set exclusively, never expose this as a writable field on any "
    "serializer. It is the sole key common.packs.applier.clear_sample_data uses "
    "to decide what to delete, so a client-writable path here would let a user "
    "mark an arbitrary real record as sample and have it deleted."
)
```

If a field like this were writable, a hostile request wouldn't need a bug in the delete logic at
all. It would just flip the flag on someone else's real record and let the legitimate "clear sample
data" action do the deleting. When you add a field the server is meant to own, ask what a client
could achieve by setting it directly, not just whether the happy path needs it to be read-only.

## Prove permission checks can fail

A permission check that always evaluates to the same answer isn't a check. It's dead code wearing
a check's shape, and this codebase has a well-documented history of exactly that happening by
accident. `Case.created_by` (like nearly every model's `created_by`) is a foreign key to `User`, not
to `Profile`. Comparing a `Profile` instance directly against it,

```python
request.profile == self.object.created_by  # always False: Profile compared to a User FK
```

Type-checks in Python and never raises, but is never `True`, which silently turned an intended
"creator or admin" check into "admin only" with no error anywhere. This isn't hypothetical in this
codebase: `git log -L` on `CaseAttachmentView.delete` in `backend/cases/views.py` shows a commit
(`c9250dd`) whose diff replaces exactly this,

```diff
-            request.profile.role == "ADMIN"
-            or request.profile.is_admin
-            or request.profile == self.object.created_by
+            is_org_admin(request.profile)
+            or request.profile.user_id == self.object.created_by_id
```

Confirming from the actual commit history, not from a comment describing it, that the
`Profile`-vs-`User` comparison was live code before it was replaced with the type-correct
`request.profile.user_id == self.object.created_by_id`.

[Permissions and roles](../architecture/permissions-and-roles.md#object-level-checks) documents this
pattern in depth, including which apps had it fixed and which, as of that page's own last check
against source, still don't; read it before writing a new `created_by` comparison, and compare
`profile.user_id` to `obj.created_by_id`, never `profile` to `obj.created_by` directly.

The only way to know a check can fail is to write a test that makes it fail. `leads/tests/
test_lead_access_and_totals.py` states the rule its own tests follow: "Every permission test asserts
both directions. A check that can only return False is indistinguishable from a check that is never
reached." In practice that means a pair of tests, not one, for example
`opportunity/tests/test_sales_goals.py`:

```python
def test_create_goal_admin(self, admin_client, org_a):
    ...
    response = admin_client.post(self.GOALS_URL, data, format="json")
    assert response.status_code == 201

def test_create_goal_non_admin_forbidden(self, user_client):
    ...
    response = user_client.post(self.GOALS_URL, data, format="json")
    assert response.status_code == 403
```

A single test asserting only the `403` case would pass identically whether the admin check works
correctly or whether it denies *everyone*, admin included, because of a mistake like the one above.
Only the paired `True` test catches that. See [Testing](testing.md) for the fast-iteration commands,
and [Adding an org-scoped model](adding-an-org-scoped-model.md#the-tests) for the same pairing
applied to tenant isolation specifically.
