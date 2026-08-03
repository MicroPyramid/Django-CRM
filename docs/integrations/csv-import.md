# CSV import

## What can be imported

**There are two, unrelated ways to bulk-create records from a CSV, plus one gap.** Contacts and
cases (tickets) share a modern, two-phase preview/commit importer. Leads have a separate, older,
single-step bulk uploader that predates it and works nothing like it. Accounts have neither,
confirmed by grepping the denied concept, not just one filename, across the whole app:
`grep -rniE "\bupload\b|csv_import|import_views|ImportPreview|ImportCommit" --include="*.py"
backend/accounts/` (excluding migrations/tests) returns nothing. If you need to bulk-create
accounts, use `POST /api/accounts/` directly (see [Accounts](../api/accounts.md)), the
[Python](python-sample.md) / [JavaScript](javascript-sample.md) samples on this site call the
equivalent lead endpoint, but the same obtain-token/list/create pattern applies unchanged.

**The lead uploader:** `POST /api/leads/upload/` (`LeadUploadView`,
`backend/leads/views/lead_interactions.py`) takes `multipart/form-data` with the file under the
field name `leads_file`, not `file` like the importers below. It only requires a `title` column
(`LeadListForm`/`csv_doc_validate`, `backend/leads/forms.py`); every other column is optional and
free-form. The file is decoded as **`iso-8859-1`, not UTF-8**: unlike the contacts/cases
importers below, so a UTF-8 file with multi-byte characters (accented names, curly quotes) won't be
rejected, it will be silently mis-decoded. There's no preview step: a valid upload returns
`{"error": false, "message": "Leads created Successfully"}` immediately and hands the parsed rows
to a Celery task (`create_lead_from_file`, `backend/leads/tasks.py`) that creates the `Lead` rows
in the background: by the time you get the `200`, nothing has necessarily been written yet, and
there's no per-row error report or count. Rows with a blank `title` are dropped before the task
even runs, and the task itself additionally expects every row to have an `email` value it can
match against a basic format check; rows that fail that check are silently skipped, and a file
with no `email` column in it at all fails the whole background job outright, not just the rows
missing one, because the check isn't guarded. A file that has no `title` column, isn't valid CSV,
or where every row is invalid is rejected synchronously with `{"error": true, "errors": {...}}`.

**Permission gating is not the same across the three surfaces, and this is worth knowing before
you rely on it.** `LeadUploadView.permission_classes = (IsAuthenticated, HasOrgContext)`, no
admin check, no `has_sales_access` check. **Any authenticated org member can bulk-create leads**
through this endpoint. The contacts and cases importers below both gate on `_can_import`
(admin or `has_sales_access`), a deliberately narrower surface than a single `POST` to their
respective list endpoints. The lead uploader has no equivalent restriction.

Both importers below share the same design: a stateless two-phase flow (`parse_and_validate` then
`commit_rows`, `backend/contacts/services/csv_import.py` and `backend/cases/services/csv_import.py`),
a 5 MB / 5,000-row cap, UTF-8-only decoding (with or without a BOM. Anything else returns a
`header_error` asking you to re-save the file, rather than silently producing mojibake that then
passes validation), and gating to admins or users with sales access:

```python
def _can_import(profile) -> bool:
    if profile is None:
        return False
    if getattr(profile, "role", None) == "ADMIN":
        return True
    if getattr(profile, "is_admin", False):
        return True
    return bool(getattr(profile, "has_sales_access", False))
```

Anyone else gets `403 {"error": true, "message": "Permission denied"}` from either endpoint of
either importer. This mass-create surface is deliberately not open to every org member the way a
single `POST` is.

## Contacts

`POST /api/contacts/import/preview/` and `POST /api/contacts/import/commit/`
(`ContactImportPreviewView` / `ContactImportCommitView`, `backend/contacts/import_views.py`), both
`multipart/form-data` with the file under the field name `file`.

Required headers: `first_name`, `last_name`. Optional: `email`, `phone`, `organization`, `title`,
`department`, `do_not_call`, `linkedin_url`, `address_line`, `city`, `state`, `postcode`,
`country`, `description`, `account_name`, `assigned_emails`, `team_names`, `tags`. Any header not
in that list, including a misspelling, fails the whole file with a `header_error` before any row
is read; there's no partial-header tolerance.

