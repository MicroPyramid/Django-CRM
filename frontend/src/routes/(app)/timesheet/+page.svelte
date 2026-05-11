<script>
  import { goto } from '$app/navigation';
  import { page } from '$app/state';
  import { ChevronLeft, ChevronRight, Clock } from '@lucide/svelte';
  import PageHeader from '$lib/components/layout/PageHeader.svelte';
  import { Button } from '$lib/components/ui/button/index.js';

  /** @type {{ data: any }} */
  let { data } = $props();

  const timesheet = $derived(data.timesheet || { days: [] });
  const days = $derived(timesheet.days || []);
  const totalMinutes = $derived(timesheet.total_minutes || 0);
  const billableMinutes = $derived(timesheet.billable_minutes || 0);

  function formatMinutes(/** @type {number} */ minutes) {
    if (!minutes) return '0m';
    const h = Math.floor(minutes / 60);
    const m = minutes % 60;
    if (h && m) return `${h}h ${m}m`;
    if (h) return `${h}h`;
    return `${m}m`;
  }

  function shiftWeek(/** @type {number} */ deltaDays) {
    const startDate = new Date(`${data.start}T00:00:00Z`);
    const endDate = new Date(`${data.end}T00:00:00Z`);
    startDate.setUTCDate(startDate.getUTCDate() + deltaDays);
    endDate.setUTCDate(endDate.getUTCDate() + deltaDays);
    const start = startDate.toISOString().slice(0, 10);
    const end = endDate.toISOString().slice(0, 10);
    const url = new URL(page.url);
    url.searchParams.set('start', start);
    url.searchParams.set('end', end);
    goto(url.pathname + '?' + url.searchParams.toString(), {
      keepFocus: true,
      noScroll: true
    });
  }

  function fmtDate(/** @type {string} */ iso) {
    return new Date(`${iso}T00:00:00`).toLocaleDateString(undefined, {
      weekday: 'short',
      month: 'short',
      day: 'numeric'
    });
  }
</script>

<svelte:head>
  <title>Timesheet - BottleCRM</title>
</svelte:head>

<PageHeader title="Timesheet">
  {#snippet titleIcon()}
    <Clock class="size-4" />
  {/snippet}
  {#snippet actions()}
    <Button variant="outline" size="sm" onclick={() => shiftWeek(-7)} class="gap-1">
      <ChevronLeft class="h-3.5 w-3.5" /> Prev
    </Button>
    <span class="font-mono text-sm text-[var(--text-secondary)]">
      {data.start} → {data.end}
    </span>
    <Button variant="outline" size="sm" onclick={() => shiftWeek(7)} class="gap-1">
      Next <ChevronRight class="h-3.5 w-3.5" />
    </Button>
  {/snippet}
</PageHeader>

<div class="flex flex-col gap-4 p-4">
  <div class="flex flex-wrap items-center gap-4 rounded-lg border border-[var(--border-default)] bg-[var(--surface-default)] p-3 text-sm">
    <span><span class="text-[var(--text-secondary)]">Total:</span> <strong>{formatMinutes(totalMinutes)}</strong></span>
    <span><span class="text-[var(--text-secondary)]">Billable:</span> <strong>{formatMinutes(billableMinutes)}</strong></span>
    {#if data.profileFilter}
      <span class="text-[var(--text-secondary)]">Profile filter: <code>{data.profileFilter}</code></span>
    {/if}
  </div>

  {#if data.loadError}
    <p class="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-800 dark:border-red-900/40 dark:bg-red-900/20 dark:text-red-200">
      {data.loadError}
    </p>
  {/if}

  <div class="grid grid-cols-1 gap-3 lg:grid-cols-7">
    {#each days as day (day.date)}
      <section class="flex flex-col gap-2 rounded-lg border border-[var(--border-default)] bg-[var(--surface-default)] p-3">
        <header class="flex items-center justify-between">
          <span class="text-sm font-medium">{fmtDate(day.date)}</span>
          <span class="text-xs tabular-nums text-[var(--text-secondary)]">
            {formatMinutes(day.total_minutes)}
          </span>
        </header>

        {#if day.entries.length === 0}
          <p class="text-xs text-[var(--text-secondary)]">No entries.</p>
        {:else}
          <ul class="space-y-1.5 text-xs">
            {#each day.entries as e (e.id)}
              <li class="rounded border border-[var(--border-muted)] bg-[var(--surface-muted)] p-2">
                <div class="flex items-baseline justify-between gap-2">
                  <a
                    class="truncate font-medium hover:underline"
                    href={`/tickets/${e.case}`}
                  >
                    {e.description || 'Untitled session'}
                  </a>
                  <span class="font-mono text-[10px] tabular-nums text-[var(--text-secondary)]">
                    {formatMinutes(e.duration_minutes)}
                  </span>
                </div>
                <div class="mt-0.5 flex items-center justify-between gap-2 text-[10px] text-[var(--text-secondary)]">
                  <span>{new Date(e.started_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                  <span class="flex items-center gap-1">
                    {#if e.billable}<span class="rounded bg-emerald-100 px-1 text-emerald-900 dark:bg-emerald-900/40 dark:text-emerald-100">Billable</span>{/if}
                    {#if e.invoice}<span class="rounded bg-blue-100 px-1 text-blue-900 dark:bg-blue-900/40 dark:text-blue-100">Invoiced</span>{/if}
                    {#if e.auto_stopped}<span class="rounded bg-amber-100 px-1 text-amber-900 dark:bg-amber-900/40 dark:text-amber-100">Auto</span>{/if}
                  </span>
                </div>
              </li>
            {/each}
          </ul>
        {/if}
      </section>
    {/each}
  </div>
</div>
