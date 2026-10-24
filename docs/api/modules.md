# Modules

An org admin can switch whole parts of BottleCRM off for the org. This page is the API side:
reading and changing the setting, what an off module answers, and what keeps running or stops
while it is off. The admin's view of the same feature is
[Modules](../getting-started/modules.md).

The catalogue is `backend/common/modules.py`; the endpoints are `OrgModulesView`
(`backend/common/views/module_views.py`) and `change_modules`
(`backend/common/module_settings.py`).

Switching a module off never deletes or changes a record. Everything is still stored, and it all
comes back when the module is switched on.

## The modules

| Key | Label | Covers | Needs |
| --- | --- | --- | --- |
| `deals` | Pipeline | Deals, deal pipelines, line items, the deal board and stage aging. | |
| `leads` | Leads | Leads, lead pipelines, and lead import and export. | |
| `goals` | Goals | Sales goals, the leaderboard and goal history. | `deals` |
| `tasks` | Tasks | Tasks, boards, the task calendar and its calendar feed. | |
| `tickets` | Tickets | Tickets, approvals, ticket analytics, routing, escalation, the reopen policy, business hours, saved replies, inbound email, CSAT and portal tickets. | |
| `knowledge_base` | Knowledge base | Articles, the public help center and portal articles. | |
| `documents` | Documents | Documents and their downloads. | |
| `invoices` | Invoices | Invoices, estimates, recurring invoices, invoice templates, invoice reports, account statements, and public invoice and estimate links. | |
| `timesheet` | Timesheet | Time entries, the timesheet and the time report. | `tickets` |

The groups, in the order they are served, are `sell` (deals, leads, goals), `serve` (tasks,
tickets, knowledge base, documents) and `bill` (invoices, timesheet). Within a group the modules
follow the org's saved order.

A label follows the org's terminology: an org that calls deals "Opportunities" sees that name for
`deals`, and likewise for `leads` and `invoices`. Every module message uses the org's label.

**Needs.** A module that needs another is available only while that one is. Goals needs Pipeline
and Timesheet needs Tickets. Switching the needed module off makes the dependent one unavailable
without changing its own setting, so switching the needed one back on restores it.

## Read the setting

`GET /api/org/modules/`, any member of the org.

```json
{
  "modules": [
    {
      "key": "deals",
      "label": "Pipeline",
      "group": "sell",
      "covers": "Deals, deal pipelines, line items, the deal board and stage aging.",
      "stops": "Everything in Pipeline leaves every menu, search and Today, and stale-deal emails stop. Converting a lead no longer creates a deal, and Goals switches off too.",
      "enabled": false,
      "available": false,
      "needs": null
    },
    {
      "key": "goals",
      "label": "Goals",
      "group": "sell",
      "covers": "Sales goals, the leaderboard and goal history.",
      "stops": "Goals leave every menu, and goal milestone emails stop.",
      "enabled": true,
      "available": false,
      "needs": "deals"
    }
  ],
  "can_edit": true
}
```

The response has all nine rows (two are shown). `enabled` is the module's own setting;
`available` is `enabled` and its need available. `stops` is the confirmation text an admin reads
before switching the module off, already carrying the org's label. `can_edit` is true for admins
and false for members.

A request with no session answers `403` (every unauthenticated API request does), and so does a
session with no organization.

## Change the setting

`PUT /api/org/modules/`, admins only. Both fields are required, and the body replaces the setting:

```json
{"off": ["tickets", "timesheet"], "order": ["deals", "leads", "goals", "tasks", "tickets", "knowledge_base", "documents", "invoices", "timesheet"]}
```

`off` lists the modules to switch off; every module not named is on. `order` lists module keys in
the order the org wants them; modules are only ordered within their group, and a module left out
of `order` follows the named ones. A successful `PUT` answers `200` with the same body as the
`GET`. `PATCH` is `405`.

A member is refused with `403`:

```json
{"error": true, "errors": "Only admins can switch modules on or off."}
```

The body is checked before anything is saved, and an invalid request changes nothing. A `400`
carries the problems under `off` and `order`:

