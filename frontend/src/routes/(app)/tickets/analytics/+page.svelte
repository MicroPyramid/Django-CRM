<script>
  import { goto } from '$app/navigation';
  import { page } from '$app/state';
  import { untrack } from 'svelte';
  import { Button } from '$lib/components/ui/button/index.js';
  import { Input } from '$lib/components/ui/input/index.js';
  import { Label } from '$lib/components/ui/label/index.js';
  import {
    Activity,
    AlertTriangle,
    BarChart3,
    Clock,
    Download,
    LineChart,
    Users
  } from '@lucide/svelte';
  import Sparkline from '$lib/components/tickets/analytics/Sparkline.svelte';
  import HBarChart from '$lib/components/tickets/analytics/HBarChart.svelte';
  import PageHeader from '$lib/components/layout/PageHeader.svelte';

  /** @type {{ data: import('./$types').PageData }} */
  let { data } = $props();

  let filters = $state(untrack(() => ({ ...data.filters })));
  $effect(() => {
    filters = { ...data.filters };
  });

  function applyFilters() {
    const u = new URL(page.url);
    for (const key of ['from', 'to', 'priority', 'team', 'agent']) {
      const v = filters[/** @type {keyof typeof filters} */ (key)];
      if (v) u.searchParams.set(key, v);
      else u.searchParams.delete(key);
    }
    goto(`${u.pathname}?${u.searchParams.toString()}`, {
      keepFocus: true,
      noScroll: true,
      invalidateAll: true
    });
  }

  function resetFilters() {
    filters = { from: '', to: '', priority: '', team: '', agent: '' };
    goto(page.url.pathname, { invalidateAll: true });
  }

  function fmtHours(/** @type {number | null} */ n) {
    if (n === null || n === undefined || !Number.isFinite(n)) return '—';
    if (n < 1) return `${Math.round(n * 60)}m`;
    if (n < 24) return `${n.toFixed(1)}h`;
    return `${(n / 24).toFixed(1)}d`;
  }

  function fmtPercent(/** @type {number | null} */ n) {
    if (n === null || n === undefined || !Number.isFinite(n)) return '—';
    return `${(n * 100).toFixed(1)}%`;
  }

  function buildExportUrl(/** @type {string} */ metric, /** @type {string} */ bucket = '') {
    const u = new URLSearchParams();
    u.set('metric', metric);
    if (bucket) u.set('bucket', bucket);
    u.set('fmt', 'csv');
    for (const key of ['from', 'to', 'priority', 'team', 'agent']) {
      const v = data.filters[/** @type {keyof typeof data.filters} */ (key)];
      if (v) u.set(key, v);
    }
    return `/api/cases/analytics/export/?${u.toString()}`;
  }
</script>

