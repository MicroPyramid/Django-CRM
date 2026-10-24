<script>
  /**
   * Settings › Lead capture: every way a lead reaches this organization.
   *
   * Webhooks are built here (the list below, each one's own page for its
   * fields and deliveries). Web forms and lead addresses keep their own
   * settings pages, so they are listed here and linked. Webhooks are
   * admin-only to read, since each one holds a key that creates leads; a
   * member sees the other two sections.
   */
  import { resolve } from '$app/paths';
  import { enhance } from '$app/forms';
  import { asInternalPath } from '#lib/utils/paths.js';
  import PageHeader from '#lib/v2/components/PageHeader.svelte';
  import SettingsCrumb from '#lib/v2/components/SettingsCrumb.svelte';
  import Pill from '#lib/v2/components/Pill.svelte';
  import NextAction from '#lib/v2/components/NextAction.svelte';
  import { count, relativeTime, shortDate } from '#lib/v2/format.js';
  import { sourceLabel, sourceOptions } from '#lib/v2/lead-sources.js';
  import { INTAKE_PRESETS, intakeState, presetLabel, presetSource } from '#lib/v2/lead-intakes.js';
  import { deliveryLabel, deliveryState, deliveryTone } from '../inbound-email/delivery.js';
  import { Plus, ShieldAlert } from '@lucide/svelte';
  import KeyOnce from './KeyOnce.svelte';

  /** @type {{ data: any, form: any }} */
  let { data, form } = $props();

  let intakes = $derived(/** @type {any[]} */ (data.intakes));
  let canAddIntake = $derived(data.intakesState === 'ok');
  let creating = $state(false);
  let busy = $state(false);

  // The new webhook's source follows its preset until somebody picks one.
  let createPreset = $state('generic');
  let pickedSource = $state(/** @type {string | null} */ (null));
  let createSource = $derived(pickedSource ?? presetSource(createPreset, data.sources));

  const createSubmit = () => {
    busy = true;
    return async (/** @type {any} */ { update, result }) => {
      await update({ reset: false });
      busy = false;
      if (result?.type === 'success' && result?.data?.created) {
        creating = false;
        pickedSource = null;
      }
    };
  };
</script>

