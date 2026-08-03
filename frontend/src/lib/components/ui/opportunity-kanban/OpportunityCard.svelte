<script>
  import { Building2, Calendar, AlertTriangle } from '@lucide/svelte';
  import { formatDate, formatCurrency } from '$lib/utils/formatting.js';

  /**
   * @typedef {Object} Opportunity
   * @property {string} id
   * @property {string} name
   * @property {string} stage
   * @property {number|string|null} [amount]
   * @property {string|null} [currency]
   * @property {number|null} [probability]
   * @property {string|null} [closed_on]
   * @property {{id: string, name: string}|null} [account]
   * @property {Array<{id: string, user_details?: {email?: string}, email?: string}>} [assigned_to]
   * @property {number} [days_in_stage]
   * @property {'green'|'yellow'|'red'} [aging_status]
   */

  /** @type {{ item: Opportunity, onclick?: () => void, ondragstart?: (e: DragEvent) => void, ondragend?: () => void }} */
  let { item, onclick, ondragstart, ondragend } = $props();

  const title = $derived(item.name || 'Untitled');
  const account = $derived(item.account);
  const amount = $derived(item.amount != null ? Number(item.amount) : null);
  const currency = $derived(item.currency || 'USD');
  const probability = $derived(item.probability);
  const closedOn = $derived(item.closed_on);
  const assignees = $derived(item.assigned_to || []);
  const agingStatus = $derived(item.aging_status);
  const daysInStage = $derived(item.days_in_stage ?? 0);

  // Hide the aging chip for closed deals. Aging is a forecasting signal
  // and stops mattering once the deal is won/lost.
  const isClosed = $derived(item.stage === 'CLOSED_WON' || item.stage === 'CLOSED_LOST');
  const showAging = $derived(!isClosed && agingStatus && agingStatus !== 'green');

  const agingClass = $derived(
    agingStatus === 'red'
      ? 'bg-rose-100 text-rose-700 dark:bg-rose-500/15 dark:text-rose-300'
      : 'bg-amber-100 text-amber-700 dark:bg-amber-500/15 dark:text-amber-300'
  );

  /** @param {any} assignee */
  function assigneeEmail(assignee) {
    return assignee?.user_details?.email || assignee?.email || '';
  }
  /** @param {any} assignee */
  function assigneeInitial(assignee) {
    const email = assigneeEmail(assignee);
    return email ? email.charAt(0).toUpperCase() : '?';
  }
  /** @param {string} email */
  function avatarColor(email) {
    const colors = [
      'bg-violet-500',
      'bg-cyan-500',
      'bg-emerald-500',
      'bg-amber-500',
      'bg-rose-500',
      'bg-indigo-500'
    ];
    const hash = email.split('').reduce((acc, c) => acc + c.charCodeAt(0), 0);
    return colors[hash % colors.length];
  }

  /** @param {KeyboardEvent} e */
  function handleKeydown(e) {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onclick?.();
    }
  }
</script>

<div
  class="opportunity-card group cursor-pointer rounded-lg border border-black/[0.04] bg-white p-2.5 text-left shadow-[0_1px_0_rgba(9,30,66,0.12)] hover:border-black/10 dark:border-white/[0.06] dark:bg-white/[0.05] dark:hover:border-white/[0.1]"
  draggable="true"
  {onclick}
  onkeydown={handleKeydown}
  {ondragstart}
  {ondragend}
  role="button"
  tabindex="0"
>
  <!-- Title -->
  <h4 class="text-[14px] leading-snug font-normal text-gray-900 dark:text-gray-100">
    {title}
  </h4>

  <!-- Account -->
  {#if account?.name}
    <div class="mt-1.5 flex items-center gap-1 text-[12px] text-gray-500 dark:text-gray-400">
      <Building2 class="h-3 w-3 shrink-0" />
      <span class="truncate">{account.name}</span>
    </div>
  {/if}

  <!-- Amount + probability -->
  {#if amount != null && amount > 0}
    <div class="mt-2 flex items-center gap-2">
      <span class="text-[13px] font-semibold text-emerald-700 dark:text-emerald-300">
        {formatCurrency(amount, currency)}
      </span>
      {#if probability != null}
        <span class="text-[11px] text-gray-500 dark:text-gray-400">
          · {probability}%
        </span>
      {/if}
    </div>
  {/if}

  <!-- Footer: close date + aging + assignees -->
  {#if closedOn || showAging || assignees.length > 0}
    <div class="mt-2 flex items-center justify-between gap-2">
      <div class="flex items-center gap-1.5">
        {#if closedOn}
          <span
            class="inline-flex items-center gap-1 rounded px-1.5 py-0.5 text-[11px] font-medium text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-white/[0.06]"
          >
            <Calendar class="h-3 w-3" />
            {formatDate(closedOn)}
          </span>
        {/if}
        {#if showAging}
          <span
            class="inline-flex items-center gap-1 rounded px-1.5 py-0.5 text-[11px] font-medium {agingClass}"
            title="{daysInStage} days in this stage"
          >
            <AlertTriangle class="h-3 w-3" />
            {daysInStage}d
          </span>
        {/if}
      </div>

      {#if assignees.length > 0}
        <div class="flex items-center -space-x-1.5">
          {#each assignees.slice(0, 3) as assignee, i (assignee.id)}
            <div
              class="relative flex h-6 w-6 items-center justify-center rounded-full {avatarColor(
                assigneeEmail(assignee)
              )} text-[10px] font-semibold text-white ring-2 ring-white dark:ring-[#262626]"
              style="z-index: {3 - i}"
              title={assigneeEmail(assignee)}
            >
              {assigneeInitial(assignee)}
            </div>
          {/each}
          {#if assignees.length > 3}
            <div
              class="relative flex h-6 w-6 items-center justify-center rounded-full bg-gray-200 text-[10px] font-semibold text-gray-700 ring-2 ring-white dark:bg-gray-700 dark:text-gray-200 dark:ring-[#262626]"
              style="z-index: 0"
            >
              +{assignees.length - 3}
            </div>
          {/if}
        </div>
      {/if}
    </div>
  {/if}
</div>

<style>
  .opportunity-card:active {
    cursor: grabbing;
  }
  .opportunity-card:focus-visible {
    outline: 2px solid rgb(34 211 238);
    outline-offset: 2px;
  }
</style>
