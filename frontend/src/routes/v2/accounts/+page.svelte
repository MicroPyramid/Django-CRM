<script>
  import PageHeader from '$lib/v2/components/PageHeader.svelte';
  import FilterBar from '$lib/v2/components/FilterBar.svelte';
  import Pill from '$lib/v2/components/Pill.svelte';
  import EmptyState from '$lib/v2/components/EmptyState.svelte';
  import { money, count } from '$lib/v2/format.js';
  import { Plus, Building2 } from '@lucide/svelte';

  /** @type {{ data: any }} */
  let { data } = $props();

  let accounts = $derived(data.accounts);
  let totals = $derived(data.totals);
</script>

<PageHeader title="Accounts">
  {#snippet sub()}
    <!-- The count is the size of the whole result set, not of this page. -->
    <span class="v2-num">{count(totals.count)}</span> accounts ·
    <span class="v2-num">{count(totals.customers)}</span> with a deal won
  {/snippet}
  {#snippet actions()}
    <a class="v2-btn v2-btn-primary" href="/v2/accounts/new"><Plus />New account</a>
  {/snippet}
</PageHeader>

<FilterBar view="All accounts" filters={[]} meta="Sorted by revenue won" />

<div class="v2-scroll">
  {#if accounts.length === 0}
    <EmptyState
      title="No accounts yet"
      body="An account is a company you sell to. One appears automatically the first time you convert a lead, or you can add one directly."
    >
      {#snippet icon()}<Building2 size={21} />{/snippet}
      {#snippet actions()}
        <a class="v2-btn v2-btn-primary" href="/v2/accounts/new">New account</a>
        <a class="v2-btn" href="/v2/leads">Go to leads</a>
      {/snippet}
    </EmptyState>
  {:else}
    <div class="v2-table-wrap">
      <table class="v2-table">
        <thead>
          <tr>
            <th>Account</th>
            <th>Industry</th>
            <th class="v2-r">Won</th>
            <th class="v2-r">Open pipeline</th>
            <th class="v2-r">Past due</th>
            <th>Tickets</th>
          </tr>
        </thead>
        <tbody>
          {#each accounts as a (a.id)}
            <tr>
              <td>
                <a class="v2-row-link" href="/v2/accounts/{a.id}">
                  <div class="v2-table-primary">{a.name}</div>
                  <div class="v2-table-secondary">
                    {[a.city, a.country_display].filter(Boolean).join(', ') || 'No address'}
                  </div>
                </a>
              </td>
              <td class="v2-muted" data-m="hide" style="font-size:12.5px">
                {a.industry || '—'}
              </td>
              <!-- All four figures are annotated in SQL by the API over the
                   whole related set, never derived from the rows on screen. -->
              <td class="v2-r v2-num" data-m="hide">
                {a.won_amount ? money(a.won_amount) : '—'}
              </td>
              <!-- Labelled on a phone: without the header row, two money
                   columns side by side are two unattributed numbers. -->
              <td class="v2-r v2-num" data-l="Pipeline">
                {a.open_pipeline ? money(a.open_pipeline) : '—'}
              </td>
              <td
                class="v2-r v2-num"
                data-l="Past due"
                style={a.overdue_amount ? 'color:var(--v2-rust);font-weight:600' : ''}
              >
                {a.overdue_amount ? money(a.overdue_amount) : '—'}
              </td>
              <td>
                {#if a.open_tickets}
                  <Pill tone="slate">{a.open_tickets} open</Pill>
                {:else}
                  <span class="v2-muted">—</span>
                {/if}
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
    <p class="v2-sub v2-pad" style="font-size:12px;padding-bottom:24px">
      {#if totals.shown < totals.count}
        Showing <span class="v2-num">{totals.shown}</span> of
        <span class="v2-num">{count(totals.count)}</span>
      {:else}
        Showing all <span class="v2-num">{count(totals.count)}</span>
      {/if}
      {#if totals.inactive}
        · <span class="v2-num">{totals.inactive}</span> inactive not shown
      {/if}
    </p>
  {/if}
</div>
