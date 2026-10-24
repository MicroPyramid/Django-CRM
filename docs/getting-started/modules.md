# Modules

Not every team uses every part of BottleCRM. An organization admin can switch whole parts off, so
the people in the org see only what they work with. There are nine modules: Pipeline, Leads,
Goals, Tasks, Tickets, Knowledge base, Documents, Invoices and Timesheet. Some orgs rename
Pipeline, Leads or Invoices; you see the org's own names throughout.

This page is for admins. The API behind it is in [Modules (API)](../api/modules.md).

## Switching a module off or on

Only admins see Modules in the apps. On the web, open Settings, then Apps (`/settings/apps`),
where Modules sits below the industry apps; the settings hub lists Apps after Organization, and
the old `/settings/modules` address redirects there. On the phone, open organization settings,
then Apps, where Modules also sits below the industry apps; the row shows for admins only, and is
named Modules on a server without industry apps. Any member can read the list through the API;
only admins can change it.

The modules are grouped as Sell, Serve and Bill. Each row shows what the module covers and whether
it is on: the web shows an On or Off label, and the phone a switch.

- **Switch off** asks you to confirm first, and the confirmation says what switching it off stops.
  On the phone, turning the switch off asks the same.
- **Switch on** takes effect at once.
- **Up and down arrows** move a module within its group.
- While the module a row needs is off, the row says "Needs" followed by that module's name, and
  the module cannot be switched on until the need is back on.
- A refused switch-off lists what to clear, with links to Web forms and Inbound email.

The order is the order of the web sidebar and of the phone's More screen. In Sell, Today stays
first and Accounts and Contacts stay last. On the phone, the bottom bar shows the first three
switched-on modules of Leads, Pipeline, Tickets and Tasks. In a browser as narrow as a phone, the
web's bottom bar shows Today and the first three switched-on modules of Pipeline, Tickets,
Invoices, Leads and Tasks. Its floating button starts a new deal, ticket, lead or task: the first
of those whose module is on.

The same settings are available through the API: read the list with `GET /api/org/modules/` and
change it with `PUT /api/org/modules/`, as [Modules (API)](../api/modules.md#change-the-setting)
describes.

**Off means off for everyone in the org.** The module leaves search and Today, and its API routes
answer as if they did not exist; the web and phone apps take it out of their menus. Its pages say
that the module is switched off for the organization, and admins get a link to Modules. Links you
sent to customers (an invoice, a survey, a help center article) stop opening, the customer portal
stops showing it, and its reminders and emails stop. A web form, an inbound mailbox or an
automation rule that works with the module stops working with it.

**Nothing is deleted.** The records are exactly where you left them. Switch the module back on and
everything is there again, in the same state.

## Needs

Two modules depend on another:

- **Goals needs Pipeline.** With Pipeline off, Goals is unavailable too, although its own switch
  keeps the setting you gave it.
- **Timesheet needs Tickets.** The same applies with Tickets off.

You cannot switch a module on while the one it needs is off. Switch the needed module on first.

## When a switch is refused

A switch-off is refused when it would lose something that is still arriving. The message says what
to clear:

- **Published web forms.** Leads, or Tickets, still receives submissions from a published web
  form. Unpublish the form first, so no submission is lost. This also covers the website lead key
  the older embed used, once it has been used.
- **Active inbound mailboxes.** Tickets still receives email at a ticket address, or Leads at a
  lead address. Switch that mailbox off first, so no email is lost. Switching Tickets off also
  takes Timesheet with it, so it is refused for these reasons too.

Reordering the modules is never refused, even while one is off.

While a module is off, a few things are held back so nothing is lost by accident:

- You cannot publish a web form, create one, or point one at a module that is off.
- You cannot delete an account, a ticket or a person that still has records in an off module. The
  message names the count, for example "This account has 3 tickets", and asks you to switch the
  module on and review them first.
- An automation rule on an off module shows as Paused, and does not run. You can still switch it
  on, but you cannot change what it does until the module is back.
- While Tasks is off, an automation rule cannot gain a Create a task step. A step it already has
  is kept, and skipped when the rule runs.
- A webhook keeps the events it already had for the module; you cannot add one for it.
- Clearing sample data leaves the sample rows of an off module alone and tells you how many.

## Starting fresh

Switching a module back on does not make it catch up. Dates that passed while it was off are not
acted on:

- Recurring invoices move to their next date after today. Nothing from the weeks it was off is
  billed.
- Invoices past their due date become Overdue, and estimates past their expiry become Expired,
  quietly: no email, no automation and no webhook.
- A payment reminder whose day fell while Invoices was off is not sent later; the next reminder is
  sent on its normal day.
- Ticket deadlines that passed while Tickets was off do not escalate.
- A deal that was already stale when Pipeline came back is not reported as stale, and goal
  milestones already reached do not email anyone.
- Customer emails that were waiting while their module was off are dropped. An invoice or estimate
  whose email was dropped stays marked Sent, so send it again.

A running timer that went stale while Timesheet was off stays running, so its owner can stop it.

## Every change is logged

Switching a module off or on, or reordering them, is recorded in the
[security audit log](../api/audit-log.md) as Modules Changed, with who did it and what changed.
