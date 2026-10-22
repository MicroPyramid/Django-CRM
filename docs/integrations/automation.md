# Automation rules

An automation rule tells BottleCRM "when this happens to a record, and these things are true, do
that". When a deal is won, create a kick-off task for its assignees and tell the account's team.
When a lead arrives from a web form, assign it to the next person in a rotation. Everything lives
in `backend/automation/`, and rules are managed through the API at `/api/automation/`.

## Who can use them

Only org admins can build, read, change, try or delete rules, and that includes reading the list
and the run history: runs name records and people a member may not be allowed to see. A member
gets `403` on every route.

Rules are managed from a signed-in session only. `/api/automation/` is on the credential deny-list
in `backend/common/scopes.py`, so a personal access token or the org API key is refused there
whatever scopes it carries. A rule keeps acting after the token that wrote it is revoked, which
makes creating one the same kind of act as creating a webhook.

## What a rule is

A rule reads as a sentence: **When** (the trigger), **Only if** (the conditions), **Then** (the
actions).

| Part | Meaning |
| --- | --- |
| `name` | What the rule is called in lists, notices and the activity feed. |
| `object_key` | The kind of record it watches: `lead`, `contact`, `account`, `deal`, `ticket` or `task`. |
| `trigger` | What sets it off: `{"event", "field", "to"}`. See [Triggers](#triggers). |
| `match` | `all` (every condition holds) or `any` (at least one does). One level, no groups. |
| `conditions` | Up to 20 `{"field", "op", "value"}` checks. An empty list always holds. |
| `actions` | Up to 10 actions, run in order. See [Actions](#actions). |
| `is_active` | Whether the rule is switched on. |
| `position` | Its place in the list. Rules on the same change run in list order. |
| `owner` | The admin who last switched it on. The rule acts as this person. Read only. |

Rules are checked against what the org offers when they are saved and again before every run, so a
rule cannot set a field or an option its record's edit form would refuse, and cannot name a person,
webhook endpoint or link outside its org. An invalid rule is refused with a `400` whose errors are
keyed by path, so an editor can mark the row:

```json
{
  "errors": {
    "conditions[2].value": ["Enter a number."],
    "actions[0].people": ["Each person must be an active member of this org."]
  }
}
```

A rule that was valid and later breaks (its field was switched off, an option was removed, its
person was deactivated) stays saved and switched on. Its runs fail with the reason, the list shows
it as **Needs attention**, and saving or switching it on again checks it afresh. Renaming it or
switching it off always works, so a broken rule can be put aside.

Every id in a rule is a canonical UUID string: lowercase and hyphenated, as the API returns ids.

## Fields

`GET /api/automation/catalogue/` lists, for each object, the fields rules may read, their type,
their choices, and whether a rule may set them. Editors are built from it alone. The catalogue
never contains server-owned fields: `org`, ids, `created_by`, `updated_by`, timestamps,
`is_active`, tokens, or anything the object's serializer treats as read only. A field is settable
exactly when the object's own edit form writes it.

| Object | Fields |
| --- | --- |
| Lead | title, first and last name, email, phone, company, job title, website, city, country, status, source, industry, rating, stage (read only), estimated value, probability, expected close date, next follow-up, assigned to |
| Contact | first and last name, email, phone, company, job title, department, city, country, do not call, assigned to |
| Account | name, email, phone, website, city, country, industry, employees, annual revenue, assigned to |
| Deal | name, stage, outcome (read only), type, source, amount, probability, close date, assigned to |
| Ticket | subject, status, priority, type, closed on, assigned to |
| Task | title, status, priority, due date, assigned to |

The org's active custom fields of types text, textarea, number, date, dropdown and checkbox are
appended to their object as `custom_fields.<key>`. An object an installed app adds to the object
registry (`common.object_registry.register_hook`) appears in the catalogue when its entry offers an
automation adapter.

A few fields behave specially:

- **Deal stage** takes a stage id and lists every pipeline's stages, grouped by pipeline. A rule
  can only move a deal to a stage of the deal's own pipeline.
- **Deal outcome** (`stage_kind`) is `open`, `won` or `lost`, read from the deal's stage kind, so
  "outcome changes to won" fires for a win in any pipeline, whatever the stage is called. It is
  read only.
- **Lead status** offers `converted` to read but not to set: converting a lead creates an account,
  a contact and a deal, and is never an edit. **Ticket status** treats `Duplicate` the same way,
  since only a merge sets it.
- **Assigned to** is a `people` field: a list of profile ids. It can be read and set, but a change
  of people cannot be a trigger.

Values compare by type: text and choices as strings, numbers as decimals, dates as `YYYY-MM-DD`,
true/false as booleans, people as lists of ids. Text comparison with `contains` ignores case.

### Parents and links

Actions can reach the record's one parent as well as the record itself:

| Object | Parent |
| --- | --- |
| Deal | its account |
| Ticket | its account |
| Task | the lead, account, deal or ticket it belongs to |
| Lead, contact, account | none |

An app that adds its own objects can also offer links to other records through
`automation.links.register_link_hook`; the catalogue lists them under each object's `links`. The
community edition ships no link hook.

## Triggers

| Trigger | JSON | Fires when |
| --- | --- | --- |
| Created | `{"event": "created", "field": null, "to": null}` | A record of the object is created. |
| Updated | `{"event": "updated", "field": null, "to": null}` | Any catalogue field of the record changed. |
| A field changes | `{"event": "updated", "field": "status", "to": null}` | That field changed, to anything. |
| A field changes to a value | `{"event": "updated", "field": "stage_kind", "to": "won"}` | That field moved into the value. |

"Changes to" fires only on the move into the value: the old value differed and the new one matches.
Later edits to a won deal do not run "outcome changes to won" again. With the chain rules in
[How a run happens](#how-a-run-happens), this is what stops a rule from setting itself off.

### What sets a rule off

Any save made through the app counts: the web and phone apps, the REST API and access tokens, a
card moved to another column on a board, a public web form submission, an emailed ticket, and saves
made by Celery tasks. Web forms and inbound email are where most new leads and tickets come from, so
a "created" rule fires on them even though nobody is signed in.

Rules run as the request finishes, after the view has saved everything and attached assignees and
tags, and before the reply goes back. So the page that reloads after a save already shows what the
rules did, and a condition such as "assigned to is not empty" sees assignees set in the same save.
Ticket routing runs first, while the ticket is created, so a "ticket created" rule sees the routed
assignees. Outside a request (a Celery task, a management command) the rules run when the change is
committed, in the process that saved it.

A record saved twice in one request is one change: a create followed by updates stays a create, and
two updates keep the first old value and the last new one. A change that was rolled back sets
nothing off.

### What does not set rules off

- **Spreadsheet imports** of leads, contacts and tickets, and **industry pack sample data** as the
  pack creates it (a later edit of a sample record counts like any other save). A 2,000-row import
  with an active "lead created: create a task" rule creates no tasks.
- **The `seed_data` management command**, which fills an org with demo records.
- **Bulk ticket edits** (`POST /api/cases/bulk/update/`). Closing 200 tickets at once runs no rules.
- **Bulk database operations that skip save signals**: queryset `update()`, `bulk_create()` and
  `bulk_update()`, such as the moves inside a ticket merge or unmerge, and the renumbering of a
  board column's other cards when one is dropped between them. Webhooks do not see them either.
- **Changes to many-to-many fields** (assignees, tags, teams) as triggers. Conditions can still read
  them.
- **Deleting a record.** Deletes are not a trigger; webhooks cover them.

## Conditions

Each condition is `{"field", "op", "value"}`. The operators a field takes depend on its type:

| Type | Operators |
| --- | --- |
| Text | `eq`, `neq`, `contains`, `not_contains`, `empty`, `not_empty` |
| Number | `eq`, `neq`, `gt`, `lt`, `empty`, `not_empty` |
| Date | `eq`, `neq`, `gt` (after), `lt` (before), `empty`, `not_empty` |
| Choice | `eq`, `neq`, `in`, `not_in`, `empty`, `not_empty` |
| True/false | `true`, `false` |
| Person, people | `eq`, `includes`, `excludes`, `empty`, `not_empty` |

- `empty`, `not_empty`, `true` and `false` take `"value": null`. An empty true/false field counts as
  false.
- `in` and `not_in` take a list of options. Dates take `YYYY-MM-DD`; relative dates ("in the next 7
  days") are not offered.
- `includes` and `excludes` take one profile id; `eq` on people takes a list and compares the whole
  set.
- `was` and `was_not` compare the value from **before** this save, on any field type except people,
  and only for an `updated` trigger. On a field the save did not change they read its current
  value.
- There is no pattern or regular expression operator. Tenant text is only ever compared, never
  evaluated.

Conditions read the record as it is when the rule runs, after the request has finished.

## Actions

Each action is planned first (which records and people it reaches, whether its values still fit)
and then applied. A rule's actions run in order inside one transaction, so a later action sees what
an earlier one did: assign someone, then notify the record's assignees, and the notice reaches the
new assignee.

`{name}` is the only placeholder, in task titles and notify messages. It is replaced by the
record's display name as plain text; nothing a tenant writes is rendered as a template, markdown or
HTML, so a record named `<img onerror=...>` shows as those characters.

### Set a field

```json
{"type": "set_field", "target": "record", "field": "probability", "value": 90}
```

`target` is `record`, `parent`, or a link id from the catalogue. `value: null` clears the field. A
people field takes a list of profile ids.

The write goes through the object's own edit path, as a partial update made by the rule's owner, so
it passes exactly the checks the edit form applies. A deal moved to a won stage still needs an
amount and a close date; a lead cannot be converted; a ticket's close and approval rules hold. A
refusal fails the step with the form's own message. Behaviour only the board has (filling a deal's
close date and probability, or a lead's status from its stage, when a card is dragged) is not
copied. A target with no parent (a deal with no account) is a skipped step, not a failure.

### Assign

```json
{"type": "assign", "people": ["<profile id>", "<profile id>"], "mode": "rotate"}
```

`replace` takes exactly one person; `rotate` takes 2 to 20 and gives each record to the next person
in turn, skipping anyone no longer active. Either way the record's current assignees are
**replaced**. The rotation's place is kept per action, so two rotating actions do not share a turn.
Newly assigned people get the module's usual assignment email.

### Create a task

```json
{
  "type": "create_task",
  "title": "Kick-off call: {name}",
  "due_in_days": 2,
  "priority": "High",
  "assign_to": "record",
  "person": null
}
```

- `title`: 1 to 200 characters, cut to fit once `{name}` is filled in.
- `due_in_days`: `null` for no due date, or 0 to 365 days from today in the org's timezone.
- `priority`: `Low`, `Medium` or `High`.
- `assign_to`: `record` (the record's assignees), `parent` (the parent's assignees), `owner` (the
  rule's owner), or `person` with that profile's id in `person`.

The task goes through the task API's own create path as the rule's owner. It links to the record
where a task can (a lead, account, deal or ticket, and a contact through its contacts); otherwise its
description carries a link to the record.

### Notify

```json
{
  "type": "notify",
  "to": ["record_assignees", "parent_assignees"],
  "people": [],
  "message": "{name} is won. Time to say hello."
}
```

`to` takes any of `record_assignees`, `record_creator`, `parent_assignees`, `admins`, and
`linked:<link id>` for the assignees of linked records. `people` adds chosen profiles. At least one
of the two must name someone. `message` is 1 to 500 characters.

Each recipient gets an in-app notification (verb `automation.message`, with the text in its
`data`) and an email carrying the message and a link to the record. Only active members of the org
are ever reached; there is no way to send to an outside address, and one is refused when the rule is
saved.

### Send a webhook

```json
{"type": "webhook", "endpoint": "<webhook endpoint id>"}
```

The endpoint must be one of the org's own active webhooks with the **Signed JSON** format. The
delivery goes through the [webhook](webhooks.md) path, so signing, the URL rules, retries and the
delivery log are the same. Its event is `rule.triggered`, sent to the chosen endpoint whatever
events it subscribes to:

```json
{
  "id": "4b0f7e0c-8f0e-4b8e-9d0f-2f4d6c1a9e11",
  "event": "rule.triggered",
  "created_at": "2026-10-22T10:15:02.114Z",
  "org_id": "a3f1c2d4-0000-4000-8000-000000000001",
  "data": {
    "rule": {"id": "9c2e...", "name": "Deal won: onboarding"},
    "object": "deal",
    "record": {"id": "0d6f...", "name": "Acme renewal", "stage": "CLOSED_WON", "...": "..."}
  }
}
```

`record` is the same payload the object's own webhook events carry.

### Nobody learns about a record they cannot open

Notify and "create a task" reach only people who can open the record, checked with that object's
read rule. Deals and leads are often private to their assignees, so "the account's assignees" may
not all be allowed to see the deal. Anyone filtered out is named in the step ("Skipped Meera: cannot
open this deal"); when nobody is left the step is skipped, not failed. Admins can open everything.

## How a run happens

- **Order.** For each change, every matching switched-on rule of the org on that object runs, in
  list order. There is no "stop here".
- **One rule, one transaction.** If any of a rule's steps fails, that rule's writes roll back, the
  run is recorded as failed with the step's reason, and the next rule still runs. Emails and
  webhooks are sent only once the rule's transaction commits. A broken rule never blocks or undoes
  the save that set it off.
- **Who it acts as.** The rule's owner. Records it creates and fields it sets are credited to the
  owner, not to whoever saved the record (and not left blank on an anonymous web form), and the
  activity feed notes the rule's name beside the change.
- **Chains.** A rule's own writes are changes too and can set off other rules, up to 3 deep. A rule
  acts on a given record at most once per chain, so two rules that undo each other stop. A rule
  never runs on a change its own run made, so a "task created: create a task" rule adds one task.
  A run set off by another rule's write shows which run caused it.
- **Owners who lose their rights.** When a rule's owner stops being an admin, is deactivated, leaves
  the org or is deleted, their active rules are switched off with a reason and the other admins are
  told. Another admin takes a rule over by switching it on again, which makes them its owner.
- **Failures reach a person.** When a run fails, the rule's owner gets an in-app notice, at most
  once a day per rule.

Rules do not need the Celery worker to run. Their emails and webhook deliveries do, as elsewhere in
the app; see [Email and Celery](../self-hosting/email-and-celery.md).

## Limits

The same on every install:

| Limit | Value |
| --- | --- |
| Conditions per rule | 20 |
| Actions per rule | 10 |
| Records one action may touch | 100 (more fails the step rather than doing part of it) |
| Chain depth | 3 |
| Runs per org per hour | 1,000 |
| Run history | 30 days |

Runs past the hourly limit do not run and are not stored one row each: each rule gets one skipped
run per hour that counts them ("312 runs skipped: the org reached its hourly limit"), and the org's
admins get one notice for that hour. So a flood of form submissions cannot grow the run table past
the limit.

## Runs

Each run records the record it ran on (with its name at the time, so the history reads well after a
rename), its status, its reason, and one step per action.

| Run status | Meaning |
| --- | --- |
| `done` | Every step was done or skipped. |
| `failed` | A step failed, or the rule no longer validated, and nothing it wrote was kept; or an email it sent could not be delivered. |
| `skipped` | Counted past the hourly limit; `skipped_count` says how many. |

| Step status | Meaning |
| --- | --- |
| `done` | The step's change stands. |
| `undone` | The step was applied, then rolled back with its failed rule. |
| `failed` | The step could not be done; its text says why. |
| `skipped` | There was nothing to do, for example nobody left to notify. |

Runs older than 30 days are deleted by a Celery task queued as new runs are written, at most once a
day per org, and by the daily beat job `automation.tasks.prune_runs` where beat runs.

Rules send these in-app notifications, each with its text in `data`:

| Verb | Sent to | `data` |
| --- | --- | --- |
| `automation.message` | a notify action's recipients | `message`, `rule` |
| `automation.failed` | the rule's owner, at most once a day per rule | `rule`, `rule_id`, `reason` |
| `automation.paused` | the org's other admins | `rules`, `reason` |
| `automation.limit` | the org's admins, once per hour | `window_start` |

## Trying a rule

`POST /api/automation/rules/<id>/try/` with `{"record_id": "<id>"}` runs only the planning half of
each action against one record of the rule's object and answers what a run would do. It never
writes: the record, its links, notifications, tasks and the rotation's place are left as they were.

```json
{
  "steps": [
    {"action": 0, "type": "create_task", "status": "planned",
     "text": "Would create the task 'Kick-off call: Acme renewal' for Asha and Ravi"},
    {"action": 1, "type": "notify", "status": "planned",
     "text": "Would notify Ravi. Skipped Meera: cannot open this deal"}
  ]
}
```

A record of another object or another org answers `404`. A rule nobody has switched on yet is
planned as the admin trying it. A rule that no longer validates answers each step as `failed`, with
the reason.

## API

All under `/api/automation/`, admin only, from a signed-in session:

| Method and path | Does |
| --- | --- |
| `GET catalogue/` | objects with their fields, parents and links; operators; action types; the org's active members; its Signed JSON webhooks; the condition and action limits |
| `GET rules/` | the org's rules, each with `status`, `status_text`, `runs_7d` and `failures_7d` |
| `POST rules/` | create, at the end of the list |
| `GET rules/<id>/` | one rule |
| `PATCH rules/<id>/` | change it (there is no `PUT`) |
| `DELETE rules/<id>/` | delete it and its runs |
| `POST rules/<id>/try/` | the steps a run would take on one record, writing nothing |
| `GET rules/<id>/runs/` | its runs, newest first, `limit`/`offset` paginated |
| `POST rules/reorder/` | a new list order: `{"ids": [...]}`; rules not named keep their order after the named ones |

Another org's id answers `404`.

Switching a rule on is a create or `PATCH` with `"is_active": true` on a rule that is off or
paused. It makes the caller the rule's owner and clears any paused reason. Editing a rule that is
already on keeps its owner. An installation can register a plan hook
(`automation.plan.register_plan_hook`) that refuses switching a rule on with `403` and
`"code": "plan_limit"`, or reports some switched-on rules as not running (status `over_limit`) with a
`summary` line on the list. The community edition registers none: every rule may be switched on and
every switched-on rule runs.

The list's `status` is `on`, `off`, `paused` (with the reason as `status_text`), `needs_attention`
(with the first problem), or `over_limit` when a plan hook says so.

The headline example, created and switched on in one request:

```json
{
  "name": "Deal won: onboarding",
  "object_key": "deal",
  "trigger": {"event": "updated", "field": "stage_kind", "to": "won"},
  "match": "all",
  "conditions": [{"field": "amount", "op": "gt", "value": 0}],
  "actions": [
    {
      "type": "create_task",
      "title": "Kick-off call: {name}",
      "due_in_days": 2,
      "priority": "High",
      "assign_to": "record",
      "person": null
    },
    {
      "type": "notify",
      "to": ["parent_assignees"],
      "people": [],
      "message": "{name} is won. Time to say hello."
    }
  ],
  "is_active": true
}
```

A run, as `GET rules/<id>/runs/` returns it:

```json
{
  "count": 1,
  "results": [
    {
      "id": "7a51...",
      "created_at": "2026-10-22T10:15:02.114Z",
      "record_id": "0d6f...",
      "record_name": "Acme renewal",
      "object_key": "deal",
      "status": "done",
      "reason": "",
      "steps": [
        {"action": 0, "type": "create_task", "status": "done",
         "text": "Created the task 'Kick-off call: Acme renewal' for Asha and Ravi"},
        {"action": 1, "type": "notify", "status": "done",
         "text": "Notified Ravi. Skipped Meera: cannot open this deal"}
      ],
      "skipped_count": 0,
      "depth": 1,
      "triggered_by": null
    }
  ]
}
```
