# Contacts

Routes in `backend/contacts/urls.py`: `backend/contacts/views.py` for CRUD and comments/attachments,
`backend/contacts/import_views.py` and `backend/contacts/services/csv_import.py` for CSV import. See
[Conventions](conventions.md) for pagination, filtering and response-shape rules assumed rather than
repeated here.

## Two links to an account, not one

Before anything else: **a contact can be joined to an account two different ways**, and they are
independent. `Contact.account` is a foreign key the model itself calls "Primary account this contact
belongs to" (`contacts/models.py:71-78`); `Account.contacts` is a separate many-to-many
(`accounts/models.py:63-65`). Nothing in the database keeps them in sync. Setting one does not set
the other by itself. The view layer bridges them on write: `link_primary_account(contact)`
(`contacts/views.py:48-65`) adds the contact to `contact.account.contacts` whenever `account` is set
via `POST /api/contacts/`, `PUT /api/contacts/{id}/` or `PATCH /api/contacts/{id}/`, but clearing the
FK later does **not** remove the M2M membership, on purpose (a person can be "no longer the primary
contact" without having "left the company"; `contacts/views.py:59-62`).

Both links are exposed on every `ContactSerializer` response, deliberately, because reading only one
tells the wrong story depending on the data:

```json
{
  "account": "<uuid or null>",
  "account_detail": {"id": "<uuid>", "name": "Acme Inc"},
  "linked_accounts": [{"id": "<uuid>", "name": "Acme Inc"}]
}
```

`account_detail` resolves the FK (`contacts/serializer.py:28-39`); `linked_accounts` is the M2M
membership (`:41-56`). The account detail page's contact list is built from `Account.contacts` (the
M2M), not the FK, so a contact whose `account` FK is set but was never added to that account's
`contacts` (see [CSV import](#csv-import) below for exactly this case) will not appear there even
though `account_detail` on the contact itself looks correct.

## List contacts

`GET /api/contacts/` (`ContactsListView.get`, `contacts/views.py:199-201`) returns a single
paginated list. Unlike leads and accounts, it is not split into two sections. It still doesn't call
DRF's `get_paginated_response()` though. [Conventions](conventions.md#pagination) names
`GET /api/cases/solutions/` as the only endpoint in this API that does. The view hand-builds `count`
and `results` itself (`contacts/views.py:166-167`), with no `next`/`previous`, alongside a legacy set
of keys kept for backwards compatibility (`:168-171`):

```json
{
  "count": 41,
  "results": [ { "...": "ContactSerializer" } ],
  "per_page": 10,
  "page_number": [1],
  "contacts_count": 41,
  "offset": 10,
  "contact_obj_list": [ { "...": "same rows as results" } ],
  "countries": [["GB", "United Kingdom"]],
  "users": [{"id": "...", "user__email": "..."}]
}
```

`active_count` and `inactive_count` (`contacts/views.py:147-148`) are computed over the full filtered
queryset *before* any `is_active` filter is applied, so a client can show "12 active, 3 inactive" while
also asking for only one of the two via `?is_active=true`/`?is_active=false`
(`:149-150`), the only exact-match boolean filter on this endpoint; every other filter here is a
substring match: `name` (`first_name` or `last_name`), `city`, `phone`, `email`, `search`
(`first_name`, `last_name`, `email` or `phone`), plus `assigned_to`/`tags` (repeatable id lists),
`created_at__gte/lte`, and `cf_<key>` (`contacts/views.py:90-139`). A non-admin caller only sees
contacts assigned to them or created by them (`:83-87`).

## Create a contact

`POST /api/contacts/` (`ContactsListView.post`, `contacts/views.py:218-311`) is validated by
`CreateContactSerializer` (`contacts/serializer.py:102-174`); see [Fields](#fields). On success
(`200`):

```json
{"error": false, "message": "Contact created Successfuly", "id": "<uuid>"}
```

(The message string is spelled exactly that way in the response, `Successfuly`, not `Successfully`;
document your integration tests against the real string, not the expected one.) Two validators worth
knowing: **`email` must be unique per org, case-insensitive**, checked only when supplied
(`validate_email`, `contacts/serializer.py:129-145`); and **`account`, if given, must belong to the
caller's org**; `validate_account` rejects a UUID from any other org's `Account` table with
`"No such account."` rather than silently attaching a cross-tenant record
(`contacts/serializer.py:114-127`). `teams`, `assigned_to` and `tags` are not part of the serializer
either, the view resolves each from the request body, tolerating either a JSON array or a
JSON-encoded string of ids (or of `{"id": "..."}` objects), consistently across all three fields and
across `POST` (`contacts/views.py:247-284`), `PUT` (`:478-518`) and `PATCH` (`:832-876`) alike.
Contacts does not have the per-field, per-verb inconsistency [Leads](leads.md#fields) documents for
the equivalent fields there. `contact_attachment` is accepted as a multipart file.

## Retrieve, update, delete

`GET /api/contacts/{id}/` (`ContactDetailView.get`, `contacts/views.py:565-654`) org-scopes the
lookup and maps a malformed id to `404` the same way accounts does
(`get_object`, `:318-332`). `assert_contact_access` (`:334-361`) is the broadest access rule in this
group of four pages: an admin, the contact's creator, one of its assignees, **or anyone assigned to
an account the contact is linked to by either route** (FK or M2M; `account_ids`, `:363-369`) may
read, update or comment on the contact; anyone else gets `403`. The response nests the record under
`contact_obj` and also returns `address_obj` (the flat address fields, echoed as their own object),
`countries` (`contacts/views.py:608`), `comments`, `attachments`, `assigned_data`, `tasks`,
`users_mention`, `custom_field_definitions`, and three computed, capped lists: `opportunities`
(up to 10, via `Opportunity.contacts`),
`cases` (up to 10, via `Case.contacts`), and `colleagues` (up to 8: other contacts sharing either
account link, matched on the account relationship rather than the free-text `organization` field,
which frequently names a different company). `tasks`, `opportunities`, `cases` and `colleagues`
hold only records the caller may open under each module's own read rule, so a non-admin sees
fewer rows than an admin on the same contact.

`open_deals` summarises every open deal naming the contact that the caller may open, uncapped:
`count`, `amount` (the total when every deal is in one currency, `null` when there are several)
and `by_currency` (`[{currency, count, amount}]`, ordered by code). A deal with no currency counts
in the org's default. Use it instead of totalling `opportunities`, which stops at 10. `opportunity_count` is
the uncapped number of deals naming the contact that the caller may open, open or closed.

`PUT /api/contacts/{id}/` (`:441-544`) and `PATCH /api/contacts/{id}/` (`:793-881`) both call
`link_primary_account` after saving (`:477`, `:830`), so changing `account` through either verb keeps
`Account.contacts` in step the same way create does. Success:
`{"error": false, "message": "Contact Updated Successfully"}`.

The detail response also carries `can_delete`: whether this caller's `DELETE` would be accepted, so a
client offers the action only then.

`DELETE /api/contacts/{id}/` (`:670-691`) is narrower than read/write access on purpose, no assignee
exception, only an admin or the contact's own creator may delete
(`self.request.profile.user_id != self.object.created_by_id`, `:676-679`).

## CSV import

Two endpoints, both gated to org admins or members with `has_sales_access`
(`can_mass_import` in `common/permissions.py`). An ordinary member gets `403`:

`POST /api/contacts/import/preview/` (`ContactImportPreviewView`, `contacts/import_views.py`) reads a
`multipart/form-data` upload in a field named `file` (must end in `.csv`, capped at 5 MB, checked
against the actual bytes read rather than the client-supplied `Content-Length`; `_read_upload`),
validates every row without writing anything, and returns:

```json
{
  "header_error": null,
  "valid": [
    {
      "row": 2, "first_name": "Ada", "last_name": "Lovelace", "email": "ada@example.com",
      "phone": "2025551234", "organization": null, "title": null, "department": null,
      "do_not_call": false, "linkedin_url": null, "address_line": null, "city": null,
      "state": null, "postcode": null, "country": null, "description": null,
      "account_id": "<uuid or null>", "assigned_ids": [], "team_ids": [], "tag_names": []
    }
  ],
  "errors": [{"row": 3, "field": "email", "message": "'not-an-email' is not a valid email"}],
  "summary": {"total": 2, "valid": 1, "invalid": 1}
}
```

`POST /api/contacts/import/commit/` (`ContactImportCommitView`) re-validates the same file
and writes inside one transaction (`commit_rows` / `_commit_validated` in
`contacts/services/csv_import.py`), if any row fails validation, **nothing is written**; a
concurrent conflict (e.g. a duplicate email created by another request between preview
and commit) rolls the whole batch back and reports `400` rather than partially importing. On success (`200`):

```json
{"error": false, "created": 12, "ids": ["<uuid>", "..."]}
```

The CSV must have a header row with `first_name` and `last_name` at minimum; the full list of
recognized optional headers is `email`, `phone`, `organization`, `title`, `department`,
`do_not_call`, `linkedin_url`, `address_line`, `city`, `state`, `postcode`, `country`,
`description`, `account_name`, `assigned_emails`, `team_names`, `tags`
(`REQUIRED_HEADERS`/`OPTIONAL_HEADERS` in `csv_import.py`); an unrecognized header or a missing
required one fails the whole file with `header_error` before any row is checked. `assigned_emails`
and `team_names` accept `;`-separated multiple values per cell. Duplicates are rejected per org: email
and phone (normalized) are always hard errors; a matching first+last name is only a hard error when
the row supplies **neither** an email nor a phone to disambiguate it from an existing contact
(`csv_import.py`). The file is capped at 5,000 data rows (`MAX_ROWS`).

**A row with `account_name` sets both links to the account.** `_commit_validated` creates each
`Contact` with `account_id=vr.account_id` and then calls `link_primary_account`, as
`POST /api/contacts/` and the `PUT`/`PATCH` update endpoints do (see
[Two links to an account](#two-links-to-an-account-not-one)), so an imported contact appears on that
account's contact list (`Account.contacts`, the M2M) as well as under `account_detail`.

### Column matching (`mapping`)

Both endpoints also accept an optional `mapping` form field, which switches them to the
column-matching mode. Its value is `"auto"` (guess each column from its header; Google Contacts,
Outlook and HubSpot exports are recognised) or a JSON object `{"<column index>": "<field>" | null}`
that sets or overrides the guess, where `null` ignores a column. In this mode the file may be a
`.csv` (UTF-8 or Windows-1252; comma, semicolon or tab delimited) or an `.xlsx` (first sheet only),
still capped at 5 MB, 5,000 rows and 1,000 columns, and the header names need not match the list
above. Without
`mapping` everything above applies unchanged.

A bad value does not cost you the person: it is dropped, counted, and the rest of the row is
imported. Only a row that cannot become a contact, or that duplicates one (by email org-wide, or by
phone and name among contacts you can see), is skipped. Rows are numbered from 1, the first row
under the header. The preview answers (the `valid` entry is shortened here):

```json
{
  "columns": [{"index": 0, "header": "First Name", "field": "first_name", "samples": ["Ada", "Grace"]}],
  "fields": [{"name": "first_name", "label": "First name", "required": true}],
  "valid": [{"row": 1, "first_name": "Ada", "last_name": "Lovelace"}],
  "skipped": [
    {
      "row": 2, "field": "email",
      "message": "A contact with this email already exists in your organization",
      "cells": ["Grace", "Hopper", "grace@example.com"], "kind": "duplicate"
    }
  ],
  "dropped": [{"field": "phone", "count": 1}],
  "summary": {"total": 2, "valid": 1, "skipped": 1}
}
```

`kind` is `"duplicate"` when the contact already exists (in the org, or earlier in the file) and
`"row"` when the row cannot become a contact; clients branch on it, not on `message`.

and the commit answers `{"error": false, "created": 1, "ids": ["<uuid>"], "skipped": [...],
"dropped": [...]}`. A file with nothing importable gets `400` `"Nothing in this file can be
imported."`. All four contacts and leads import endpoints share a per-user rate limit,
`IMPORT_THROTTLE` (default `30/minute`; see [Environment variables](../reference/environment-variables.md#imports)).

## Duplicates and merging

`POST /api/contacts/duplicates/` takes the fields a create form has typed so far as a JSON body
(`email`, `phone`, `first_name`, `last_name`) and answers `{"duplicates": [...]}`: at most 10 active contacts, newest first.
`GET /api/contacts/{id}/duplicates/` answers the same list for a saved contact, leaving the contact itself out,
plus `can_delete` for that contact. Each hit carries only `id`, `name`, `email`, `phone`, `matched_on`
(the rules it matched) and `can_delete` (whether the caller could merge it away), never the record.
Both search only the contacts the caller may open, so a hidden one is neither listed nor counted, and
a hidden or missing `{id}` is the same `404`. A value longer than the model allows is a `400`. The
create-form check is a `POST` that writes nothing, so that an email address and a phone number never
land in a URL and the access logs that record it. From django-crm 1.13.0 a token needs only the
module's `read` scope (`contacts:read`) for it, because it writes nothing; before that it needed
`contacts:write`. It is throttled at 120 requests a minute per user, and the
clients debounce well under that.

Matching: email, case-insensitive; first and last name together. Phone numbers match on their last ten digits (or every digit of a shorter number,
seven at least), whatever the separators.

`POST /api/contacts/{id}/merge/` with `{"merge_id": "<uuid>"}` merges the contact named in the body into the
one in the URL. The caller must be able to open both (either one hidden or missing is the same `404`),
must be allowed to edit the one kept (for contacts, anyone who can open it), and must hold the delete rule on the one merged away
(admin, superuser or its creator), else `403`. Merging a contact into itself, or a missing or
malformed `merge_id`, is a `400`. Both rows are locked for the merge, which runs in one
transaction:

- Every link to the merged contact moves to the kept one: accounts (both links), leads, deals, tickets, tasks, board cards, invoices, estimates, recurring invoices, orders, account emails, CSAT surveys and portal replies, comments, attachments and
  activity. A link the kept contact already has is not doubled.
- The kept contact's values win. Its blank fields, including custom fields key by key, take the other's
  values; owners (`assigned_to`, `teams`) are taken only when the kept contact has none; tags
  are the union of both. "Do not call" set on either contact stays set. Portal sign-in codes minted for the merged contact are deleted with it, and its open portal sessions stop working; when the kept contact has no email it takes the merged one's, as an edit could.
- The merged contact is then deleted, which sends the usual `contact.deleted` webhook, and a
  `RECORD_MERGED` row naming both ids and both names is written to the audit log. There is no undo. From
  django-crm 1.13.0 that webhook's `assigned_to` lists the owners the merged contact had before the
  merge, even when they moved to the kept one; before, it was built after the move and could list
  nobody.

The response is `{"error": false, "message": "...", "id": "<kept id>"}`.

## Fields

The contact payload also carries `source`, `source_detail` and `source_ref`, and a read-only
`phone_e164` (the phone normalised for matching).

`CreateContactSerializer.Meta.fields` (`contacts/serializer.py:147-174`) is what
`POST /api/contacts/`, `PUT /api/contacts/{id}/` and `PATCH /api/contacts/{id}/` accept. Unlike
`Lead.first_name`/`last_name`, `Contact.first_name` and `Contact.last_name` have neither
`blank=True` nor a serializer override (`contacts/models.py:19-20`). **both are genuinely
required**.

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `first_name` | string | **required** | |
| `last_name` | string | **required** | |
| `email` | string | optional | Unique per org, case-insensitive, when supplied |
| `phone` | string | optional | |
| `source` | a key of the org's [lead sources](leads.md#lead-sources) | optional | Same rule as a lead's `source`. Set at lead conversion from the lead |
| `source_detail` | string, at most 100 | optional | |
| `source_ref` | string, at most 255 | optional | |
| `organization` | string | optional | Free text, may name a different company than `account` links to |
| `title` | string | optional | |
| `department` | string | optional | |
| `do_not_call` | boolean | optional | Defaults `false` |
| `linkedin_url` | string | optional | Validated as a URL |
| `address_line`, `city`, `state`, `postcode` | string | optional | |
| `country` | one of `COUNTRIES` | optional | |
| `description` | text | optional | |
| `account` | uuid | optional | Must belong to the caller's org; see [Two links to an account](#two-links-to-an-account-not-one) |
| `is_active` | boolean | optional | Defaults `true` |

Not part of the serializer, but accepted in the same request and resolved by the view (see
[Create a contact](#create-a-contact)): `teams`, `assigned_to`, `tags` (each a list of ids,
org-scoped), and `contact_attachment` (a multipart file).

`GET /api/contacts/` and `GET /api/contacts/{id}/` additionally return, but never accept as input:
`id`, `created_by`, `created_at`, `updated_at`, `org` (nested), `account_detail`, `linked_accounts`
(both described above), `contact_attachment`, and `custom_fields` (validated separately against the
org's `CustomFieldDefinition` rows).
