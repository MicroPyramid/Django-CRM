<script>
  import { Clock, AlertTriangle, PauseCircle } from '@lucide/svelte';

  /** @type {{ ticketItem: any, formOptions: any }} */
  let { ticketItem, formOptions } = $props();

  function fmt(d) {
    if (!d) return '—';
    return new Date(d).toLocaleDateString();
  }

  function fmtFull(d) {
    if (!d) return '—';
    return new Date(d).toLocaleString();
  }

  const sla = $derived(ticketItem.sla || {});
  const isPending = $derived(ticketItem.status === 'Pending');
  const showFirstResponse = $derived(
    !!sla.firstResponseDeadline && !sla.firstResponseAt
  );
  const showResolution = $derived(
    !!sla.resolutionDeadline && !sla.resolvedAt
  );
  const tooltip =
    'Counted in business hours. Excludes weekends, holidays, and time spent waiting on customer.';
</script>

<aside class="space-y-4">
  <section class="rounded-lg border border-[var(--border-default)] bg-[var(--surface-default)] p-4">
    <h3 class="mb-3 text-sm font-medium text-[var(--text-secondary)]">Properties</h3>
    <dl class="space-y-2 text-sm">
      <div class="flex justify-between gap-2">
        <dt class="text-[var(--text-secondary)]">Account</dt>
        <dd class="text-right text-[var(--text-primary)]">{ticketItem.account?.name || '—'}</dd>
      </div>
      <div class="flex justify-between gap-2">
        <dt class="text-[var(--text-secondary)]">Assigned to</dt>
        <dd class="text-right text-[var(--text-primary)]">
          {ticketItem.assignedTo.map((a) => a.name).join(', ') || 'Unassigned'}
        </dd>
      </div>
      <div class="flex justify-between gap-2">
        <dt class="text-[var(--text-secondary)]">Created</dt>
        <dd class="text-right text-[var(--text-primary)]">{fmt(ticketItem.createdAt)}</dd>
      </div>
      <div class="flex justify-between gap-2">
        <dt class="text-[var(--text-secondary)]">Closed on</dt>
        <dd class="text-right text-[var(--text-primary)]">{fmt(ticketItem.closedOn)}</dd>
      </div>
    </dl>
  </section>

  {#if showFirstResponse || showResolution}
    <section
      class="rounded-lg border border-[var(--border-default)] bg-[var(--surface-default)] p-4"
    >
      <h3 class="mb-2 flex items-center gap-1 text-sm font-medium text-[var(--text-secondary)]">
        <Clock class="h-3.5 w-3.5" />
        SLA
        <span
          class="text-[10px] font-normal italic text-[var(--text-secondary)]"
          title={tooltip}
        >
          (business hours)
        </span>
      </h3>
      <dl class="space-y-2 text-sm">
        {#if showFirstResponse}
          <div class="flex justify-between gap-2">
            <dt class="text-[var(--text-secondary)]">First response by</dt>
            <dd
              class="text-right {sla.firstResponseBreached
                ? 'text-[var(--color-danger-default)]'
                : 'text-[var(--text-primary)]'} flex items-center justify-end gap-1"
              title={tooltip}
            >
              {#if sla.firstResponseBreached}
                <AlertTriangle class="h-3.5 w-3.5" />
              {:else if isPending}
                <PauseCircle class="h-3.5 w-3.5 text-[var(--text-secondary)]" />
              {/if}
              <span class={isPending ? 'italic text-[var(--text-secondary)]' : ''}>
                {fmtFull(sla.firstResponseDeadline)}
              </span>
            </dd>
          </div>
        {/if}
        {#if showResolution}
          <div class="flex justify-between gap-2">
            <dt class="text-[var(--text-secondary)]">Resolve by</dt>
            <dd
              class="text-right {sla.resolutionBreached
                ? 'text-[var(--color-danger-default)]'
                : 'text-[var(--text-primary)]'} flex items-center justify-end gap-1"
              title={tooltip}
            >
              {#if sla.resolutionBreached}
                <AlertTriangle class="h-3.5 w-3.5" />
              {:else if isPending}
                <PauseCircle class="h-3.5 w-3.5 text-[var(--text-secondary)]" />
              {/if}
              <span class={isPending ? 'italic text-[var(--text-secondary)]' : ''}>
                {fmtFull(sla.resolutionDeadline)}
              </span>
            </dd>
          </div>
        {/if}
        {#if isPending}
          <p class="pt-1 text-xs italic text-[var(--text-secondary)]">
            Paused — counter resumes when status leaves Pending.
          </p>
        {/if}
      </dl>
    </section>
  {/if}

  {#if ticketItem.tags?.length}
    <section class="rounded-lg border border-[var(--border-default)] bg-[var(--surface-default)] p-4">
      <h3 class="mb-2 text-sm font-medium text-[var(--text-secondary)]">Tags</h3>
      <div class="flex flex-wrap gap-1">
        {#each ticketItem.tags as tag}
          <span class="rounded-md bg-[var(--surface-sunken)] px-2 py-0.5 text-xs">{tag.name}</span>
        {/each}
      </div>
    </section>
  {/if}
</aside>