<PageHeader title="Lead capture">
  {#snippet crumb()}<SettingsCrumb />{/snippet}
  {#snippet sub()}
    Every way a lead reaches this organization: webhooks, web forms and lead addresses.
  {/snippet}
  {#snippet actions()}
    {#if canAddIntake}
      <button class="v2-btn v2-btn-primary" onclick={() => (creating = !creating)}>
        <Plus />New webhook
      </button>
    {/if}
  {/snippet}
</PageHeader>

<div class="v2-scroll">
  <div class="v2-pad" style="padding-top:16px;padding-bottom:32px">
    {#if form?.created?.key}
      <KeyOnce
        title="Webhook added. Copy its URL and key now"
        url={form.created.url}
        secret={form.created.key}
      />
      <p class="v2-sub" style="font-size:12.5px;margin:-6px 0 18px">
        Next, check which fields of a post fill which lead fields:
        <a
          href={resolve(asInternalPath(`/settings/lead-capture/${form.created.id}`))}
          style="color:inherit">set up {form.created.name}</a
        >.
      </p>
    {/if}

    {#if data.intakesState !== 'absent'}
      <section class="lc-section">
        <h2 class="v2-section">Webhooks</h2>
        <p class="v2-sub lc-lede">
          A URL to paste into Google Ads lead forms, Tally, Gravity Forms, a property portal or any
          tool that posts to a URL. Each post becomes a lead; someone who enquires again lands on
          the lead they already have.
        </p>

        {#if data.intakesState === 'forbidden'}
          <NextAction
            label="Admins only"
            text="Each webhook holds a key that creates leads in this organization, so only admins can see or change them."
          />
        {:else if data.intakesState === 'failed'}
          <p class="v2-error">Webhooks could not be loaded. Reload the page to try again.</p>
        {:else}
          {#if form?.create?.error && !creating}
            <div style="margin-bottom:14px">
              <NextAction label="That did not work" text={form.create.error} tone="rust" />
            </div>
          {/if}

          {#if creating}
            <form
              method="POST"
              action="?/create"
              use:enhance={createSubmit}
              class="v2-card lc-create"
            >
              <div class="v2-field lc-wide">
                <label for="lc-name">Name</label>
                <input
                  id="lc-name"
                  name="name"
                  class="v2-input"
                  required
                  maxlength="100"
                  placeholder="e.g. Google Ads spring campaign"
                  value={form?.create?.values?.name ?? ''}
                />
              </div>
              <div class="v2-field">
                <label for="lc-preset">Leads come from</label>
                <select id="lc-preset" name="preset" class="v2-input" bind:value={createPreset}>
                  {#each INTAKE_PRESETS as p (p.value)}
                    <option value={p.value}>{p.label}</option>
                  {/each}
                </select>
              </div>
              <div class="v2-field">
                <label for="lc-source">Record the source as</label>
                <select
                  id="lc-source"
                  name="default_source"
                  class="v2-input"
                  value={createSource}
                  onchange={(e) => (pickedSource = e.currentTarget.value)}
                >
                  <option value="">Decide later</option>
                  {#each sourceOptions(data.sources) as s (s.key)}
                    <option value={s.key}>{s.label}</option>
                  {/each}
                </select>
              </div>
              {#if form?.create?.error}
                <p class="v2-error lc-wide" style="margin:0">{form.create.error}</p>
              {/if}
              <div class="lc-wide lc-actions">
                <button class="v2-btn v2-btn-primary lc-tap" disabled={busy}>Add webhook</button>
                <button
                  type="button"
                  class="v2-btn lc-tap"
                  disabled={busy}
                  onclick={() => (creating = false)}
                >
                  Cancel
                </button>
              </div>
            </form>
          {/if}

          {#if intakes.length}
            <div class="v2-table-wrap">
              <table class="v2-table">
                <thead>
                  <tr>
                    <th>Webhook</th>
                    <th>State</th>
                    <th>Last post</th>
                    <th data-m="hide">Added</th>
                  </tr>
                </thead>
                <tbody>
                  {#each intakes as i (i.id)}
                    {@const s = intakeState(i)}
                    <tr>
                      <td data-m="title">
                        <a
                          class="v2-row-link"
                          href={resolve(asInternalPath(`/settings/lead-capture/${i.id}`))}
                        >
                          <div class="v2-table-primary">{i.name}</div>
                          <div class="v2-table-secondary">
                            {presetLabel(i.preset)}
                            {#if i.default_source}
                              · {sourceLabel(data.sources, i.default_source)}{/if}
                            {#if i.last_error}
                              <span style="color:var(--v2-clay);font-weight:600">
                                · last post refused</span
                              >
                            {/if}
                          </div>
                        </a>
                      </td>
                      <td data-m="tag"><Pill tone={s.tone}>{s.label}</Pill></td>
                      <td
                        data-m="meta"
                        data-l={i.last_received_at ? 'Last post' : undefined}
                        class="v2-muted"
                      >
                        {i.last_received_at ? relativeTime(i.last_received_at) : 'No posts yet'}
                      </td>
                      <td data-m="hide" class="v2-muted">
                        {i.created_at ? shortDate(i.created_at) : ''}
                      </td>
                    </tr>
                  {/each}
                </tbody>
              </table>
            </div>
          {:else if !creating}
            <div class="v2-card lc-empty">
              <p class="v2-sub" style="margin:0">No webhooks yet.</p>
              <button class="v2-btn v2-btn-primary lc-tap" onclick={() => (creating = true)}>
                <Plus />New webhook
              </button>
            </div>
          {/if}
        {/if}
      </section>
    {/if}

    <section class="lc-section">
      <h2 class="v2-section">Web forms</h2>
      <p class="v2-sub lc-lede">Forms embedded on your own site. Each submission becomes a lead.</p>
      {#if data.webForms === null}
        <p class="v2-error">Web forms could not be loaded. Reload the page to try again.</p>
      {:else if data.webForms.length}
        <div class="v2-card" style="overflow:hidden">
          {#each data.webForms as f (f.id)}
            <a class="lc-row" href={resolve(asInternalPath(`/settings/web-forms/${f.id}`))}>
              <span class="lc-row-name">{f.name}</span>
              <span class="v2-sub lc-row-meta">
                <span class="v2-num">{count(f.submission_count)}</span>
                {f.submission_count === 1 ? 'submission' : 'submissions'}
              </span>
              <Pill tone={f.is_published ? 'moss' : 'slate'}>
                {f.is_published ? 'Published' : 'Draft'}
              </Pill>
            </a>
          {/each}
        </div>
        {#if data.webFormsTruncated}
          <p class="v2-sub" style="font-size:12px;margin:8px 0 0">
            The most recent ones. The rest are in Web forms.
          </p>
        {/if}
      {:else}
        <p class="v2-sub" style="font-size:12.5px">No lead forms yet.</p>
      {/if}
      <a class="v2-btn lc-tap lc-more" href={resolve('settings/web-forms')}>Open web forms</a>
    </section>

    <section class="lc-section">
      <h2 class="v2-section">Lead addresses</h2>
      <p class="v2-sub lc-lede">
        Forward an enquiry to one of these, or point a portal's notification email at it, and it
        becomes a lead with the sender's name, email and phone.
      </p>
      {#if data.leadAddresses === null}
        <p class="v2-error">Lead addresses could not be loaded. Reload the page to try again.</p>
      {:else if !data.leadAddressesOffered}
        <p class="v2-sub" style="font-size:12.5px">
          This server does not turn email into leads yet. Inbound email makes tickets only.
        </p>
      {:else}
        {#if data.leadAddresses.length}
          <div class="v2-card" style="overflow:hidden">
            {#each data.leadAddresses as m (m.id)}
              {@const state = deliveryState(m)}
              <div class="lc-row">
                <span class="lc-row-name" style="overflow-wrap:anywhere">{m.address}</span>
                <span class="v2-sub lc-row-meta">
                  {sourceLabel(data.sources, m.lead_source) || 'Email'}{m.lead_source_detail
                    ? ` · ${m.lead_source_detail}`
                    : ''}
                </span>
                <Pill tone={deliveryTone(state)}>{deliveryLabel(state, 'leads')}</Pill>
              </div>
            {/each}
          </div>
        {:else}
          <p class="v2-sub" style="font-size:12.5px">No lead addresses yet.</p>
        {/if}
        <a class="v2-btn lc-tap lc-more" href={resolve('settings/inbound-email')}>
          Open inbound email
        </a>
      {/if}
    </section>

    {#if canAddIntake}
      <div class="lc-note">
        <ShieldAlert size={16} style="color:var(--v2-clay);flex:none;margin-top:1px" />
        <div>
          <div style="font-weight:600;font-size:13px">A webhook key can only create leads</div>
          <p class="v2-sub" style="font-size:12px;margin:4px 0 0;line-height:1.5">
            It reads nothing and reaches no other record. Send it in the
            <code class="lc-code">Authorization: Bearer</code> header where the tool allows; a tool
            that only takes a URL can add <code class="lc-code">?key=</code>, but proxies and logs
            keep query strings, so the header is safer. Replacing a key keeps the old one working
            for 7 days. Each webhook's page lists its newest 50 posts, accepted or refused, and
            posts are kept for 30 days.
          </p>
        </div>
      </div>
    {/if}
  </div>
</div>

<style>
  .lc-section {
    margin-bottom: 28px;
  }
  .lc-lede {
    font-size: 12.5px;
    margin: 4px 0 12px;
    max-width: 70ch;
    line-height: 1.5;
  }
  .lc-create {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px 16px;
    padding: 14px 15px;
    margin-bottom: 16px;
  }
  .lc-wide {
    grid-column: 1 / -1;
  }
  .lc-actions {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }
  .lc-empty {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    flex-wrap: wrap;
    padding: 14px 16px;
  }
  .lc-row {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 6px 12px;
    padding: 12px 16px;
    min-height: 44px;
    border-top: 1px solid var(--v2-line);
    color: inherit;
    text-decoration: none;
  }
  .lc-row:first-child {
    border-top: 0;
  }
  a.lc-row:hover {
    background: var(--v2-bg-sunk);
  }
  .lc-row-name {
    flex: 1 1 200px;
    min-width: 0;
    font-weight: 600;
    font-size: 13px;
  }
  .lc-row-meta {
    font-size: 12px;
  }
  .lc-more {
    margin-top: 10px;
  }
  .lc-tap {
    min-height: 44px;
  }
  .lc-code {
    white-space: nowrap;
  }
  .lc-note {
    display: flex;
    gap: 10px;
    align-items: flex-start;
    padding: 14px 16px;
    border: 1px solid var(--v2-line);
    border-radius: var(--v2-radius);
  }
  @media (max-width: 768px) {
    .lc-create {
      grid-template-columns: 1fr;
    }
  }
</style>
