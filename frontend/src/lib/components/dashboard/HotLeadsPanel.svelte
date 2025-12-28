<script>
  import { Badge } from '$lib/components/ui/badge/index.js';
  import { Button } from '$lib/components/ui/button/index.js';
  import { Flame, Phone, Mail, ChevronRight, Calendar, Sparkles } from '@lucide/svelte';

  /**
   * @typedef {Object} Lead
   * @property {string} id
   * @property {string} [first_name]
   * @property {string} [last_name]
   * @property {string} [company]
   * @property {string} [rating]
   * @property {string} [next_follow_up]
   * @property {string} [last_contacted]
   */

  /**
   * @typedef {Object} Props
   * @property {Lead[]} [leads] - Hot leads
   */

  /** @type {Props} */
  let { leads = [] } = $props();

  // Using design system lead temperature tokens
  const ratingConfig = /** @type {Record<string, { bg: string, text: string, border: string, iconColor: string }>} */ ({
    HOT: {
      bg: 'bg-[var(--lead-hot-bg)] dark:bg-[var(--lead-hot)]/15',
      text: 'text-[var(--lead-hot)]',
      border: 'border-[var(--lead-hot)]/30',
      iconColor: 'text-[var(--lead-hot)]'
    },
    WARM: {
      bg: 'bg-[var(--lead-warm-bg)] dark:bg-[var(--lead-warm)]/15',
      text: 'text-[var(--lead-warm)]',
      border: 'border-[var(--lead-warm)]/30',
      iconColor: 'text-[var(--lead-warm)]'
    },
    COLD: {
      bg: 'bg-[var(--lead-cold-bg)] dark:bg-[var(--lead-cold)]/15',
      text: 'text-[var(--lead-cold)]',
      border: 'border-[var(--lead-cold)]/30',
      iconColor: 'text-[var(--lead-cold)]'
    }
  });

  /**
   * Format date for display
   * @param {string | null | undefined} dateStr
   */
  function formatFollowUp(dateStr) {
    if (!dateStr) return 'No follow-up set';
    const date = new Date(dateStr);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);

    const dateOnly = new Date(date);
    dateOnly.setHours(0, 0, 0, 0);

    if (dateOnly.getTime() === today.getTime()) return 'Today';
    if (dateOnly.getTime() === tomorrow.getTime()) return 'Tomorrow';
    if (dateOnly.getTime() < today.getTime()) {
      const days = Math.floor((today.getTime() - dateOnly.getTime()) / (1000 * 60 * 60 * 24));
      return `${days}d overdue`;
    }
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  }

  /**
   * Check if follow-up is overdue
   * @param {string | null | undefined} dateStr
   */
  function isOverdue(dateStr) {
    if (!dateStr) return false;
    const date = new Date(dateStr);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    return date < today;
  }

  /**
   * Get lead name
   * @param {Lead} lead
   */
  function getLeadName(lead) {
    const parts = [lead.first_name, lead.last_name].filter(Boolean);
    return parts.length > 0 ? parts.join(' ') : 'Unnamed Lead';
  }
</script>

<div class="flex h-full flex-col overflow-hidden rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--surface-raised)] dark:bg-[var(--surface-raised)]/80 dark:backdrop-blur-sm">
  <!-- Header - Orange accent for hot leads -->
  <div class="flex items-center justify-between border-b border-[var(--border-default)]/50 px-5 py-4">
    <div class="flex items-center gap-3">
      <div class="flex size-8 items-center justify-center rounded-[var(--radius-md)] bg-[var(--lead-hot-bg)] dark:bg-[var(--lead-hot)]/15">
        <Flame class="size-4 text-[var(--lead-hot)]" />
      </div>
      <h3 class="text-[var(--text-primary)] text-sm font-semibold tracking-tight">Hot Leads</h3>
    </div>
    <Button variant="ghost" size="sm" href="/leads?rating=HOT" class="gap-1 text-xs font-medium">
      View all
      <ChevronRight class="size-3.5" />
    </Button>
  </div>

  <!-- Leads list -->
  <div class="flex-1 overflow-auto">
    {#if leads.length === 0}
      <div class="flex h-full flex-col items-center justify-center py-10 text-center">
        <div class="mb-3 flex size-12 items-center justify-center rounded-[var(--radius-lg)] bg-[var(--surface-sunken)]">
          <Sparkles class="size-6 text-[var(--text-tertiary)]" />
        </div>
        <p class="text-[var(--text-secondary)] text-sm font-medium">No hot leads</p>
        <p class="text-[var(--text-tertiary)] text-xs">Mark leads as "Hot" to see them here</p>
      </div>
    {:else}
      <div class="divide-y divide-[var(--border-default)]/30">
        {#each leads as lead (lead.id)}
          {@const config = ratingConfig[lead.rating || 'HOT'] || ratingConfig.HOT}
          <a
            href="/leads?view={lead.id}"
            class="group flex items-center gap-3 px-5 py-3 transition-all duration-200 hover:bg-[var(--color-primary-light)] dark:hover:bg-[var(--color-primary-default)]/5"
          >
            <!-- Lead info -->
            <div class="min-w-0 flex-1">
              <p class="text-[var(--text-primary)] truncate text-sm font-medium transition-colors group-hover:text-[var(--color-primary-default)]">
                {getLeadName(lead)}
              </p>
              <p class="text-[var(--text-secondary)] mt-0.5 truncate text-xs">
                {lead.company || 'No company'}
              </p>
            </div>

            <!-- Rating badge -->
            <Badge
              class="flex-shrink-0 gap-1.5 border text-[10px] font-semibold {config.bg} {config.text} {config.border}"
            >
              <Flame class="size-3 {config.iconColor}" />
              {lead.rating || 'HOT'}
            </Badge>

            <!-- Follow-up date -->
            {#if lead.next_follow_up}
              <div class="flex flex-shrink-0 items-center gap-1.5">
                <Calendar class="size-3.5 text-[var(--text-tertiary)]" />
                <span
                  class="text-xs font-medium tabular-nums
                    {isOverdue(lead.next_follow_up) ? 'text-[var(--task-overdue)]' : 'text-[var(--text-secondary)]'}"
                >
                  {formatFollowUp(lead.next_follow_up)}
                </span>
              </div>
            {/if}

            <!-- Hover actions -->
            <div class="flex flex-shrink-0 gap-1 opacity-0 transition-all duration-200 group-hover:opacity-100">
              <Button
                variant="ghost"
                size="icon"
                class="size-7 rounded-[var(--radius-md)] hover:bg-[var(--activity-call)]/10 hover:text-[var(--activity-call)]"
                title="Call"
              >
                <Phone class="size-3.5" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                class="size-7 rounded-[var(--radius-md)] hover:bg-[var(--activity-email)]/10 hover:text-[var(--activity-email)]"
                title="Email"
              >
                <Mail class="size-3.5" />
              </Button>
            </div>
          </a>
        {/each}
      </div>
    {/if}
  </div>
</div>
