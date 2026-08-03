# Python sample

## What this does

A complete, runnable script that talks to the BottleCRM REST API from plain Python: it obtains an
access token, lists the org's leads, and creates one.

"Obtains a token" here means reading a **personal access token** (`bcrm_pat_…`) from the
environment, rather than driving one of the interactive sign-in flows on
[Authentication](../api/authentication.md). A PAT is what BottleCRM issues specifically so a script
doesn't need a browser, an OAuth client secret, or a magic-link email round trip just to make API
calls. See [Tokens and API keys](../api/tokens-and-api-keys.md#personal-access-tokens) for how it
authenticates and what it inherits. There are two ways to mint one, and which applies depends on
your role: an **admin** can do it from the CRM's **Settings → API tokens** page
(`/settings/api-tokens`). That page is admin-only (it lists every token in the org, not just your
own), so a non-admin who opens it sees "Admins only" and never reaches the create form. **Any
role** can instead call `POST /api/profile/tokens/` directly, the same self-service endpoint the
settings page's own create form posts to, which is the option to use if you aren't an admin, or
you just want a token without the UI. For a local backend you're running yourself, the fastest way
is the Django shell:

```bash
cd backend
uv run python manage.py shell -c "
from common.models import Profile, PersonalAccessToken
p = Profile.objects.filter(role='ADMIN', is_active=True).first()
print(PersonalAccessToken.generate(p, 'python-sample')[0])
"
```

This prints the raw `bcrm_pat_…` token once, copy it, there's no way to retrieve it again later.

## The script

```python
#!/usr/bin/env python3
"""List an org's leads and create one, using a BottleCRM personal access token.

Usage:
    BCRM_BASE_URL=http://localhost:8000 BCRM_TOKEN=bcrm_pat_... python leads_sample.py

See docs/api/tokens-and-api-keys.md for how to mint BCRM_TOKEN, and
docs/api/leads.md for the shape of the /api/leads/ responses this script reads.
"""

import os
import sys
import time

import requests

BASE_URL = os.environ.get("BCRM_BASE_URL", "http://localhost:8000").rstrip("/")
TOKEN = os.environ.get("BCRM_TOKEN")

if not TOKEN:
    sys.exit(
        "Set BCRM_TOKEN to a bcrm_pat_... personal access token "
        "(see docs/api/tokens-and-api-keys.md)."
    )

session = requests.Session()
session.headers.update(
    {
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/json",
    }
)


def list_leads():
    """GET /api/leads/, the response splits leads into open/closed sections
    rather than one flat list; see docs/api/leads.md#list-leads."""
    resp = session.get(f"{BASE_URL}/api/leads/")
    resp.raise_for_status()
    data = resp.json()
    open_section = data["open_leads"]
    leads = open_section["open_leads"]
    print(
        f"{len(leads)} open lead(s) on this page "
        f"(of {open_section['leads_count']} total open):"
    )
    for lead in leads:
        name = f"{lead.get('first_name') or ''} {lead.get('last_name') or ''}".strip()
        print(
            f"  - {name or '(no name)'} <{lead.get('email') or 'no email'}> "
            f"[{lead.get('status')}]"
        )
    return data


def create_lead():
    """POST /api/leads/. A 200 with {"error": false, ...} is success; the
    response does not echo the created record, so we look it up afterward."""
    email = f"sample.lead+{int(time.time())}@example.com"
    payload = {
        "first_name": "Sample",
        "last_name": "Lead",
        "email": email,
        "status": "assigned",
        "source": "other",
    }
    resp = session.post(f"{BASE_URL}/api/leads/", json=payload)
    body = resp.json()
    if resp.status_code >= 400 or body.get("error"):
        sys.exit(f"Create failed ({resp.status_code}): {body}")
    print(f"Create response: {body}")
    return email


def find_by_email(email):
    """GET /api/leads/?email=...; `email` is a case-insensitive contains
    filter (docs/api/conventions.md#filtering-and-search), which is fine here
    since the address we just created is unique in this org."""
    resp = session.get(f"{BASE_URL}/api/leads/", params={"email": email})
    resp.raise_for_status()
    matches = resp.json()["open_leads"]["open_leads"]
    if matches:
        print(f"Found the new lead: id={matches[0]['id']}")
    else:
        print("New lead not on this page (increase limit/offset to find it).")


if __name__ == "__main__":
    print("Listing existing leads...")
    list_leads()
    print("\nCreating a lead...")
    new_email = create_lead()
    print("\nConfirming it was created...")
    find_by_email(new_email)
```

## Running it

Save the script as `leads_sample.py`. You need a reachable BottleCRM backend (local or
self-hosted) and a personal access token for a profile in the org you want to query, minted as
described [above](#what-this-does).

`requests` isn't a dependency of this documentation site or of the CRM's own frontend. The
simplest way to run the script without installing anything into a project is `uv run` with an
inline dependency:

```bash
BCRM_BASE_URL=http://localhost:8000 \
BCRM_TOKEN=bcrm_pat_... \
  uv run --with requests python leads_sample.py
```

Or, with a regular virtualenv: `pip install requests` and then
`python leads_sample.py` with the same two environment variables set.

**A note on verification:** this script was checked by static means, every URL and field against
[Leads](../api/leads.md) and [Conventions](../api/conventions.md), and the whole script for valid
Python syntax, rather than executed against a live database, to avoid writing a row into a shared
instance this documentation didn't provision. The example output below is illustrative, not a
captured run:

```text
Listing existing leads...
3 open lead(s) on this page (of 3 total open):
  - Jordan Blake <jordan.blake@example.com> [assigned]
  - Priya Shah <priya.shah@example.com> [in process]
  - (no name) <no email> [assigned]

Creating a lead...
Create response: {'error': False, 'message': 'Lead Created Successfully'}

Confirming it was created...
Found the new lead: id=3f2a1c9e-....
```

A validation failure: for example, running the script twice in the same second so the generated
email collides. Comes back as a `400` and the script exits with the error body BottleCRM returned,
per [Errors](../api/errors.md#validation-errors):

```text
Create failed (400): {'error': True, 'errors': {'email': ['Another lead in this organisation already uses that email address.']}}
```
