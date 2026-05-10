<script>
  import { Megaphone, Route } from '@lucide/svelte';

  /** @type {{ ticketItem: any }} */
  let { ticketItem } = $props();

  const priorityColor = $derived(
    {
      Urgent: 'bg-[var(--priority-urgent-bg)] text-[var(--priority-urgent)]',
      High: 'bg-[var(--priority-high-bg)] text-[var(--priority-high)]',
      Normal: 'bg-[var(--priority-medium-bg)] text-[var(--priority-medium)]',
      Low: 'bg-[var(--priority-low-bg)] text-[var(--priority-low)]'
    }[ticketItem.priority] ||
      'bg-[var(--surface-sunken)] text-[var(--text-secondary)]'
  );

  const escalationCount = $derived(ticketItem.escalationCount || 0);

  /** @param {string | null | undefined} ts */
  function formatTimestamp(ts) {
    if (!ts) return '';
    try {
      return new Date(ts).toLocaleString();
    } catch {
      return ts;
    }
  }
</script>

<header class="flex flex-wrap items-start justify-between gap-3">
  <div class="min-w-0 flex-1">
    <h1 class="text-xl font-semibold text-[var(--text-primary)]">{ticketItem.subject}</h1>
    <div class="mt-1 flex flex-wrap items-center gap-2 text-xs text-[var(--text-secondary)]">
      <span class="inline-flex items-center rounded-md border border-[var(--border-default)] px-2 py-0.5">
        {ticketItem.status}
      </span>
      <span class="inline-flex items-center rounded-md px-2 py-0.5 {priorityColor}">
        {ticketItem.priority}
      </span>
      {#if ticketItem.ticketType}
        <span class="inline-flex items-center rounded-md border border-[var(--border-default)] px-2 py-0.5">
          {ticketItem.ticketType}
        </span>
      {/if}
      {#if ticketItem.routedByRuleName}
        <span
          class="inline-flex items-center gap-1 rounded-md border border-blue-200 bg-blue-50 px-2 py-0.5 text-blue-700 dark:border-blue-900/40 dark:bg-blue-900/20 dark:text-blue-200"
          title="Auto-assigned by rule: {ticketItem.routedByRuleName}"
        >
          <Route class="h-3 w-3" />
          Auto-assigned: {ticketItem.routedByRuleName}
        </span>
      {/if}
      {#if escalationCount > 0}
        <span
          class="inline-flex items-center gap-1 rounded-md bg-rose-600 px-2 py-0.5 font-medium uppercase tracking-wide text-white"
          title={ticketItem.lastEscalationFiredAt
            ? `Last escalation fired ${formatTimestamp(ticketItem.lastEscalationFiredAt)} (${escalationCount}x)`
            : 'Escalated'}
        >
          <Megaphone class="h-3 w-3" />
          Escalated{escalationCount > 1 ? ` ×${escalationCount}` : ''}
        </span>
      {/if}
    </div>
  </div>
</header>
