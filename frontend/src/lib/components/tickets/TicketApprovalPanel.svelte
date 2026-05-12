<script>
  import { invalidateAll } from '$app/navigation';
  import { onMount, untrack } from 'svelte';
  import { toast } from 'svelte-sonner';
  import { ShieldCheck, Loader2, X, Check, Ban } from '@lucide/svelte';
  import { Button } from '$lib/components/ui/button/index.js';

  /**
   * Tier 3 approvals: pane on the ticket detail page.
   *
   * Three modes are rendered, depending on what we find on the ticket:
   *   1. There is at least one approval row → show the most recent + actions.
   *   2. No approvals exist but the agent can hit "Request approval".
   *   3. The latest is rejected → show the reason inline.
   *
   * The "Request approval to close" affordance auto-resolves the rule
   * server-side; if no rule matches, the API responds 400 and we surface that.
   *
   * `initialApprovals` is supplied by `+page.server.js` so the panel paints
   * fully populated on first render — the post-mount fetch is only a fallback
   * for callers that didn't seed the data.
   *
   * @type {{
   *   ticketId: string,
   *   currentProfileId?: string,
   *   isAdmin?: boolean,
   *   initialApprovals?: Array<any>
   * }}
   */
  let { ticketId, currentProfileId, isAdmin = false, initialApprovals } = $props();

  /** @type {Array<any>} */
  let approvals = $state(untrack(() => initialApprovals ?? []));
  let loading = $state(untrack(() => initialApprovals === undefined));
  let pending = $state(false);
  let rejectReason = $state('');
  let rejectingId = $state(/** @type {string | null} */ (null));
  let note = $state('');

  const latest = $derived(approvals.length > 0 ? approvals[0] : null);
  const hasOpen = $derived(latest && latest.state === 'pending');
  const canActOnLatest = $derived(latestActionable(latest));
  // After the latest request has been cancelled or rejected, the workflow is
  // finished but the ticket still needs approval — let the agent fire a fresh
  // request without leaving the page.
  const canRerequest = $derived(
    latest && (latest.state === 'cancelled' || latest.state === 'rejected')
  );

  onMount(() => {
    if (initialApprovals === undefined) load();
  });

  async function load() {
    loading = true;
    try {
      const res = await fetch(`/api/cases/approvals/?case=${ticketId}&state=all`);
      if (!res.ok) {
        approvals = [];
        return;
      }
      const body = await res.json();
      approvals = body?.approvals || [];
    } finally {
      loading = false;
    }
  }

  /** @param {any} entry */
  function latestActionable(entry) {
    if (!entry || entry.state !== 'pending') return false;
    // Heuristic: anyone in the rule's approver pool, OR an admin role match.
    // The backend is authoritative — we just hide the buttons we know
    // would 403 to keep the UI from teasing actions the user can't take.
    const role = entry.rule_summary?.approver_role;
    if (isAdmin && role === 'ADMIN') return true;
    // Without the explicit approver list (kept off the inbox payload to keep
    // it small), fall back to "show buttons; let the server reject it".
    return true;
  }

  async function requestApproval() {
    pending = true;
    try {
      const res = await fetch(`/api/cases/${ticketId}/request-approval/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ note })
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        toast.error(body?.error || body?.errors || 'Approval request failed');
        return;
      }
      toast.success('Approval requested');
      note = '';
      await load();
      await invalidateAll();
    } finally {
      pending = false;
    }
  }

  /** @param {string} id */
  async function approve(id) {
    pending = true;
    try {
      const res = await fetch(`/api/cases/approvals/${id}/approve/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        toast.error(body?.error || 'Approve failed');
        return;
      }
      toast.success('Approved');
      await load();
      await invalidateAll();
    } finally {
      pending = false;
    }
  }

  /** @param {string} id */
  async function reject(id) {
    if (!rejectReason.trim()) {
      toast.error('Reason is required.');
      return;
    }
    pending = true;
    try {
      const res = await fetch(`/api/cases/approvals/${id}/reject/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason: rejectReason })
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        toast.error(body?.error || 'Reject failed');
        return;
      }
      toast.success('Rejected');
      rejectReason = '';
      rejectingId = null;
      await load();
    } finally {
      pending = false;
    }
  }

  /** @param {string} id */
  async function cancel(id) {
    if (!window.confirm('Cancel this approval request?')) return;
    pending = true;
    try {
      const res = await fetch(`/api/cases/approvals/${id}/cancel/`, {
        method: 'POST'
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        toast.error(body?.error || 'Cancel failed');
        return;
      }
      toast.success('Cancelled');
      await load();
    } finally {
      pending = false;
    }
  }

  /** @param {string} state */
  function badgeClass(state) {
    switch (state) {
      case 'pending':
        return 'bg-amber-100 text-amber-900 dark:bg-amber-900/30 dark:text-amber-200';
      case 'approved':
        return 'bg-emerald-100 text-emerald-900 dark:bg-emerald-900/30 dark:text-emerald-200';
      case 'rejected':
        return 'bg-red-100 text-red-900 dark:bg-red-900/30 dark:text-red-200';
      case 'cancelled':
        return 'bg-[var(--surface-muted)] text-[var(--text-secondary)]';
      default:
        return 'bg-[var(--surface-muted)] text-[var(--text-secondary)]';
    }
  }
</script>

<section
  class="rounded-md border border-[var(--border-default)] bg-[var(--surface-default)] p-3 text-sm"
>
  <header class="mb-2 flex items-center gap-2">
    <ShieldCheck class="h-4 w-4 text-[var(--text-secondary)]" />
    <h3 class="font-medium">Approvals</h3>
    {#if loading}
      <Loader2 class="ml-auto h-3.5 w-3.5 animate-spin text-[var(--text-secondary)]" />
    {/if}
  </header>

  {#if loading}
    <p class="text-xs text-[var(--text-secondary)]">Checking…</p>
  {:else if !latest}
    <div class="space-y-2">
      <p class="text-xs text-[var(--text-secondary)]">
        No approval has been requested for this ticket yet.
      </p>
      <textarea
        bind:value={note}
        rows="2"
        placeholder="Optional note for the approver"
        class="w-full rounded border border-[var(--border-default)] bg-[var(--surface-default)] p-2 text-xs"
      ></textarea>
      <Button
        size="sm"
        variant="outline"
        disabled={pending}
        onclick={requestApproval}
      >
        {#if pending}<Loader2 class="mr-1 h-3.5 w-3.5 animate-spin" />{/if}
        Request approval to close
      </Button>
    </div>
  {:else}
    <div class="space-y-2">
      <div class="flex items-center justify-between">
        <span class="text-xs text-[var(--text-secondary)]">
          {latest.rule_summary?.name || 'Rule'}
        </span>
        <span
          class={`rounded px-2 py-0.5 text-[10px] font-medium uppercase ${badgeClass(latest.state)}`}
        >
          {latest.state}
        </span>
      </div>

      <p class="text-xs text-[var(--text-secondary)]">
        Requested by {latest.requested_by?.email || 'unknown'}
        {#if latest.note}
          — <span class="italic">"{latest.note}"</span>
        {/if}
      </p>

      {#if latest.state === 'rejected' && latest.reason}
        <p class="rounded bg-red-50 p-2 text-xs text-red-900 dark:bg-red-900/30 dark:text-red-200">
          <strong>Rejected:</strong> {latest.reason}
        </p>
      {/if}

      {#if hasOpen && canActOnLatest}
        <div class="flex flex-wrap items-center gap-2 pt-1">
          <Button
            size="sm"
            disabled={pending}
            onclick={() => approve(latest.id)}
          >
            <Check class="mr-1 h-3.5 w-3.5" />
            Approve
          </Button>
          <Button
            size="sm"
            variant="outline"
            disabled={pending}
            onclick={() => (rejectingId = rejectingId === latest.id ? null : latest.id)}
          >
            <X class="mr-1 h-3.5 w-3.5" />
            Reject
          </Button>
          {#if currentProfileId && latest.requested_by?.id === currentProfileId}
            <Button
              size="sm"
              variant="ghost"
              disabled={pending}
              onclick={() => cancel(latest.id)}
            >
              <Ban class="mr-1 h-3.5 w-3.5" />
              Cancel my request
            </Button>
          {:else if isAdmin}
            <Button
              size="sm"
              variant="ghost"
              disabled={pending}
              onclick={() => cancel(latest.id)}
            >
              <Ban class="mr-1 h-3.5 w-3.5" />
              Cancel (admin)
            </Button>
          {/if}
        </div>

        {#if rejectingId === latest.id}
          <textarea
            bind:value={rejectReason}
            rows="2"
            placeholder="Reason for rejection (required)"
            class="w-full rounded border border-[var(--border-default)] bg-[var(--surface-default)] p-2 text-xs"
          ></textarea>
          <Button
            size="sm"
            variant="outline"
            disabled={pending || !rejectReason.trim()}
            onclick={() => reject(latest.id)}
          >
            Confirm rejection
          </Button>
        {/if}
      {/if}

      {#if canRerequest}
        <div class="mt-2 space-y-2 border-t border-[var(--border-default)] pt-2">
          <p class="text-xs text-[var(--text-secondary)]">
            Send a new approval request for this ticket.
          </p>
          <textarea
            bind:value={note}
            rows="2"
            placeholder="Optional note for the approver"
            class="w-full rounded border border-[var(--border-default)] bg-[var(--surface-default)] p-2 text-xs"
          ></textarea>
          <Button
            size="sm"
            variant="outline"
            disabled={pending}
            onclick={requestApproval}
          >
            {#if pending}<Loader2 class="mr-1 h-3.5 w-3.5 animate-spin" />{/if}
            Request approval again
          </Button>
        </div>
      {/if}

      {#if approvals.length > 1}
        <details class="pt-1 text-xs">
          <summary class="cursor-pointer text-[var(--text-secondary)] hover:text-[var(--text-primary)]">
            Earlier requests ({approvals.length - 1})
          </summary>
          <ul class="mt-1 space-y-1">
            {#each approvals.slice(1) as a (a.id)}
              <li class="rounded bg-[var(--surface-muted)] p-1.5">
                <span class={`mr-2 rounded px-1.5 py-0.5 text-[10px] font-medium uppercase ${badgeClass(a.state)}`}>
                  {a.state}
                </span>
                <span class="text-[var(--text-secondary)]">
                  {a.rule_summary?.name || 'Rule'} ·
                  {new Date(a.created_at).toLocaleDateString()}
                </span>
              </li>
            {/each}
          </ul>
        </details>
      {/if}
    </div>
  {/if}
</section>
