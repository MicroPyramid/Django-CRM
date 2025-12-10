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
   * @property {'cyan' | 'violet' | 'emerald' | 'amber' | 'rose'} [accentColor] - Accent color theme
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
    accentColor = 'cyan',
    class: className,
    ...restProps
  } = $props();

  const hasTrend = $derived(trend !== undefined && trend !== null);
  const isPositive = $derived(trend !== undefined && trend >= 0);

  // Color configurations for different accent colors
  const colorConfig = {
    cyan: {
      iconBg: 'bg-cyan-500/10 dark:bg-cyan-500/20',
      iconColor: 'text-cyan-600 dark:text-cyan-400',
      borderGlow: 'hover:border-cyan-500/30 dark:hover:border-cyan-400/30',
      shadowGlow: 'dark:hover:shadow-cyan-500/10'
    },
    violet: {
      iconBg: 'bg-violet-500/10 dark:bg-violet-500/20',
      iconColor: 'text-violet-600 dark:text-violet-400',
      borderGlow: 'hover:border-violet-500/30 dark:hover:border-violet-400/30',
      shadowGlow: 'dark:hover:shadow-violet-500/10'
    },
    emerald: {
      iconBg: 'bg-emerald-500/10 dark:bg-emerald-500/20',
      iconColor: 'text-emerald-600 dark:text-emerald-400',
      borderGlow: 'hover:border-emerald-500/30 dark:hover:border-emerald-400/30',
      shadowGlow: 'dark:hover:shadow-emerald-500/10'
    },
    amber: {
      iconBg: 'bg-amber-500/10 dark:bg-amber-500/20',
      iconColor: 'text-amber-600 dark:text-amber-400',
      borderGlow: 'hover:border-amber-500/30 dark:hover:border-amber-400/30',
      shadowGlow: 'dark:hover:shadow-amber-500/10'
    },
    rose: {
      iconBg: 'bg-rose-500/10 dark:bg-rose-500/20',
      iconColor: 'text-rose-600 dark:text-rose-400',
      borderGlow: 'hover:border-rose-500/30 dark:hover:border-rose-400/30',
      shadowGlow: 'dark:hover:shadow-rose-500/10'
    }
  };

  const colors = $derived(colorConfig[accentColor] || colorConfig.cyan);
</script>

<div
  class={cn(
    'group relative overflow-hidden rounded-xl border border-border/50 bg-card/80 p-5 backdrop-blur-sm transition-all duration-300',
    'hover:-translate-y-0.5 hover:shadow-lg',
    'dark:bg-card/50 dark:hover:shadow-xl',
    colors.borderGlow,
    colors.shadowGlow,
    className
  )}
  {...restProps}
>
  <!-- Subtle gradient overlay on hover -->
  <div class="pointer-events-none absolute inset-0 opacity-0 transition-opacity duration-300 group-hover:opacity-100">
    <div class="absolute inset-0 bg-gradient-to-br from-white/5 via-transparent to-transparent dark:from-white/[0.02]"></div>
  </div>

  <div class="relative flex items-start justify-between gap-4">
    <div class="flex min-w-0 flex-col gap-1.5">
      <!-- Label -->
      <p class="text-muted-foreground text-xs font-semibold uppercase tracking-wider">
        {label}
      </p>

      <!-- Value -->
      <p class="text-foreground truncate text-2xl font-bold tabular-nums tracking-tight lg:text-3xl">
        {value}
      </p>

      <!-- Subtitle -->
      {#if subtitle}
        <p class="text-muted-foreground/70 text-[10px] font-medium">{subtitle}</p>
      {/if}

      <!-- Trend indicator -->
      {#if hasTrend}
        <div class="mt-1 flex items-center gap-1.5">
          {#if isPositive}
            <div class="flex items-center gap-1 rounded-full bg-emerald-500/10 px-2 py-0.5 dark:bg-emerald-500/20">
              <TrendingUp class="size-3 text-emerald-600 dark:text-emerald-400" />
              <span class="text-xs font-semibold text-emerald-600 dark:text-emerald-400">
                +{trend}%
              </span>
            </div>
          {:else}
            <div class="flex items-center gap-1 rounded-full bg-rose-500/10 px-2 py-0.5 dark:bg-rose-500/20">
              <TrendingDown class="size-3 text-rose-600 dark:text-rose-400" />
              <span class="text-xs font-semibold text-rose-600 dark:text-rose-400">
                {trend}%
              </span>
            </div>
          {/if}
          {#if trendLabel}
            <span class="text-muted-foreground text-[10px]">{trendLabel}</span>
          {/if}
        </div>
      {/if}
    </div>

    <!-- Icon -->
    {#if icon}
      <div
        class={cn(
          'flex size-11 flex-shrink-0 items-center justify-center rounded-xl transition-transform duration-300 group-hover:scale-105',
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
