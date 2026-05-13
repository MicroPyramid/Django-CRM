<script>
  import { toast } from 'svelte-sonner';
  import * as Popover from '$lib/components/ui/popover/index.js';
  import { Button } from '$lib/components/ui/button/index.js';
  import { Input } from '$lib/components/ui/input/index.js';
  import { BookOpen, Loader2, Plus, Search } from '@lucide/svelte';

  /**
   * Agent-facing KB suggester. Typeahead over published solutions in the
   * org; "Insert" pastes the solution body into the active textarea AND
   * records the ticket↔solution link via the existing endpoint.
   *
   * @type {{
   *   ticketId: string,
   *   onInsert: (body: string) => void,
   *   disabled?: boolean
   * }}
   */
  let { ticketId, onInsert, disabled = false } = $props();

  let open = $state(false);
  let query = $state('');
  let loading = $state(false);
  let insertingId = $state(/** @type {string | null} */ (null));
  /** @type {Array<{ id: string, title: string, snippet: string, body: string, updated_at: string | null }>} */
  let results = $state([]);

  /** @type {ReturnType<typeof setTimeout> | null} */
  let debounceTimer = null;

  async function fetchSuggestions(/** @type {string} */ q) {
    loading = true;
    try {
      const u = new URL(
        `/api/cases/${ticketId}/solution-suggestions/`,
        window.location.origin
      );
      if (q) u.searchParams.set('q', q);
      const res = await fetch(u);
      if (!res.ok) throw new Error('Failed to load solutions');
      const data = await res.json();
      results = data?.results || [];
    } catch (err) {
      console.error(err);
      toast.error('Failed to load solutions');
    } finally {
      loading = false;
    }
  }

  // Fetch on open + on query change (debounced).
  $effect(() => {
    if (!open) return;
    if (debounceTimer) clearTimeout(debounceTimer);
    const q = query;
    debounceTimer = setTimeout(() => {
      fetchSuggestions(q);
    }, 300);
  });

  /** @param {{ id: string, title: string, snippet: string, body: string }} solution */
  async function insert(solution) {
    insertingId = solution.id;
    try {
      onInsert(solution.body || solution.snippet);
      // Best-effort: record the link. Failure here doesn't block the insert
      // because the agent has already pasted the body and is mid-edit.
      fetch(`/api/cases/${ticketId}/solutions/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ solution_id: solution.id })
      }).catch((err) => {
        console.warn('Failed to record solution link:', err);
      });
      open = false;
      query = '';
    } catch (err) {
      console.error(err);
      toast.error('Failed to insert solution');
    } finally {
      insertingId = null;
    }
  }
</script>

<Popover.Root bind:open>
  <Popover.Trigger asChild class="">
    {#snippet child({ props })}
      <Button
        {...props}
        type="button"
        variant="ghost"
        size="sm"
        {disabled}
        class="gap-1.5 text-xs"
        title="Suggest a knowledge-base article"
      >
        <BookOpen class="h-3.5 w-3.5" />
        Solutions
      </Button>
    {/snippet}
  </Popover.Trigger>
  <Popover.Content class="w-96 p-0" align="end">
    <div class="border-b border-[var(--border-default)] p-2">
      <div class="relative">
        <Search
          class="pointer-events-none absolute top-1/2 left-2 h-3.5 w-3.5 -translate-y-1/2 text-[var(--text-secondary)]"
        />
        <Input
          type="text"
          placeholder="Search solutions…"
          bind:value={query}
          class="h-8 pl-7 text-sm"
        />
      </div>
    </div>
    <div class="max-h-80 overflow-y-auto">
      {#if loading && results.length === 0}
        <div
          class="flex items-center justify-center gap-2 p-4 text-xs text-[var(--text-secondary)]"
        >
          <Loader2 class="h-3.5 w-3.5 animate-spin" /> Loading…
        </div>
      {:else if results.length === 0}
        <div class="p-4 text-center text-xs text-[var(--text-secondary)]">
          No published solutions matched.
        </div>
      {:else}
        <ul>
          {#each results as s (s.id)}
            <li class="border-b border-[var(--border-default)]/40 last:border-b-0">
              <div class="flex items-start gap-2 px-3 py-2">
                <div class="min-w-0 flex-1">
                  <div class="text-sm font-medium text-[var(--text-primary)]">
                    {s.title}
                  </div>
                  <div
                    class="mt-0.5 line-clamp-3 text-xs text-[var(--text-secondary)]"
                  >
                    {s.snippet}
                  </div>
                </div>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  class="shrink-0 gap-1 text-xs"
                  disabled={insertingId !== null}
                  onclick={() => insert(s)}
                  title="Insert this solution into the reply"
                >
                  {#if insertingId === s.id}
                    <Loader2 class="h-3.5 w-3.5 animate-spin" />
                  {:else}
                    <Plus class="h-3.5 w-3.5" />
                  {/if}
                  Insert
                </Button>
              </div>
            </li>
          {/each}
        </ul>
      {/if}
    </div>
  </Popover.Content>
</Popover.Root>
