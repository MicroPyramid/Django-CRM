<script>
  import { Trophy, ArrowRight } from '@lucide/svelte';
  import { Progress } from '$lib/components/ui/progress/index.js';
  import { formatCurrency } from '$lib/utils/formatting.js';
  import { orgSettings } from '$lib/stores/org.js';
  import { resolve } from '$app/paths';

  /** @type {{ goals?: any[] }} */
  let { goals = [] } = $props();

  const orgCurrency = $derived($orgSettings.default_currency || 'USD');

  /**
   * @param {string} statusValue
   */
  function getStatusColor(statusValue) {
    switch (statusValue) {
      case 'on_track':
        return 'text-emerald-600 dark:text-emerald-400';
      case 'at_risk':
        return 'text-amber-600 dark:text-amber-400';
      case 'behind':
        return 'text-red-600 dark:text-red-400';
      case 'completed':
        return 'text-blue-600 dark:text-blue-400';
      default:
        return 'text-[var(--text-secondary)]';
    }
  }

  /**
   * @param {number} percent
   */
  function getProgressColor(percent) {
    if (percent >= 100) return '[&>[data-slot=progress-indicator]]:bg-blue-500';
    if (percent >= 75) return '[&>[data-slot=progress-indicator]]:bg-emerald-500';
    if (percent >= 50) return '[&>[data-slot=progress-indicator]]:bg-amber-500';
    return '[&>[data-slot=progress-indicator]]:bg-red-500';
  }
</script>

<div
  class="rounded-[var(--radius-xl)] border border-[var(--border-default)] bg-[var(--surface-raised)] p-6 shadow-[var(--shadow-sm)] dark:bg-[var(--surface-raised)]/80"
>
  <div class="mb-4 flex items-center justify-between">
    <div class="flex items-center gap-3">
      <div
        class="flex size-9 items-center justify-center rounded-[var(--radius-md)] bg-amber-50 dark:bg-amber-500/15"
      >
        <Trophy class="size-5 text-amber-500" />
      </div>
      <h2 class="text-base font-semibold tracking-tight text-[var(--text-primary)]">
        Goal Progress
      </h2>
    </div>
    <a
      href={resolve('/goals')}
      class="flex items-center gap-1 text-xs font-medium text-[var(--color-primary-default)] hover:underline"
    >
      View All
      <ArrowRight class="size-3" />
    </a>
  </div>

  {#if goals.length === 0}
    <div class="py-6 text-center">
      <p class="mb-2 text-sm text-[var(--text-tertiary)]">No active goals</p>
      <a
        href={resolve('/goals')}
        class="text-xs font-medium text-[var(--color-primary-default)] hover:underline"
      >
        Create a goal
      </a>
    </div>
  {:else}
    <div class="space-y-4">
      {#each goals as goal}
        <div class="space-y-1.5">
          <div class="flex items-center justify-between">
            <span class="truncate text-sm font-medium text-[var(--text-primary)]">{goal.name}</span>
            <span class="text-xs font-semibold {getStatusColor(goal.status)}">
              {goal.progress_percent}%
            </span>
          </div>
          <Progress
            value={goal.progress_percent}
            max={100}
            class="h-1.5 {getProgressColor(goal.progress_percent)}"
          />
          <div class="flex items-center justify-between text-[10px] text-[var(--text-tertiary)]">
            <span>
              {goal.goal_type === 'REVENUE'
                ? formatCurrency(goal.progress_value || 0, orgCurrency, true)
                : `${goal.progress_value || 0} deals`}
            </span>
            <span>
              {goal.goal_type === 'REVENUE'
                ? formatCurrency(goal.target_value || 0, orgCurrency, true)
                : `${goal.target_value || 0} deals`}
            </span>
          </div>
        </div>
      {/each}
    </div>
  {/if}
</div>
