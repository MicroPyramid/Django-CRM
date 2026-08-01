<script>
  import PageHeader from '$lib/v2/components/PageHeader.svelte';
  import FilterBar from '$lib/v2/components/FilterBar.svelte';
  import Pill from '$lib/v2/components/Pill.svelte';
  import Avatar from '$lib/v2/components/Avatar.svelte';
  import StageMeter from '$lib/v2/components/StageMeter.svelte';
  import EmptyState from '$lib/v2/components/EmptyState.svelte';
  import { money, count, shortDate } from '$lib/v2/format.js';
  import { STAGE_LABEL, AGING_TONE, AGING_LABEL } from '$lib/v2/enums.js';
  import { Columns3, List, Plus } from '@lucide/svelte';

  /** @type {{ data: any }} */
  let { data } = $props();

  let deals = $derived(data.deals);
  let totals = $derived(data.totals);
  let view = $derived(data.view);

  /* Lanes are built server-side from `/opportunities/kanban/`, which returns
     every stage with its true count. They used to be grouped on the client
     from whatever the list happened to return — correct only until the first
     page boundary, and wrong in the way that looks right: all the columns
     render, each is just short. */
  let lanes = $derived(data.lanes);

  // Only filters actually applied by the query appear as chips.
  const FILTERS = [{ key: 'stage', label: 'Stage', value: 'is not Closed' }];
</script>

<PageHeader title="Pipeline">
  {#snippet sub()}
    <!-- Totals come from the API aggregate, never from the rows on screen. -->
    <span class="v2-num">{count(totals.count)}</span> open deals ·
    <span class="v2-num">{money(totals.amount_sum)}</span> ·
    <span class="v2-num">{money(totals.weighted_sum)}</span> weighted ·
    <span class="v2-num" style="color:var(--v2-rust)">{totals.stalled_count}</span> stalled
  {/snippet}
  {#snippet actions()}
    {#if view === 'board'}
      <a class="v2-btn v2-btn-quiet" href="/pipeline"><List />List</a>
      <span class="v2-btn" aria-current="true"><Columns3 />Board</span>
    {:else}
      <span class="v2-btn" aria-current="true"><List />List</span>
      <a class="v2-btn v2-btn-quiet" href="/pipeline?view=board"><Columns3 />Board</a>
    {/if}
    <a class="v2-btn v2-btn-primary" href="/pipeline/new"><Plus />New deal</a>
  {/snippet}
</PageHeader>

<!-- The board meta used to read "Drag a card to move a stage". There is a real
     move endpoint, but nothing here is draggable, and an interface that names
     a gesture it does not support is the specific habit this redesign exists
     to break. It says where the stage is actually changed instead. -->
<FilterBar
  view="All open deals"
  filters={FILTERS}
  meta={view === 'board' ? 'Open a deal to change its stage' : 'Sorted by value'}
/>

{#if view === 'board'}
  <div class="v2-board">
    {#each lanes as lane (lane.stage)}
      <section class="v2-lane">
        <div class="v2-lane-head">
          <span class="v2-label">{STAGE_LABEL[lane.stage]}</span>
          <span class="v2-num">{count(lane.count)} · {money(lane.sum)}</span>
        </div>
        <div class="v2-lane-body">
          {#if lane.truncated}
            <!-- The API caps a column at 100 cards. Saying so beats a lane
                 that silently stops — the header count would not match the
                 cards under it and there would be nothing to explain why. -->
            <p class="v2-sub" style="padding:6px 2px;font-size:11.5px">
              Showing the first <span class="v2-num">{lane.rows.length}</span>. Filter to see the
              rest.
            </p>
          {/if}
          {#each lane.rows as d (d.id)}
            <a class="v2-deal-card" href="/pipeline/{d.id}">
              <div style="font-weight:600;letter-spacing:-0.012em;line-height:1.3">{d.name}</div>
              <div class="v2-sub" style="margin-top:2px">{d.account.name}</div>
              <div style="margin-top:9px">
                <Pill tone={AGING_TONE[d.aging_status]} dot>
                  {AGING_LABEL[d.aging_status] +
                    (d.aging_status === 'green' ? '' : ` · ${d.days_in_current_stage}d`)}
                </Pill>
              </div>
              <div class="v2-deal-card-foot">
                <Avatar name={d.assigned_to} size={21} />
                <span class="v2-num" style="font-weight:600">{money(d.amount)}</span>
                <span class="v2-sub" style="margin-left:auto;font-size:11.5px"
                  >{shortDate(d.closed_on)}</span
                >
              </div>
            </a>
          {:else}
            <p class="v2-sub" style="padding:10px 2px;font-size:12px">Nothing in this stage.</p>
          {/each}
        </div>
      </section>
    {/each}
  </div>
{:else if deals.length === 0}
  <div class="v2-scroll">
    <EmptyState
      title="No open deals"
      body="Every deal is either closed or not created yet. Start one from an account you are already talking to, or convert a lead that is ready."
    >
      {#snippet icon()}<Columns3 size={21} />{/snippet}
      {#snippet actions()}
        <a class="v2-btn v2-btn-primary" href="/pipeline/new">New deal</a>
        <a class="v2-btn" href="/leads">Go to leads</a>
      {/snippet}
    </EmptyState>
  </div>
{:else}
  <div class="v2-scroll">
    <div class="v2-table-wrap">
      <table class="v2-table">
        <thead>
          <tr>
            <th>Deal</th>
            <th>Stage</th>
            <th>Health</th>
            <th class="v2-r">Value</th>
            <th>Closing</th>
            <th class="v2-r">In stage</th>
            <th>Owner</th>
          </tr>
        </thead>
        <tbody>
          {#each deals as d (d.id)}
            <tr>
              <td>
                <a class="v2-row-link" href="/pipeline/{d.id}">
                  <div class="v2-table-primary">{d.name}</div>
                  <div class="v2-table-secondary">{d.account.name}</div>
                </a>
              </td>
              <td><StageMeter stage={d.stage} /></td>
              <td data-m="tag">
                <Pill tone={AGING_TONE[d.aging_status]} dot>{AGING_LABEL[d.aging_status]}</Pill>
              </td>
              <td class="v2-r v2-num" style="font-weight:600">{money(d.amount)}</td>
              <td>{shortDate(d.closed_on)}</td>
              <!-- Hidden on a phone: the Health pill beside the title is computed
                   from this same number, so showing both spends a line to say
                   the same thing twice. -->
              <td
                class="v2-r v2-num"
                data-m="hide"
                style={d.aging_status === 'red'
                  ? 'color:var(--v2-rust);font-weight:600'
                  : 'color:var(--v2-slate)'}
              >
                {d.days_in_current_stage}d
              </td>
              <td data-m="hide"><Avatar name={d.assigned_to} size={22} /></td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
    <p class="v2-sub v2-pad" style="font-size:12px;padding-bottom:24px">
      Showing <span class="v2-num">{deals.length}</span> of
      <span class="v2-num">{count(totals.count)}</span>
    </p>
  </div>
{/if}
