<script>
  import { Badge } from '$lib/components/ui/badge/index.js';
  import { Button } from '$lib/components/ui/button/index.js';
  import { Progress } from '$lib/components/ui/progress/index.js';
  import { Sparkles, ChevronRight, Calendar } from '@lucide/svelte';
  import { formatCurrency } from '$lib/utils/formatting.js';

  /**
   * @typedef {Object} Opportunity
   * @property {string} id
   * @property {string} name
   * @property {number | null} amount
   * @property {string} [currency] - Currency code (e.g., 'USD', 'INR')
   * @property {string} stage
   * @property {number | null} probability
   * @property {string} [createdAt]
   * @property {{ name: string } | null} [account]
   * @property {string} [closed_on]
   */

  /**
   * @typedef {Object} Props
   * @property {Opportunity[]} [opportunities] - Opportunities list
   */

  /** @type {Props} */
  let { opportunities = [] } = $props();

  const stageConfig = /** @type {Record<string, { label: string, bg: string, text: string, border: string }>} */ ({
    PROSPECTING: {
      label: 'Prospecting',
      bg: 'bg-slate-500/10 dark:bg-slate-500/15',
      text: 'text-slate-600 dark:text-slate-400',
      border: 'border-slate-500/30'
    },
    QUALIFICATION: {
      label: 'Qualification',
      bg: 'bg-cyan-500/10 dark:bg-cyan-500/15',
      text: 'text-cyan-600 dark:text-cyan-400',
      border: 'border-cyan-500/30'
    },
    PROPOSAL: {
      label: 'Proposal',
      bg: 'bg-violet-500/10 dark:bg-violet-500/15',
      text: 'text-violet-600 dark:text-violet-400',
      border: 'border-violet-500/30'
    },
    NEGOTIATION: {
      label: 'Negotiation',
      bg: 'bg-amber-500/10 dark:bg-amber-500/15',
      text: 'text-amber-600 dark:text-amber-400',
      border: 'border-amber-500/30'
    },
    CLOSED_WON: {
      label: 'Won',
      bg: 'bg-emerald-500/10 dark:bg-emerald-500/15',
      text: 'text-emerald-600 dark:text-emerald-400',
      border: 'border-emerald-500/30'
    },
    CLOSED_LOST: {
      label: 'Lost',
      bg: 'bg-rose-500/10 dark:bg-rose-500/15',
      text: 'text-rose-600 dark:text-rose-400',
      border: 'border-rose-500/30'
    }
  });

  /**
   * Calculate days until close
   * @param {string | undefined} closeDateStr
   */
  function getDaysUntilClose(closeDateStr) {
    if (!closeDateStr) return null;
    const closeDate = new Date(closeDateStr);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const diffTime = closeDate.getTime() - today.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  }

  /**
   * Format days until close
   * @param {number | null} days
   */
  function formatDaysUntilClose(days) {
    if (days === null) return '';
    if (days < 0) return `${Math.abs(days)}d overdue`;
    if (days === 0) return 'Today';
    if (days === 1) return 'Tomorrow';
    return `${days}d`;
  }

  // Only show open opportunities
  const openOpportunities = $derived(
    opportunities.filter((o) => !['CLOSED_WON', 'CLOSED_LOST'].includes(o.stage))
  );
</script>

<div class="flex h-full flex-col overflow-hidden rounded-xl border border-border/50 bg-card/80 backdrop-blur-sm dark:bg-card/50">
  <!-- Header -->
  <div class="flex items-center justify-between border-b border-border/50 px-5 py-4">
    <div class="flex items-center gap-3">
      <div class="flex size-8 items-center justify-center rounded-lg bg-gradient-to-br from-emerald-500/10 to-teal-500/10 dark:from-emerald-500/20 dark:to-teal-500/20">
        <Sparkles class="size-4 text-emerald-600 dark:text-emerald-400" />
      </div>
      <h3 class="text-foreground text-sm font-semibold tracking-tight">My Opportunities</h3>
    </div>
    <Button variant="ghost" size="sm" href="/opportunities" class="gap-1 text-xs font-medium">
      View all
      <ChevronRight class="size-3.5" />
    </Button>
  </div>

  <!-- Opportunities list -->
  <div class="flex-1 overflow-auto">
    {#if openOpportunities.length === 0}
      <div class="flex h-full flex-col items-center justify-center py-10 text-center">
        <div class="mb-3 flex size-12 items-center justify-center rounded-xl bg-muted/50">
          <Sparkles class="text-muted-foreground/50 size-6" />
        </div>
        <p class="text-muted-foreground text-sm font-medium">No open opportunities</p>
        <p class="text-muted-foreground/70 text-xs">Create one to start tracking</p>
      </div>
    {:else}
      <div class="divide-y divide-border/30">
        {#each openOpportunities.slice(0, 5) as opp (opp.id)}
          {@const daysUntilClose = getDaysUntilClose(opp.closed_on)}
          {@const config = stageConfig[opp.stage] || stageConfig.PROSPECTING}
          <a
            href="/opportunities?view={opp.id}"
            class="group block px-5 py-3.5 transition-all duration-200 hover:bg-muted/30"
          >
            <!-- Top row: Name and Amount -->
            <div class="mb-2.5 flex items-start justify-between gap-3">
              <div class="min-w-0 flex-1">
                <p class="text-foreground truncate text-sm font-medium transition-colors group-hover:text-primary">
                  {opp.name}
                </p>
                <p class="text-muted-foreground mt-0.5 truncate text-xs">
                  {opp.account?.name || 'No account'}
                </p>
              </div>
              <span class="text-foreground flex-shrink-0 text-base font-bold tabular-nums tracking-tight">
                {formatCurrency(opp.amount, opp.currency || 'USD')}
              </span>
            </div>

            <!-- Bottom row: Stage, Progress, Close Date -->
            <div class="flex items-center gap-3">
              <!-- Stage badge -->
              <Badge
                class="flex-shrink-0 border text-[10px] font-semibold {config.bg} {config.text} {config.border}"
              >
                {config.label}
              </Badge>

              <!-- Probability progress -->
              <div class="flex flex-1 items-center gap-2">
                <Progress value={opp.probability || 0} class="h-1.5 flex-1" />
                <span class="text-muted-foreground w-8 text-right text-xs font-medium tabular-nums">
                  {opp.probability || 0}%
                </span>
              </div>

              <!-- Close date -->
              {#if daysUntilClose !== null}
                <div class="flex flex-shrink-0 items-center gap-1.5">
                  <Calendar class="text-muted-foreground size-3.5" />
                  <span
                    class="text-xs font-medium tabular-nums
                      {daysUntilClose < 0
                        ? 'text-rose-500 dark:text-rose-400'
                        : daysUntilClose <= 7
                          ? 'text-amber-500 dark:text-amber-400'
                          : 'text-muted-foreground'}"
                  >
                    {formatDaysUntilClose(daysUntilClose)}
                  </span>
                </div>
              {/if}
            </div>
          </a>
        {/each}
      </div>
    {/if}
  </div>
</div>
