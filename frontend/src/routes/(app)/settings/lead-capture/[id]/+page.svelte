<script>
  /**
   * One lead webhook: where to post and with what key, test it, switch it,
   * replace its key, set what a post becomes, and read its newest deliveries.
   *
   * The full key is never on this page except straight after a replace; reads
   * carry only its last four characters.
   */
  import { resolve } from '$app/paths';
  import { enhance } from '$app/forms';
  import { asInternalPath } from '#lib/utils/paths.js';
  import PageHeader from '#lib/v2/components/PageHeader.svelte';
  import SettingsCrumb from '#lib/v2/components/SettingsCrumb.svelte';
  import Pill from '#lib/v2/components/Pill.svelte';
  import NextAction from '#lib/v2/components/NextAction.svelte';
  import ConfirmAction from '#lib/v2/components/ConfirmAction.svelte';
  import { relativeTime } from '#lib/v2/format.js';
  import { missingOption, missingOptions, inactiveOptionLabel } from '#lib/v2/pickers.js';
  import { sourceOptions } from '#lib/v2/lead-sources.js';
  import {
    deliveryResult,
    intakeState,
    mappingTargets,
    presetLabel,
    targetsFor
  } from '#lib/v2/lead-intakes.js';
  import CopyValue from '../CopyValue.svelte';
  import KeyOnce from '../KeyOnce.svelte';
  import MappingEditor from './MappingEditor.svelte';

  /** @type {{ data: any, form: any }} */
  let { data, form } = $props();

  let busy = $state(false);
  const working = () => {
    busy = true;
    return async (/** @type {any} */ { update }) => {
      await update({ reset: false });
      busy = false;
    };
  };

  let actionError = $derived(
    form?.save?.error ??
      form?.toggle?.error ??
      form?.test?.error ??
      form?.key?.error ??
      form?.remove?.error ??
      null
  );

  /** What each preset's sender asks for, in its own words. */
  const HOW = /** @type {Record<string, string>} */ ({
    google_ads:
      "In the Google Ads lead form, add a webhook: paste the URL as the webhook URL and the key as the key. Google's Send test data arrives here as a test.",
    tally:
      'In Tally, add a webhook under Integrations: paste the URL, and paste the key as its signing secret.',
    gravity_forms:
      'With the Gravity Forms Webhooks add-on, add a feed that posts to the URL, with a request header Authorization set to Bearer, a space, and the key.',
    generic:
      'Post JSON or a form to the URL with the header Authorization: Bearer and the key. A tool that only takes a URL can add ?key= and the key to it instead, though the header is safer.'
  });

  // The stored owner and tags when the pickers cannot offer them (someone
  // deactivated, a tag archived): a select with no matching option submits
  // nothing, and the save would drop them.
  let missingOwner = $derived(
    data.forbidden || !data.intake.assignee
      ? null
      : missingOption(data.people, {
          id: data.intake.assignee,
          name: data.intake.assignee_name ?? 'A former member'
        })
  );
  let activeTags = $derived(
    data.forbidden ? [] : data.tags.filter((/** @type {any} */ t) => t.is_active !== false)
  );
  let missingTags = $derived(
    data.forbidden
      ? []
      : missingOptions(
          activeTags,
          data.intake.tags.map((/** @type {string} */ id) => ({
            id,
            name: data.tags.find((/** @type {any} */ t) => t.id === id)?.name ?? 'A removed tag'
          }))
        )
  );
</script>

