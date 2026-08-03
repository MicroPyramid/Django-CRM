# Permissions and roles

Authentication (covered in [Authentication](authentication.md)) establishes who is making a
request. This page is about the separate question every view still has to answer for itself: given
that identity, is this specific action on this specific object allowed? DRF's permission classes
answer the first, coarse half of that; object-level checks inside the view answer the rest.

## Roles

`Profile.role` (`backend/common/models.py`) is a two-value `CharField`:
`common.utils.ROLES = (("ADMIN", "ADMIN"), ("USER", "USER"))`, defaulting to `USER`. That's the
role a person holds *within one org*: a user with profiles in two orgs can be `ADMIN` in one and
`USER` in the other, because a role lives on the `Profile` (the user-org membership row), not on
`User` itself.

A second, independent flag exists alongside it: `Profile.is_organization_admin`, a plain boolean,
exposed as the `.is_admin` property. It is genuinely a separate field from `role`, nothing
enforces that the two agree, and a fair amount of permission-checking code treats either one as
sufficient for "this person is an admin":

```python
# common/permissions.py. IsOrgAdmin
return request.profile.role == "ADMIN" or request.profile.is_organization_admin
```

```python
# cases/access.py
def is_org_admin(profile):
    """True for the two ways this codebase spells "admin"."""
    return profile.role == "ADMIN" or bool(getattr(profile, "is_admin", False))
```

When you write a new admin check, check both, the way these two do, a check that only tests
`role == "ADMIN"` will silently deny someone whose admin status was granted only through
`is_organization_admin`, and vice versa.

Separately from any org role, `IsSuperAdmin` (`backend/common/permissions.py`) gates
platform-level access on `User.is_superuser`. An explicit flag set with `manage.py
createsuperuser`, the Django admin, or another audited path, never inferred from an email address
or domain. The class's own docstring explains why that matters: deriving super-admin status from
an email domain would hand platform-wide access (every org, every user) to anyone who can obtain
an account at that domain, turning an ordinary signup into vertical privilege escalation. This flag
is unrelated to any `Profile.role`; a `User` can be `is_superuser` with no org membership at all.

## Permission classes

`backend/common/permissions.py` defines the building blocks every view composes:

