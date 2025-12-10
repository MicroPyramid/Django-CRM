<script>
  import { Badge } from '$lib/components/ui/badge/index.js';
  import { ChevronRight, Trophy, XCircle } from '@lucide/svelte';
  import { formatCurrency } from '$lib/utils/formatting.js';

  /**
   * @typedef {Object} StageData
   * @property {number} count - Number of opportunities in this stage
   * @property {number} value - Total value of opportunities in this stage
   * @property {string} label - Display label for the stage
   */

  /**
   * @typedef {Object} Props
   * @property {Record<string, StageData>} [pipelineData] - Pipeline data by stage
   * @property {string} [currency] - Currency code for formatting (default: USD)
   */

  /** @type {Props} */
  let { pipelineData = {}, currency = 'USD' } = $props();

  const stages = [
    {
      id: 'PROSPECTING',
      color: 'bg-slate-500',
      textColor: 'text-slate-600 dark:text-slate-400',
      bgColor: 'bg-slate-500/10 dark:bg-slate-500/15',
      borderColor: 'border-slate-500/30 dark:border-slate-400/20',
      glowColor: 'hover:shadow-slate-500/10'
    },
    {
      id: 'QUALIFICATION',
      color: 'bg-cyan-500',
      textColor: 'text-cyan-600 dark:text-cyan-400',
      bgColor: 'bg-cyan-500/10 dark:bg-cyan-500/15',
      borderColor: 'border-cyan-500/30 dark:border-cyan-400/20',
      glowColor: 'hover:shadow-cyan-500/10 dark:hover:shadow-cyan-400/20'
    },
    {
      id: 'PROPOSAL',
      color: 'bg-violet-500',
      textColor: 'text-violet-600 dark:text-violet-400',
      bgColor: 'bg-violet-500/10 dark:bg-violet-500/15',
      borderColor: 'border-violet-500/30 dark:border-violet-400/20',
      glowColor: 'hover:shadow-violet-500/10 dark:hover:shadow-violet-400/20'
    },
    {
      id: 'NEGOTIATION',
      color: 'bg-amber-500',
      textColor: 'text-amber-600 dark:text-amber-400',
      bgColor: 'bg-amber-500/10 dark:bg-amber-500/15',
      borderColor: 'border-amber-500/30 dark:border-amber-400/20',
      glowColor: 'hover:shadow-amber-500/10 dark:hover:shadow-amber-400/20'
    },
    {
      id: 'CLOSED_WON',
      color: 'bg-emerald-500',
      textColor: 'text-emerald-600 dark:text-emerald-400',
      bgColor: 'bg-emerald-500/10 dark:bg-emerald-500/15',
      borderColor: 'border-emerald-500/30 dark:border-emerald-400/20',
      glowColor: 'hover:shadow-emerald-500/10 dark:hover:shadow-emerald-400/20',
      icon: Trophy
    },
    {
      id: 'CLOSED_LOST',
      color: 'bg-rose-500',
      textColor: 'text-rose-600 dark:text-rose-400',
      bgColor: 'bg-rose-500/10 dark:bg-rose-500/15',
      borderColor: 'border-rose-500/30 dark:border-rose-400/20',
      glowColor: 'hover:shadow-rose-500/10',
      icon: XCircle
    }
  ];
</script>

<div class="overflow-x-auto">
  <div class="flex min-w-max items-center gap-2">
    {#each stages as stage, index}
      {@const data = pipelineData[stage.id] || { count: 0, value: 0, label: stage.id }}
      <a
        href="/opportunities?stage={stage.id}"
        class="group relative min-w-[130px] flex-1 overflow-hidden rounded-xl border px-4 py-3.5 transition-all duration-300 hover:-translate-y-0.5 hover:shadow-lg {stage.borderColor} {stage.bgColor} {stage.glowColor}"
      >
        <!-- Gradient overlay on hover -->
        <div class="pointer-events-none absolute inset-0 bg-gradient-to-br from-white/10 via-transparent to-transparent opacity-0 transition-opacity duration-300 group-hover:opacity-100 dark:from-white/5"></div>

        <div class="relative flex flex-col gap-2">
          <!-- Stage header -->
          <div class="flex items-center justify-between gap-2">
            <div class="flex items-center gap-2">
              <div class="size-2.5 rounded-full {stage.color} shadow-sm"></div>
              <span class="text-foreground text-xs font-semibold tracking-tight">
                {data.label || stage.id.replace('_', ' ')}
              </span>
            </div>
            <Badge
              variant="secondary"
              class="h-5 min-w-[1.5rem] justify-center px-1.5 text-[10px] font-bold {stage.textColor} {stage.bgColor} border {stage.borderColor}"
            >
              {data.count}
            </Badge>
          </div>

          <!-- Value with optional icon -->
          <div class="flex items-center gap-2">
            {#if stage.icon}
              <stage.icon class="size-4 {stage.textColor}" />
            {/if}
            <p class="text-foreground text-lg font-bold tabular-nums tracking-tight">
              {formatCurrency(data.value, currency, true)}
            </p>
          </div>
        </div>
      </a>

      <!-- Connector arrows between active stages -->
      {#if index < 4}
        <div class="flex-shrink-0 px-1">
          <ChevronRight class="text-muted-foreground/30 size-5 transition-colors group-hover:text-muted-foreground/50" />
        </div>
      {/if}

      <!-- Divider before closed stages -->
      {#if index === 3}
        <div class="flex flex-shrink-0 flex-col items-center gap-1 px-2">
          <div class="bg-border/50 h-4 w-px"></div>
          <span class="text-muted-foreground/50 text-[8px] font-medium uppercase tracking-widest">Closed</span>
          <div class="bg-border/50 h-4 w-px"></div>
        </div>
      {/if}
    {/each}
  </div>
</div>
