# Management commands

Every command below is BottleCRM's own. The entire `common/management/commands/` package holds
exactly these five files. Run `uv run python manage.py help` from `backend/` and everything
outside the `[common]` section comes from Django itself or an installed third-party package
(`django`, `auth`, `contenttypes`, `sessions`, `staticfiles`, `django_ses`, `drf_spectacular`,
`rest_framework`, `token_blacklist`), none of it is project-specific, so it isn't repeated here.
Run any command from `backend/` with `uv run python manage.py <command>` (or, against the Docker
stack, `docker compose exec backend python manage.py <command>`).

## manage_rls

Read-only diagnostics for Row-Level Security. None of its three flags modify the database. RLS
policies are enabled and disabled by Django migrations, calling `get_enable_policy_sql()`, never by
this command (the module's own docstring says so explicitly). It checks the tables listed in
`ORG_SCOPED_TABLES` (`common/rls/__init__.py`), which as of this writing has **61 entries**. The
repository's `CLAUDE.md` still says 24; that figure is out of date, and the count is deliberately
not repeated anywhere outside `ORG_SCOPED_TABLES` itself so it cannot drift again.

```bash
uv run python manage.py manage_rls --status
uv run python manage.py manage_rls --test
uv run python manage.py manage_rls --verify-user
```

| Flag | What it does |
| --- | --- |
| `--status` | For every table in `ORG_SCOPED_TABLES`, queries `pg_class.relrowsecurity`/`relforcerowsecurity` and prints `ENABLED (forced)`, `disabled`, or `TABLE NOT FOUND`, plus whether the connected role is a superuser. This is also the **default**, running `manage_rls` with no flags at all runs `--status`. |
| `--test` | Picks two organizations (preferring ones that actually have `Lead` rows), sets the RLS context to each in turn and counts visible leads, then sets an empty context and counts again. Zero rows with no context and nonzero with a real context means isolation is working; nonzero rows with no context is a warning, not a failure, since some policies deliberately allow an empty context. |
| `--verify-user` | Queries `pg_user` for `usesuper`/`usecreatedb` on the connected role and prints an explicit `WARNING: Superusers bypass RLS!` with remediation SQL if the role is a superuser. |

This only covers what the command itself does. For why a superuser role defeats every policy
silently, how to create a correctly-restricted role, and what each flag's output actually proves,
see [PostgreSQL and RLS](../self-hosting/postgresql-and-rls.md#verifying-isolation).

## seed_data

Generates a large, randomized dataset, accounts, contacts, leads, opportunities, cases, tasks,
invoices and more, for one or more organizations, entirely from curated fictional name/company
pools and reserved demo domains (`example.com`/`.example`) so nothing it creates resembles a real
person or business. The first organization created (`--orgs` index 0) is always named
`MicroPyramid`, specifically so local-dev workflows have a stable org name to sign in against with
`devlogin --org MicroPyramid` (see below). For the default, single-org run, re-running the command
with the same `--email` reuses that existing user, org, and profile rather than creating duplicates;
`create_org` does an `Org.objects.get_or_create(name="MicroPyramid", ...)`. That reuse guarantee
is specific to index 0: any organization beyond the first (`--orgs 2` or higher) gets a name drawn
randomly from a company-name pool each run, so re-running with `--orgs 2` typically accumulates
additional organizations rather than reusing the second one from the previous run.

```bash
uv run python manage.py seed_data --email you@example.com
uv run python manage.py seed_data --email you@example.com --orgs 2 --leads 100 --seed 42
uv run python manage.py seed_data --email you@example.com --clear --no-input
```

| Flag | Default | What it does |
| --- | --- | --- |
| `--email` | `aswin.1231@gmail.com` | Email of the admin user to create (or reuse) as the seeded org's admin profile. |
| `--orgs` | `1` | Number of organizations to create. |
| `--users-per-org` | `3` | Additional non-admin users created per org. |
| `--leads` | `20` | Leads per org. |
| `--accounts` | `10` | Accounts per org. |
| `--contacts` | `15` | Contacts per org. |
| `--opportunities` | `10` | Opportunities per org. |
| `--cases` | `5` | Cases per org. |
| `--tasks` | `10` | Tasks per org. |
| `--goals` | `8` | Sales goals per org. |
| `--teams` | `2` | Teams per org. |
| `--tags` | `5` | Tags per org. |
| `--products` | `20` | Products per org. |
| `--invoices` | `50` | Invoices per org. |
| `--estimates` | `15` | Estimates per org. |
| `--recurring-invoices` | `5` | Recurring invoices per org. |
| `--invoice-templates` | `3` | Invoice templates per org. |
| `--currency` | `USD` | Default org currency; restricted to `CURRENCY_CODES` choices. |
| `--country` | `US` | Default org country code; also selects the Faker locale used for generated names/addresses (falls back to `en_US` for an unmapped code). |
| `--seed` | none | Random seed, for a reproducible run. |
| `--password` | `testpass123` | Password set on newly created users. |
| `--clear` | off (flag) | Deletes existing CRM data before seeding, **not** users, orgs, or profiles. Prompts for confirmation unless `--no-input` is also given. This is a separate, broader operation from a vertical pack's own sample-data clearing (see [Demo data and packs](../getting-started/demo-data.md#clearing-sample-data)) and isn't scoped to pack-created records specifically. |
| `--no-input` | off (flag) | Skips the `--clear` confirmation prompt. |

See [Demo data and packs](../getting-started/demo-data.md) for the narrative walkthrough, including
what a full seeded org looks like and how vertical packs layer on top of it.

## devlogin

Mints a JWT access/refresh pair for an existing user directly from the command line, no OAuth
provider, no outbound email, no browser round-trip. **Refuses to run unless `settings.DEBUG` is
`True`**, raising a `CommandError` as the very first thing `handle()` does. That means it prints an
error and exits non-zero in any environment where `DEBUG=False`, not that it silently does nothing.

```bash
uv run python manage.py devlogin <email> --org <name-or-uuid>
uv run python manage.py devlogin <email> --create
```

| Argument | What it does |
| --- | --- |
| `email` (positional, required) | The user to mint a token for. |
| `--org` | Optional org name or UUID. **Resolves id first, then name**: it tries `Org.objects.get(id=org_arg)` first, and only falls back to matching on `Org.name` if that lookup fails (not found, or `org_arg` isn't a valid UUID at all). More than one org sharing that name is refused outright rather than guessed at, pass an id instead. The target user must already have an **active** `Profile` in the resolved org. This command does not create one, and raises a `CommandError` naming the missing user/org pair if none exists. |
| `--create` | Creates the user (with a random, discarded password) if no user with that email exists yet. This only creates the `User` row. It has no effect on the `Profile` requirement above; a freshly created user still needs a `Profile` in the target org before `--org` will succeed for them. |

On success it prints an access token and a refresh token, the org's UUID if `--org` was given (a
token minted this way already carries the `org_id` claim, so no follow-up org-switch call is
needed), and a `localStorage.setItem(...)` snippet for a browser console. That snippet alone does
**not** sign you into the SvelteKit app itself; see
[Using the tokens in the browser](../getting-started/first-sign-in.md#using-the-tokens-in-the-browser)
for the cookies `hooks.server.js` actually checks. See
[First sign-in: Local development](../getting-started/first-sign-in.md#local-development-devlogin)
for the full walkthrough, including what happens with no `--org` at all.

## create_default_admin

Creates a Django superuser, but only if none already exists; `User.objects.filter(is_superuser=
True).exists()` short-circuits the whole command to a no-op if one is found, so it's safe to run on
every startup. It takes no arguments at all (no `add_arguments` override). It reads `ADMIN_EMAIL`
and `ADMIN_PASSWORD` directly with `os.environ.get`, independently of `crm/settings.py` (`ADMIN_EMAIL`
happens to share a name and a default with the copy `settings.py` also reads; `ADMIN_PASSWORD` is
read nowhere else). **If `ADMIN_PASSWORD` is unset or empty, the command falls back to the literal
password `admin`** and prints a warning. It does not refuse to create the account. This command
runs automatically on every Docker container start (`docker/backend/entrypoint.sh`, immediately
after `migrate`), so in the Docker quick start it never needs to be invoked directly, and an unset
`ADMIN_PASSWORD` in a real deployment means the bootstrap superuser's password really is `admin`
until it's changed by hand.

```bash
uv run python manage.py create_default_admin
```

## audit_org_fields

A one-time Phase 1 multi-tenancy hardening tool, not a general or self-updating auditor: it checks
a **hardcoded** pair of Python lists inside the command itself, `models_with_nullable_org`
(currently just `common.Address` and `common.Tags`) and `models_with_required_org` (thirteen named
models), not every org-scoped model that exists today. A model added to the codebase since this
command was last edited is invisible to it either way.

```bash
uv run python manage.py audit_org_fields
uv run python manage.py audit_org_fields --fix
uv run python manage.py audit_org_fields --verbose
```

The audit always runs; there is no way to suppress it short of not invoking the command. A
`--check` flag used to be accepted by the parser and never read in `handle()`, so passing it or
omitting it produced identical output; it has been removed rather than left as a flag that means
nothing.

| Flag | What it does |
| --- | --- |
| `--fix` | For `common.Address` rows with a null `org`, attempts to backfill it from a related `Profile`. For `common.Tags`, `--fix` does **not** fix anything. It prints a message asking for manual review instead. For any other model that turns up with a null `org`, it also just prints "Automatic fix not implemented." |
| `--verbose` | Two effects, one per pass: in the nullable-org pass it prints each model's field configuration (`null`, `blank`, `related_query_name`); in the required-org pass it's what makes a "Model not found" warning print at all. Without `--verbose`, a `LookupError` there is swallowed silently. |

Output uses ✅/❌/⚠️ markers per model and ends with a summary and a suggested next-steps block
(create a migration, run `makemigrations`/`migrate`): it never modifies the schema itself, only
data, and only when `--fix` is passed.
