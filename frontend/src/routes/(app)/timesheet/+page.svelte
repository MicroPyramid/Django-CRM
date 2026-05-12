<script>
  import { goto } from '$app/navigation';
  import { page } from '$app/state';
  import { onDestroy } from 'svelte';
  import { ChevronLeft, ChevronRight, Clock, User } from '@lucide/svelte';
  import PageHeader from '$lib/components/layout/PageHeader.svelte';
  import { Button } from '$lib/components/ui/button/index.js';
  import { Input } from '$lib/components/ui/input/index.js';
  import { Label } from '$lib/components/ui/label/index.js';

  /** @type {{ data: any }} */
  let { data } = $props();

  const timesheet = $derived(data.timesheet || { days: [] });
  const days = $derived(timesheet.days || []);
  const totalMinutes = $derived(timesheet.total_minutes || 0);
  const billableMinutes = $derived(timesheet.billable_minutes || 0);
  const runningCount = $derived(timesheet.running_count || 0);

  // Local form state so typing in date inputs doesn't fire a navigation per keystroke.
  let startInput = $state(data.start);
  let endInput = $state(data.end);
  let profileInput = $state(data.profileFilter);
  $effect(() => {
    startInput = data.start;
    endInput = data.end;
    profileInput = data.profileFilter;
  });

  // Tick once a second so running-timer durations refresh in the UI.
  let nowMs = $state(Date.now());
  const interval = setInterval(() => {
    if (runningCount > 0) nowMs = Date.now();
  }, 1000);
  onDestroy(() => clearInterval(interval));

  function formatMinutes(/** @type {number} */ minutes) {
    if (!minutes) return '0m';
    const h = Math.floor(minutes / 60);
    const m = minutes % 60;
    if (h && m) return `${h}h ${m}m`;
    if (h) return `${h}h`;
    return `${m}m`;
  }

  /**
   * Live duration for a running entry, ticking from started_at.
   * @param {string} startedAt - ISO timestamp
   */
  function liveMinutes(startedAt) {
    const started = new Date(startedAt).getTime();
    return Math.max(0, Math.floor((nowMs - started) / 60000));
  }

  /**
   * Navigate to a new (start, end, profile) tuple. Empty profile clears the param.
   * @param {{ start?: string, end?: string, profile?: string }} next
   */
  function applyRange(next) {
    const url = new URL(page.url);
    if (next.start) url.searchParams.set('start', next.start);
    if (next.end) url.searchParams.set('end', next.end);
    if (next.profile !== undefined) {
      if (next.profile) url.searchParams.set('profile', next.profile);
      else url.searchParams.delete('profile');
    }
    goto(url.pathname + '?' + url.searchParams.toString(), {
      keepFocus: true,
      noScroll: true
    });
  }

  function shiftWeek(/** @type {number} */ deltaDays) {
    const startDate = new Date(`${data.start}T00:00:00Z`);
    const endDate = new Date(`${data.end}T00:00:00Z`);
    startDate.setUTCDate(startDate.getUTCDate() + deltaDays);
    endDate.setUTCDate(endDate.getUTCDate() + deltaDays);
    applyRange({
      start: startDate.toISOString().slice(0, 10),
      end: endDate.toISOString().slice(0, 10)
    });
  }

  function applyInputs() {
    if (!startInput || !endInput) return;
    if (endInput < startInput) {
      // Swap silently rather than 400-ing later.
      const tmp = startInput;
      startInput = endInput;
      endInput = tmp;
    }
    applyRange({ start: startInput, end: endInput, profile: profileInput });
  }

  /**
   * Quick-pick a date range. Anchored to the local-zone "today" rather than UTC
   * so the user's expectation of "this week" matches their calendar.
   * @param {'this-week' | 'last-week' | 'this-month' | 'last-7' | 'last-30'} preset
   */
  function applyPreset(preset) {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    /** @param {Date} d */
    const iso = (d) =>
      `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
    /** @param {Date} base */
    const monOf = (base) => {
      const d = new Date(base);
      const dow = (d.getDay() + 6) % 7; // Mon=0
      d.setDate(d.getDate() - dow);
      return d;
    };

    let start = new Date(today);
    let end = new Date(today);
    if (preset === 'this-week') {
      start = monOf(today);
      end = new Date(start);
      end.setDate(end.getDate() + 6);
    } else if (preset === 'last-week') {
      start = monOf(today);
      start.setDate(start.getDate() - 7);
      end = new Date(start);
      end.setDate(end.getDate() + 6);
    } else if (preset === 'this-month') {
      start = new Date(today.getFullYear(), today.getMonth(), 1);
      end = new Date(today.getFullYear(), today.getMonth() + 1, 0);
    } else if (preset === 'last-7') {
      start = new Date(today);
      start.setDate(start.getDate() - 6);
      end = today;
    } else if (preset === 'last-30') {
      start = new Date(today);
      start.setDate(start.getDate() - 29);
      end = today;
    }
    applyRange({ start: iso(start), end: iso(end), profile: profileInput });
  }

  function fmtDate(/** @type {string} */ iso) {
    return new Date(`${iso}T00:00:00`).toLocaleDateString(undefined, {
      weekday: 'short',
      month: 'short',
      day: 'numeric'
    });
  }

  const viewingLabel = $derived.by(() => {
    if (!data.profileFilter || !data.isAdmin) return 'Your timesheet';
    const u = data.users?.find(
      /** @param {any} u */ (u) => u.id === data.profileFilter
    );
    if (!u) return 'Filtered timesheet';
    return `${u.name || u.email}'s timesheet`;
  });
