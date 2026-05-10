<script>
  import { goto } from '$app/navigation';
  import { toast } from 'svelte-sonner';
  import {
    Network,
    Loader2,
    Link as LinkIcon,
    Unlink,
    Asterisk
  } from '@lucide/svelte';
  import { Button } from '$lib/components/ui/button/index.js';
  import LinkParentDialog from './LinkParentDialog.svelte';

  /**
   * Tier 3 parent/child: shows the descendant tree (or "this is a child of X"
   * banner) on a ticket detail page. Hidden entirely when the ticket has no
   * parent and no children, behind a "Link parent" affordance.
   *
   * @type {{
   *   ticketId: string,
   *   parentSummary: { id: string, name: string, status: string } | null,
   *   isProblem: boolean,
   *   childCount: number,
   *   onLinkChange?: () => void
   * }}
   */
  let {
    ticketId,
    parentSummary,
    isProblem,
    childCount,
    onLinkChange
  } = $props();

  /** @type {{ root: any, focus_id: string } | null} */
  let tree = $state(null);
  let loading = $state(false);
  let linkOpen = $state(false);
  let unlinking = $state(false);

  const hasGraph = $derived(parentSummary !== null || childCount > 0);

  // Reload the tree on mount AND whenever the graph signal flips — link/
  // unlink calls invalidateAll() upstream, which refreshes parentSummary /
  // childCount; without this effect the tree stays null on a freshly-linked
  // ticket and the section renders empty under the Unlink button.
  $effect(() => {
    if (hasGraph) loadTree();
    else tree = null;
  });

  async function loadTree() {
    loading = true;
    try {
      const res = await fetch(`/api/cases/${ticketId}/tree/`);
      if (!res.ok) throw new Error(`tree ${res.status}`);
      tree = await res.json();
    } catch (err) {
      console.error(err);
      toast.error('Failed to load ticket tree');
    } finally {
      loading = false;
    }
  }

  async function unlinkParent() {
    if (!parentSummary) return;
    if (!window.confirm('Unlink this ticket from its parent?')) return;
    unlinking = true;
    try {
      const res = await fetch(`/api/cases/${ticketId}/link/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ parent_id: null })
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        toast.error(body?.error || 'Failed to unlink');
        return;
      }
      toast.success('Parent unlinked');
      onLinkChange?.();
    } finally {
      unlinking = false;
    }
  }

  /** @param {{ id: string, name: string }} parent */
  function onLinked(parent) {
    toast.success(`Linked under "${parent.name}"`);
    onLinkChange?.();
  }

  /** @param {string} status */
  function statusClass(status) {
    if (status === 'Closed') return 'bg-emerald-100 text-emerald-800';
    if (status === 'Pending') return 'bg-amber-100 text-amber-800';
    if (status === 'Duplicate') return 'bg-zinc-200 text-zinc-700';
    return 'bg-blue-100 text-blue-800';
  }
</script>

<section class="rounded-lg border border-[var(--border-default)] bg-[var(--surface-default)] p-4">
  <div class="mb-3 flex items-center justify-between">
    <h3 class="flex items-center gap-2 text-sm font-medium text-[var(--text-secondary)]">
      <Network class="h-4 w-4" />
      Ticket tree
      {#if isProblem}
        <span class="inline-flex items-center gap-1 rounded bg-purple-100 px-1.5 py-0.5 text-[10px] font-semibold text-purple-700">
          <Asterisk class="h-2.5 w-2.5" /> PROBLEM
        </span>
      {/if}
    </h3>
    <div class="flex items-center gap-1">
      {#if parentSummary}
        <Button
          type="button"
          variant="ghost"
          size="sm"
          class="gap-1 text-xs"
          disabled={unlinking}
          onclick={unlinkParent}
        >
          <Unlink class="h-3.5 w-3.5" />
          Unlink parent
        </Button>
      {:else}
        <Button
          type="button"
          variant="ghost"
          size="sm"
          class="gap-1 text-xs"
          onclick={() => (linkOpen = true)}
        >
          <LinkIcon class="h-3.5 w-3.5" />
          Link parent
        </Button>
      {/if}
    </div>
  </div>

  {#if !hasGraph}
    <p class="text-xs text-[var(--text-secondary)]">
      This ticket is standalone. Link it under a parent to coordinate related
      tickets together.
    </p>
  {:else if loading}
    <div class="flex items-center gap-2 text-xs text-[var(--text-secondary)]">
      <Loader2 class="h-3.5 w-3.5 animate-spin" /> Loading tree…
    </div>
  {:else if tree}
    <ul class="space-y-1 text-sm">
      {@render node(tree.root, 0, tree.focus_id)}
    </ul>
  {/if}
</section>

{#snippet node(n, depth, focusId)}
  <li>
    <div
      class="flex items-center gap-2 rounded px-2 py-1 hover:bg-[var(--surface-muted)] {n.id === focusId ? 'bg-[var(--surface-muted)] font-medium' : ''}"
      style="padding-left: {depth * 16 + 8}px"
    >
      <button
        type="button"
        class="min-w-0 flex-1 truncate text-left hover:text-[var(--color-primary-default)]"
        onclick={() => goto(`/tickets/${n.id}`)}
      >
        {n.name}
        {#if n.is_problem}
          <span class="ml-1 inline-flex items-center rounded bg-purple-100 px-1 py-0.5 text-[9px] font-semibold text-purple-700">P</span>
        {/if}
      </button>
      <span class="rounded px-1.5 py-0.5 text-[10px] font-medium {statusClass(n.status)}">
        {n.status}
      </span>
    </div>
    {#if n.children?.length}
      <ul class="space-y-1">
        {#each n.children as child (child.id)}
          {@render node(child, depth + 1, focusId)}
        {/each}
      </ul>
    {:else if n.truncated}
      <p
        class="text-[11px] italic text-[var(--text-secondary)]"
        style="padding-left: {(depth + 1) * 16 + 8}px"
      >
        Tree truncated at this depth.
      </p>
    {/if}
  </li>
{/snippet}

<LinkParentDialog
  ticketId={ticketId}
  bind:open={linkOpen}
  onOpenChange={(v) => (linkOpen = v)}
  onLinked={onLinked}
/>
