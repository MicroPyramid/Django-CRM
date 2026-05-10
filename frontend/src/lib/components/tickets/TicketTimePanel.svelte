<script>
  import { invalidateAll } from '$app/navigation';
  import { onDestroy, onMount } from 'svelte';
  import { toast } from 'svelte-sonner';
  import {
    Clock,
    Pause,
    Play,
    Plus,
    Trash2,
    DollarSign,
    Loader2
  } from '@lucide/svelte';
  import { Button } from '$lib/components/ui/button/index.js';
  import ManualTimeEntryDialog from './ManualTimeEntryDialog.svelte';

  /**
   * Time-tracking panel for the ticket detail page.
   *
   * @type {{
   *   ticketId: string,
   *   currentUserId: string,
   *   isAdmin: boolean,
   *   timeSummary?: { total_minutes: number, billable_minutes: number, by_profile: Array<any> }
   * }}
   */
  let { ticketId, currentUserId, isAdmin = false, timeSummary } = $props();

  /** @type {Array<any>} */
  let entries = $state([]);
  let loading = $state(true);
  let manualOpen = $state(false);
  let actionPending = $state(false);
  /** ms tick used to redraw the running timer's elapsed minutes display. */
  let tick = $state(Date.now());
  /** @type {ReturnType<typeof setInterval> | undefined} */
  let interval;

  // Match by the embedded User.id; the JWT exposes the user id but not the
  // profile id, so this is the cheapest way to know "is this my running timer".
  const myRunningEntry = $derived(
    entries.find(
      (e) => e.profile?.user_details?.id === currentUserId && !e.ended_at
    )
  );
  const totalMinutes = $derived(
    timeSummary?.total_minutes ??
      entries.reduce((sum, e) => sum + (e.duration_minutes || 0), 0)
  );
  const billableMinutes = $derived(
    timeSummary?.billable_minutes ??
      entries
        .filter((e) => e.billable)
        .reduce((sum, e) => sum + (e.duration_minutes || 0), 0)
  );

  onMount(async () => {
    await load();
    interval = setInterval(() => {
      tick = Date.now();
    }, 30 * 1000);
  });
  onDestroy(() => {
    if (interval) clearInterval(interval);
  });

  async function load() {
    loading = true;
    try {
      const res = await fetch(`/api/cases/${ticketId}/time-entries/`);
      if (!res.ok) {
        loading = false;
        return;
      }
      entries = await res.json();
    } finally {
      loading = false;
    }
  }

  async function startTimer() {
    actionPending = true;
    try {
      const res = await fetch(`/api/cases/${ticketId}/time-entries/start/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      });
      if (!res.ok) {
        const e = await res.json().catch(() => ({}));
        toast.error(e?.error || 'Could not start timer');
        return;
      }
      toast.success('Timer started.');
      await load();
      await invalidateAll();
    } finally {
      actionPending = false;
    }
  }

  async function stopTimer(/** @type {string} */ entryId) {
    actionPending = true;
    try {
      const res = await fetch(`/api/time-entries/${entryId}/stop/`, {
        method: 'POST'
      });
      if (!res.ok) {
        const e = await res.json().catch(() => ({}));
        toast.error(e?.error || 'Could not stop timer');
        return;
      }
      toast.success('Timer stopped.');
      await load();
      await invalidateAll();
    } finally {
      actionPending = false;
    }
  }

  async function toggleBillable(/** @type {any} */ entry) {
    if (entry.invoice) return;
    actionPending = true;
    try {
      const res = await fetch(`/api/time-entries/${entry.id}/`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ billable: !entry.billable })
      });
      if (!res.ok) {
        const e = await res.json().catch(() => ({}));
        toast.error(e?.error || 'Could not update entry');
        return;
      }
      await load();
      await invalidateAll();
    } finally {
      actionPending = false;
    }
  }

  async function deleteEntry(/** @type {string} */ entryId) {
    if (!confirm('Delete this time entry?')) return;
    actionPending = true;
    try {
      const res = await fetch(`/api/time-entries/${entryId}/`, {
        method: 'DELETE'
      });
      if (!res.ok) {
        const e = await res.json().catch(() => ({}));
        toast.error(e?.error || 'Could not delete entry');
        return;
      }
      await load();
      await invalidateAll();
    } finally {
      actionPending = false;
    }
  }

  function formatMinutes(/** @type {number} */ minutes) {
    if (!minutes) return '0m';
    const h = Math.floor(minutes / 60);
    const m = minutes % 60;
    if (h && m) return `${h}h ${m}m`;
    if (h) return `${h}h`;
    return `${m}m`;
  }

  function runningMinutes(/** @type {any} */ entry) {
    if (!entry || entry.ended_at) return 0;
    return Math.max(
      Math.floor((tick - new Date(entry.started_at).getTime()) / 60000),
      0
    );
  }

  function ownerLabel(/** @type {any} */ entry) {
    return (
      entry.profile?.user_details?.email ||
      entry.profile?.email ||
      entry.profile?.id?.slice?.(0, 8) ||
      'someone'
    );
  }
</script>

<section class="rounded-lg border border-[var(--border-default)] bg-[var(--surface-default)] p-4">
  <div class="mb-3 flex items-center justify-between gap-2">
    <h3 class="flex items-center gap-2 text-sm font-medium text-[var(--text-primary)]">
      <Clock class="h-4 w-4" />
      Time
      <span
        class="ml-2 rounded bg-[var(--surface-muted)] px-2 py-0.5 text-[10px] uppercase text-[var(--text-secondary)]"
      >
        {formatMinutes(totalMinutes)}
        {#if billableMinutes > 0}
          · {formatMinutes(billableMinutes)} billable
        {/if}
      </span>
    </h3>
    <div class="flex items-center gap-2">
      {#if myRunningEntry}
        <Button
          size="sm"
          variant="outline"
          class="gap-1"
          onclick={() => stopTimer(myRunningEntry.id)}
          disabled={actionPending}
        >
          <Pause class="h-3.5 w-3.5" />
          Stop ({formatMinutes(runningMinutes(myRunningEntry))})
        </Button>
      {:else}
        <Button
          size="sm"
          class="gap-1"
          onclick={startTimer}
          disabled={actionPending}
        >
          <Play class="h-3.5 w-3.5" />
          Start timer
        </Button>
      {/if}
      <Button
        size="sm"
        variant="outline"
        class="gap-1"
        onclick={() => (manualOpen = true)}
      >
        <Plus class="h-3.5 w-3.5" />
        Log time
      </Button>
    </div>
  </div>

  {#if loading}
    <div class="flex items-center gap-2 py-3 text-xs text-[var(--text-secondary)]">
      <Loader2 class="h-3.5 w-3.5 animate-spin" /> Loading entries…
    </div>
  {:else if entries.length === 0}
    <p class="py-3 text-sm text-[var(--text-secondary)]">
      No time logged on this ticket yet.
    </p>
  {:else}
    <ul class="divide-y divide-[var(--border-muted)]">
      {#each entries as e (e.id)}
        <li class="flex items-start gap-2 py-2 text-sm">
          <div class="mt-0.5 flex-shrink-0">
            {#if e.ended_at}
              <span
                class="inline-flex h-6 min-w-[3rem] items-center justify-center rounded bg-[var(--surface-muted)] px-1.5 text-[11px] font-medium tabular-nums"
              >
                {formatMinutes(e.duration_minutes)}
              </span>
            {:else}
              <span
                class="inline-flex h-6 min-w-[3rem] items-center justify-center rounded bg-emerald-100 px-1.5 text-[11px] font-medium tabular-nums text-emerald-900 dark:bg-emerald-900/40 dark:text-emerald-100"
              >
                <Loader2 class="mr-1 h-3 w-3 animate-spin" />
                {formatMinutes(runningMinutes(e))}
              </span>
            {/if}
          </div>
          <div class="min-w-0 flex-1">
            <div class="flex flex-wrap items-baseline gap-2">
              <span class="font-medium text-[var(--text-primary)]">
                {ownerLabel(e)}
              </span>
              <span class="text-[11px] text-[var(--text-secondary)]">
                {new Date(e.started_at).toLocaleString()}
              </span>
              {#if e.auto_stopped}
                <span
                  class="rounded bg-amber-100 px-1.5 py-0.5 text-[10px] uppercase text-amber-900 dark:bg-amber-900/40 dark:text-amber-100"
                >
                  Auto-stopped
                </span>
              {/if}
              {#if e.invoice}
                <span
                  class="rounded bg-blue-100 px-1.5 py-0.5 text-[10px] uppercase text-blue-900 dark:bg-blue-900/40 dark:text-blue-100"
                >
                  Invoiced
                </span>
              {/if}
            </div>
            {#if e.description}
              <p class="mt-0.5 truncate text-[var(--text-secondary)]">
                {e.description}
              </p>
            {/if}
          </div>
          <div class="flex shrink-0 items-center gap-1">
            <button
              type="button"
              onclick={() => toggleBillable(e)}
              disabled={actionPending || !!e.invoice}
              title={e.invoice
                ? 'Already invoiced — billable flag is locked'
                : e.billable
                  ? 'Mark non-billable'
                  : 'Mark billable'}
              class={`inline-flex h-7 w-7 items-center justify-center rounded text-[var(--text-secondary)] hover:text-[var(--text-primary)] disabled:cursor-not-allowed disabled:opacity-40 ${e.billable ? 'text-emerald-600 dark:text-emerald-400' : ''}`}
            >
              <DollarSign class="h-3.5 w-3.5" />
            </button>
            {#if (e.profile?.user_details?.id === currentUserId || isAdmin) && !e.invoice}
              <button
                type="button"
                onclick={() => deleteEntry(e.id)}
                disabled={actionPending}
                title="Delete"
                class="inline-flex h-7 w-7 items-center justify-center rounded text-[var(--text-secondary)] hover:text-red-600"
              >
                <Trash2 class="h-3.5 w-3.5" />
              </button>
            {/if}
          </div>
        </li>
      {/each}
    </ul>
  {/if}
</section>

<ManualTimeEntryDialog {ticketId} bind:open={manualOpen} />
