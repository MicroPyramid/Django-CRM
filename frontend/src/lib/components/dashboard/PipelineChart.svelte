<script>
  import { BarChart3 } from '@lucide/svelte';
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

  // Only show open stages in the chart (not closed)
  const stages = [
    {
      id: 'PROSPECTING',
      color: 'bg-slate-500',
      bgLight: 'bg-slate-500/20',
      text: 'text-slate-600 dark:text-slate-400'
    },
    {
      id: 'QUALIFICATION',
      color: 'bg-cyan-500',
      bgLight: 'bg-cyan-500/20',
      text: 'text-cyan-600 dark:text-cyan-400'
    },
    {
      id: 'PROPOSAL',
      color: 'bg-violet-500',
      bgLight: 'bg-violet-500/20',
      text: 'text-violet-600 dark:text-violet-400'
    },
    {
      id: 'NEGOTIATION',
      color: 'bg-amber-500',
      bgLight: 'bg-amber-500/20',
      text: 'text-amber-600 dark:text-amber-400'
    }
  ];

  const maxValue = $derived(Math.max(...stages.map((s) => pipelineData[s.id]?.value || 0), 1));
  const totalPipeline = $derived(stages.reduce((sum, s) => sum + (pipelineData[s.id]?.value || 0), 0));
</script>

<div class="overflow-hidden rounded-xl border border-border/50 bg-card/80 p-6 backdrop-blur-sm dark:bg-card/50">
  <!-- Header -->
  <div class="mb-6 flex items-center gap-3">
    <div class="flex size-8 items-center justify-center rounded-lg bg-gradient-to-br from-cyan-500/10 to-violet-500/10 dark:from-cyan-500/20 dark:to-violet-500/20">
      <BarChart3 class="size-4 text-cyan-600 dark:text-cyan-400" />
    </div>
    <h3 class="text-foreground text-sm font-semibold tracking-tight">Pipeline by Stage</h3>
  </div>

  <!-- Bar chart -->
  <div class="space-y-4">
    {#each stages as stage}
      {@const data = pipelineData[stage.id] || { count: 0, value: 0, label: stage.id }}
      {@const percentage = maxValue > 0 ? (data.value / maxValue) * 100 : 0}
      <div class="group space-y-2">
        <!-- Label row -->
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <div class="size-2.5 rounded-full {stage.color}"></div>
            <span class="text-muted-foreground text-xs font-medium">{data.label || stage.id}</span>
          </div>
          <span class="text-foreground text-sm font-bold tabular-nums tracking-tight">
            {formatCurrency(data.value, currency, true)}
          </span>
        </div>

        <!-- Progress bar -->
        <div class="relative h-3 w-full overflow-hidden rounded-full {stage.bgLight}">
          <div
            class="absolute inset-y-0 left-0 rounded-full transition-all duration-700 ease-out {stage.color}"
            style="width: {percentage}%"
          ></div>
          <!-- Shimmer effect on hover -->
          <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent opacity-0 transition-opacity duration-300 group-hover:opacity-100"></div>
        </div>
      </div>
    {/each}
  </div>

  <!-- Summary -->
  <div class="mt-6 flex items-center justify-between border-t border-border/50 pt-4">
    <span class="text-muted-foreground text-xs font-medium">Total Open Pipeline</span>
    <span class="text-foreground text-lg font-bold tabular-nums tracking-tight">
      {formatCurrency(totalPipeline, currency, true)}
    </span>
  </div>
</div>
