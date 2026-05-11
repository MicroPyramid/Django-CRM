<script>
  import { goto, invalidateAll } from '$app/navigation';
  import { page } from '$app/state';
  import { toast } from 'svelte-sonner';
  import { ShieldCheck, Loader2, Check, X, Ban } from '@lucide/svelte';
  import PageHeader from '$lib/components/layout/PageHeader.svelte';
  import { Button } from '$lib/components/ui/button/index.js';

  /** @type {{ data: any }} */
  let { data } = $props();

  const approvals = $derived(data.approvals || []);
  const tab = $derived(data.tab);
  const stateFilter = $derived(data.stateFilter);
  const isAdmin = $derived(!!data.isAdmin);

  let pending = $state(false);
  let rejectReason = $state('');
  let rejectingId = $state(/** @type {string | null} */ (null));

  function setTab(/** @type {'mine'|'all'} */ next) {
    const url = new URL(page.url);
    url.searchParams.set('tab', next);
    goto(url.pathname + '?' + url.searchParams.toString());
  }

  function setState(/** @type {string} */ next) {
    const url = new URL(page.url);
    url.searchParams.set('state', next);
    goto(url.pathname + '?' + url.searchParams.toString());
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
      rejectingId = null;
      rejectReason = '';
      await invalidateAll();
    } finally {
      pending = false;
    }
  }

  /** @param {string} id */
  async function cancel(id) {
    if (!window.confirm('Cancel this request?')) return;
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
      await invalidateAll();
    } finally {
      pending = false;
    }
  }

  /** @param {string} state */
  function badgeClass(state) {
    if (state === 'pending')
      return 'bg-amber-100 text-amber-900 dark:bg-amber-900/30 dark:text-amber-200';
    if (state === 'approved')
      return 'bg-emerald-100 text-emerald-900 dark:bg-emerald-900/30 dark:text-emerald-200';
    if (state === 'rejected')
      return 'bg-red-100 text-red-900 dark:bg-red-900/30 dark:text-red-200';
    return 'bg-[var(--surface-muted)] text-[var(--text-secondary)]';
  }
</script>

<svelte:head>
  <title>Approvals - BottleCRM</title>
</svelte:head>

<PageHeader title="Approvals">
  {#snippet titleIcon()}
    <ShieldCheck class="size-4" />
  {/snippet}
</PageHeader>

<div class="flex flex-col gap-4 p-4">
  <div class="flex flex-wrap items-center gap-3 text-sm">
    <div class="inline-flex rounded-md border border-[var(--border-default)] p-0.5">
      <button
        type="button"
        onclick={() => setTab('mine')}
        class="rounded px-3 py-1 text-xs {tab === 'mine'
          ? 'bg-[var(--surface-muted)] font-medium'
          : 'text-[var(--text-secondary)] hover:bg-[var(--surface-muted)]'}"
      >
        Mine
      </button>
      <button
        type="button"
        onclick={() => setTab('all')}
        class="rounded px-3 py-1 text-xs {tab === 'all'
          ? 'bg-[var(--surface-muted)] font-medium'
          : 'text-[var(--text-secondary)] hover:bg-[var(--surface-muted)]'}"
      >
        All
      </button>
    </div>

    <select
      value={stateFilter}
      onchange={(e) => setState(/** @type {HTMLSelectElement} */ (e.currentTarget).value)}
      class="rounded-md border border-[var(--border-default)] bg-[var(--surface-default)] px-2 py-1 text-xs"
    >
      <option value="pending">Pending</option>
      <option value="approved">Approved</option>
      <option value="rejected">Rejected</option>
      <option value="cancelled">Cancelled</option>
      <option value="all">All states</option>
    </select>

    {#if pending}
      <Loader2 class="h-3.5 w-3.5 animate-spin text-[var(--text-secondary)]" />
    {/if}
  </div>

  {#if data.loadError}
    <p class="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-900 dark:border-red-900/40 dark:bg-red-900/20 dark:text-red-200">
      {data.loadError}
    </p>
  {:else if approvals.length === 0}
    <p class="rounded-md border border-[var(--border-default)] bg-[var(--surface-muted)] p-4 text-center text-sm text-[var(--text-secondary)]">
      No approvals match this filter.
    </p>
  {:else}
    <ul class="flex flex-col gap-2">
      {#each approvals as a (a.id)}
        <li class="rounded-md border border-[var(--border-default)] bg-[var(--surface-default)] p-3 text-sm">
          <div class="flex flex-wrap items-center justify-between gap-2">
            <div class="flex flex-col">
              <a
                href={`/tickets/${a.case_summary?.id}`}
                class="font-medium hover:underline"
              >
                {a.case_summary?.name || 'Ticket'}
              </a>
              <span class="text-xs text-[var(--text-secondary)]">
                {a.rule_summary?.name || 'Rule'} · {a.case_summary?.priority}
              </span>
            </div>
            <span
              class={`rounded px-2 py-0.5 text-[10px] font-medium uppercase ${badgeClass(a.state)}`}
            >
              {a.state}
            </span>
          </div>

          <p class="mt-1 text-xs text-[var(--text-secondary)]">
            Requested by {a.requested_by?.email || 'unknown'} on
            {new Date(a.created_at).toLocaleDateString()}
            {#if a.note}
              — <span class="italic">"{a.note}"</span>
            {/if}
          </p>

          {#if a.state === 'rejected' && a.reason}
            <p class="mt-1 rounded bg-red-50 p-2 text-xs text-red-900 dark:bg-red-900/30 dark:text-red-200">
              <strong>Rejected:</strong> {a.reason}
            </p>
          {/if}

          {#if a.state === 'pending'}
            <div class="mt-2 flex flex-wrap gap-2">
              <Button size="sm" disabled={pending} onclick={() => approve(a.id)}>
                <Check class="mr-1 h-3.5 w-3.5" /> Approve
              </Button>
              <Button
                size="sm"
                variant="outline"
                disabled={pending}
                onclick={() => (rejectingId = rejectingId === a.id ? null : a.id)}
              >
                <X class="mr-1 h-3.5 w-3.5" /> Reject
              </Button>
              {#if a.requested_by?.id === data.currentProfileId || isAdmin}
                <Button
                  size="sm"
                  variant="ghost"
                  disabled={pending}
                  onclick={() => cancel(a.id)}
                >
                  <Ban class="mr-1 h-3.5 w-3.5" /> Cancel
                </Button>
              {/if}
            </div>

            {#if rejectingId === a.id}
              <textarea
                bind:value={rejectReason}
                rows="2"
                placeholder="Reason (required)"
                class="mt-2 w-full rounded border border-[var(--border-default)] bg-[var(--surface-default)] p-2 text-xs"
              ></textarea>
              <Button
                size="sm"
                variant="outline"
                class="mt-1"
                disabled={pending || !rejectReason.trim()}
                onclick={() => reject(a.id)}
              >
                Confirm rejection
              </Button>
            {/if}
          {/if}
        </li>
      {/each}
    </ul>
  {/if}
</div>
