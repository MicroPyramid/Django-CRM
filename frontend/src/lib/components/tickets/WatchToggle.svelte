<script>
  import { untrack } from 'svelte';
  import { Eye, EyeOff, Loader2 } from '@lucide/svelte';
  import { toast } from 'svelte-sonner';
  import { Button } from '$lib/components/ui/button/index.js';
  import * as Popover from '$lib/components/ui/popover/index.js';

  /**
   * @type {{
   *   ticketId: string,
   *   currentUserId: string | null,
   *   initialWatchers?: Array<{
   *     id: string,
   *     profile_id: string,
   *     user_id: string | null,
   *     email: string,
   *     subscribed_via: string,
   *   }>,
   * }}
   */
  let { ticketId, currentUserId, initialWatchers = [] } = $props();

  // Snapshot the SSR-loaded list once; subsequent mutations are local.
  let watchers = $state(untrack(() => [...initialWatchers]));
  let busy = $state(false);
  let popoverOpen = $state(false);

  const isWatching = $derived(
    !!currentUserId && watchers.some((w) => w.user_id === currentUserId)
  );

  async function refresh() {
    try {
      const res = await fetch(`/api/cases/${ticketId}/watchers/`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      watchers = data.watchers || [];
    } catch (err) {
      console.error('watchers refresh failed', err);
    }
  }

  async function toggle() {
    if (busy) return;
    busy = true;
    const wasWatching = isWatching;
    try {
      const res = await fetch(`/api/cases/${ticketId}/watch/`, {
        method: wasWatching ? 'DELETE' : 'POST'
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      await refresh();
      toast.success(wasWatching ? 'Stopped watching' : 'Now watching');
    } catch (err) {
      console.error('watch toggle failed', err);
      toast.error('Could not update watch state.');
    } finally {
      busy = false;
    }
  }

  /** @param {string} via */
  const viaLabel = (via) =>
    ({
      manual: 'manual',
      mention: 'mentioned',
      auto_assignee: 'auto (assignee)',
      auto_team: 'auto (team)'
    })[via] || via;
</script>

<div class="flex items-stretch gap-1">
  <Button
    variant="outline"
    size="sm"
    class="gap-1"
    onclick={toggle}
    disabled={busy}
    aria-pressed={isWatching}
    title={isWatching ? 'Stop watching this ticket' : 'Watch this ticket'}
  >
    {#if busy}
      <Loader2 class="h-4 w-4 animate-spin" />
    {:else if isWatching}
      <Eye class="h-4 w-4 fill-current" />
    {:else}
      <EyeOff class="h-4 w-4" />
    {/if}
    {isWatching ? 'Watching' : 'Watch'}
  </Button>

  <Popover.Root bind:open={popoverOpen}>
    <Popover.Trigger asChild class="">
      {#snippet child({ props })}
        <Button
          {...props}
          variant="outline"
          size="sm"
          class="px-2"
          aria-label="Show watchers"
          title="Show watchers"
        >
          {watchers.length}
        </Button>
      {/snippet}
    </Popover.Trigger>
    <Popover.Content align="end" class="w-72 p-0">
      <div class="border-b border-[var(--border-default)] px-3 py-2 text-xs font-semibold uppercase tracking-wide text-[var(--text-secondary)]">
        Watchers ({watchers.length})
      </div>
      {#if watchers.length === 0}
        <div class="px-3 py-3 text-sm text-[var(--text-secondary)]">
          No one is watching this ticket yet.
        </div>
      {:else}
        <ul class="max-h-72 divide-y divide-[var(--border-default)] overflow-y-auto">
          {#each watchers as w (w.id)}
            <li class="flex items-center justify-between gap-2 px-3 py-2 text-sm">
              <span class="min-w-0 truncate">{w.email}</span>
              <span class="shrink-0 rounded-full bg-[var(--surface-muted)] px-1.5 py-0.5 text-[10px] text-[var(--text-secondary)]">
                {viaLabel(w.subscribed_via)}
              </span>
            </li>
          {/each}
        </ul>
      {/if}
    </Popover.Content>
  </Popover.Root>
</div>