</script>

<svelte:head>
  <title>Timesheet - BottleCRM</title>
</svelte:head>

<PageHeader title="Timesheet">
  {#snippet titleIcon()}
    <Clock class="size-4" />
  {/snippet}
</PageHeader>

<div class="flex flex-col gap-4 p-4">
  <!-- Filter bar -->
  <section
    class="flex flex-wrap items-end gap-3 rounded-lg border border-[var(--border-default)] bg-[var(--surface-default)] p-3"
  >
    <div>
      <Label for="start" class="text-xs">From</Label>
      <Input
        id="start"
        type="date"
        bind:value={startInput}
        class="h-8 w-40 text-xs"
      />
    </div>
    <div>
      <Label for="end" class="text-xs">To</Label>
      <Input
        id="end"
        type="date"
        bind:value={endInput}
        class="h-8 w-40 text-xs"
      />
    </div>

    {#if data.isAdmin}
      <div>
        <Label for="profile" class="text-xs">Profile</Label>
        <select
          id="profile"
          bind:value={profileInput}
          class="h-8 rounded-md border border-[var(--border-default)] bg-[var(--surface-default)] px-2 text-xs"
        >
          <option value="">Me</option>
          {#each data.users as u (u.id)}
            <option value={u.id}>{u.name || u.email}</option>
          {/each}
        </select>
      </div>
    {/if}

    <Button size="sm" onclick={applyInputs}>Apply</Button>

    <div class="ml-auto flex items-center gap-1">
      <Button variant="outline" size="sm" onclick={() => shiftWeek(-7)} class="gap-1">
        <ChevronLeft class="h-3.5 w-3.5" /> Prev
      </Button>
      <Button variant="outline" size="sm" onclick={() => shiftWeek(7)} class="gap-1">
        Next <ChevronRight class="h-3.5 w-3.5" />
      </Button>
    </div>

    <div class="flex w-full flex-wrap items-center gap-1.5 pt-1">
      <span class="text-[10px] font-semibold uppercase tracking-wider text-[var(--text-secondary)]">Quick select:</span>
      <Button variant="ghost" size="sm" class="h-6 px-2 text-xs" onclick={() => applyPreset('this-week')}>This week</Button>
      <Button variant="ghost" size="sm" class="h-6 px-2 text-xs" onclick={() => applyPreset('last-week')}>Last week</Button>
      <Button variant="ghost" size="sm" class="h-6 px-2 text-xs" onclick={() => applyPreset('last-7')}>Last 7d</Button>
      <Button variant="ghost" size="sm" class="h-6 px-2 text-xs" onclick={() => applyPreset('last-30')}>Last 30d</Button>
      <Button variant="ghost" size="sm" class="h-6 px-2 text-xs" onclick={() => applyPreset('this-month')}>This month</Button>
    </div>
  </section>

  <!-- Summary -->
  <div
    class="flex flex-wrap items-center gap-4 rounded-lg border border-[var(--border-default)] bg-[var(--surface-default)] p-3 text-sm"
  >
    <span class="flex items-center gap-1.5 text-[var(--text-secondary)]">
      <User class="size-3.5" />
      {viewingLabel}
    </span>
    <span><span class="text-[var(--text-secondary)]">Total:</span> <strong>{formatMinutes(totalMinutes)}</strong></span>
    <span><span class="text-[var(--text-secondary)]">Billable:</span> <strong>{formatMinutes(billableMinutes)}</strong></span>
    {#if runningCount > 0}
      <span class="inline-flex items-center gap-1 rounded bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-900 dark:bg-emerald-900/40 dark:text-emerald-100">
        <span class="size-1.5 animate-pulse rounded-full bg-emerald-600 dark:bg-emerald-300"></span>
        {runningCount} running
      </span>
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
              {@const running = e.is_running || !e.ended_at}
              {@const minutes = running ? liveMinutes(e.started_at) : e.duration_minutes}
              <li
                class="rounded border p-2 {running
                  ? 'border-emerald-300 bg-emerald-50 dark:border-emerald-900/40 dark:bg-emerald-900/10'
                  : 'border-[var(--border-muted)] bg-[var(--surface-muted)]'}"
              >
                <div class="flex items-baseline justify-between gap-2">
                  <a
                    class="truncate font-medium hover:underline"
                    href={`/tickets/${e.case}`}
                  >
                    {e.description || 'Untitled session'}
                  </a>
                  <span class="font-mono text-[10px] tabular-nums text-[var(--text-secondary)]">
                    {formatMinutes(minutes)}
                  </span>
                </div>
                <div class="mt-0.5 flex items-center justify-between gap-2 text-[10px] text-[var(--text-secondary)]">
                  <span>{new Date(e.started_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                  <span class="flex items-center gap-1">
                    {#if running}
                      <span class="inline-flex items-center gap-1 rounded bg-emerald-100 px-1 text-emerald-900 dark:bg-emerald-900/40 dark:text-emerald-100">
                        <span class="size-1 animate-pulse rounded-full bg-emerald-600 dark:bg-emerald-300"></span>
                        Running
                      </span>
                    {/if}
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
