# Interactions

An interaction is a call, meeting, email, WhatsApp message or SMS logged on a record, or an
**enquiry**: a lead asking, written each time one arrives through a web form, a lead webhook or a
lead address. Notes stay comments; an interaction is a separate record with a kind, a direction and
a time, and a lead's first response is measured from them (see
[Answering leads](../features/answering-leads.md)). Routes are in `backend/interactions/urls.py`,
views in `interactions/views.py`, the visibility rule in `interactions/access.py`, and every write
goes through `interactions/service.py`.

| Endpoint | Does |
| --- | --- |
| `GET /api/interactions/?lead={id}` | A record's interactions, newest first (or `contact=`, `account=`, `opportunity=`, `case=`) |
| `POST /api/interactions/` | Log one on a record (`201`) |
| `PATCH /api/interactions/{id}/` | Change one |
| `DELETE /api/interactions/{id}/` | Delete one (`204`) |

There is no `PUT`, and no single-interaction `GET`: a record's list carries every field.

## Who sees what

Each interaction has one **home**: the record it was logged on (for an enquiry, the lead, or the
contact a converted lead became). Whoever may open the home record sees the interaction, by that
record's own rule (`visible_leads_qs`, `visible_contacts_qs`, and so on), and nobody else, admins
seeing everything in their org as they do on every record. An interaction can also be linked to
other records, and those links only decide which other timelines list it: a contact's timeline
shows an interaction homed on a lead only to people who may open that lead. A second link never
shows a record to someone who cannot open it.

