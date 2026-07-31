<script>
  import { Building2, AlertCircle } from '@lucide/svelte';

  /**
   * @typedef {Object} Lead
   * @property {string} id
   * @property {string} [title]
   * @property {string} [full_name]
   * @property {string} [fullName]
   * @property {string} [company_name]
   * @property {string} [company]
   * @property {string} [email]
   * @property {string} [rating]
   * @property {number|string} [opportunity_amount]
   * @property {number|string} [opportunityAmount]
   * @property {string} [currency]
   * @property {string} [next_follow_up]
   * @property {string} [nextFollowUp]
   * @property {boolean} [is_follow_up_overdue]
   * @property {boolean} [isFollowUpOverdue]
   * @property {Array<{id: string, user_details?: {email?: string}, email?: string}>} [assigned_to]
   * @property {Array<{id: string, user_details?: {email?: string}, email?: string}>} [assignedTo]
   */

  /** @type {{ item: Lead, onclick?: () => void, ondragstart?: (e: DragEvent) => void, ondragend?: () => void }} */
  let { item, onclick, ondragstart, ondragend } = $props();

  // Rating label strip colors
  const ratingLabelBg = {
    HOT: 'bg-rose-500',
    WARM: 'bg-amber-400',
    COLD: 'bg-sky-400'
  };

  // Computed values
  const title = $derived(item.title || item.full_name || item.fullName || 'Untitled Lead');
  const company = $derived(item.company_name || item.company || '');
  const amount = $derived(item.opportunity_amount || item.opportunityAmount);
  const currency = $derived(item.currency || 'AED');
  const isOverdue = $derived(item.is_follow_up_overdue || item.isFollowUpOverdue);
  const rating = $derived(item.rating);
  const assignees = $derived(item.assigned_to || item.assignedTo || []);
  const labelBg = $derived(rating ? ratingLabelBg[rating] : null);

  /**
   * @param {number|string} value
   * @param {string} curr
   */
  function formatAmount(value, curr) {
    const num = typeof value === 'string' ? parseFloat(value) : value;
    if (isNaN(num)) return '';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: curr,
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
      notation: num >= 100000 ? 'compact' : 'standard'
    }).format(num);
  }

  /** @param {any} assignee */
  function getAssigneeInitials(assignee) {
    const email = assignee?.user_details?.email || assignee?.email || '';
    if (!email) return '?';
    return email.charAt(0).toUpperCase();
  }

  /** @param {any} assignee */
  function getAssigneeName(assignee) {
    return assignee?.user_details?.email || assignee?.email || 'Unknown';
  }

  function getAvatarColor(email) {
    const colors = [
      'bg-violet-500',
      'bg-cyan-500',
      'bg-emerald-500',
      'bg-amber-500',
      'bg-rose-500',
      'bg-indigo-500'
    ];
    const hash = email.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
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
  class="lead-card group cursor-pointer rounded-lg border bg-white p-2.5 text-left shadow-[0_1px_0_rgba(9,30,66,0.12)] hover:border-black/10 dark:bg-white/[0.05] dark:hover:border-white/[0.1]
    {isOverdue
    ? 'border-l-[3px] border-rose-300 border-l-rose-500 dark:border-rose-500/40'
    : 'border-black/[0.04] dark:border-white/[0.06]'}"
  draggable="true"
  {onclick}
  onkeydown={handleKeydown}
  {ondragstart}
  {ondragend}
  role="button"
  tabindex="0"
>
  <!-- Rating label strip -->
  {#if labelBg}
    <div class="mb-1.5 inline-flex h-1.5 w-10 rounded-sm {labelBg}" title="{rating} lead"></div>
  {/if}

  <!-- Title -->
  <h4 class="text-[14px] leading-snug font-normal text-gray-900 dark:text-gray-100">
    {title}
  </h4>

  <!-- Company -->
  {#if company}
    <div class="mt-1.5 flex items-center gap-1 text-[12px] text-gray-500 dark:text-gray-400">
      <Building2 class="h-3 w-3 shrink-0" />
      <span class="truncate">{company}</span>
    </div>
  {/if}

  <!-- Footer: amount / overdue + assignees -->
  {#if amount || isOverdue || assignees.length > 0}
    <div class="mt-2 flex items-center justify-between gap-2">
      <div class="flex items-center gap-1.5">
        {#if amount}
          <span
            class="rounded px-1.5 py-0.5 text-[11px] font-semibold text-emerald-700 dark:text-emerald-300"
          >
            {formatAmount(amount, currency)}
          </span>
        {/if}
        {#if isOverdue}
          <span
            class="inline-flex items-center gap-1 rounded px-1.5 py-0.5 text-[11px] font-medium text-rose-700 dark:text-rose-300"
            title="Follow-up overdue"
          >
            <AlertCircle class="h-3 w-3" />
            Overdue
          </span>
        {/if}
      </div>

      {#if assignees.length > 0}
        <div class="flex items-center -space-x-1.5">
          {#each assignees.slice(0, 3) as assignee, i (assignee.id)}
            <div
              class="relative flex h-6 w-6 items-center justify-center rounded-full {getAvatarColor(
                getAssigneeName(assignee)
              )} text-[10px] font-semibold text-white ring-2 ring-white dark:ring-[#262626]"
              style="z-index: {3 - i}"
              title={getAssigneeName(assignee)}
            >
              {getAssigneeInitials(assignee)}
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
  .lead-card:active {
    cursor: grabbing;
  }
  .lead-card:focus-visible {
    outline: 2px solid rgb(34 211 238);
    outline-offset: 2px;
  }
</style>
