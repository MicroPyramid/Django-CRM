<script>
  import { Building2, DollarSign, Flame, Snowflake, Thermometer, Sparkles } from '@lucide/svelte';

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

  // Rating configurations with icons and colors
  const ratingConfig = {
    HOT: {
      icon: Flame,
      bg: 'bg-gradient-to-r from-rose-500/20 to-orange-500/20',
      text: 'text-rose-500 dark:text-rose-400',
      border: 'border-rose-500/30',
      glow: 'shadow-rose-500/20',
      pulse: true
    },
    WARM: {
      icon: Thermometer,
      bg: 'bg-gradient-to-r from-amber-500/15 to-yellow-500/15',
      text: 'text-amber-600 dark:text-amber-400',
      border: 'border-amber-500/30',
      glow: 'shadow-amber-500/10',
      pulse: false
    },
    COLD: {
      icon: Snowflake,
      bg: 'bg-gradient-to-r from-sky-500/15 to-cyan-500/15',
      text: 'text-sky-600 dark:text-cyan-400',
      border: 'border-sky-500/30',
      glow: 'shadow-sky-500/10',
      pulse: false
    }
  };

  // Computed values
  const title = $derived(item.title || item.full_name || item.fullName || 'Untitled Lead');
  const company = $derived(item.company_name || item.company || '');
  const amount = $derived(item.opportunity_amount || item.opportunityAmount);
  const currency = $derived(item.currency || 'AED');
  const followUp = $derived(item.next_follow_up || item.nextFollowUp);
  const isOverdue = $derived(item.is_follow_up_overdue || item.isFollowUpOverdue);
  const rating = $derived(item.rating);
  const assignees = $derived(item.assigned_to || item.assignedTo || []);
  const config = $derived(rating ? ratingConfig[rating] : null);

  /**
   * Format currency amount with compact notation
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

  /**
   * Get initials from assignee
   * @param {any} assignee
   */
  function getAssigneeInitials(assignee) {
    const email = assignee?.user_details?.email || assignee?.email || '';
    if (!email) return '?';
    return email.charAt(0).toUpperCase();
  }

  /**
   * Get assignee display name
   * @param {any} assignee
   */
  function getAssigneeName(assignee) {
    return assignee?.user_details?.email || assignee?.email || 'Unknown';
  }

  // Generate a consistent color from email for avatar
  function getAvatarColor(email) {
    const colors = [
      'from-violet-500 to-purple-600',
      'from-cyan-500 to-blue-600',
      'from-emerald-500 to-teal-600',
      'from-amber-500 to-orange-600',
      'from-rose-500 to-pink-600',
      'from-indigo-500 to-blue-600'
    ];
    const hash = email.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
    return colors[hash % colors.length];
  }

  /**
   * Handle keyboard events
   * @param {KeyboardEvent} e
   */
  function handleKeydown(e) {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onclick?.();
    }
  }
</script>

<div
  class="lead-card group relative cursor-pointer overflow-hidden rounded-xl border transition-all duration-300 ease-out
    {isOverdue ? 'border-l-[3px] border-l-rose-500' : 'border-white/10 dark:border-white/[0.06]'}
    bg-white/80 dark:bg-white/[0.03]
    backdrop-blur-sm
    hover:border-white/20 dark:hover:border-white/[0.1]
    hover:shadow-lg hover:shadow-black/5 dark:hover:shadow-black/20
    hover:-translate-y-0.5"
  class:hot-card={rating === 'HOT'}
  draggable="true"
  {onclick}
  onkeydown={handleKeydown}
  {ondragstart}
  {ondragend}
  role="button"
  tabindex="0"