Interactions follow the module of their home. With Leads, Pipeline or Tickets switched off, an
interaction homed on a lead, deal or ticket is hidden from every list and answers `404`, and naming
such a record in a list or a log is the module's own `404` (see
[Errors: Switched-off modules](errors.md#switched-off-modules)). Contacts and accounts are core.

A record the caller may not open, a record in another org and an id that does not exist all answer
`404` with the same body.

## Who may change one

The person who logged it, or an org admin, may edit or delete it; anyone else who can see it gets a
`403`. Enquiries, and anything written by intake or an integration (an `origin` other than `manual`
or `phone_tap`), are read-only for everyone, admins included: `403`. Each object carries `can_edit`
for the caller, so a client can hide the controls.

## The object

```json
{
  "id": "0b8e2a8c-2d55-4f0e-9a3b-6a1d1c2f4e10",
  "kind": "call",
  "direction": "outbound",
  "occurred_at": "2026-10-24T09:14:00Z",
  "duration_seconds": 240,
  "duration_estimated": true,
  "outcome": "connected",
  "subject": "",
  "body": "Wants a viewing on Saturday.",
  "logged_by": "8a4e5b9e-...-profile-id",
  "logged_by_details": {"id": "8a4e5b9e-...", "name": "Sam", "email": "sam@example.com"},
  "participants": [],
  "lead": "5b0c5c1e-6a0e-4f43-9d6e-1f0f3c1a2b3c",
  "contact": null,
  "account": null,
  "opportunity": null,
  "case": null,
  "home": "lead",
  "origin": "phone_tap",
  "external_id": "",
  "created_at": "2026-10-24T09:19:02Z",
  "can_edit": true
}
```

- `kind`: `call`, `meeting`, `email`, `whatsapp`, `sms` or `enquiry`.
- `direction`: `inbound` or `outbound`.
- `outcome`: for a call, `connected`, `no_answer`, `voicemail`, `busy` or `wrong_number`, or `""`;
  always `""` for any other kind.
- `logged_by`: the profile that logged it, or `null` for an enquiry or a row an integration wrote.
- `participants`: a list of `{name, email, phone}` written by integrations; not accepted from a
  client.
- `home`: `lead`, `contact`, `account`, `opportunity` (a deal) or `case` (a ticket); the field of
  that name holds its id.
- `origin`: `manual` or `phone_tap` for a person's log; `intake`, `email` or `webform` for an
  enquiry, by the route it arrived through; an integration's own key otherwise.

## Listing a record's interactions

`GET /api/interactions/?lead={id}` takes exactly one of `lead`, `contact`, `account`,
`opportunity` and `case`; none, two, or a malformed id is a `400`. The answer is
`{"interactions": [...], "count": n}`, newest `occurred_at` first, holding only the interactions
whose home the caller can see. `count` is the total of those; `limit` (default 50, at most 200) and
`offset` page through them, and a value that is not a non-negative number falls back to the
default.

## Logging one

`POST /api/interactions/` with:

| Field | |
| --- | --- |
| `kind` | Required. Not `enquiry`: enquiries are written when a lead arrives |
| `direction` | `outbound` (the default) or `inbound` |
| `occurred_at` | Default now. More than five minutes in the future is refused |
| `duration_seconds` | A whole number of seconds, or `null` |
| `duration_estimated` | `true` when the time is a guess (the phone app estimates a call from the time away) |
| `outcome` | Calls only; on any other kind it is a `400` |
| `subject` | Up to 200 characters |
| `body` | Up to 10,000 characters |
| `origin` | `manual` (the default) or `phone_tap` |
| `lead`, `contact`, `account`, `opportunity`, `case` | Exactly one, which becomes the home |

`logged_by`, `org`, `home`, `participants` and `external_id` are set by the server; a body that
names them is not read. The record must be one the caller may open (`404` otherwise). On a ticket
the caller must also be allowed to work it: a watcher, who may read a ticket but not reply on it,
gets a `403`. The answer is `201` with the object.

Errors use the usual shape (see [Errors](errors.md#validation-errors)):

```json
{"error": true, "errors": {"outcome": ["Only a call has an outcome."]}}
```

## Changing one

`PATCH /api/interactions/{id}/` takes the fields above. The kind, the home and the record links
never change: sending them back as they are is fine, and a different value is a `400`. The same
rules as logging apply (no outcome on a meeting, nothing more than five minutes ahead).

`DELETE /api/interactions/{id}/` answers `204`.

## A lead's response fields

Every write that touches a lead (logging, editing or deleting an interaction linked to it)
recomputes the lead's `first_response_at`, `first_response_by` and `last_outbound_at` from its
stored interactions, so a deleted or backdated call is reflected at once and a lead whose only
response was deleted is waiting for an answer again. Deleting a record that is an interaction's
home (a converted lead's calls live on its contact) deletes the interaction too, and each lead it
was linked to is recomputed once the delete has committed. Every **outbound** call, meeting, email,
WhatsApp message or SMS counts, whatever its `origin` and whether or not it has a `logged_by`: an
integration's message answers a lead, and so does a call by a member who has since been removed
from the org (their `logged_by` becomes `null`). A call with no answer counts too. Inbound
messages and enquiries never count.

- `first_response_at` is the earliest of them; `first_response_by` is the person who logged it,
  or `null` when nobody did.
- `last_outbound_at` is the latest.
- Neither is ever earlier than the lead's `created_at`: a call logged with a time before the lead
  was entered is a response time of zero, and the lead does not read as waiting.
- The lead's `last_contacted` date moves to the org-local date of `last_outbound_at` when that is
  later than the date stored; it never moves back.

These are written straight to the lead's row, so they send no `lead.updated` webhook and run no
automation rule; `interaction.created` is the event to listen for. The fields, the unanswered list
and response times are in [Leads](leads.md).

## Enquiries, conversion and merges

Each arrival through a web form, a lead webhook or a lead address is an `enquiry` (inbound, no
`logged_by`, `subject` naming the form, webhook or address, `body` the message) on the lead it
created or merged into. A repeat enquiry from a converted lead lands on the contact it became,
linked to that contact's account and to the lead. A sender's retry that is answered `duplicate`
writes nothing. See [Lead capture](../features/lead-capture.md).

Converting a lead keeps each interaction's lead link, moves its home to the new contact (to the
account when the conversion made or linked no contact), and links the account and the deal.
Merging one lead into another moves the merged lead's interactions to the lead kept and recomputes
its response fields. Deleting a record deletes the interactions it is home to, recomputing any
lead they were linked to, and only unlinks the others.

## Webhooks and tokens

`interaction.created` is sent for every interaction, logged or written by intake (see
[Webhooks](../integrations/webhooks.md#events)).

For personal access tokens the resource is `interactions`: `interactions:read` to list,
`interactions:write` to log, change and delete (see
[Tokens and API keys](tokens-and-api-keys.md#scopes)). A token also needs the scope of the home
record's own resource, the one that record's comments need: `leads`, `contacts`, `accounts`,
`opportunities` or `cases`, `read` to list and `write` to log, change or delete. Without it the
answer is the same `403` the middleware gives, naming the missing scope:

```json
{"detail": "This token is not scoped for read access to leads. It needs the leads:read scope."}
```

A timeline leaves out interactions homed on a resource the token cannot read, so a token with
`contacts:read` alone does not see a contact's calls that are homed on a lead. The organization
API key reads every timeline and writes none. A signed-in session is not limited by scopes.
