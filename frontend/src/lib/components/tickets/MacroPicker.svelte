<script>
  import { toast } from 'svelte-sonner';
  import * as Popover from '$lib/components/ui/popover/index.js';
  import { Button } from '$lib/components/ui/button/index.js';
  import { Input } from '$lib/components/ui/input/index.js';
  import { Loader2, MessageSquareQuote, Search } from '@lucide/svelte';

  /**
   * @type {{
   *   ticketId: string,
   *   onApply: (renderedBody: string) => void,
   *   disabled?: boolean
   * }}
   */
  let { ticketId, onApply, disabled = false } = $props();

  let open = $state(false);
  /** @type {Array<{ id: string, title: string, body: string, scope: 'org' | 'personal' }>} */
  let macros = $state([]);
  let query = $state('');
  let loading = $state(false);
  let applyingId = $state(/** @type {string | null} */ (null));

  // Fetch lazily on first open. We keep the cached list across re-opens
  // since macros change rarely; the settings page re-fetches authoritatively.
  let fetched = $state(false);

  async function ensureLoaded() {
    if (fetched) return;
    loading = true;
    try {
      const res = await fetch('/api/macros/');
      if (!res.ok) throw new Error('Failed to load macros');
      const data = await res.json();
      macros = data?.results || [];
      fetched = true;
    } catch (err) {
      console.error(err);
      toast.error('Failed to load macros');
    } finally {
      loading = false;
    }
  }

  $effect(() => {
    if (open) ensureLoaded();
  });

  const filtered = $derived.by(() => {
    const q = query.trim().toLowerCase();
    if (!q) return macros;
    return macros.filter(
      (m) =>
        m.title.toLowerCase().includes(q) || m.body.toLowerCase().includes(q)
    );
  });

  const orgGroup = $derived(filtered.filter((m) => m.scope === 'org'));
  const personalGroup = $derived(filtered.filter((m) => m.scope === 'personal'));

  /** @param {{ id: string, title: string, body: string, scope: string }} macro */
  async function apply(macro) {
    applyingId = macro.id;
    try {
      const res = await fetch(`/api/macros/${macro.id}/render/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ case_id: ticketId })
      });
      if (!res.ok) {
        const errBody = await res.json().catch(() => ({}));
        toast.error(errBody?.error || 'Failed to apply macro');
        return;
      }
      const data = await res.json();
      onApply(data?.rendered_body || macro.body);
      open = false;
      query = '';
    } catch (err) {
      console.error(err);
      toast.error('Failed to apply macro');
    } finally {
      applyingId = null;
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
        title="Insert a saved macro"
      >
        <MessageSquareQuote class="h-3.5 w-3.5" />
        Macros
      </Button>
    {/snippet}
  </Popover.Trigger>
  <Popover.Content class="w-80 p-0" align="end">
    <div class="border-b border-[var(--border-default)] p-2">
      <div class="relative">
        <Search
          class="pointer-events-none absolute top-1/2 left-2 h-3.5 w-3.5 -translate-y-1/2 text-[var(--text-secondary)]"
        />
        <Input
          type="text"
          placeholder="Search macros…"
          bind:value={query}
          class="h-8 pl-7 text-sm"
        />
      </div>
    </div>
    <div class="max-h-72 overflow-y-auto">
      {#if loading}
        <div
          class="flex items-center justify-center gap-2 p-4 text-xs text-[var(--text-secondary)]"
        >
          <Loader2 class="h-3.5 w-3.5 animate-spin" /> Loading macros…
        </div>
      {:else if filtered.length === 0}
        <div class="p-4 text-center text-xs text-[var(--text-secondary)]">
          {macros.length === 0 ? 'No macros configured.' : 'No matches.'}
        </div>
      {:else}
        {#if personalGroup.length > 0}
          <div class="px-3 pt-2 pb-1 text-[10px] font-semibold tracking-wider text-[var(--text-secondary)] uppercase">
            My macros
          </div>
          <ul>
            {#each personalGroup as m (m.id)}
              <li>
                <button
                  type="button"
                  class="flex w-full items-start gap-2 px-3 py-2 text-left text-sm hover:bg-[var(--surface-muted)] disabled:opacity-50"
                  disabled={applyingId !== null}
                  onclick={() => apply(m)}
                >
                  <span class="min-w-0 flex-1">
                    <span class="block truncate font-medium">{m.title}</span>
                    <span
                      class="mt-0.5 line-clamp-2 block text-xs text-[var(--text-secondary)]"
                    >
                      {m.body}
                    </span>
                  </span>
                  {#if applyingId === m.id}
                    <Loader2 class="h-3.5 w-3.5 animate-spin" />
                  {/if}
                </button>
              </li>
            {/each}
          </ul>
        {/if}
        {#if orgGroup.length > 0}
          <div class="px-3 pt-2 pb-1 text-[10px] font-semibold tracking-wider text-[var(--text-secondary)] uppercase">
            Org macros
          </div>
          <ul>
            {#each orgGroup as m (m.id)}
              <li>
                <button
                  type="button"
                  class="flex w-full items-start gap-2 px-3 py-2 text-left text-sm hover:bg-[var(--surface-muted)] disabled:opacity-50"
                  disabled={applyingId !== null}
                  onclick={() => apply(m)}
                >
                  <span class="min-w-0 flex-1">
                    <span class="block truncate font-medium">{m.title}</span>
                    <span
                      class="mt-0.5 line-clamp-2 block text-xs text-[var(--text-secondary)]"
                    >
                      {m.body}
                    </span>
                  </span>
                  {#if applyingId === m.id}
                    <Loader2 class="h-3.5 w-3.5 animate-spin" />
                  {/if}
                </button>
              </li>
            {/each}
          </ul>
        {/if}
      {/if}
    </div>
  </Popover.Content>
</Popover.Root>
