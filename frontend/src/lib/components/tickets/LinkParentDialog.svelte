<script>
  import { invalidateAll } from '$app/navigation';
  import { toast } from 'svelte-sonner';
  import { Loader2, Link as LinkIcon } from '@lucide/svelte';
  import { Button } from '$lib/components/ui/button/index.js';
  import * as Dialog from '$lib/components/ui/dialog/index.js';

  /**
   * Tier 3 parent/child: typeahead picker for assigning a parent ticket.
   * The candidate list is filtered to the current org by the search proxy
   * and additionally trimmed of (1) the ticket itself and (2) descendants
   * (resolved client-side from /tree/) so an agent cannot create a cycle.
   *
   * @type {{
   *   ticketId: string,
   *   open: boolean,
   *   onOpenChange: (v: boolean) => void,
   *   onLinked?: (parent: { id: string, name: string }) => void
   * }}
   */
  let {
    ticketId,
    open = $bindable(false),
    onOpenChange,
    onLinked
  } = $props();

  let query = $state('');
  /** @type {Array<{id: string, name: string, status: string, priority: string}>} */
  let candidates = $state([]);
  /** @type {{id: string, name: string} | null} */
  let selected = $state(null);
  let searching = $state(false);
  let submitting = $state(false);
  /** @type {Set<string>} */
  let descendantIds = $state(new Set());

  let searchTimer = /** @type {any} */ (null);

  async function fetchDescendants() {
    try {
      const res = await fetch(`/api/cases/${ticketId}/tree/`);
      if (!res.ok) return;
      const data = await res.json();
      const ids = new Set([ticketId]);
      const walk = (n) => {
        if (!n) return;
        ids.add(n.id);
        (n.children || []).forEach(walk);
      };
      walk(data.root);
      descendantIds = ids;
    } catch {
      descendantIds = new Set([ticketId]);
    }
  }

  $effect(() => {
    if (open) {
      fetchDescendants();
    } else {
      query = '';
      candidates = [];
      selected = null;
    }
  });

  /** @param {string} q */
  async function runSearch(q) {
    if (!q || q.length < 2) {
      candidates = [];
      return;
    }
    searching = true;
    try {
      const params = new URLSearchParams({ search: q, limit: '20' });
      const res = await fetch(`/api/cases/search?${params.toString()}`);
      if (!res.ok) {
        candidates = [];
        return;
      }
      const data = await res.json();
      candidates = (data.cases || [])
        .filter(
          (/** @type {any} */ c) =>
            !descendantIds.has(c.id) && c.status !== 'Duplicate'
        )
        .map((/** @type {any} */ c) => ({
          id: c.id,
          name: c.name,
          status: c.status,
          priority: c.priority
        }));
    } finally {
      searching = false;
    }
  }

  $effect(() => {
    if (searchTimer) clearTimeout(searchTimer);
    const q = query;
    searchTimer = setTimeout(() => runSearch(q), 200);
  });

  async function submit() {
    if (!selected) return;
    submitting = true;
    try {
      const res = await fetch(`/api/cases/${ticketId}/link/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ parent_id: selected.id })
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        toast.error(body?.error || 'Link failed');
        return;
      }
      onLinked?.({ id: selected.id, name: selected.name });
      open = false;
      await invalidateAll();
    } finally {
      submitting = false;
    }
  }
</script>

<Dialog.Root
  bind:open
  onOpenChange={(v) => onOpenChange?.(v)}
>
  <Dialog.Content class="sm:max-w-lg">
    <Dialog.Header>
      <Dialog.Title class="flex items-center gap-2">
        <LinkIcon class="h-4 w-4" />
        Link this ticket under a parent
      </Dialog.Title>
      <Dialog.Description>
        Pick the umbrella problem ticket. Tree depth is limited to three levels;
        descendants of the current ticket are not selectable.
      </Dialog.Description>
    </Dialog.Header>

    <div class="space-y-3">
      <div class="space-y-1">
        <label for="parent-search" class="text-sm font-medium">
          Search candidate parents
        </label>
        <input
          id="parent-search"
          type="text"
          placeholder="Type a ticket name…"
          class="w-full rounded-md border border-[var(--border-default)] bg-[var(--surface-default)] px-3 py-2 text-sm"
          bind:value={query}
          autocomplete="off"
        />
      </div>

      {#if searching}
        <div class="flex items-center gap-2 text-xs text-[var(--text-secondary)]">
          <Loader2 class="h-3.5 w-3.5 animate-spin" /> Searching…
        </div>
      {:else if candidates.length === 0 && query.length >= 2}
        <p class="text-xs text-[var(--text-secondary)]">No matches.</p>
      {:else if candidates.length > 0}
        <ul class="max-h-64 overflow-y-auto rounded border border-[var(--border-default)]">
          {#each candidates as c (c.id)}
            <li>
              <button
                type="button"
                class="flex w-full items-center justify-between gap-2 px-3 py-2 text-left text-sm hover:bg-[var(--surface-muted)] {selected?.id === c.id ? 'bg-[var(--surface-muted)] font-medium' : ''}"
                onclick={() => (selected = c)}
              >
                <span class="min-w-0 truncate">{c.name}</span>
                <span class="shrink-0 text-[10px] text-[var(--text-secondary)]">
                  {c.status} · {c.priority}
                </span>
              </button>
            </li>
          {/each}
        </ul>
      {/if}
    </div>

    <Dialog.Footer>
      <Button
        type="button"
        variant="outline"
        onclick={() => (open = false)}
        disabled={submitting}
      >
        Cancel
      </Button>
      <Button
        type="button"
        disabled={!selected || submitting}
        onclick={submit}
      >
        {#if submitting}<Loader2 class="mr-1 h-3.5 w-3.5 animate-spin" />{/if}
        Link parent
      </Button>
    </Dialog.Footer>
  </Dialog.Content>
</Dialog.Root>
