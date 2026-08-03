# JavaScript sample

## What this does

The same flow as the [Python sample](python-sample.md), in JavaScript: obtain an access token,
list the org's leads, and create one, using only the built-in `fetch`, no npm dependencies. It's
written for Node (tested for compatibility with Node 24), but the `fetch` calls themselves would
run unmodified in any modern browser's console against a CORS-enabled backend.

As with the Python sample, "obtains a token" means reading a personal access token (`bcrm_pat_…`)
from the environment rather than driving an interactive sign-in. See
[Tokens and API keys](../api/tokens-and-api-keys.md#personal-access-tokens) for what a PAT
authenticates as, and the [Python sample](python-sample.md#what-this-does) for how to mint one
locally.

## The script

```javascript
#!/usr/bin/env node
// List an org's leads and create one, using a BottleCRM personal access token.
//
// Usage:
//   BCRM_BASE_URL=http://localhost:8000 BCRM_TOKEN=bcrm_pat_... node leads-sample.mjs
//
// Requires Node 18+ for the built-in `fetch`. The flag history, precisely:
// --experimental-fetch was a Node 17.5 flag; Node 18 made fetch available
// with no flag at all (still labeled experimental, with a startup warning);
// Node 21 dropped that warning and made fetch stable. Tested for Node 24.
// No npm dependencies.
//
// See docs/api/tokens-and-api-keys.md for how to mint BCRM_TOKEN, and
// docs/api/leads.md for the shape of the /api/leads/ responses this reads.

const BASE_URL = (process.env.BCRM_BASE_URL || "http://localhost:8000").replace(/\/$/, "");
const TOKEN = process.env.BCRM_TOKEN;

if (!TOKEN) {
  console.error(
    "Set BCRM_TOKEN to a bcrm_pat_... personal access token " +
      "(see docs/api/tokens-and-api-keys.md)."
  );
  process.exit(1);
}

const headers = {
  Authorization: `Bearer ${TOKEN}`,
  Accept: "application/json",
  "Content-Type": "application/json",
};

// GET /api/leads/, the response splits leads into open/closed sections
// rather than one flat list; see docs/api/leads.md#list-leads.
async function listLeads() {
  const res = await fetch(`${BASE_URL}/api/leads/`, { headers });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(`List failed (${res.status}): ${JSON.stringify(data)}`);
  }
  const openSection = data.open_leads;
  const leads = openSection.open_leads;
  console.log(
    `${leads.length} open lead(s) on this page (of ${openSection.leads_count} total open):`
  );
  for (const lead of leads) {
    const name = `${lead.first_name ?? ""} ${lead.last_name ?? ""}`.trim();
    console.log(
      `  - ${name || "(no name)"} <${lead.email ?? "no email"}> [${lead.status}]`
    );
  }
  return data;
}

// POST /api/leads/. A 200 with {"error": false, ...} is success; the
// response does not echo the created record, so we look it up afterward.
async function createLead() {
  const email = `sample.lead+${Date.now()}@example.com`;
  const res = await fetch(`${BASE_URL}/api/leads/`, {
    method: "POST",
    headers,
    body: JSON.stringify({
      first_name: "Sample",
      last_name: "Lead",
      email,
      status: "assigned",
      source: "other",
    }),
  });
  const body = await res.json();
  if (!res.ok || body.error) {
    throw new Error(`Create failed (${res.status}): ${JSON.stringify(body)}`);
  }
  console.log(`Create response: ${JSON.stringify(body)}`);
  return email;
}

// GET /api/leads/?email=...; `email` is a case-insensitive contains filter
// (docs/api/conventions.md#filtering-and-search), fine here since the address
// we just created is unique in this org.
async function findByEmail(email) {
  const url = new URL(`${BASE_URL}/api/leads/`);
  url.searchParams.set("email", email);
  const res = await fetch(url, { headers });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(`Lookup failed (${res.status}): ${JSON.stringify(data)}`);
  }
  const matches = data.open_leads.open_leads;
  if (matches.length) {
    console.log(`Found the new lead: id=${matches[0].id}`);
  } else {
    console.log("New lead not on this page (increase limit/offset to find it).");
  }
}

async function main() {
  console.log("Listing existing leads...");
  await listLeads();
  console.log("\nCreating a lead...");
  const email = await createLead();
  console.log("\nConfirming it was created...");
  await findByEmail(email);
}

main().catch((err) => {
  console.error(err.message);
  process.exit(1);
});
```

## Running it

Save the script as `leads-sample.mjs`. It uses no `import`/`export` and no top-level `await` (the
`await` calls are all inside `async function main()`, invoked with `.catch()` rather than awaited
at the top level), so it runs the same way whether Node treats the file as CommonJS or an ES
module, the `.mjs` extension just removes any ambiguity from a `package.json` in the same
directory. You need a reachable
BottleCRM backend and a personal access token, minted as described in the
[Python sample](python-sample.md#what-this-does):

```bash
BCRM_BASE_URL=http://localhost:8000 \
BCRM_TOKEN=bcrm_pat_... \
  node leads-sample.mjs
```

**A note on verification:** like the Python sample, this script was checked by static means,
every URL and field against [Leads](../api/leads.md) and [Conventions](../api/conventions.md), and
the whole file with `node --check`, rather than executed against a live database, to avoid
writing a row into a shared instance this documentation didn't provision. The example output is
illustrative, not a captured run, and is identical in shape to the
[Python sample's](python-sample.md#running-it) since both call the same endpoints:

```text
Listing existing leads...
3 open lead(s) on this page (of 3 total open):
  - Jordan Blake <jordan.blake@example.com> [assigned]
  - Priya Shah <priya.shah@example.com> [in process]
  - (no name) <no email> [assigned]

Creating a lead...
Create response: {"error":false,"message":"Lead Created Successfully"}

Confirming it was created...
Found the new lead: id=3f2a1c9e-....
```

A validation failure comes back as a `400` and the script throws with the error body BottleCRM
returned, per [Errors](../api/errors.md#validation-errors):

```text
Create failed (400): {"error":true,"errors":{"email":["Another lead in this organisation already uses that email address."]}}
```
