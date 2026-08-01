<script>
  /**
   * Status and visibility are two separate facts, and the list shows both.
   * An article can be approved and still invisible to customers; v1 showed
   * status alone, so those read as live and nobody published them.
   *
   * Now on the real API, which changed one thing about that claim: publishing
   * is admin-only, so for everybody else the approved-and-invisible row is
   * information rather than a button. It still says so — knowing a colleague
   * has to release it is worth more than a control that answers 403.
   */
  import PageHeader from '$lib/v2/components/PageHeader.svelte';
  import FilterBar from '$lib/v2/components/FilterBar.svelte';
  import StatCard from '$lib/v2/components/StatCard.svelte';
  import Pill from '$lib/v2/components/Pill.svelte';
  import EmptyState from '$lib/v2/components/EmptyState.svelte';
  import { count, relativeDays } from '$lib/v2/format.js';
  import { SOLUTION_STATUS_LABEL, SOLUTION_STATUS_TONE } from '$lib/v2/enums.js';
  import { enhance } from '$app/forms';
  import { BookOpen, Eye, EyeOff, Plus } from '@lucide/svelte';

  /** @type {{ data: any, form: any }} */
  let { data, form } = $props();

  let articles = $derived(data.articles);
  let totals = $derived(data.totals);

  let filters = $derived(
    [
      data.status ? { key: 'status', label: 'Status', value: data.status } : null,
      data.visibility ? { key: 'visibility', label: 'Visibility', value: data.visibility } : null,
      data.search ? { key: 'search', label: 'Search', value: data.search } : null
    ].filter(Boolean)
  );

  /** Whether any filter is on, which decides what an empty result means. */
  let filtered = $derived(filters.length > 0);
</script>

<PageHeader title="Knowledge base">
  {#snippet sub()}
    <!-- "1 customers can see" is what the mock's phrasing produced the moment
         the number was real. Stable at every count, and it still says what
         published means rather than just naming the flag. -->
    <span class="v2-num">{count(totals.count)}</span>
    {totals.count === 1 ? 'article' : 'articles'} ·
    <span class="v2-num">{count(totals.published)}</span> visible to customers
  {/snippet}
  {#snippet actions()}
    <a class="v2-btn v2-btn-primary" href="/solutions/new"><Plus />New article</a>
  {/snippet}
</PageHeader>

<div class="v2-pad" style="padding-top:14px;flex:none">
  <div class="v2-stats">
    <StatCard
      label="Approved, not published"
      value={count(totals.approved_unpublished)}
      tone={totals.approved_unpublished ? 'clay' : 'slate'}
      detail={totals.approved_unpublished
        ? data.canRelease
          ? 'Ready to go live'
          : 'Waiting on an admin'
        : 'Nothing waiting'}
    />
    <StatCard label="Published" value={count(totals.published)} tone="moss" />
    <StatCard label="Draft" value={count(totals.draft)} tone="slate" />
    <StatCard label="Total" value={count(totals.count)} tone="ink" />
  </div>
</div>

<FilterBar
  view={filtered ? 'Filtered, last edited first' : 'All articles, last edited first'}
  {filters}
  meta="Published means customers can be shown it — approving it is a separate step"
/>

{#if form?.error}
  <p class="v2-pad" style="color:var(--v2-rust);font-size:12.5px;padding-top:10px">{form.error}</p>
{/if}

<div class="v2-scroll">
  {#if articles.length === 0}
    <EmptyState
      title={filtered ? 'No articles match that' : 'No articles yet'}
      body={filtered
        ? 'Nothing in the knowledge base matches those filters. Clearing them shows everything.'
        : 'Write the answer once, link it from the tickets that ask for it, and stop retyping it. The first one usually comes straight out of a ticket you just resolved.'}
    >
      {#snippet icon()}<BookOpen size={21} />{/snippet}
      {#snippet actions()}
        {#if filtered}
          <a class="v2-btn" href="/solutions">Clear filters</a>
        {/if}
        <a class="v2-btn v2-btn-primary" href="/solutions/new">New article</a>
        <a class="v2-btn" href="/tickets">Go to tickets</a>
      {/snippet}
    </EmptyState>
  {:else}
    <div class="v2-table-wrap">
      <table class="v2-table">
        <thead>
          <tr>
            <th>Article</th>
            <th>Status</th>
            <th>Visibility</th>
            <th class="v2-r">Tickets solved</th>
            <th>Author</th>
            <th class="v2-r">Edited</th>
            <th style="width:110px"></th>
          </tr>
        </thead>
        <tbody>
          {#each articles as s (s.id)}
            <tr>
              <td style="white-space:normal;max-width:460px" data-m="title">
                <a class="v2-row-link" href="/solutions/{s.id}">
                  <span class="v2-table-primary">{s.title}</span>
                </a>
              </td>
              <td data-m="tag">
                <Pill tone={SOLUTION_STATUS_TONE[s.status]}>
                  {SOLUTION_STATUS_LABEL[s.status]}
                </Pill>
              </td>
              <td>
                {#if s.is_published}
                  <span
                    style="display:inline-flex;gap:5px;align-items:center;color:var(--v2-slate);font-size:12.5px"
                  >
                    <Eye size={13} />Customers can see it
                  </span>
                {:else}
                  <span
                    style="display:inline-flex;gap:5px;align-items:center;font-size:12.5px"
                    style:color={s.awaiting_release ? 'var(--v2-clay)' : 'var(--v2-slate)'}
                  >
                    <EyeOff size={13} />Internal only
                  </span>
                {/if}
              </td>
              <!-- The unit lives in the header, so the cell stays a bare
                   number and the column reads as a column. -->
              <td class="v2-r v2-num" class:v2-muted={!s.use_count} data-m="meta">
                {s.use_count || '—'}
              </td>
              <td data-m="hide">{s.author || '—'}</td>
              <td class="v2-r v2-muted" data-m="hide">{relativeDays(s.updated_at)}</td>
              <td>
                <!--
                  Only the rows that are actually ready get the publish
                  control, and only for somebody who may press it. Offering it
                  on a draft would mean a state transition the server has to
                  reject; offering it to a non-admin would mean a 403.
                -->
                {#if s.awaiting_release && data.canRelease}
                  <form method="POST" action="?/publish" use:enhance>
                    <input type="hidden" name="id" value={s.id} />
                    <button class="v2-btn v2-btn-sm" type="submit">Publish</button>
                  </form>
                {/if}
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
    <p class="v2-sub v2-pad" style="font-size:12px;padding-bottom:24px">
      Showing <span class="v2-num">{articles.length}</span> of
      <span class="v2-num">{count(totals.matched)}</span>
      {#if filtered}
        · <a href="/solutions" style="color:inherit">clear filters</a>
      {/if}
    </p>
  {/if}
</div>
