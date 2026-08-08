<script>
  import { resolve } from '$app/paths';
  /**
   * The organisation itself (read view).
   *
   * Most of this is the company profile, and the thing worth saying about it
   * is where it ends up: these fields are printed on every invoice and
   * estimate a customer receives. v1 presents them as a generic settings form,
   * so a wrong VAT number looks like a wrong preference rather than a wrong
   * document. The page groups them under that heading instead.
   *
   * Two behaviour switches sit at the bottom. They are not preferences either
   *: one stops customer surveys org-wide, the other changes what a close
   * button offers to do, so each says what turning it off actually causes.
   * They are real `Org` columns and, until this page was wired, had no way to
   * be edited at all.
   *
   * The org API key is NOT here, in any form. It is a credential that
   * authenticates as the org's first admin, so the API never serialises it onto
   * this payload. Rotating it belongs behind an explicit, audited action
   * (`OrgApiKeyView`), not on a page reachable by browsing.
   *
   * Editing is admin-only. `can_edit` (from the JWT role claim) decides whether
   * the "Edit details" link shows; the edit route and the backend PATCH are what
   * enforce it. A member sees this page read-only.
   *
   * VERTICAL PACK SECTION
   * `can_edit`: the same admin-derived flag the rest of this page already
   * uses to gate the "Edit details" link: also gates the pack list and its
   * actions here, because `PackApplyView`/`PackSampleDataView` are ADMIN-only
   * for the identical reason: this is org-wide configuration, not a personal
   * setting. A member sees only which pack (if any) is currently applied,
   * with no buttons, matching the 403 the backend would return if the UI
   * offered one anyway.
   *
   * Applying is additive-only and idempotent, so the currently-applied pack
   * stays clickable. Re-applying it is expected to report everything
   * skipped, not to be disallowed.
   *
   * The report after an apply shows created AND skipped, by name, because a
   * pack applied to an org that already has some of this configured is the
   * normal case, not a partial failure. A plain success toast would say
   * less than what actually happened. "Clear sample data" needs an in-page
   * confirm step (never the native `confirm()`, which blocks the browser
   * automation this app is smoke-tested with) before it deletes anything.
   */
  import PageHeader from '$lib/v2/components/PageHeader.svelte';
  import SettingsCrumb from '$lib/v2/components/SettingsCrumb.svelte';
  import Pill from '$lib/v2/components/Pill.svelte';
  import NextAction from '$lib/v2/components/NextAction.svelte';
  import { count, shortDate } from '$lib/v2/format.js';
  import { FileText, ShieldAlert, Pencil, Trash2 } from '@lucide/svelte';
  import { enhance } from '$app/forms';

  /** @type {{ data: any, form: any }} */
  let { data, form } = $props();

  let org = $derived(data.org);
  let packs = $derived(data.packs ?? []);
  /** The registry entry matching `org.vertical`, or null if unapplied / unknown. */
  let appliedPack = $derived(packs.find((/** @type {any} */ p) => p.id === org.vertical) ?? null);

  let address = $derived(
    [org.address_line, org.city, org.state, org.postcode, org.country].filter(Boolean).join(', ')
  );

  /** Disables every Apply / Clear button while any one of them is in flight. */
  let busy = $state(false);
  let confirmingClear = $state(false);

  /** Shared submit handler for the per-pack Apply forms. */
  const applySubmit = () => {
    busy = true;
    return async (/** @type {any} */ { update }) => {
      await update();
      busy = false;
    };
  };

  /** Clearing also drops back out of the confirm step on a successful run. */
  const clearSubmit = () => {
    busy = true;
    return async (/** @type {any} */ { update, result }) => {
      await update();
      busy = false;
      if (result?.type === 'success') confirmingClear = false;
    };
  };

  /**
   * "Created 18 items, skipped 3 you already had". The exact wording this
   * section exists to show instead of a success toast.
   * @param {{ created?: any[], skipped?: any[] }} report
   */
  function reportSummary(report) {
    const created = report?.created?.length ?? 0;
    const skipped = report?.skipped?.length ?? 0;
    if (!created && !skipped) return 'Nothing to add. This org already has all of it.';
    if (!skipped) return `Created ${created} item${created === 1 ? '' : 's'}.`;
    if (!created) {
      return `Already had everything from this pack, skipped ${skipped} item${skipped === 1 ? '' : 's'} you already had.`;
    }
    return `Created ${created} item${created === 1 ? '' : 's'}, skipped ${skipped} you already had.`;
  }
