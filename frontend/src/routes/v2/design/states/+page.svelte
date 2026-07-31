<script>
  /**
   * Every empty and error state in one place, so they can be compared and
   * kept consistent. These are the same component the real routes use — this
   * page is a catalogue, not a second implementation.
   *
   * The rules they all follow:
   *   · say what happened, in the interface's voice
   *   · say what to do next, and make it clickable
   *   · never apologise, never say "Something went wrong"
   *   · an empty screen is an invitation, not a failure — "The queue is
   *     clear" is good news and reads like it
   *   · a permission error never confirms whether the record exists
   */
  import PageHeader from '$lib/v2/components/PageHeader.svelte';
  import EmptyState from '$lib/v2/components/EmptyState.svelte';
  import {
    Columns3,
    LifeBuoy,
    Search,
    Filter,
    FileQuestion,
    Lock,
    TriangleAlert,
    WifiOff
  } from '@lucide/svelte';

  const EMPTY = [
    {
      key: 'first-run',
      note: 'First run — nothing exists yet',
      icon: Columns3,
      title: 'No open deals',
      body: 'Every deal is either closed or not created yet. Start one from an account you are already talking to, or convert a lead that is ready.',
      primary: 'New deal',
      secondary: 'Go to leads'
    },
    {
      key: 'good-news',
      note: 'Empty because you finished — not a failure',
      icon: LifeBuoy,
      title: 'The queue is clear',
      body: 'Nothing is waiting on your team right now. New tickets arrive here from email, the portal, and anyone who replies to a closed one.',
      primary: null,
      secondary: 'Knowledge base'
    },
    {
      key: 'filtered',
      note: 'Filters hid everything — offer the way back',
      icon: Filter,
      title: 'No deals match these filters',
      body: 'Owner is Marcus Cole and closing is this month. Widen one of them, or clear the filters to see all 63 open deals.',
      primary: 'Clear filters',
      secondary: 'Change owner'
    },
    {
      key: 'search',
      note: 'Search found nothing — suggest what does work',
      icon: Search,
      title: 'Nothing matches “northwnd”',
      body: 'Try a shorter piece of the name, an invoice number, or an email address. Search covers deals, accounts, people, tickets and invoices.',
      primary: null,
      secondary: 'Clear search'
    }
  ];

  const ERRORS = [
    {
      key: '404',
      note: '404 — may not exist, may not be yours',
      icon: FileQuestion,
      title: 'That record is not here',
      body: 'It may have been deleted, or it belongs to a team you are not part of.',
      primary: null,
      secondary: 'Back to Today'
    },
    {
      key: '403',
      note: '403 — never confirms the record exists',
      icon: Lock,
      title: 'You do not have access to this',
      body: 'Ask an admin in your organisation to give you access, or head back to Today.',
      primary: null,
      secondary: 'Back to Today'
    },
    {
      key: '500',
      note: '500 — says what was not lost',
      icon: TriangleAlert,
      title: 'That did not load',
      body: 'The server did not answer. Nothing you did caused this, and nothing was saved or lost.',
      primary: 'Try again',
      secondary: 'Back to Today'
    },
    {
      key: 'offline',
      note: 'Offline — the one case where waiting is the answer',
      icon: WifiOff,
      title: 'You are offline',
      body: 'This page is showing what was loaded before the connection dropped. It will refresh itself once you are back.',
      primary: null,
      secondary: 'Retry now'
    }
  ];
</script>

<PageHeader title="Empty & error states">
  {#snippet crumb()}
    <a href="/v2/design">Design system</a> ›
  {/snippet}
  {#snippet sub()}
    Eight states, one component. Each says what happened and what to do next.
  {/snippet}
</PageHeader>

<div class="v2-scroll">
  <div class="v2-pad" style="padding-top:16px;padding-bottom:36px">
    <h2 class="v2-section" style="margin-bottom:4px">Empty</h2>
    <p class="v2-sub" style="margin:0 0 14px;max-width:70ch">
      Empty is not the same as broken, and the four below are not the same as each other. A list
      nobody has filled in yet needs a different sentence from one your own filters just emptied.
    </p>
    <div class="v2-states-grid">
      {#each EMPTY as s (s.key)}
        <div class="v2-card" style="padding:0 16px">
          <div
            class="v2-label"
            style="padding:11px 0 0;border-bottom:1px solid var(--v2-line-soft);padding-bottom:11px"
          >
            {s.note}
          </div>
          <EmptyState title={s.title} body={s.body}>
            {#snippet icon()}<s.icon size={21} />{/snippet}
            {#snippet actions()}
              {#if s.primary}<button class="v2-btn v2-btn-primary">{s.primary}</button>{/if}
              <button class="v2-btn">{s.secondary}</button>
            {/snippet}
          </EmptyState>
        </div>
      {/each}
    </div>

    <h2 class="v2-section" style="margin:30px 0 4px">Error</h2>
    <p class="v2-sub" style="margin:0 0 14px;max-width:70ch">
      These render from <code>/v2/+error.svelte</code>, so any failed load in v2 lands on one of
      them rather than a blank page. Only the ones worth retrying offer a retry.
    </p>
    <div class="v2-states-grid">
      {#each ERRORS as s (s.key)}
        <div class="v2-card" style="padding:0 16px">
          <div class="v2-label" style="padding:11px 0;border-bottom:1px solid var(--v2-line-soft)">
            {s.note}
          </div>
          <EmptyState title={s.title} body={s.body}>
            {#snippet icon()}<s.icon size={21} />{/snippet}
            {#snippet actions()}
              {#if s.primary}<button class="v2-btn v2-btn-primary">{s.primary}</button>{/if}
              <button class="v2-btn">{s.secondary}</button>
            {/snippet}
          </EmptyState>
        </div>
      {/each}
    </div>

    <h2 class="v2-section" style="margin:30px 0 4px">See a real one</h2>
    <p class="v2-sub" style="margin:0 0 12px;max-width:70ch">
      These are not staged screenshots — the routes below fail for real and land on the error
      boundary.
    </p>
    <div style="display:flex;gap:8px;flex-wrap:wrap">
      <a class="v2-btn" href="/v2/pipeline/OPP-000">404 · a deal that does not exist</a>
      <a class="v2-btn" href="/v2/contacts/nobody">404 · a contact that does not exist</a>
      <a class="v2-btn" href="/v2/solutions/SOL-99">404 · an article that does not exist</a>
    </div>
  </div>
</div>

<style>
  .v2-states-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
  }
  @media (max-width: 1000px) {
    .v2-states-grid {
      grid-template-columns: 1fr;
    }
  }
</style>