>
  <!-- Subtle gradient overlay for depth -->
  <div class="pointer-events-none absolute inset-0 bg-gradient-to-br from-white/50 via-transparent to-transparent dark:from-white/[0.02]"></div>

  <!-- Hot lead animated glow -->
  {#if rating === 'HOT'}
    <div class="hot-glow pointer-events-none absolute -inset-[1px] rounded-xl bg-gradient-to-r from-rose-500/20 via-orange-500/20 to-rose-500/20 opacity-0 blur-sm transition-opacity duration-300 group-hover:opacity-100"></div>
  {/if}

  <div class="relative p-3.5">
    <!-- Header: Title + Rating -->
    <div class="flex items-start justify-between gap-2">
      <h4 class="flex-1 truncate text-[0.9rem] font-semibold leading-tight tracking-tight text-gray-900 dark:text-white/95">
        {title}
      </h4>

      {#if config}
        {@const RatingIcon = config.icon}
        <div class="rating-badge flex shrink-0 items-center gap-1 rounded-full px-2 py-0.5 text-[0.65rem] font-bold uppercase tracking-wider {config.bg} {config.text} {config.border} border"
          class:rating-pulse={config.pulse}>
          <RatingIcon class="h-3 w-3" />
          {rating}
        </div>
      {/if}
    </div>

    <!-- Company -->
    {#if company}
      <div class="mt-1.5 flex items-center gap-1.5">
        <Building2 class="h-3.5 w-3.5 shrink-0 text-gray-400 dark:text-gray-500" />
        <span class="truncate text-sm text-gray-600 dark:text-gray-400">{company}</span>
      </div>
    {/if}

    <!-- Amount - Featured Display -->
    {#if amount}
      <div class="mt-3 flex items-center gap-2">
        <div class="flex items-center gap-1.5 rounded-lg bg-gradient-to-r from-emerald-500/10 to-teal-500/10 px-2.5 py-1.5 dark:from-emerald-500/15 dark:to-teal-500/15">
          <DollarSign class="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
          <span class="text-sm font-bold tracking-tight text-emerald-700 dark:text-emerald-300">
            {formatAmount(amount, currency)}
          </span>
        </div>
      </div>
    {/if}

    <!-- Footer: Assignees -->
    {#if assignees.length > 0}
      <div class="mt-3 flex items-center justify-between">
        <div class="flex items-center -space-x-2">
          {#each assignees.slice(0, 3) as assignee, i (assignee.id)}
            <div
              class="relative flex h-7 w-7 items-center justify-center rounded-full bg-gradient-to-br {getAvatarColor(getAssigneeName(assignee))} text-[0.7rem] font-semibold text-white shadow-sm ring-2 ring-white dark:ring-gray-900"
              style="z-index: {3 - i}"
              title={getAssigneeName(assignee)}
            >
              {getAssigneeInitials(assignee)}
            </div>
          {/each}
          {#if assignees.length > 3}
            <div
              class="relative flex h-7 w-7 items-center justify-center rounded-full bg-gray-200 text-[0.65rem] font-bold text-gray-600 ring-2 ring-white dark:bg-gray-700 dark:text-gray-300 dark:ring-gray-900"
              style="z-index: 0"
            >
              +{assignees.length - 3}
            </div>
          {/if}
        </div>

        <!-- Quick sparkle indicator for high-value leads -->
        {#if amount && parseFloat(String(amount)) > 300000}
          <div class="flex items-center gap-1 text-amber-500 dark:text-amber-400" title="High-value lead">
            <Sparkles class="h-4 w-4" />
          </div>
        {/if}
      </div>
    {/if}
  </div>
</div>

<style>
  .lead-card {
    --card-shadow: 0 1px 3px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.06);
    box-shadow: var(--card-shadow);
  }

  .lead-card:hover {
    --card-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.08), 0 8px 10px -6px rgba(0, 0, 0, 0.04);
  }

  :global(.dark) .lead-card {
    --card-shadow: 0 1px 3px rgba(0, 0, 0, 0.2), 0 1px 2px rgba(0, 0, 0, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.03);
  }

  :global(.dark) .lead-card:hover {
    --card-shadow: 0 20px 40px -10px rgba(0, 0, 0, 0.4), 0 8px 20px -8px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.05);
  }

  .lead-card:active {
    cursor: grabbing;
    transform: rotate(1.5deg) scale(1.03);
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.2);
  }

  :global(.dark) .lead-card:active {
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5), 0 0 30px -5px rgba(34, 211, 238, 0.15);
  }

  .lead-card:focus-visible {
    outline: 2px solid rgb(34 211 238);
    outline-offset: 2px;
  }

  /* Hot card special styling */
  .hot-card {
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.9) 0%, rgba(255, 251, 250, 0.95) 100%);
  }

  :global(.dark) .hot-card {
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.04) 0%, rgba(251, 113, 133, 0.03) 100%);
  }

  /* Rating badge pulse for HOT leads */
  .rating-pulse {
    animation: pulse-glow 2s ease-in-out infinite;
  }

  @keyframes pulse-glow {
    0%, 100% {
      opacity: 1;
    }
    50% {
      opacity: 0.7;
    }
  }

  /* Hot glow effect */
  .hot-glow {
    background-size: 200% 100%;
    animation: shimmer-glow 3s ease-in-out infinite;
  }

  @keyframes shimmer-glow {
    0%, 100% {
      background-position: 0% 50%;
    }
    50% {
      background-position: 100% 50%;
    }
  }
</style>
