<script>
  import { invalidateAll } from '$app/navigation';
  import { onMount } from 'svelte';
  import { toast } from 'svelte-sonner';
  import { Loader2 } from '@lucide/svelte';
  import { Button } from '$lib/components/ui/button/index.js';
  import * as Dialog from '$lib/components/ui/dialog/index.js';

  /**
   * Tier 3 parent/child: confirm closing a parent ticket, with an explicit
   * checkbox for cascading the close to its open descendants. We always
   * show the open descendants up-front so the user sees the blast radius.
   *
   * @type {{
   *   ticketId: string,
   *   ticketSubject: string,
   *   childCount: number,
   *   open: boolean,
   *   onOpenChange: (v: boolean) => void
   * }}
   */
  let {
    ticketId,
    ticketSubject,
    childCount,
    open = $bindable(false),
    onOpenChange
  } = $props();

  let cascade = $state(true);
  let comment = $state('');
  let submitting = $state(false);
  /** @type {Array<{id: string, name: string, status: string}>} */
  let openDescendants = $state([]);
  let loading = $state(false);

  $effect(() => {
    if (open) loadOpenDescendants();
    else {
      cascade = true;
      comment = '';
      openDescendants = [];
    }
  });

  async function loadOpenDescendants() {
    loading = true;
    try {
      const res = await fetch(`/api/cases/${ticketId}/tree/`);
      if (!res.ok) return;
      const data = await res.json();
      const acc = [];
      const walk = (n) => {
        if (!n) return;
        if (n.id !== ticketId && n.status !== 'Closed') {
          acc.push({ id: n.id, name: n.name, status: n.status });
        }
        (n.children || []).forEach(walk);
      };
      walk(data.root);
      openDescendants = acc;
    } finally {
      loading = false;
    }
  }

  async function submit() {
    submitting = true;
    try {
      const res = await fetch(`/api/cases/${ticketId}/close-with-children/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ resolution_comment: comment, cascade })
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        toast.error(body?.error || 'Close failed');
        return;
      }
      const data = await res.json();
      const n = (data.cascaded_case_ids || []).length;
      toast.success(
        n > 0
          ? `Ticket closed; ${n} child ticket${n === 1 ? '' : 's'} cascaded.`
          : 'Ticket closed.'
      );
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
      <Dialog.Title>Close ticket with children</Dialog.Title>
      <Dialog.Description>
        Close <strong>{ticketSubject}</strong>{childCount > 0
          ? ` and review the ${childCount} linked child ticket${childCount === 1 ? '' : 's'} below.`
          : '.'}
      </Dialog.Description>
    </Dialog.Header>

    <div class="space-y-3">
      {#if loading}
        <div class="flex items-center gap-2 text-xs text-[var(--text-secondary)]">
          <Loader2 class="h-3.5 w-3.5 animate-spin" /> Inspecting ticket tree…
        </div>
      {:else if openDescendants.length > 0}
        <div class="rounded-md border border-amber-200 bg-amber-50 p-3 text-sm dark:border-amber-900/40 dark:bg-amber-900/20">
          <p class="mb-1 font-medium text-amber-900 dark:text-amber-100">
            {openDescendants.length} open child ticket{openDescendants.length === 1 ? '' : 's'}:
          </p>
          <ul class="space-y-0.5 text-xs">
            {#each openDescendants as d (d.id)}
              <li class="flex items-center justify-between gap-2">
                <span class="min-w-0 truncate">{d.name}</span>
                <span class="shrink-0 rounded bg-white/60 px-1 py-0.5 text-[10px] dark:bg-black/20">{d.status}</span>
              </li>
            {/each}
          </ul>
        </div>
      {:else if childCount > 0}
        <p class="text-xs text-[var(--text-secondary)]">
          All linked children are already closed. Cascade is a no-op.
        </p>
      {/if}

      <label class="flex items-start gap-2 text-sm">
        <input
          type="checkbox"
          class="mt-1"
          bind:checked={cascade}
          disabled={openDescendants.length === 0}
        />
        <span>
          <span class="font-medium">Also close all open children</span>
          <span class="block text-xs text-[var(--text-secondary)]">
            Adds a "PARENT_CLOSED_CASCADE" audit row to each child.
          </span>
        </span>
      </label>

      <div class="space-y-1">
        <label for="resolution-comment" class="text-sm font-medium">
          Resolution comment (optional)
        </label>
        <textarea
          id="resolution-comment"
          bind:value={comment}
          rows="3"
          placeholder="Shared note recorded against each cascaded child"
          class="w-full rounded-md border border-[var(--border-default)] bg-[var(--surface-default)] p-2 text-sm"
        ></textarea>
      </div>
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
      <Button type="button" disabled={submitting} onclick={submit}>
        {#if submitting}<Loader2 class="mr-1 h-3.5 w-3.5 animate-spin" />{/if}
        Close ticket
      </Button>
    </Dialog.Footer>
  </Dialog.Content>
</Dialog.Root>