`assigned_emails`, `team_names` and `tags` accept multiple values separated by `;` in one cell.
`account_name`, `assigned_emails` and `team_names` must resolve to an existing account, active
profile or team in your org. An unresolved reference is a row error, not a silent skip or an
auto-create (tags are the one exception: an unrecognized tag name is auto-created at commit).
`country`, if present, must be one of the codes documented on the [Leads](../api/leads.md#fields)
page's `country` field (same `COUNTRIES` list, shared across the codebase).

## Tickets

`POST /api/cases/import/preview/` and `POST /api/cases/import/commit/`
(`CaseImportPreviewView` / `CaseImportCommitView`, `backend/cases/import_views.py`), same
`multipart/form-data` shape.

Required headers: `name`, `status`, `priority`. Optional: `description`, `case_type`,
`account_name`, `contact_emails`, `assigned_emails`, `team_names`, `tags`, `closed_on`.
`status` and `priority` are matched case-insensitively against the same `STATUS_CHOICE` /
`PRIORITY_CHOICE` enums the API uses (`New`, `Assigned`, `Pending`, `Closed`, `Rejected`,
`Duplicate`; `Low`, `Normal`, `High`, `Urgent`). A value outside those is a row error, not a
free-text fallback. `case_type`, if present, must be one of `Question`, `Incident`, `Problem`.
`closed_on` must be `YYYY-MM-DD`. `contact_emails` (plural, `;`-separated) must resolve to
existing contacts in your org. This importer does not auto-create contacts the way inbound email
does (see [Inbound email](inbound-email.md#how-inbound-email-becomes-a-ticket)).

## Matching

Every reference field: `account_name`, `contact_emails`/`assigned_emails`/`team_names`, and each
importer's own duplicate check, is resolved against your org only. Both importers bulk-prefetch
every distinct reference value in the file once (one query per reference type, not one per row), so
a 5,000-row file with several reference columns runs on the order of ten queries during validation,
not tens of thousands, and, just as importantly, the lookups can't reach across tenants: a CSV
that names another org's account or a team that doesn't exist in your org fails to resolve the same
way a typo would, because the prefetch never looks outside `org=`.

Duplicate detection differs by importer, because "duplicate" means something different for a
person than for a ticket:

- **Contacts**: `email` is a hard error against both the file (another row with the same address)
  and the org's existing contacts. The database enforces a per-org, case-insensitive unique
  constraint, and the importer mirrors it so the failure surfaces as a row error instead of an
  `IntegrityError` at commit. `phone` is a hard error too, normalized with the same digits-only,
  last-10-characters comparison the rest of the codebase uses (`common.validators.normalize_phone`),
  even though there's no database constraint backing it. A full-name collision (`first_name` +
  `last_name`) is **only** an error when the row has neither an email nor a phone to disambiguate
  it from an existing same-named contact. Two people can legitimately share a name, so the check
  only fires when there's nothing else to tell them apart.
- **Tickets**: `name` is a hard error against both the file and the org's existing case names.
  There is no email/phone-style disambiguation exception, because a ticket name isn't expected to
  double as a person's identity the way a contact's is.

## Response shape

Both endpoints of both importers return the same shape. `preview` never writes to the database.
It re-runs the identical validation `commit` does and returns:

```json
{
  "header_error": null,
  "valid": [{"row": 2, "first_name": "Ada", "last_name": "Lovelace", "...": "..."}],
  "errors": [{"row": 3, "field": "email", "message": "'not-an-email' is not a valid email"}],
  "summary": {"total": 2, "valid": 1, "invalid": 1}
}
```

`row` is 1-based against the data rows (the header is not row 1, so the first data row is `row: 1`).
`header_error` is non-null instead of `valid`/`errors` for a whole-file problem, a missing
required header, an unrecognized header, non-UTF-8 content, an empty file, or more than 5,000 data
rows, and when it's set, `valid` and `errors` are always empty; there's no partial parse of a file
that fails at the header stage.

`commit` re-parses and re-validates the file from scratch. It does not trust a client-side
"these rows already passed preview" claim, and refuses to write anything if *any* row is invalid:

```json
{"error": false, "created": 42, "ids": ["<uuid>", "..."]}
```

```json
{
  "error": true,
  "message": "Fix the invalid rows before importing",
  "errors": [{"row": 3, "field": "email", "message": "..."}],
  "created": 0
}
```

A `header_error` at commit time returns the same field, `created: 0`, and no `errors` array.

The two importers handle one edge case differently: a conflicting row created by someone else
between your preview and your commit call, most plausibly the same email landing twice from two
concurrent contact imports. The **contacts** importer's `commit_rows` wraps the write in a
`try`/`except IntegrityError` and turns that race into a clean response instead of a `500`:

```json
{
  "error": true,
  "message": "A contact was created concurrently that conflicts with this import (likely a duplicate email). Re-run preview and try again.",
  "detail": "...",
  "created": 0
}
```

The **cases (tickets)** importer's `commit_rows` has no equivalent `try`/`except`, because it
doesn't need one the same way: `Case` has no database-level uniqueness constraint on `name` (unlike
`Contact.email`, which the database itself enforces per org), so the same race there wouldn't raise
an `IntegrityError` at all. It would instead create two same-named cases, since the importer's
"duplicate name" check only ever looked at what existed *at validation time*. This is a narrow
window, you'd need two concurrent commits importing the same ticket name at once, but it's worth
knowing the two importers aren't symmetric here.
