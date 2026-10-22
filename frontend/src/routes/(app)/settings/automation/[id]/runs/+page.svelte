<script>
  /**
   * One rule's runs from the last 30 days, newest first. Each opens to what
   * its steps did. Read only. Every text here is rendered as text.
   */
  import { resolve } from '$app/paths';
  import { asInternalPath } from '#lib/utils/paths.js';
  import PageHeader from '#lib/v2/components/PageHeader.svelte';
  import EmptyState from '#lib/v2/components/EmptyState.svelte';
  import Pill from '#lib/v2/components/Pill.svelte';
  import AdminsOnly from '#lib/v2/components/automation/AdminsOnly.svelte';
  import { recordRoute, runNotes } from '#lib/v2/automation.js';
  import { runTime } from '#lib/v2/format.js';
  import { ChevronLeft, ChevronDown } from '@lucide/svelte';

  /** @type {{ data: any }} */
  let { data } = $props();

  const RUN = /** @type {Record<string, {label: string, tone: 'moss'|'rust'|'slate'}>} */ ({
    done: { label: 'Done', tone: 'moss' },
    failed: { label: 'Failed', tone: 'rust' },
    skipped: { label: 'Skipped', tone: 'slate' }
  });
  const STEP = /** @type {Record<string, string>} */ ({
    done: 'Done',
    undone: 'Undone',
    failed: 'Failed',
    skipped: 'Skipped'
  });

  let runs = $derived(data.runs ?? []);
  let hasNewer = $derived(data.offset > 0);
  let hasOlder = $derived(data.offset + data.pageSize < data.count);
  let rulePath = $derived(
    data.rule ? `/settings/automation/${data.rule.id}` : '/settings/automation'
  );
  let runsPath = $derived(`${rulePath}/runs`);
  let timezone = $derived(data.org?.timezone || 'UTC');
</script>

<PageHeader title={data.forbidden ? 'Runs' : data.rule.name}>
  {#snippet crumb()}
    {#if !data.forbidden}
      <a class="rn-crumb" href={resolve(asInternalPath(rulePath))}><ChevronLeft size={13} />Rule</a>
    {/if}
  {/snippet}
  {#snippet sub()}
    {#if !data.forbidden}Runs from the last 30 days, newest first.{/if}
  {/snippet}
</PageHeader>

<div class="v2-scroll">
  <div class="v2-pad" style="padding-bottom:32px">
    {#if data.forbidden}
      <AdminsOnly />
    {:else if !runs.length && data.offset === 0}
      <EmptyState
        title="No runs yet"
        body="When this rule runs, each run and what it did shows here for 30 days."
      />
    {:else}
      {#if !runs.length}
        <p class="rn-none">No more runs.</p>
      {/if}
      <div class="rn-list">
        {#each runs as run (run.id)}
          {@const pill = RUN[run.status] ?? { label: run.status, tone: 'slate' }}
          {@const href = recordRoute(run.object_key, run.record_id)}
          {@const steps = run.steps ?? []}
          {@const said = runNotes(run)}
          {#snippet head()}
            <span class="rn-when">{runTime(run.created_at, timezone)}</span>
            <span class="rn-rec">
              {#if href}
                <a href={resolve(asInternalPath(href))}>{run.record_name || 'Record'}</a>
              {:else}
                {run.record_name || 'Record'}
              {/if}
            </span>
            <Pill tone={pill.tone}>{pill.label}</Pill>
          {/snippet}
          {#snippet notes()}
            {#if said.reason || said.by}
              <span class="rn-notes">
                {#if said.reason}<span class="rn-reason">{said.reason}</span>{/if}
                {#if said.by}<span class="rn-by">{said.by}</span>{/if}
              </span>
            {/if}
          {/snippet}
          {#if steps.length}
            <details class="v2-card rn-run">
              <summary class="rn-sum">
                {@render head()}
                <ChevronDown class="rn-chev" size={16} />
                {@render notes()}
              </summary>
              <div class="rn-body">
                <ul class="rn-steps">
                  {#each steps as step, i (i)}
                    <li class="rn-step rn-{step.status}">
                      <span>{step.text}</span>
                      <span class="rn-st">{STEP[step.status] ?? step.status}</span>
                    </li>
                  {/each}
                </ul>
              </div>
            </details>
          {:else}
            <div class="v2-card rn-run">
              <div class="rn-sum">{@render head()}{@render notes()}</div>
            </div>
          {/if}
        {/each}
      </div>
      {#if hasNewer || hasOlder}
        <div style="display:flex;gap:8px;margin-top:12px">
          {#if hasNewer}
            <a
              class="v2-btn v2-btn-sm rn-tap"
              href={resolve(
                asInternalPath(`${runsPath}?offset=${Math.max(0, data.offset - data.pageSize)}`)
              )}>Newer</a
            >
          {/if}
          {#if hasOlder}
            <a
              class="v2-btn v2-btn-sm rn-tap"
              href={resolve(asInternalPath(`${runsPath}?offset=${data.offset + data.pageSize}`))}
              >Older</a
            >
          {/if}
        </div>
      {/if}
    {/if}
  </div>
</div>

<style>
  .rn-crumb {
    display: inline-flex;
    align-items: center;
    gap: 2px;
  }
  .rn-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  .rn-sum {
    list-style: none;
    min-height: 44px;
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 4px 12px;
    padding: 6px 14px;
  }
  details > .rn-sum {
    cursor: pointer;
  }
  .rn-sum::-webkit-details-marker {
    display: none;
  }
  .rn-sum :global(.rn-chev) {
    flex: none;
    color: var(--v2-slate);
    transition: transform 0.15s;
  }
  details[open] > .rn-sum :global(.rn-chev) {
    transform: rotate(180deg);
  }
  .rn-when {
    font-size: 12px;
    color: var(--v2-slate);
    min-width: 110px;
  }
  .rn-rec {
    flex: 1;
    min-width: 0;
    font-weight: 600;
    overflow-wrap: anywhere;
  }
  .rn-body {
    padding: 0 14px 12px;
    font-size: 13px;
  }
  .rn-notes {
    flex-basis: 100%;
    min-width: 0;
    font-size: 13px;
    overflow-wrap: anywhere;
  }
  .rn-notes > span {
    display: block;
    margin: 2px 0;
  }
  .rn-by {
    color: var(--v2-slate);
  }
  .rn-steps {
    list-style: none;
    margin: 8px 0 0;
    padding: 0;
  }
  .rn-step {
    display: flex;
    justify-content: space-between;
    gap: 12px;
    padding: 4px 0;
  }
  .rn-st {
    flex: none;
    font-size: 12px;
    color: var(--v2-slate);
  }
  .rn-failed .rn-st {
    color: var(--v2-rust);
  }
  .rn-done .rn-st {
    color: var(--v2-moss);
  }
  .rn-none {
    text-align: center;
    padding: 24px 0;
  }
  .rn-tap {
    min-height: 44px;
    display: inline-flex;
    align-items: center;
  }
</style>
