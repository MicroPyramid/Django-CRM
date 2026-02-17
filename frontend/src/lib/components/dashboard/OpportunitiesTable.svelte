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

  // Using design system stage tokens
  const stageConfig =
    /** @type {Record<string, { label: string, bg: string, text: string, border: string }>} */ ({
      PROSPECTING: {
        label: 'Prospecting',
        bg: 'bg-[var(--stage-new-bg)] dark:bg-[var(--stage-new)]/15',
        text: 'text-[var(--stage-new)]',
        border: 'border-[var(--stage-new)]/30'
      },
      QUALIFICATION: {
        label: 'Qualification',
        bg: 'bg-[var(--stage-qualified-bg)] dark:bg-[var(--stage-qualified)]/15',
        text: 'text-[var(--stage-qualified)]',
        border: 'border-[var(--stage-qualified)]/30'
      },
      PROPOSAL: {
        label: 'Proposal',
        bg: 'bg-[var(--stage-proposal-bg)] dark:bg-[var(--stage-proposal)]/15',
        text: 'text-[var(--stage-proposal)]',
        border: 'border-[var(--stage-proposal)]/30'
      },
      NEGOTIATION: {
        label: 'Negotiation',
        bg: 'bg-[var(--stage-negotiation-bg)] dark:bg-[var(--stage-negotiation)]/15',
        text: 'text-[var(--stage-negotiation)]',
        border: 'border-[var(--stage-negotiation)]/30'
      },
      CLOSED_WON: {
        label: 'Won',
        bg: 'bg-[var(--stage-won-bg)] dark:bg-[var(--stage-won)]/15',
        text: 'text-[var(--stage-won)]',
        border: 'border-[var(--stage-won)]/30'
      },
      CLOSED_LOST: {
        label: 'Lost',
        bg: 'bg-[var(--stage-lost-bg)] dark:bg-[var(--stage-lost)]/15',
        text: 'text-[var(--stage-lost)]',
        border: 'border-[var(--stage-lost)]/30'
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

<div
  class="flex h-full flex-col overflow-hidden rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--surface-raised)] dark:bg-[var(--surface-raised)]/80 dark:backdrop-blur-sm"
>
  <!-- Header - Green/Success accent for opportunities -->
  <div
    class="flex items-center justify-between border-b border-[var(--border-default)]/50 px-5 py-4"
  >
    <div class="flex items-center gap-3">
      <div
        class="flex size-8 items-center justify-center rounded-[var(--radius-md)] bg-[var(--color-success-light)] dark:bg-[var(--color-success-default)]/15"
      >
        <Sparkles class="size-4 text-[var(--color-success-default)]" />
      </div>
      <h3 class="text-sm font-semibold tracking-tight text-[var(--text-primary)]">
        My Opportunities
      </h3>
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
        <div
          class="mb-3 flex size-12 items-center justify-center rounded-[var(--radius-lg)] bg-[var(--surface-sunken)]"
        >
          <Sparkles class="size-6 text-[var(--text-tertiary)]" />
        </div>
        <p class="text-sm font-medium text-[var(--text-secondary)]">No open opportunities</p>
        <p class="text-xs text-[var(--text-tertiary)]">Create one to start tracking</p>
      </div>
    {:else}
      <div class="divide-y divide-[var(--border-default)]/30">
        {#each openOpportunities.slice(0, 5) as opp (opp.id)}
          {@const daysUntilClose = getDaysUntilClose(opp.closed_on)}
          {@const config = stageConfig[opp.stage] || stageConfig.PROSPECTING}
          <a
            href="/opportunities?view={opp.id}"
            class="group block px-5 py-3.5 transition-all duration-200 hover:bg-[var(--color-primary-light)] dark:hover:bg-[var(--color-primary-default)]/5"
          >
            <!-- Top row: Name and Amount -->
            <div class="mb-2.5 flex items-start justify-between gap-3">
              <div class="min-w-0 flex-1">
                <p
                  class="truncate text-sm font-medium text-[var(--text-primary)] transition-colors group-hover:text-[var(--color-primary-default)]"
                >
                  {opp.name}
                </p>
                <p class="mt-0.5 truncate text-xs text-[var(--text-secondary)]">
                  {opp.account?.name || 'No account'}
                </p>
              </div>
              <span
                class="flex-shrink-0 text-base font-bold tracking-tight text-[var(--text-primary)] tabular-nums"
              >
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
                <span
                  class="w-8 text-right text-xs font-medium text-[var(--text-secondary)] tabular-nums"
                >
                  {opp.probability || 0}%
                </span>
              </div>

              <!-- Close date -->
              {#if daysUntilClose !== null}
                <div class="flex flex-shrink-0 items-center gap-1.5">
                  <Calendar class="size-3.5 text-[var(--text-tertiary)]" />
                  <span
                    class="text-xs font-medium tabular-nums
                      {daysUntilClose < 0
                      ? 'text-[var(--task-overdue)]'
                      : daysUntilClose <= 7
                        ? 'text-[var(--task-due-today)]'
                        : 'text-[var(--text-secondary)]'}"
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