<PageHeader title="Tickets Analytics">
  {#snippet titleIcon()}
    <BarChart3 class="size-4" />
  {/snippet}
  {#snippet actions()}
    <a
      href="/tickets"
      class="text-xs font-medium text-[var(--text-secondary)] hover:underline"
    >
      ← Back to tickets
    </a>
  {/snippet}
</PageHeader>

<div class="space-y-6 p-6">
  <!-- Filter bar -->
  <section
    class="flex flex-wrap items-end gap-3 rounded-lg border border-[var(--border-default)] bg-[var(--surface-default)] p-4"
  >
    <div>
      <Label for="from" class="text-xs">From</Label>
      <Input
        id="from"
        type="date"
        bind:value={filters.from}
        class="h-8 w-36 text-xs"
      />
    </div>
    <div>
      <Label for="to" class="text-xs">To</Label>
      <Input
        id="to"
        type="date"
        bind:value={filters.to}
        class="h-8 w-36 text-xs"
      />
    </div>
    <div>
      <Label for="priority" class="text-xs">Priority</Label>
      <select
        id="priority"
        bind:value={filters.priority}
        class="h-8 rounded-md border border-[var(--border-default)] bg-[var(--surface-default)] px-2 text-xs"
      >
        <option value="">All</option>
        {#each data.priorities as p (p)}
          <option value={p}>{p}</option>
        {/each}
      </select>
    </div>
    <div>
      <Label for="agent" class="text-xs">Agent</Label>
      <select
        id="agent"
        bind:value={filters.agent}
        class="h-8 rounded-md border border-[var(--border-default)] bg-[var(--surface-default)] px-2 text-xs"
      >
        <option value="">All</option>
        {#each data.formOptions.users as u (u.id)}
          <option value={u.id}>{u.email}</option>
        {/each}
      </select>
    </div>
    <div>
      <Label for="team" class="text-xs">Team</Label>
      <select
        id="team"
        bind:value={filters.team}
        class="h-8 rounded-md border border-[var(--border-default)] bg-[var(--surface-default)] px-2 text-xs"
      >
        <option value="">All</option>
        {#each data.formOptions.teams as t (t.id)}
          <option value={t.id}>{t.name}</option>
        {/each}
      </select>
    </div>
    <Button size="sm" onclick={applyFilters}>Apply</Button>
    <Button size="sm" variant="ghost" onclick={resetFilters}>Reset</Button>
  </section>

  <!-- Tile grid -->
  <div class="grid grid-cols-1 gap-4 lg:grid-cols-2">
    <!-- FRT tile -->
    <section
      class="space-y-3 rounded-lg border border-[var(--border-default)] bg-[var(--surface-default)] p-4"
    >
      <header class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <Clock class="size-4 text-[var(--color-primary-default)]" />
          <h2 class="text-sm font-semibold">First Response Time</h2>
        </div>
        <a
          href={buildExportUrl('frt')}
          download
          class="inline-flex items-center gap-1 text-xs text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
        >
          <Download class="size-3" /> Export
        </a>
      </header>
      <div class="grid grid-cols-3 gap-2">
        <div>
          <div class="text-xs text-[var(--text-secondary)]">Median</div>
          <div class="text-lg font-bold tabular-nums">
            {fmtHours(data.metrics.frt.median_hours)}
          </div>
        </div>
        <div>
          <div class="text-xs text-[var(--text-secondary)]">p90</div>
          <div class="text-lg font-bold tabular-nums">
            {fmtHours(data.metrics.frt.p90_hours)}
          </div>
        </div>
        <div>
          <div class="text-xs text-[var(--text-secondary)]">Tickets</div>
          <div class="text-lg font-bold tabular-nums">{data.metrics.frt.count}</div>
        </div>
      </div>
      <Sparkline
        points={data.metrics.frt.series.map((s) => ({ x: s.bucket, y: s.median }))}
        format={fmtHours}
        label="FRT median trend"
      />
      {#if data.metrics.frt.breach_count > 0}
        <div class="flex items-center gap-2 text-xs text-amber-700">
          <AlertTriangle class="size-3.5" />
          {data.metrics.frt.breach_count} tickets breached the FRT SLA in this window.
        </div>
      {/if}
    </section>

    <!-- MTTR tile -->
    <section
      class="space-y-3 rounded-lg border border-[var(--border-default)] bg-[var(--surface-default)] p-4"
    >
      <header class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <Activity class="size-4 text-[var(--color-primary-default)]" />
          <h2 class="text-sm font-semibold">Mean Time To Resolution</h2>
        </div>
        <a
          href={buildExportUrl('mttr')}
          download
          class="inline-flex items-center gap-1 text-xs text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
        >
          <Download class="size-3" /> Export
        </a>
      </header>
      <div class="grid grid-cols-3 gap-2">
        <div>
          <div class="text-xs text-[var(--text-secondary)]">Mean</div>
          <div class="text-lg font-bold tabular-nums">
            {fmtHours(data.metrics.mttr.mean_hours)}
          </div>
        </div>
        <div>
          <div class="text-xs text-[var(--text-secondary)]">Median</div>
          <div class="text-lg font-bold tabular-nums">
            {fmtHours(data.metrics.mttr.median_hours)}
          </div>
        </div>
        <div>
          <div class="text-xs text-[var(--text-secondary)]">p90</div>
          <div class="text-lg font-bold tabular-nums">
            {fmtHours(data.metrics.mttr.p90_hours)}
          </div>
        </div>
      </div>
      <HBarChart
        bars={data.priorities.map((p) => ({
          label: p,
          value: data.metrics.mttr.by_priority?.[p]?.median_hours ?? null
        }))}
        format={fmtHours}
      />
    </section>

    <!-- Backlog tile -->
    <section
      class="space-y-3 rounded-lg border border-[var(--border-default)] bg-[var(--surface-default)] p-4"
    >
      <header class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <LineChart class="size-4 text-[var(--color-primary-default)]" />
          <h2 class="text-sm font-semibold">Backlog Over Time</h2>
        </div>
      </header>
      <Sparkline
        points={data.metrics.backlog.series.map((s) => ({ x: s.date, y: s.open_count }))}
        format={(n) => Math.round(n).toString()}
        label="Open backlog"
      />
      {#if data.metrics.backlog.series.some((s) => s.urgent_count > 0)}
        <div class="text-xs text-[var(--text-secondary)]">
          Peak Urgent open: <span class="font-semibold text-red-600">
            {Math.max(...data.metrics.backlog.series.map((s) => s.urgent_count))}
          </span>
        </div>
      {/if}
    </section>

    <!-- SLA tile -->
    <section
      class="space-y-3 rounded-lg border border-[var(--border-default)] bg-[var(--surface-default)] p-4"
    >
      <header class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <AlertTriangle class="size-4 text-[var(--color-primary-default)]" />
          <h2 class="text-sm font-semibold">SLA Breach Rate</h2>
        </div>
        <a
          href={buildExportUrl('sla', 'frt_breach')}
          download
          class="inline-flex items-center gap-1 text-xs text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
          title="Export FRT-breach tickets"
        >
          <Download class="size-3" /> Export FRT breaches
        </a>
      </header>
      <div class="grid grid-cols-2 gap-2">
        <div>
          <div class="text-xs text-[var(--text-secondary)]">FRT breach rate</div>
          <div class="text-lg font-bold tabular-nums">
            {fmtPercent(data.metrics.sla.frt_breach_rate)}
          </div>
          <div class="text-xs text-[var(--text-secondary)]">
            {data.metrics.sla.frt_breach_count}/{data.metrics.sla.total} tickets
          </div>
        </div>
        <div>
          <div class="text-xs text-[var(--text-secondary)]">Resolution breach rate</div>
          <div class="text-lg font-bold tabular-nums">
            {fmtPercent(data.metrics.sla.resolution_breach_rate)}
          </div>
          <div class="text-xs text-[var(--text-secondary)]">
            {data.metrics.sla.resolution_breach_count}/{data.metrics.sla.total} tickets
          </div>
        </div>
      </div>
      <HBarChart
        bars={data.priorities.map((p) => ({
          label: p,
          value: data.metrics.sla.by_priority?.[p]?.frt_breach_rate ?? null
        }))}
        format={fmtPercent}
      />
    </section>
  </div>

  <!-- Per-agent table -->
  <section
    class="space-y-3 rounded-lg border border-[var(--border-default)] bg-[var(--surface-default)] p-4"
  >
    <header class="flex items-center justify-between">
      <div class="flex items-center gap-2">
        <Users class="size-4 text-[var(--color-primary-default)]" />
        <h2 class="text-sm font-semibold">Per-Agent</h2>
      </div>
    </header>
    {#if data.metrics.agents.results.length === 0}
      <div class="p-3 text-center text-xs italic text-[var(--text-secondary)]">
        No assigned tickets in this window.
      </div>
    {:else}
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b border-[var(--border-default)] text-left text-xs text-[var(--text-secondary)]">
            <th class="py-1.5 font-medium">Agent</th>
            <th class="py-1.5 text-right font-medium">Handled</th>
            <th class="py-1.5 text-right font-medium">Avg FRT</th>
            <th class="py-1.5 text-right font-medium">Breach rate</th>
            <th class="py-1.5 text-right font-medium">CSAT</th>
          </tr>
        </thead>
        <tbody>
          {#each data.metrics.agents.results as row (row.profile_id)}
            <tr class="border-b border-[var(--border-default)]/40">
              <td class="py-1.5">{row.email || row.name}</td>
              <td class="py-1.5 text-right tabular-nums">{row.handled}</td>
              <td class="py-1.5 text-right tabular-nums">
                {fmtHours(row.avg_frt_hours)}
              </td>
              <td class="py-1.5 text-right tabular-nums">
                {fmtPercent(row.breach_rate)}
              </td>
              <td class="py-1.5 text-right tabular-nums text-[var(--text-secondary)]">
                {row.csat_avg ?? '—'}
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
      <p class="text-[10px] italic text-[var(--text-secondary)]">
        CSAT averages each agent's responded surveys (1-5 stars) within the
        active window. Tickets with no survey response are simply excluded.
      </p>
    {/if}
  </section>
</div>