</script>

<PageHeader title="Organization">
  {#snippet crumb()}<SettingsCrumb />{/snippet}
  {#snippet sub()}
    <span class="v2-num">{count(org.member_count)}</span> members · created
    {shortDate(org.created_at)}
  {/snippet}
  {#snippet actions()}
    {#if data.can_edit}
      <a class="v2-btn v2-btn-primary" href={resolve('/settings/organization/edit')}>
        <Pencil size={13} />Edit details
      </a>
    {/if}
  {/snippet}
</PageHeader>

<div class="v2-scroll">
  <div class="v2-pad" style="padding-top:18px;padding-bottom:32px">
    <div class="v2-split">
      <div>
        <div class="v2-label" style="margin-bottom:10px">What customers see</div>
        <div class="v2-card" style="padding:16px 18px;margin-bottom:12px">
          <dl class="v2-kv">
            <dt>Legal name</dt>
            <dd>{org.company_name || '—'}</dd>
            <dt>Trading as</dt>
            <dd>{org.name}</dd>
            <dt>Address</dt>
            <dd>{address || '—'}</dd>
            <dt>Tax ID</dt>
            <dd class="v2-num" style="font-size:12px">{org.tax_id || '—'}</dd>
            <dt>Email</dt>
            <dd>{org.email || '—'}</dd>
            <dt>Phone</dt>
            <dd class="v2-num" style="font-size:12px">{org.phone || '—'}</dd>
            <dt>Website</dt>
            <dd>{org.website || '—'}</dd>
            <dt>Logo</dt>
            <dd>{org.logo_url ? 'Set' : 'Not set'}</dd>
          </dl>
        </div>

        <div class="v2-card" style="padding:14px 16px">
          <div style="display:flex;gap:10px;align-items:flex-start">
            <FileText size={16} style="color:var(--v2-slate);flex:none;margin-top:2px" />
            <p class="v2-sub" style="font-size:12.5px;margin:0;line-height:1.5">
              These fields are printed on every invoice and estimate. Changing one changes documents
              from that moment on; PDFs already sent keep what they were sent with. How they are
              laid out is set in
              <a href={resolve('/invoices/templates')} style="color:inherit">invoice templates</a>.
            </p>
          </div>
        </div>
      </div>

      <div>
        <div class="v2-label" style="margin-bottom:10px">Defaults</div>
        <div class="v2-card" style="overflow:hidden;margin-bottom:20px">
          <div class="v2-setting">
            <div class="v2-setting-body">
              <b>Currency</b>
              <span class="v2-sub" style="font-size:11.5px">
                Applied to new invoices and estimates. Existing ones keep theirs.
              </span>
            </div>
            <span class="v2-num" style="font-size:13px">{org.default_currency || '—'}</span>
          </div>
          <div class="v2-setting">
            <div class="v2-setting-body">
              <b>Country</b>
              <span class="v2-sub" style="font-size:11.5px">Default for new addresses.</span>
            </div>
            <span style="font-size:13px">{org.default_country || '—'}</span>
          </div>
          <div class="v2-setting">
            <div class="v2-setting-body">
              <b>Time zone</b>
              <span class="v2-sub" style="font-size:11.5px">
                When a day starts here, so "due today" and "overdue" mean what your team expects.
              </span>
            </div>
            <span style="font-size:13px">{(org.timezone || 'UTC').replace(/_/g, ' ')}</span>
          </div>
        </div>

        <div class="v2-label" style="margin-bottom:10px">Behaviour</div>
        <div class="v2-card" style="overflow:hidden">
          <div class="v2-setting">
            <div class="v2-setting-body">
              <b>Satisfaction surveys</b>
              <!-- Org-level kill switch: the post-close signal short-circuits
                   before any email is sent. Off is silent, everywhere. -->
              <span class="v2-sub" style="font-size:11.5px">
                Off stops every survey org-wide, with no per-team exception and no notice on the
                ticket.
              </span>
            </div>
            <Pill tone={org.csat_enabled ? 'moss' : 'slate'}>
              {org.csat_enabled ? 'Sending' : 'Off'}
            </Pill>
          </div>
          <div class="v2-setting">
            <div class="v2-setting-body">
              <b>Close child tickets with the parent</b>
              <!-- Only the DEFAULT state of the prompt; the person closing the
                   ticket still confirms. This used to claim the prompt without
                   saying where it is, and there is no such prompt on the web:
                   `close-with-children` has no caller in `frontend/src`, so
                   closing a parent here leaves its children open. The phone is
                   the client that asks, and the one this setting reaches. -->
              <span class="v2-sub" style="font-size:11.5px">
                Sets how the close prompt starts on the mobile app, which offers to close a parent's
                open children with it. On the web there is no such prompt yet: closing a parent
                leaves its children open.
              </span>
            </div>
            <Pill tone={org.auto_close_children_on_parent_close ? 'clay' : 'slate'}>
              {org.auto_close_children_on_parent_close ? 'Offered on' : 'Offered off'}
            </Pill>
          </div>
        </div>

        <div class="v2-card" style="padding:14px 16px;margin-top:20px">
          <div style="display:flex;gap:10px;align-items:flex-start">
            <ShieldAlert size={16} style="color:var(--v2-slate);flex:none;margin-top:2px" />
            <div>
              <div style="font-weight:600;font-size:13px">The organisation API key is not here</div>
              <p class="v2-sub" style="font-size:12.5px;margin:5px 0 0;line-height:1.5">
                It authenticates as the whole organisation, so it is never rendered on a page you
                can reach by browsing. For per-person programmatic access, use
                <a href={resolve('/settings/api-tokens')} style="color:inherit">API tokens</a>,
                which can be revoked one at a time.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div style="margin-top:24px">
      <div class="v2-label" style="margin-bottom:10px">Vertical pack</div>
      <div class="v2-card" style="padding:16px 18px">
        <p class="v2-sub" style="font-size:12.5px;margin:0 0 14px;line-height:1.5">
          A pack adds starter pipelines, tags, custom fields, products and a set of sample records
          (accounts, contacts, deals, tickets, tasks and leads) for one kind of business. Applying
          one only fills in what this org is missing. Anything already set up is left exactly as it
          is, and applying the same pack twice is safe.
        </p>

        <div style="display:flex;align-items:center;gap:10px;margin-bottom:16px">
          <span class="v2-sub" style="font-size:11.5px">First pack applied</span>
          {#if appliedPack}
            <Pill tone="moss">{appliedPack.name}</Pill>
          {:else if org.vertical}
            <Pill tone="slate">{org.vertical}</Pill>
          {:else}
            <span class="v2-sub" style="font-size:12.5px">None yet</span>
          {/if}
        </div>

        {#if !data.can_edit}
          <p class="v2-sub" style="font-size:12px;margin:0">
            Applying a pack or clearing sample data is limited to administrators.
          </p>
        {:else}
          {#if form?.error}
            <div style="margin-bottom:14px">
              <NextAction label="That did not work" text={form.error} tone="rust" />
            </div>
          {/if}

          {#if form?.report}
            {@const created = form.report.created ?? []}
            {@const skipped = form.report.skipped ?? []}
            {@const appliedName =
              packs.find((/** @type {any} */ p) => p.id === form.appliedPackId)?.name ??
              form.appliedPackId}
            <div
              class="v2-card"
              style="padding:14px 16px;margin-bottom:16px;border-color:color-mix(in srgb, var(--v2-moss) 40%, var(--v2-line))"
            >
              <div style="font-weight:650;font-size:13px">Applied “{appliedName}”</div>
              <p class="v2-sub" style="font-size:12.5px;margin:4px 0 10px">
                {reportSummary(form.report)}
              </p>
              {#if skipped.length}
                <div class="v2-label" style="margin-bottom:4px">Skipped, already had these</div>
                <ul style="margin:0 0 10px;padding-left:18px;font-size:12.5px;line-height:1.7">
                  {#each skipped as item (item.type + ':' + item.name)}
                    <li>
                      {item.name}
                      <span class="v2-sub" style="font-size:11px">
                        ({item.type.replaceAll('_', ' ')}, {item.reason})
                      </span>
                    </li>
                  {/each}
                </ul>
              {/if}
              {#if created.length}
                <div class="v2-label" style="margin-bottom:4px">Created</div>
                <ul style="margin:0;padding-left:18px;font-size:12.5px;line-height:1.7">
                  {#each created as item (item.type + ':' + item.name)}
                    <li>
                      {item.name}
                      <span class="v2-sub" style="font-size:11px">
                        ({item.type.replaceAll('_', ' ')})
                      </span>
                    </li>
                  {/each}
                </ul>
              {/if}
            </div>
          {/if}

          <div class="v2-card" style="overflow:hidden;margin-bottom:20px">
            {#each packs as pack (pack.id)}
              <div class="v2-setting">
                <div class="v2-setting-body">
                  <b>{pack.name}</b>
                  <span class="v2-sub" style="font-size:11.5px">
                    {pack.description}
                    {#if pack.version}· v{pack.version}{/if}
                  </span>
                </div>
                {#if pack.id === org.vertical}
                  <Pill tone="moss">Applied</Pill>
                {/if}
                <form method="POST" action="?/apply" use:enhance={applySubmit}>
                  <input type="hidden" name="pack_id" value={pack.id} />
                  <button class="v2-btn v2-btn-sm" disabled={busy}>Apply</button>
                </form>
              </div>
            {/each}
            {#if !packs.length}
              <div class="v2-setting">
                <span class="v2-sub" style="font-size:12.5px">No packs available right now.</span>
              </div>
            {/if}
          </div>

          <div class="danger">
            {#if confirmingClear}
              <form
                method="POST"
                action="?/clearSampleData"
                use:enhance={clearSubmit}
                style="display:flex;gap:8px;align-items:center;flex-wrap:wrap"
              >
                <span class="v2-sub" style="font-size:12px">
                  Permanently delete every sample record a pack created for this org? This cannot be
                  undone. Your real records are never touched, and any sample record you have since
                  attached real work to is kept.
                </span>
                <button class="v2-btn danger-btn" type="submit" disabled={busy}>
                  <Trash2 size={14} /> Clear sample data
                </button>
                <button
                  class="v2-btn"
                  type="button"
                  disabled={busy}
                  onclick={() => (confirmingClear = false)}
                >
                  Cancel
                </button>
              </form>
            {:else if form?.cleared !== undefined}
              <span class="v2-sub" style="font-size:12.5px">
                {form.cleared
                  ? `Deleted ${form.cleared} sample ${form.cleared === 1 ? 'record' : 'records'}.`
                  : 'No sample data to clear.'}
                {#if form.retained}
                  Kept {form.retained}
                  {form.retained === 1 ? 'record' : 'records'} you have since attached real work to.
                {/if}
              </span>
            {:else}
              <button
                class="v2-btn danger-btn"
                type="button"
                onclick={() => (confirmingClear = true)}
              >
                <Trash2 size={14} /> Clear sample data
              </button>
              <span class="v2-sub" style="font-size:11.5px">
                Removes only the records a pack created as samples. Your real records are never
                touched.
              </span>
            {/if}
          </div>
        {/if}
      </div>
    </div>
  </div>
</div>

<style>
  /* Mirrors the destructive-action pattern used on the product-edit page
     (frontend/src/routes/(app)/invoices/products/[id]/edit/+page.svelte):
     same class names, same look, so "delete something" reads the same way
     everywhere in the app. */
  .danger {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
    border-top: 1px solid var(--v2-line-soft);
    padding-top: 16px;
  }
  .danger-btn {
    color: var(--v2-rust);
    border-color: color-mix(in srgb, var(--v2-rust) 32%, transparent);
  }
  .danger-btn:hover {
    background: color-mix(in srgb, var(--v2-rust) 9%, transparent);
  }
</style>
