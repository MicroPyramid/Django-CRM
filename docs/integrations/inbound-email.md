# Inbound email

BottleCRM can turn email sent to a support address into a case (support ticket), and thread
replies onto the same case automatically. This is the **only** webhook in the product, and it runs
in one direction only: BottleCRM *receives* mail through it. Nothing in this codebase posts a
webhook out to a URL you configure — there is no equivalent "notify my system when a case closes"
hook. If you need BottleCRM to push events elsewhere, you're integrating through the
[MCP server](mcp-server.md) or polling the REST API; nothing here does that for you.

## How inbound email becomes a ticket

The pipeline (`backend/cases/inbound/pipeline.py`, entry point `ingest()`) runs the same four
steps for every message that reaches a configured mailbox:

1. **Spam/noise filtering** (`cases/inbound/spam.py`). A message is dropped — recorded, but no
   case touched — if it looks like a bounce, carries `Auto-Submitted: <anything but "no">`,
   `Precedence: bulk|list|junk`, `X-Autoreply: yes`, or both `List-Id` and `List-Unsubscribe`
   headers (a mailing-list signature; either header alone isn't enough, since transactional mail
   sometimes carries `List-Unsubscribe` on its own). A message with no `Message-ID` at all is also
   treated as a drop — without one there's nothing to thread or de-duplicate on.
2. **Threading** (`cases/inbound/threading.py`, `find_existing_case`). `In-Reply-To` and every id
   in `References` are merged into one de-duplicated candidate list, and a **single** query
   matches that whole list against prior messages' `Message-ID`s, ordered by most-recently-received
   — so if more than one candidate id matches, the most recently received message wins; it is not
   "`In-Reply-To` first, then `References`" as two separate lookups. Only after that does the match
   fall through to a case's own thread id (`external_thread_id`, including one inherited from a case
   merged into it, via `alt_thread_ids`) and, as a last resort, a `[Case #<8-hex-chars>]` prefix
   surviving in the subject line. If the matched case was since merged into another, the reply is
   attached to the surviving primary instead.
3. **Contact resolution** (`cases/inbound/contacts.py`). The `From:` address is matched
   case-insensitively against existing contacts in the mailbox's org; if none matches, a new
   `Contact` is auto-created from the display name (or the email's local part, if there's no
   display name) and linked to the case.