- **`HasOrgContext`**: requires `request.profile` and `request.org` to both be set (by the
  middleware described in [Overview](overview.md#request-lifecycle)) and `request.profile.is_active`
  to be true. This is the check that turns "the JWT didn't carry a valid org claim" into a clean
  403 with the message "Organization context is required. Please login again." at the view layer,
  mirroring what `RequireOrgContext` already enforces at the middleware layer.
- **`IsOrgAdmin`**: `role == "ADMIN"` or `is_organization_admin`, as shown above.
- **`IsSuperAdmin`**: `user.is_superuser`, as shown above.

The standard combination on nearly every org-scoped view in this codebase is

```python
permission_classes = (IsAuthenticated, HasOrgContext)
```

For example `CaseListView`, `CaseAttachmentView`, and `CaseCommentView` in
`backend/cases/views.py`, or `TagsListView` in `backend/common/views/tags_views.py`. Notice what
that combination does *not* do: it doesn't check role, and it doesn't check which specific object
the request is about. `IsAuthenticated` + `HasOrgContext` gets you "a real, active member of this
org is making this request" and nothing more specific than that. Role checks
(`request.profile.role == "ADMIN"`) and object-level checks are layered on inside the view methods
themselves: DRF's declarative `permission_classes` list doesn't see the object being acted on
until the view has already fetched it, so per-object authorization has to live in code, which is
what the next section covers.

## Object-level checks

`backend/cases/access.py` is the clearest example in the codebase of object-level authorization
done deliberately, in one place, rather than re-implemented per view. Its own module docstring
explains the problem it fixes: before this module existed, "who may read/write/delete a case" was
answered independently in five different call sites, and had drifted into three different answers
by accident. A watcher could see their case in the list but got a 403 opening it, because the list
view's queryset included watchers and the detail view's permission check didn't. That's the
consequence of not centralizing this kind of check: verbs disagree with each other silently, and
the person who notices is a user hitting a wall the product didn't intend.

The module now states three explicit, different rules and enforces them from one place:

```python
def is_org_admin(profile):
    return profile.role == "ADMIN" or bool(getattr(profile, "is_admin", False))

def has_case_write_access(profile, case):
    if is_org_admin(profile):
        return True
    if profile.user_id == case.created_by_id:
        return True
    return profile.id in {p.id for p in case.assigned_to.all()}

def assert_case_delete_access(profile, case):
    """Narrower than writing on purpose: an assignee is somebody the work was
    handed to, which is a reason to let them work the ticket and not a reason
    to let them erase it."""
    if is_org_admin(profile):
        return
    if profile.user_id == case.created_by_id:
        return
    raise PermissionDenied(_DENIED)
```

Two things worth noticing in `has_case_write_access`: the comparison is `profile.user_id ==
case.created_by_id`, a `User` id compared to a `User` id, not `profile == case.created_by`.
`Case.created_by` (from `common/mixins.py`'s `AuditModel`, which nearly every model inherits
transitively through `BaseModel`. See [Data model](data-model.md#conventions) for the few
exceptions) is a foreign key to `User`, not to `Profile`. Comparing a `Profile` instance directly to
a `User` foreign key is always `False`. A comparison that type-checks in Python but can never be
true, which quietly turns an intended "creator or admin" check into an "admin only" check with no
error anywhere.

`backend/cases/views.py`'s own `CaseAttachmentView.delete` docstring documents two separate defects
having been live in that endpoint before the fix. An unscoped `objects.get(pk=pk)` lookup (no org
filter at all), and this same `created_by` type mismatch, and its closing line says only that "the
same one-line **lookup** bug is still open in `leads`, `tasks` and `opportunity`." That sentence is
about the missing-org-filter defect specifically, not the `created_by` comparison, and, checked
against the current source of all three apps rather than taken on the docstring's word. It's now
stale for one of the three:

- **`leads`** (`leads/views/lead_interactions.py`). The unscoped lookup is still open (`.objects
  .get(pk=pk)` at line 204, no `org=`). The `created_by` comparison here is correct, though:
  `request.profile.user == self.object.created_by` (line 208) compares a `User` to a `User`, not a
  `Profile` to a `User`, so this endpoint's `created_by` check works.
- **`tasks`** (`tasks/views/task_views.py`). Both defects are fixed: the lookup is
  org-filtered (`.filter(pk=pk, org=request.profile.org)`, lines 975-977) and the comparison is
  `request.profile.user_id == self.object.created_by_id` (line 987), with a comment at lines 982-984
  explaining why. The cases docstring's claim that the lookup bug is "still open" in `tasks` is
  stale.
- **`opportunity`** (`opportunity/views/opportunity_interactions.py` and `kanban_views.py`). Both
  defects are open, and the type mismatch exists at two separate call sites: `request.profile ==
  self.object.created_by` in the attachment delete (`opportunity_interactions.py:158` for the
  unscoped lookup, `:162` for the comparison) and again as `is_owner = request.profile ==
  opportunity.created_by` in the Kanban move endpoint (`kanban_views.py:162`).

So as of this writing: the `created_by` type-mismatch bug itself is open in `opportunity` only (two
call sites); the separate unscoped-lookup bug is open in `leads` and `opportunity`. Neither defect
is something this documentation task fixes. It's flagged here, precisely, because a docstring that
lists which apps still have a bug goes stale exactly like any other comment does, and the fix in
this case is checking the current source yourself, the way this paragraph did, rather than trusting
either the docstring or a prior summary of it. When you write a `created_by` comparison, compare
`profile.user_id` to `obj.created_by_id`, and write a test that proves the check can return both
`True` and `False`.

## Read wide, write narrow

A pattern recurs across this codebase enough to name: for a given kind of resource, who may *read*
it is broader than who may *change* it, which in turn is broader than who may *destroy* it. Two
concrete shapes of it:

**Per-object access**, as in `cases/access.py` above:

```
read    admin · creator · assignee · watcher
write   admin · creator · assignee
delete  admin · creator
```

Watching a case is subscribing to updates, not being handed the keys to it, so the watcher clause
that widens *read* access is deliberately not carried into *write* or *delete*. Each verb states its
own rule; none is inferred from another.

**Shared, org-wide configuration** (tags, vertical packs, and similar org-level settings) follows
a simpler but equally deliberate version of the same shape: any active member of the org may read
it, only an admin may change it. `TagsListView` (`backend/common/views/tags_views.py`) is a clean
example: `get` has no additional check beyond the standard `(IsAuthenticated, HasOrgContext)`, but
`post` gates explicitly:

```python
def post(self, request, *args, **kwargs):
    """Create a new tag (admin only)."""
    if request.profile.role != "ADMIN" and not request.user.is_superuser:
        return Response(
            {"error": True, "errors": "Only admins can create tags"},
            status=status.HTTP_403_FORBIDDEN,
        )
```

`common/views/pack_views.py` states the same shape as a doc comment before a single line of code:
"any authenticated member may list packs; only an org ADMIN may apply one or clear sample data."
When you're adding a new endpoint over something that's genuinely shared, org-wide configuration
rather than a record with a specific owner, this is the default to reach for: don't gate the read
at all beyond org membership, and gate every write and destroy behind an explicit admin check in
the view, not a `permission_classes` entry that would also block the read.
