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

  const ratingConfig = /** @type {Record<string, { bg: string, text: string, border: string, iconColor: string }>} */ ({
    HOT: {
      bg: 'bg-orange-500/10 dark:bg-orange-500/15',
      text: 'text-orange-600 dark:text-orange-400',
      border: 'border-orange-500/30 dark:border-orange-400/20',
      iconColor: 'text-orange-500 dark:text-orange-400'
    },
    WARM: {
      bg: 'bg-amber-500/10 dark:bg-amber-500/15',
      text: 'text-amber-600 dark:text-amber-400',
      border: 'border-amber-500/30 dark:border-amber-400/20',
      iconColor: 'text-amber-500 dark:text-amber-400'
    },
    COLD: {
      bg: 'bg-cyan-500/10 dark:bg-cyan-500/15',
      text: 'text-cyan-600 dark:text-cyan-400',
      border: 'border-cyan-500/30 dark:border-cyan-400/20',
      iconColor: 'text-cyan-500 dark:text-cyan-400'
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

<div class="flex h-full flex-col overflow-hidden rounded-xl border border-border/50 bg-card/80 backdrop-blur-sm dark:bg-card/50">
  <!-- Header -->
  <div class="flex items-center justify-between border-b border-border/50 px-5 py-4">
    <div class="flex items-center gap-3">
      <div class="flex size-8 items-center justify-center rounded-lg bg-gradient-to-br from-orange-500/10 to-red-500/10 dark:from-orange-500/20 dark:to-red-500/20">
        <Flame class="size-4 text-orange-500 dark:text-orange-400" />
      </div>
      <h3 class="text-foreground text-sm font-semibold tracking-tight">Hot Leads</h3>
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
        <div class="mb-3 flex size-12 items-center justify-center rounded-xl bg-muted/50">
          <Sparkles class="text-muted-foreground/50 size-6" />
        </div>
        <p class="text-muted-foreground text-sm font-medium">No hot leads</p>
        <p class="text-muted-foreground/70 text-xs">Mark leads as "Hot" to see them here</p>
      </div>
    {:else}
      <div class="divide-y divide-border/30">
        {#each leads as lead (lead.id)}
          {@const config = ratingConfig[lead.rating || 'HOT'] || ratingConfig.HOT}
          <a
            href="/leads?view={lead.id}"
            class="group flex items-center gap-3 px-5 py-3 transition-all duration-200 hover:bg-muted/30"
          >
            <!-- Lead info -->
            <div class="min-w-0 flex-1">
              <p class="text-foreground truncate text-sm font-medium transition-colors group-hover:text-primary">
                {getLeadName(lead)}
              </p>
              <p class="text-muted-foreground mt-0.5 truncate text-xs">
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
                <Calendar class="text-muted-foreground size-3.5" />
                <span
                  class="text-xs font-medium tabular-nums
                    {isOverdue(lead.next_follow_up) ? 'text-rose-500 dark:text-rose-400' : 'text-muted-foreground'}"
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
                class="size-7 rounded-lg hover:bg-cyan-500/10 hover:text-cyan-600 dark:hover:bg-cyan-500/20 dark:hover:text-cyan-400"
                title="Call"
              >
                <Phone class="size-3.5" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                class="size-7 rounded-lg hover:bg-violet-500/10 hover:text-violet-600 dark:hover:bg-violet-500/20 dark:hover:text-violet-400"
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