| Problem | Field | Message |
| --- | --- | --- |
| Field missing | `off` or `order` | `This field is required.` |
| Not a list of strings | `off` or `order` | `Send a list of module keys.` |
| A key that is not a module | `off` or `order` | `Unknown module: "crm".` (one entry per key) |
| A key named twice | `order` | `Name each module once.` |
| A module switched on while its need stays off | `off` | `Goals needs Pipeline. Switch Pipeline on first.` |
| A web form still takes submissions | `off` | `Leads still receives submissions from the published web form "Contact us". Unpublish it first, so no submission is lost.` |
| Several such forms | `off` | `Tickets still receives submissions from 2 published web forms: "Billing help", "Zed help". Unpublish them first, so no submission is lost.` |
| An active mailbox | `off` | `Tickets still receives email at help@example.com. Switch that mailbox off first, so no email is lost.` |
| Several active mailboxes | `off` | `Tickets still receives email at 2 mailboxes: a@example.com, b@example.com. Switch them off first, so no email is lost.` |

`off` can carry several messages at once. Lists of forms or mailboxes name at most five and then
say `and N more`. The form and mailbox checks apply only to a module the change makes
unavailable, so an admin can still reorder while a module is already off. Forms for leads and
active lead addresses count against Leads, and forms for tickets and active ticket mailboxes count
against Tickets; because Timesheet needs Tickets, switching Tickets off is refused for the same
reasons.

A body that is not valid JSON answers DRF's own `400`, `{"detail": "JSON parse error ..."}`.

A change that alters the off list or the order is written to the
[security audit log](audit-log.md) as `MODULES_CHANGED`.

## What an off module answers

A signed-in request to a route of an unavailable module answers `404` for every method (`GET`,
`HEAD`, `OPTIONS`, `POST`, `PUT`, `PATCH`, `DELETE`):

```json
{"detail": "Tickets is switched off for this organization.", "code": "module_off", "module": "tickets"}
```

This applies to a session, a personal access token and the organization API key alike. The module
named is the one that is actually off: with Goals on and Pipeline off, a goals route names
`deals`. A personal access token's own scope refusal (`403`) still comes first, and the
organization API key is read-only, so a write with it is refused as it always was.

The inbound mailbox routes (`/api/cases/mailboxes/`) belong to Tickets or Leads and stay
reachable while either is on, since a mailbox makes tickets or leads. Some routes need more than
one module. The time entry routes need Tickets and Timesheet; invoice
creation from a deal needs Invoices and Pipeline; invoice creation from time entries needs
Invoices, Tickets and Timesheet. Products belong to Pipeline or Invoices and stay reachable while
either is on. `GET /api/org/help-center/` is the Knowledge base's settings route and answers the
same `404` for every method while it is off.

Anything outside the nine modules (accounts, contacts, web forms, webhooks, automation, search,
the dashboard and the rest of `/api/org/`) is always reachable.

### Public, portal and inbound entry points

These are not signed-in requests, so they answer what they already answer for a link that does
not exist, and never name the module. The lead webhook is the one exception: a post that carries
its key already proves it is the org's own sender, so it is told why nothing was made.

| Entry point | Module | Answer while off |
| --- | --- | --- |
| Public invoice and estimate links (view, PDF, accept, decline) | Invoices | `404` `{"error": true, "message": "Invoice not found or link expired"}` (the same body for an estimate link) |
| CSAT survey link | Tickets | `410` `{"error": "Survey link is no longer valid."}` |
| Inbound email webhook for a mailbox | Tickets, or Leads for a lead address | `404` `{"error": true, "errors": "Mailbox not found"}` |
| Generated-address catch-all | Tickets or Leads, by each recipient's mailbox | `200`, and that recipient's mail is dropped |
| Portal tickets (list, create, detail, comment) | Tickets | `404` `{"error": "Case not found"}` |
| Portal articles (list, detail) | Knowledge base | `404` `{"error": "Article not found"}` |
| Portal article suggestions | Knowledge base | `200` `{"articles": []}`, as an empty query answers |
| Public help center | Knowledge base | `404` `{"error": "Not found"}` |
| Calendar feed link | Tasks | `404` `{"error": "Not found"}` |
| Web form page, definition and submit | Leads or Tickets, by the form's target | `404`, as for an unknown form |
| Lead webhook (`POST /api/public/leads/<intake_id>/`) | Leads | `403` `{"detail": "Leads are switched off for this organization."}` to a post with the webhook's key, logged as a refused delivery; without the key, the `401` any wrong key gets |

A web form's CORS response headers follow the same rule: while the form's target module is off
they match an unknown form's, so nothing tells an outsider which case it was. Sign-in to the
portal is unaffected.

## Web forms

A form belongs to Leads or Tickets by its `target`. While that module is off:

- Publishing the form is refused with `400`: `Leads is switched off for this organization. Switch
  it on before publishing this form.`
- Creating a form with no `target` while Leads is off is `400` under `target`, because the default
  target is `lead`. Choosing a target whose module is off, or changing a form to one, is refused
  the same way, with the module message.
