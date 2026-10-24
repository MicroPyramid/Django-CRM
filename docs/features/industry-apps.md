# Industry apps

An industry app shapes an organization for one kind of business: the words it uses for leads and
deals, pipelines for leads, tickets and tasks, custom fields, tags, lead sources and products, and,
if you want them, sample records to try things on. Four apps ship with BottleCRM:

| App id | Name | For |
| --- | --- | --- |
| `professional-services` | Professional services | Agencies, consultancies and accounting firms selling billable work. |
| `real-estate` | Real estate | Brokers, agencies and developers selling residential and commercial property. |
| `education-admissions` | Education admissions | Coaching centres, training institutes and colleges managing admissions. |
| `events-weddings` | Events & weddings | Wedding planners, event agencies and venues taking enquiries through to a delivered event. |

Each app is one of the manifests described in [Demo data and packs](../getting-started/demo-data.md),
and its manifest `version` is the app's version. What makes it an app is a record of the install,
kept per organization (`InstalledApp`, table `installed_app`): the version installed, who installed
it and when, what the app created and everything it has ever offered the org.

Only organization admins install, update and remove apps; any member can see which are installed.
On the web, apps are under Settings, then Apps, above the Modules section; the phone has the same
screen. New organizations can pick an app when they are created.

## Install

Installing first shows what the app will do, and does nothing until you confirm:

- **Wording**, such as "Deals called Engagements". An app sets only words the org has not set.
- **Fields, pipelines, tags, sources and products.** Anything the org already has, by name for
  pipelines and tags, by key for fields and sources and by SKU for products, is listed as kept.
  The app does not rename it, change it or add a second one, and it never becomes the app's.
- **Parts of a switched-off module** are listed as skipped: a ticket pipeline while Tickets is off,
  or products while both Pipeline and Invoices are off. See [Modules](../getting-started/modules.md).
- **Sample records.** Offered when the org has no sample records yet, and switched on by default
  only when the org has no real leads, contacts or accounts. Every sample record is marked as one,
  and Clear sample data removes them later.

New pipelines arrive beside the org's own and never become the default, so existing records stay
where they are. Installing never changes or deletes a record.

## Update

An app shows **Update** when updating would add something the org does not have: a part the app
has never offered this org before, or one it skipped for a module that has since been switched
on. A newer version that adds nothing the org lacks shows no Update. An update never changes
anything that exists: no label, option, stage or word is rewritten, an item the org deleted does
not come back, and no sample records come with it.

A stage new to a pipeline the org already has is not added. An update, or installing a removed
app again, names it, so an admin can add it by hand where it fits; a stage like that is not an
update on its own.

## Remove

Removing an app hides what it added and keeps every record:

- its custom fields are switched off, which keeps every value already stored;
- its lead sources and products are made inactive, so pickers stop offering them, while records
  and invoice lines that use them keep them;
- each word it set goes back to the default, unless the org's wording has changed since;
- its pipelines and tags stay, because records live in them and carry them, and sample records stay
  until Clear sample data removes them.

Only what the app created is touched; anything it kept stays as it was. Install the app again and
everything removal switched off comes back on, and its words come back unless another app has set
them since. Anything the org deleted or switched off itself while the app was installed stays that
way.

## Several apps

More than one app can be installed. The first one's wording wins: a later app skips words already
set. When two installed apps offer the same field, source, product or word and the one that added
it is removed, it passes to the other instead of being switched off.

## Organizations that applied a pack before apps

An organization that applied a pack before apps existed has that app installed, at the version it
applied last, by whoever applied it. The app owns what its runs created and the org still has, so
removing it treats those parts as above. If the app now offers something the org lacks, it
shows Update.

## API

Every endpoint takes the org from the signed-in profile, never from the request. An app id is a
key of the catalogue, and anything else answers `404`.

### List the apps

`GET /api/apps/`, any member. The apps in catalogue order, each with this org's state:

```json
{
  "apps": [
    {
      "id": "real-estate",
      "name": "Real estate",
      "description": "Brokers, agencies and developers selling residential and commercial property.",
      "version": 2,
      "status": "installed",
      "installed_version": 2,
      "update_available": false,
      "skipped_modules": ["tickets"],
      "installed_at": "2026-10-24T10:15:00Z",
      "installed_by_details": {"id": "6f1c2d3e-...", "name": "Maria Lopez"}
    }
  ]
}
```

`status` is `not_installed`, `installed` or `removed`. `skipped_modules` lists the modules whose
parts an installed app skipped and has not added since. `update_available` is `true` exactly when
an update would add something, which is when `POST .../upgrade/` does not answer `409`.

### Preview

`GET /api/apps/<id>/preview/?action=install|upgrade|remove`, admins only. Writes nothing.

```json
{
  "action": "install",
  "items": [
    {"type": "wording", "target": "lead", "label": "Leads called Enquiries", "effect": "add"},
    {"type": "pipeline", "target": "lead", "label": "Sales", "effect": "add"},
    {"type": "tag", "target": null, "label": "Hot", "effect": "keep"}
  ],
  "sample_data": {"offered": true, "default_on": true, "records": 58}
}
```

`type` is `wording`, `field`, `pipeline`, `stage`, `tag`, `source` or `product`, and items come in
that order. `target` is the record type the item belongs to (`lead`, `contact`, `account`, `deal`,
`ticket`, `task`, `invoice`), or `null` for tags, sources and products. `effect` is one of:

| Effect | Meaning |
| --- | --- |
| `add` | The action creates it, or sets the word. |
| `keep` | It stays as it is: the org already has it, another installed app still uses it, or (on removal) records live in it. |
| `turn_off` | Removal switches it off. |
| `turn_on` | Installing a removed app switches it back on. |
| `restore_wording` | Removal puts the default word back. |
| `skipped_module` | Its module is off, so the action skips it. |
| `add_by_hand` | A stage new to a pipeline the org has; the update does not add it. |

`sample_data` says whether sample records are offered, whether they are on by default and how many
the app would create. An update or removal never offers them.

### Install, update, remove

| Endpoint | Body | Refused with `409` when |
| --- | --- | --- |
| `POST /api/apps/<id>/install/` | `{"sample_data": true}`; without it, the preview's default | the app is installed |
| `POST /api/apps/<id>/upgrade/` | none | the app is not installed, or an update would add nothing |
| `POST /api/apps/<id>/remove/` | none | the app is not installed |

Each answers `200` with `{"app": ...}`, the app as the list shows it. A member gets `403`, an
unknown id `404`, and a `sample_data` that is not a boolean `400`. Installing a removed app
installs it again. Install and update each write a pack application record, and all three write a
security audit row (`APP_INSTALLED`, `APP_UPGRADED`, `APP_REMOVED`; see
[Security audit log](../api/audit-log.md#app-changes)).

`POST /api/packs/<id>/apply/` installs the app with sample records and answers with the run's
report, as it did before apps. On an installed app it adds nothing and answers an empty report.
`GET /api/packs/` still lists the catalogue for the organization creation page.

The code is `backend/common/apps_catalogue.py` (the actions), `backend/common/packs/planner.py`
(the preview) and `backend/common/packs/applier.py` (what creates each part).