4. **Case creation or update.** No match in step 2 creates a new `Case` — subject becomes the name
   (truncated to 64 characters), body becomes the description, and **`status` is always `"New"`**
   (`pipeline.py`: `status="New"` is hardcoded — the mailbox has no `default_status` field, so
   don't go looking for one). `priority` and `case_type` do come from the mailbox's
   `default_priority`/`default_case_type`, and if the mailbox has a `default_assignee`, that
   profile is added to the new case's `assigned_to`. A match reuses the existing case, attaches the
   contact if not already linked, and can reopen a closed case (subject to the org's reopen policy)
   if the reply arrives inside the configured reopen window.

Every message — including dropped ones — is recorded as exactly one `EmailMessage` row
(`org` + `message_id` is the idempotency key, so a provider retry never creates a duplicate case).
That gives admins a forensic trail even for the mail that never became a ticket, and it's what
[the mailbox list's per-mailbox counts](#configuring-a-mailbox) are computed from.

## Configuring a mailbox

`InboundMailbox` (`backend/cases/models.py`) is a per-org row managed at
`GET`/`POST /api/cases/mailboxes/` and `GET`/`PUT`/`DELETE /api/cases/mailboxes/{id}/`
(`InboundMailboxListCreateView` / `InboundMailboxDetailView`,
`backend/cases/inbound_views.py`), admin-only for every write (`POST`, `PUT`, `DELETE` all check
`role == "ADMIN"` or `is_admin`; a non-admin gets `403`). Reads are open to any org member.

The model declares four provider choices — `ses`, `mailgun`, `postmark`, `imap` — but **only `ses`
is actually implemented today**. The webhook itself checks this: any mailbox whose `provider` is
not `"ses"` returns `501 Not Implemented` for every notification it receives
(`InboundMailboxWebhookView.post`, `backend/cases/inbound_views.py`). The `imap_host` /
`imap_port` / `imap_username` / `imap_password_enc` fields exist on the model already so that a
future IMAP implementation doesn't need a schema migration, but nothing reads them yet — setting
`provider` to anything but `ses` configures a mailbox that will reject every message sent to it.

Fields worth knowing when creating one:

| Field | Notes |
| --- | --- |
| `address` | The inbound email address. On **create**, `validate_address` pre-checks for a case-insensitive duplicate in your org and returns a clean `400` if one exists (`self.instance is None` gates this — it's explicitly a create-only check). On **update** (`PUT`), that pre-check does not run at all: renaming a mailbox's `address` onto one already used elsewhere in your org skips the serializer check entirely and goes straight to `.save()`, where the database's own `UniqueConstraint` on `(org, address)` rejects it — deterministically, on every such `PUT`, not just under a race, and with no `try`/`except` around the write to turn it into a clean error. Expect an unhandled `IntegrityError` (`500`), not a `400`, if you rename a mailbox onto an address your org already has. |
| `provider` | Must be `ses` for the mailbox to accept mail (see above). |
| `webhook_secret` | Auto-generated (`secrets.token_urlsafe(32)`) on create if you don't supply one. See [Securing the endpoint](#securing-the-endpoint) for what it does and does not do. |
| `topic_arn` | Leave blank on create — it's pinned automatically from the first verified SNS `SubscriptionConfirmation`, not set by hand. See below. |
| `default_priority`, `default_case_type` | Set directly on any new case this mailbox creates; both optional. There is no `default_status` — a new case's `status` is always `"New"`, not configurable per mailbox (see [above](#how-inbound-email-becomes-a-ticket)). |
| `default_assignee_id` | Optional. If set, that profile is added to the new case's `assigned_to` (a many-to-many "add", not a status or ownership field of its own). |
| `is_active` | An inactive mailbox's webhook returns `404` for every notification, same as a mailbox id that doesn't exist — set this to disable a mailbox without deleting its history. |

`GET /api/cases/mailboxes/` adds two per-mailbox fields on top of the serializer above —
`cases_last_30d` and `last_received_at` — plus an org-wide `totals` object
(`{"count", "active", "cases_last_30d"}`), all computed by `_mailbox_analytics`
(`backend/cases/inbound_views.py`) from the `EmailMessage.mailbox` foreign key, not stored on the
mailbox row itself. `cases_last_30d` counts distinct cases *created* in the last 30 days that have
an inbound message through that mailbox (a reply to an older case doesn't count as a new ticket);
`last_received_at` is the newest inbound message's `received_at`, including dropped ones — the
address still received mail even if the pipeline discarded it. Neither field is present on
`GET /api/cases/mailboxes/{id}/`, which returns only the plain serializer.

## The SNS webhook

Point an AWS SES receipt rule (via an SNS topic, "SNS Notification with full content" or the
older JSON-envelope form — the parser handles both) at:

```
POST /api/cases/inbound/<mailbox_id>/
```

This route is deliberately public — `authentication_classes = ()`, `permission_classes =
(AllowAny,)` — because SNS has no way to send your BottleCRM credentials. The `<mailbox_id>` in the
URL is what scopes each notification to one org: the view looks the mailbox up by that id (and
`is_active=True`) before doing anything else, and because the webhook bypasses
`RLSContextMiddleware` entirely (there's no authenticated session to derive an org from), the view
sets the RLS session variable by hand from `mailbox.org_id` before touching any other org-scoped
table.

On a `Notification`, the view acks with:

```json
{"ok": true, "case_id": "<uuid or null>", "dropped": false, "reason": "", "created_case": true}
```

`dropped`/`reason` reflect the spam-filtering outcome from [the pipeline](#how-inbound-email-becomes-a-ticket)
above; the response is still `200` even when the message was dropped, and deliberately so — SES
already accepted the message from the original sender, and returning a `4xx` here would just
trigger pointless provider retries of a message that was correctly classified as noise, not lost.

## Securing the endpoint

Because the endpoint takes no credential, trust is established entirely by verifying the message
itself, in two layers — and it takes both:

1. **SNS signature verification** (`cases/inbound/sns.py`, `verify_sns_message`). The payload's
   `Signature` is checked against the certificate at its `SigningCertURL`, which is pinned to the
   `sns.<region>.amazonaws.com` host family, fetched with redirects disabled and TLS verified
   against the system CA store, and itself checked for a matching Common Name and a currently-valid
   validity window before its public key is trusted. This proves the payload was genuinely signed
   by *some* SNS topic in *some* AWS account — nothing more.
2. **TopicArn pinning.** A valid SNS signature alone isn't enough, because anyone with an AWS
   account can create a topic and have SNS sign messages for it. Each mailbox is pinned to the
   exact `TopicArn` it should accept: the pin is captured automatically, trust-on-first-use, from
   the first signature-verified `SubscriptionConfirmation` a mailbox receives, and every
   `Notification` after that must carry the exact same `TopicArn` or it's rejected. A mailbox with
   no pin yet rejects every `Notification` outright (only a `SubscriptionConfirmation` can
   establish the pin), and once pinned, a mailbox does not silently re-pin to a different topic —
   without this, anyone who learned a mailbox's UUID could point their own SNS topic at it and have
   AWS legitimately sign forged mail on their behalf, which — because the pipeline threads replies
   onto existing cases — means injecting messages into a live customer conversation, not just
   spam tickets.

Both failure modes return the same generic `403` (`"Signature verification failed"`) rather than
distinguishing "bad signature" from "wrong topic" — a caller who gets past the existence check
below can't tell which of the two rejected them, or what the pinned `TopicArn` is. That existence
check is a separate, earlier step: a `mailbox_id` that doesn't match any active mailbox returns
`404` before either check above ever runs, which does let a caller distinguish "this id belongs to
no mailbox" from "this id belongs to a mailbox, but the request failed verification" (a `403`, a
`501` for an unsupported provider, and so on) — a real, if narrow, way to enumerate valid mailbox
ids, notwithstanding the source comment's stated intent not to leak that. Mailbox ids are UUIDs,
not sequential, so this isn't practically brute-forceable, but it's not the airtight non-disclosure
the comment claims either.

**`webhook_secret` is not part of this verification.** It is stored on the mailbox, auto-generated
on create, and settable/rotatable by an admin through the mailbox CRUD endpoints above, but nothing
in `InboundMailboxWebhookView.post` reads or compares it — the two checks above are what actually
gate the endpoint. What `webhook_secret` (and `topic_arn`, held to the same bar) does get is
**stripped from every API response to a non-admin caller**: `InboundMailboxSerializer.to_representation`
pops both fields unless the requesting profile is an admin, so a regular org member who can list
mailboxes never sees either value. Treat both as admin-only secrets when deciding who in your org
should have access to the CRM at all — not because a leaked `webhook_secret` lets someone forge
mail today, but because a leaked `topic_arn` embeds your AWS account id, and because the field is
positioned to matter if a future provider integration does check it.
