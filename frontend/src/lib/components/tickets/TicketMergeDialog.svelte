<script>
  import { enhance } from '$app/forms';
  import { goto } from '$app/navigation';
  import { toast } from 'svelte-sonner';
  import { GitMerge, Loader2 } from '@lucide/svelte';
  import { Button } from '$lib/components/ui/button/index.js';
  import * as Dialog from '$lib/components/ui/dialog/index.js';

  /** @type {{ ticketId: string, ticketSubject: string, open: boolean, onOpenChange: (v: boolean) => void }} */
  let { ticketId, ticketSubject, open = $bindable(false), onOpenChange } = $props();

  /** @type {string} */
  let query = $state('');
  /** @type {Array<{id: string, name: string, status: string, priority: string}>} */
  let candidates = $state([]);
  /** @type {{id: string, name: string} | null} */
  let selected = $state(null);
  let confirmText = $state('');
  let searching = $state(false);
  let submitting = $state(false);

  const shortId = (/** @type {string} */ id) =>
    (id || '').replace(/-/g, '').slice(0, 8);

  let searchTimer = /** @type {any} */ (null);

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
      const json = await res.json();
      candidates = (json.cases || [])
        .filter((/** @type {any} */ c) => c.id !== ticketId)
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

  function reset() {
    query = '';
    candidates = [];
    selected = null;
    confirmText = '';
  }

  $effect(() => {
    if (!open) reset();
  });

  const expectedConfirm = $derived(selected ? shortId(selected.id) : '');
  const confirmOk = $derived(
    selected != null && confirmText.toLowerCase() === expectedConfirm.toLowerCase()
  );
</script>

<Dialog.Root
  bind:open
  onOpenChange={(v) => {
    onOpenChange?.(v);
  }}
>
  <Dialog.Content class="sm:max-w-lg">
    <Dialog.Header>
      <Dialog.Title class="flex items-center gap-2">
        <GitMerge class="h-4 w-4" />
        Merge this ticket into another
      </Dialog.Title>
      <Dialog.Description>
        All comments, attachments, and inbound emails on
        <strong>{ticketSubject}</strong> will be moved to the primary. This ticket is
        kept as a "Duplicate" pointing to the primary. <strong>Undo is not available.</strong>
      </Dialog.Description>
    </Dialog.Header>

    <form
      method="POST"
      action="?/merge"
      use:enhance={() => {
        submitting = true;
        return async ({ result, update }) => {
          submitting = false;
          if (result.type === 'success') {
            const data = /** @type {any} */ (result.data);
            const sourceShort = shortId(data?.sourceId || ticketId);
            const targetId = data?.targetId;
            if (data?.alreadyMerged) {
              toast.message(`Already merged into #${shortId(targetId)}`);
            } else {
              toast.success(`Merged from #${sourceShort}`);
            }
            open = false;
            if (targetId) goto(`/tickets/${targetId}`);
            else await update();
          } else if (result.type === 'failure') {
            const data = /** @type {any} */ (result.data);
            toast.error(data?.error || 'Merge failed');
          } else {
            await update();
          }
        };
      }}
      class="space-y-3"
    >
      <input type="hidden" name="into_id" value={selected?.id || ''} />

      <div class="space-y-1">
        <label for="merge-target-search" class="text-sm font-medium">
          Search target ticket
        </label>
        <input
          id="merge-target-search"
          type="text"
          placeholder="Type a ticket name…"
          class="w-full rounded-md border border-[var(--border-default)] bg-[var(--surface-default)] px-3 py-2 text-sm"
          bind:value={query}
          autocomplete="off"
        />
      </div>

      {#if searching}
        <div class="flex items-center gap-2 text-xs text-[var(--text-secondary)]">
          <Loader2 class="h-3 w-3 animate-spin" />
          Searching…
        </div>
      {:else if query && candidates.length === 0}
        <p class="text-xs text-[var(--text-secondary)]">No matching cases.</p>
      {:else if candidates.length > 0 && !selected}
        <ul
          class="max-h-48 divide-y divide-[var(--border-default)] overflow-auto rounded-md border border-[var(--border-default)]"
        >
          {#each candidates as candidate (candidate.id)}
            <li>
              <button
                type="button"
                onclick={() => {
                  selected = { id: candidate.id, name: candidate.name };
                  candidates = [];
                  query = '';
                }}
                class="flex w-full items-start justify-between gap-2 px-3 py-2 text-left text-sm hover:bg-[var(--surface-sunken)]"
              >
                <span class="min-w-0 flex-1 truncate">{candidate.name}</span>
                <span
                  class="shrink-0 rounded bg-[var(--surface-sunken)] px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-[var(--text-secondary)]"
                >
                  {candidate.status}
                </span>
                <span
                  class="shrink-0 font-mono text-[10px] text-[var(--text-secondary)]"
                >
                  #{shortId(candidate.id)}
                </span>
              </button>
            </li>
          {/each}
        </ul>
      {/if}

      {#if selected}
        <div
          class="rounded-md border border-[var(--border-default)] bg-[var(--surface-sunken)] p-3 text-sm"
        >
          <div class="flex items-center justify-between gap-2">
            <span class="min-w-0 truncate font-medium">{selected.name}</span>
            <button
              type="button"
              onclick={() => (selected = null)}
              class="text-xs text-[var(--text-secondary)] underline"
            >
              Change
            </button>
          </div>
          <div class="mt-1 font-mono text-[10px] text-[var(--text-secondary)]">
            #{expectedConfirm}
          </div>
          <div class="mt-3 space-y-1">
            <label for="merge-confirm" class="text-xs font-medium">
              Type <code class="font-mono">{expectedConfirm}</code> to confirm:
            </label>
            <input
              id="merge-confirm"
              type="text"
              autocomplete="off"
              bind:value={confirmText}
              class="w-full rounded-md border border-[var(--border-default)] bg-[var(--surface-default)] px-3 py-2 font-mono text-sm"
            />
          </div>
        </div>
      {/if}

      <Dialog.Footer>
        <Button type="button" variant="outline" onclick={() => (open = false)}>
          Cancel
        </Button>
        <Button
          type="submit"
          disabled={!confirmOk || submitting}
          class="gap-1"
        >
          {#if submitting}
            <Loader2 class="h-3 w-3 animate-spin" />
          {/if}
          Merge into selected
        </Button>
      </Dialog.Footer>
    </form>
  </Dialog.Content>
</Dialog.Root>