{#if data.forbidden}
  <PageHeader title="Webhook">
    {#snippet crumb()}<SettingsCrumb />{/snippet}
  </PageHeader>
  <div class="v2-pad" style="padding-top:40px">
    <NextAction
      label="Admins only"
      text="Each webhook holds a key that creates leads in this organization, so only admins can see or change them."
    />
  </div>
{:else}
  {@const i = data.intake}
  {@const state = intakeState(i)}
  <PageHeader title={i.name || 'Webhook'}>
    {#snippet crumb()}
      <a href={resolve('settings/lead-capture')} style="color:inherit">Lead capture</a>
    {/snippet}
    {#snippet sub()}
      {presetLabel(i.preset)} · <Pill tone={state.tone}>{state.label}</Pill>
    {/snippet}
  </PageHeader>

  <div class="v2-scroll">
    <div class="v2-pad" style="padding-top:16px;padding-bottom:32px">
      {#if form?.replaced?.key}
        <KeyOnce title="Key replaced. Copy the new one now" secret={form.replaced.key} replaced />
      {/if}
      {#if actionError}
        <div style="margin-bottom:16px">
          <NextAction label="That did not work" text={actionError} tone="rust" />
        </div>
      {/if}
      {#if form?.tested}
        <p class="v2-sub ic-note">Test sent. It is at the top of the deliveries below.</p>
      {:else if form?.saved}
        <p class="v2-sub ic-note">Saved.</p>
      {/if}

      <section class="v2-card ic-card">
        <h2 class="v2-section ic-head">Where to send leads</h2>
        <CopyValue label="Webhook URL" value={i.url} id="ic-url" />
        <p class="v2-sub ic-text">
          Key ending in <span class="v2-num">{i.key_hint || '????'}</span>. It was shown once, when
          the webhook was added or its key last replaced.
        </p>
        <p class="v2-sub ic-text">{HOW[i.preset] ?? HOW.generic}</p>
        {#if i.last_received_at}
          <p class="v2-sub ic-text">Last post {relativeTime(i.last_received_at)}.</p>
        {/if}
        {#if i.last_error}
          <p class="v2-sub ic-text" style="color:var(--v2-clay)">
            Last refused post: {i.last_error}
          </p>
        {/if}
        <div class="ic-actions">
          {#if i.is_active}
            <form method="POST" action="?/test" use:enhance={working}>
              <button class="v2-btn v2-btn-primary ic-tap" disabled={busy}>Send a test</button>
            </form>
          {/if}
          <form method="POST" action="?/toggle" use:enhance={working}>
            <input type="hidden" name="is_active" value={i.is_active ? 'false' : 'true'} />
            <button class="v2-btn ic-tap" disabled={busy}>
              {i.is_active ? 'Switch off' : 'Switch on'}
            </button>
          </form>
          <ConfirmAction
            action="?/key"
            label="Replace key"
            confirmLabel="Replace it"
            explain="A new key is shown once. The current one keeps working for 7 days."
          />
          <ConfirmAction
            action="?/remove"
            label="Delete"
            confirmLabel="Delete permanently"
            explain="The URL stops working at once and its delivery log goes with it. Leads it made stay."
          />
        </div>
        {#if !i.is_active}
          <p class="v2-sub ic-text">
            Switched off: posts to the URL are refused, answered as if it did not exist.
          </p>
        {/if}
      </section>

      <form
        method="POST"
        action="?/save"
        use:enhance={working}
        class="v2-card ic-card"
        style="margin-bottom:22px"
      >
        <h2 class="v2-section ic-head">What a post becomes</h2>
        <div class="ic-grid">
          <div class="v2-field ic-wide">
            <label for="ic-name">Name</label>
            <input
              id="ic-name"
              name="name"
              class="v2-input"
              required
              maxlength="100"
              value={i.name}
            />
          </div>
          <div class="v2-field">
            <label for="ic-source">Source</label>
            <select id="ic-source" name="default_source" class="v2-input" value={i.default_source}>
              <option value="">Not specified</option>
              {#each sourceOptions(data.sources, i.default_source) as s (s.key)}
                <option value={s.key}>{s.label}</option>
              {/each}
            </select>
          </div>
          <div class="v2-field">
            <label for="ic-detail">Sub-source</label>
            <input
              id="ic-detail"
              name="source_detail"
              class="v2-input"
              maxlength="100"
              placeholder="e.g. Spring campaign"
              value={i.source_detail}
            />
          </div>
          <div class="v2-field">
            <label for="ic-owner">Owner of each new lead</label>
            <select id="ic-owner" name="assignee" class="v2-input" value={i.assignee ?? ''}>
              <option value="">Nobody</option>
              {#if missingOwner}
                <option value={missingOwner.id}>
                  {inactiveOptionLabel(missingOwner.name)}
                </option>
              {/if}
              {#each data.people as p (p.id)}
                <option value={p.id}>{p.name}</option>
              {/each}
            </select>
            <p class="v2-hint">
              A lead that matches one already here keeps its owner. To share new leads out in turn,
              use an automation rule.
            </p>
          </div>
          <div class="v2-field">
            <label for="ic-tags">Tag each lead with</label>
            <select id="ic-tags" name="tags" class="v2-input ic-multi" multiple size="4">
              {#each missingTags as t (t.id)}
                <option value={t.id} selected>{inactiveOptionLabel(t.name)}</option>
              {/each}
              {#each activeTags as t (t.id)}
                <option value={t.id} selected={i.tags.includes(t.id)}>{t.name}</option>
              {/each}
            </select>
          </div>
        </div>

        <div class="ic-mapping">
          <div class="v2-label" style="margin-bottom:4px">Fields</div>
          <p class="v2-sub ic-text" style="margin-top:0">
            Name each field by its path in the post, with dots between levels, for example
            <code>data.email</code>. A field no row uses goes into the lead's enquiry text, so
            nothing anyone typed is lost.
          </p>
          <MappingEditor
            rows={i.mapping}
            targets={targetsFor(mappingTargets(data.customFields), i.mapping)}
          />
        </div>

        <button class="v2-btn v2-btn-primary ic-tap" style="margin-top:16px" disabled={busy}>
          Save
        </button>
      </form>

      <div class="ic-deliveries-head">
        <h2 class="v2-section">Deliveries</h2>
        <a
          class="v2-btn v2-btn-sm ic-tap"
          href={resolve(asInternalPath(`/settings/lead-capture/${i.id}`))}
        >
          Refresh
        </a>
      </div>
      <p class="v2-sub ic-text" style="margin-top:0">
        The newest 50 posts, accepted or refused. Posts are kept for 30 days.
      </p>

      {#if data.deliveriesFailed}
        <p class="v2-error">The deliveries could not be loaded. Refresh to try again.</p>
      {:else if !data.deliveries.length}
        <p class="v2-sub" style="font-size:12.5px">
          Nothing has arrived yet. Send a test, or post a lead from the tool.
        </p>
      {:else}
        <div class="v2-table-wrap">
          <table class="v2-table">
            <thead>
              <tr>
                <th>When</th>
                <th>Result</th>
                <th>Lead</th>
                <th data-m="hide">Sender's id</th>
              </tr>
            </thead>
            <tbody>
              {#each data.deliveries as d (d.id)}
                {@const r = deliveryResult(d.result)}
                <tr>
                  <td data-m="title">
                    <div class="v2-table-primary">
                      {d.received_at ? relativeTime(d.received_at) : 'Unknown time'}
                    </div>
                    {#if d.error}
                      <div class="v2-table-secondary" style="overflow-wrap:anywhere">{d.error}</div>
                    {/if}
                  </td>
                  <td data-m="tag"><Pill tone={r.tone}>{r.label}</Pill></td>
                  <td data-m="meta">
                    {#if d.lead}
                      <a class="ic-lead" href={resolve(asInternalPath(`/leads/${d.lead}`))}
                        >Open lead</a
                      >
                    {:else}
                      <span class="v2-muted">No lead</span>
                    {/if}
                  </td>
                  <td data-m="hide" class="v2-num v2-muted" style="overflow-wrap:anywhere">
                    {d.external_id}
                  </td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
      {/if}
    </div>
  </div>
{/if}

<style>
  .ic-card {
    padding: 15px 16px;
    margin-bottom: 18px;
  }
  .ic-head {
    margin-bottom: 12px;
  }
  .ic-text {
    font-size: 12.5px;
    margin: 10px 0 0;
    line-height: 1.5;
    max-width: 72ch;
  }
  .ic-actions {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    align-items: center;
    margin-top: 14px;
  }
  .ic-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 13px 18px;
    align-items: start;
  }
  .ic-wide {
    grid-column: 1 / -1;
  }
  .ic-multi {
    height: auto;
  }
  .ic-mapping {
    margin-top: 18px;
    padding-top: 14px;
    border-top: 1px solid var(--v2-line-soft);
  }
  .ic-deliveries-head {
    display: flex;
    align-items: center;
    gap: 10px;
    justify-content: space-between;
  }
  .ic-lead {
    color: inherit;
    display: inline-flex;
    align-items: center;
    min-height: 44px;
  }
  .ic-tap {
    min-height: 44px;
    display: inline-flex;
    align-items: center;
  }
  .ic-note {
    color: var(--v2-moss);
    font-size: 12.5px;
    margin: 0 0 14px;
    font-weight: 550;
  }
  @media (max-width: 768px) {
    .ic-grid {
      grid-template-columns: 1fr;
    }
  }
</style>
