<script>
  import { resolve } from '$app/paths';
  import { goto } from '$app/navigation';
  import {
    Search,
    Columns3,
    Building2,
    Users,
    Target,
    LifeBuoy,
    Receipt,
    BookOpen,
    Plus,
    CornerDownLeft
  } from '@lucide/svelte';

  /**
   * One search across every record type, opened with ⌘K.
   *
   * v1 had a search box per list, each scoped to that list, so finding a
   * ticket meant knowing it was a ticket first. This asks once.
   *
   * Empty query shows actions rather than an empty box. The fastest way to
   * start a new deal is ⌘K, "new", Enter, and that only works if the actions
   * are there before you type.
   *
   * @type {{ open: boolean, onclose: () => void }}
   */
  let { open = false, onclose } = $props();

  const ACTIONS = [
    {
      kind: 'Actions',
      id: 'act-deal',
      title: 'New deal',
      meta: 'Pipeline',
      href: '/pipeline/new',
      icon: Plus
    },
    {
      kind: 'Actions',
      id: 'act-today',
      title: 'Go to Today',
      meta: '',
      href: '/',
      icon: Columns3
    },
    {
      kind: 'Actions',
      id: 'act-tasks',
      title: 'Go to Tasks',
      meta: '',
      href: '/tasks',
      icon: Columns3
    },
    {
      kind: 'Actions',
      id: 'act-invoices',
      title: 'Go to Invoices',
      meta: '',
      href: '/invoices',
      icon: Receipt
    }
  ];

  const ICON = {
    Deals: Columns3,
    Accounts: Building2,
    Contacts: Users,
    Leads: Target,
    Tickets: LifeBuoy,
    Invoices: Receipt,
    'Knowledge base': BookOpen,
    Actions: Plus
  };

  let query = $state('');
  let hits = $state(/** @type {any[]} */ ([]));
  let cursor = $state(0);
  /** @type {HTMLInputElement | undefined} */
  let input = $state();

  let rows = $derived(query.trim() ? hits : ACTIONS);

  /** Grouped for display, but `rows` stays flat so ↑/↓ crosses group borders. */
  let groups = $derived(
    rows.reduce((acc, r) => {
      const g = acc.find((x) => x.kind === r.kind);
      if (g) g.rows.push(r);
      else acc.push({ kind: r.kind, rows: [r] });
      return acc;
    }, /** @type {{kind: string, rows: any[]}[]} */ ([]))
  );

  // Re-runs whenever the query changes. `seq` drops out-of-order responses,
  // which matters now that this is a network call rather than a filter. The
  // request goes to /api/search, a server route that scopes to the org and
  // keeps the httpOnly token off the client.
  let seq = 0;
  $effect(() => {
    const q = query;
    const mine = ++seq;
    if (!q.trim()) {
      hits = [];
      cursor = 0;
      return;
    }
    fetch(`/api/search?q=${encodeURIComponent(q)}`)
      .then((r) => r.json())
      .then((r) => {
        if (mine !== seq) return;
        hits = r.results || [];
        cursor = 0;
      })
      .catch(() => {
        if (mine !== seq) return;
        hits = [];
        cursor = 0;
      });
  });

  $effect(() => {
    if (open) input?.focus();
  });

  function onkeydown(e) {
    if (e.key === 'Escape') {
      e.preventDefault();
      onclose();
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      cursor = rows.length ? (cursor + 1) % rows.length : 0;
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      cursor = rows.length ? (cursor - 1 + rows.length) % rows.length : 0;
    } else if (e.key === 'Enter') {
      e.preventDefault();
      choose(rows[cursor]);
    }
  }

  function choose(row) {
    if (!row) return;
    onclose();
    query = '';
    goto(resolve(row.href));
  }
</script>

{#if open}
  <!--
    A backdrop click closes; that is a convenience, not the only way out, so
    the keyboard handler on the dialog carries Escape. Nothing here is
    reachable by mouse alone that is not also reachable by key alone.
  -->
  <div
    class="v2-scrim"
    role="presentation"
    onclick={(e) => {
      if (e.target === e.currentTarget) onclose();
    }}
  >
    <div
      class="v2-palette"
      role="dialog"
      aria-modal="true"
      aria-label="Search"
      tabindex="-1"
      {onkeydown}
    >
      <div class="v2-palette-input">
        <Search size={17} style="color:var(--v2-slate);flex:none" />
        <input
          bind:this={input}
          bind:value={query}
          type="text"
          placeholder="Search deals, accounts, people, tickets, invoices…"
          aria-label="Search"
          aria-autocomplete="list"
          autocomplete="off"
          spellcheck="false"
        />
        <kbd class="v2-kbd">esc</kbd>
      </div>

      <div class="v2-palette-list" role="listbox" aria-label="Results">
        {#each groups as group (group.kind)}
          <div class="v2-palette-group v2-label">{group.kind}</div>
          {#each group.rows as row (row.id)}
            {@const i = rows.indexOf(row)}
            {@const Icon = row.icon ?? ICON[row.kind] ?? Search}
            <button
              class="v2-palette-row"
              type="button"
              role="option"
              aria-selected={i === cursor}
              onmouseenter={() => (cursor = i)}
              onclick={() => choose(row)}
            >
              <Icon />
              <span style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap"
                >{row.title}</span
              >
              {#if row.meta}<span class="v2-palette-meta">{row.meta}</span>{/if}
            </button>
          {/each}
        {:else}
          <p class="v2-sub" style="padding:22px 15px;text-align:center;margin:0">
            Nothing matches “{query}”. Try an account name, a deal, or an invoice number.
          </p>
        {/each}
      </div>

      <div class="v2-palette-foot">
        <span><kbd class="v2-kbd">↑</kbd> <kbd class="v2-kbd">↓</kbd> move</span>
        <span><CornerDownLeft size={11} style="vertical-align:-1px" /> open</span>
        <span><kbd class="v2-kbd">esc</kbd> close</span>
        {#if query.trim()}
          <span style="margin-left:auto" class="v2-num">{hits.length} found</span>
        {/if}
      </div>
    </div>
  </div>
{/if}
