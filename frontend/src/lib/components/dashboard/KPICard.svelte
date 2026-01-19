<script>
  import { cn } from '$lib/utils.js';
  import { TrendingUp, TrendingDown } from '@lucide/svelte';

  /**
   * @typedef {Object} Props
   * @property {string} label - The metric label (e.g., "Active Leads")
   * @property {string | number} value - The metric value
   * @property {string} [subtitle] - Small note below the value (e.g., "INR only")
   * @property {import('svelte').Snippet} [icon] - Icon snippet to display
   * @property {number} [trend] - Percentage change (positive or negative)
   * @property {string} [trendLabel] - Label for trend (e.g., "vs last month")
   * @property {'orange' | 'cyan' | 'violet' | 'emerald' | 'amber' | 'rose' | 'blue'} [accentColor] - Accent color theme
   * @property {string} [class] - Additional classes
   */

  /** @type {Props & Record<string, any>} */
  let {
    label,
    value,
    subtitle,
    icon,
    trend,
    trendLabel,
    accentColor = 'orange',
    class: className,
    ...restProps
  } = $props();

  const hasTrend = $derived(trend !== undefined && trend !== null);
  const isPositive = $derived(trend !== undefined && trend >= 0);

  // Color configurations using design system tokens
  const colorConfig = {
    orange: {
      iconBg: 'bg-[var(--color-primary-light)] dark:bg-[var(--color-primary-default)]/15',
      iconColor: 'text-[var(--color-primary-default)] dark:text-[var(--color-primary-default)]',
      borderGlow: 'hover:border-[var(--color-primary-default)]/30',
      shadowGlow: 'dark:hover:shadow-[var(--color-primary-default)]/10'
    },
    cyan: {
      iconBg: 'bg-cyan-500/10 dark:bg-cyan-500/20',
      iconColor: 'text-cyan-600 dark:text-cyan-400',
      borderGlow: 'hover:border-cyan-500/30 dark:hover:border-cyan-400/30',
      shadowGlow: 'dark:hover:shadow-cyan-500/10'
    },
    violet: {
      iconBg: 'bg-[var(--stage-proposal-bg)] dark:bg-[var(--stage-proposal)]/15',
      iconColor: 'text-[var(--stage-proposal)] dark:text-[var(--stage-proposal)]',
      borderGlow: 'hover:border-[var(--stage-proposal)]/30',
      shadowGlow: 'dark:hover:shadow-[var(--stage-proposal)]/10'
    },
    blue: {
      iconBg: 'bg-[var(--stage-qualified-bg)] dark:bg-[var(--stage-qualified)]/15',
      iconColor: 'text-[var(--stage-qualified)] dark:text-[var(--stage-qualified)]',
      borderGlow: 'hover:border-[var(--stage-qualified)]/30',
      shadowGlow: 'dark:hover:shadow-[var(--stage-qualified)]/10'
    },
    emerald: {
      iconBg: 'bg-[var(--color-success-light)] dark:bg-[var(--stage-won)]/15',
      iconColor: 'text-[var(--stage-won)] dark:text-[var(--stage-won)]',
      borderGlow: 'hover:border-[var(--stage-won)]/30',
      shadowGlow: 'dark:hover:shadow-[var(--stage-won)]/10'
    },
    amber: {
      iconBg: 'bg-[var(--stage-negotiation-bg)] dark:bg-[var(--stage-negotiation)]/15',
      iconColor: 'text-[var(--stage-negotiation)] dark:text-[var(--stage-negotiation)]',
      borderGlow: 'hover:border-[var(--stage-negotiation)]/30',
      shadowGlow: 'dark:hover:shadow-[var(--stage-negotiation)]/10'
    },
    rose: {
      iconBg: 'bg-[var(--stage-lost-bg)] dark:bg-[var(--stage-lost)]/15',
      iconColor: 'text-[var(--stage-lost)] dark:text-[var(--stage-lost)]',
      borderGlow: 'hover:border-[var(--stage-lost)]/30',
      shadowGlow: 'dark:hover:shadow-[var(--stage-lost)]/10'
    }
  };

  const colors = $derived(colorConfig[accentColor] || colorConfig.orange);
</script>

<div
  class={cn(
    'group relative overflow-hidden rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--surface-raised)] p-5 transition-all duration-300',
    'hover:-translate-y-0.5 hover:shadow-[var(--shadow-md)]',
    'dark:border-[var(--border-default)] dark:bg-[var(--surface-raised)]/80 dark:backdrop-blur-sm dark:hover:shadow-lg',
    colors.borderGlow,
    colors.shadowGlow,
    className
  )}
  {...restProps}
>
  <!-- Subtle gradient overlay on hover -->
  <div class="pointer-events-none absolute inset-0 opacity-0 transition-opacity duration-300 group-hover:opacity-100">
    <div class="absolute inset-0 bg-gradient-to-br from-[var(--color-primary-default)]/5 via-transparent to-transparent dark:from-[var(--color-primary-default)]/[0.03]"></div>
  </div>

  <div class="relative flex items-start justify-between gap-4">
    <div class="flex min-w-0 flex-col gap-1.5">
      <!-- Label -->
      <p class="text-[var(--text-secondary)] text-xs font-semibold uppercase tracking-wider">
        {label}
      </p>

      <!-- Value -->
      <p class="text-[var(--text-primary)] truncate text-2xl font-bold tabular-nums tracking-tight lg:text-3xl">
        {value}
      </p>

      <!-- Subtitle -->
      {#if subtitle}
        <p class="text-[var(--text-tertiary)] text-[10px] font-medium">{subtitle}</p>
      {/if}

      <!-- Trend indicator -->
      {#if hasTrend}
        <div class="mt-1 flex items-center gap-1.5">
          {#if isPositive}
            <div class="flex items-center gap-1 rounded-full bg-[var(--color-success-light)] px-2 py-0.5 dark:bg-[var(--stage-won)]/15">
              <TrendingUp class="size-3 text-[var(--stage-won)]" />
              <span class="text-xs font-semibold text-[var(--stage-won)]">
                +{trend}%
              </span>
            </div>
          {:else}
            <div class="flex items-center gap-1 rounded-full bg-[var(--stage-lost-bg)] px-2 py-0.5 dark:bg-[var(--stage-lost)]/15">
              <TrendingDown class="size-3 text-[var(--stage-lost)]" />
              <span class="text-xs font-semibold text-[var(--stage-lost)]">
                {trend}%
              </span>
            </div>
          {/if}
          {#if trendLabel}
            <span class="text-[var(--text-tertiary)] text-[10px]">{trendLabel}</span>
          {/if}
        </div>
      {/if}
    </div>

    <!-- Icon -->
    {#if icon}
      <div
        class={cn(
          'flex size-11 flex-shrink-0 items-center justify-center rounded-[var(--radius-lg)] transition-transform duration-300 group-hover:scale-105',
          colors.iconBg
        )}
      >
        <div class={colors.iconColor}>
          {@render icon()}
        </div>
      </div>
    {/if}
  </div>
</div>