- A form that was already published cannot be left behind: switching the module off is refused
  while it is published (see the table above).

## Records that mention an off module

Responses keep their keys when they embed records of an off module; the embedded part is empty:
lists are `[]`, counts are `0`, and single links and summaries are `null`. Specific cases:

- A time entry keeps a read-only `invoiced` boolean while Invoices is off; its `invoice` is `null`.
- A deal's `next_activity` is `null` while Tasks is off.
- A product's `used_on` is `0` while Invoices is off.
- Task webhook payloads still carry the bare ids of a task's deal, ticket or lead.

A write that omits or sends `null` for a link to an off module's record keeps the stored link. A
write that names a different record of an off module is `400` on that field, with the module
message. Choosing an off module's webhook event, saved view list, custom field target or web form
target is refused the same way.

Other surfaces follow the modules too:

- **Saved views** of an off module are left out of the list and answer `404`; creating one is
  refused.
- **Webhooks.** Nothing is emitted for an off module, and the event catalogue leaves it out. An
  endpoint keeps the events it already stored for an off module, and subscribing to a new one is
  `400` under `events` with the module message. Deliveries already queued are still sent.
- **Automation.** A rule whose object belongs to an off module lists with status `paused` and the
  text `Paused: Tickets is switched off`, and does not run. It can still be switched on. Creating
  a rule on such an object, or changing a rule's object, trigger, conditions, actions or match,
  is `400` with the module message. While Tasks is off, the catalogue's `actions` leaves out
  `create_task`, and a Create a task step the stored rule does not already have is `400` under
  `actions[N].type` with the module message. A step the rule already has is kept, and skipped
  when the rule runs.
- **Tags** leave an off module's usage out of the per-module figures, and a tag used only by an
  off module is never reported as unused.
- **Packs and sample data.** Applying a pack reports the parts of an off module as skipped with
  the module message. Clearing sample data keeps the sample rows of an off module and reports
  them under `switched_off_by_type`.

## Scheduled jobs

The scheduled jobs in this table skip an org whose module is off, and a module that comes back on
starts fresh: they do not act on dates that passed while it was off.

| Job | While the module is off | After it is switched on |
| --- | --- | --- |
| Recurring invoices | Nothing is generated or sent. | Every schedule moves to its next date after today. No backlog is billed. |
| Overdue invoices and expired estimates | Not marked. | Invoices past due become Overdue and estimates past expiry become Expired, silently: no webhook, rule or email. |
| Payment reminders | None are sent. | A reminder whose day fell while off is not sent later; the next one in the cadence is sent on its day. |
| Stale-deal alerts (Pipeline) | None are sent. | A deal already stale at switch-on is never alerted. |
| Goal milestone emails (Goals) | None are sent. | Milestones already reached count as announced, so only new ones send. |
| SLA escalation (Tickets) | The scan skips the org. | A deadline that passed while off never escalates. |
| Stale timers (Timesheet) | A running timer is not stopped. | Timers that went stale while off are left running for their owner to stop. |

The clean-up jobs do not check modules. They prune read notifications, automation runs and webhook
delivery logs past their retention, and expired sign-in tokens, whatever an org has switched off.
Webhook deliveries already queued are still sent.

Customer emails already queued (a survey, a portal notice, an invoice, an estimate, a payment
reminder) are dropped if their module is off when they would be sent. Sending a draft invoice or
estimate marks it Sent before the email is queued, so one whose email was dropped this way stays
marked Sent; send it again once Invoices is back on.

## Deleting around an off module

While a module is off its records are out of sight, so a delete that would destroy or be blocked by
them is refused instead. Deleting an account, a ticket or a person answers `409`:

```json
{"error": true, "errors": "This account has 3 tickets. Tickets is switched off, so switch it on to review them before deleting.", "code": "module_off", "module": "tickets"}
```

The message is `<Subject> has N <things>. <Label> is switched off, so switch it on to review
them before deleting.` (`it ... it` for one). The permission check runs first, so a member who may
not delete the record still gets `403`. What can block a delete:

| Deleting | Reaches |
| --- | --- |
| An account | Its tickets, deals, invoices, estimates and recurring invoices |
| A ticket | Its time entries |
| A person (a user's profile in the org) | Their time entries, approvals, watched tickets, saved replies, boards and board memberships |

Unlinking is unchanged: removing a contact from a ticket, or a deal from an invoice, behaves as it
always did. The Django admin site is for operators and is not guarded by modules; deleting a user
there removes the user's profiles and their records.
