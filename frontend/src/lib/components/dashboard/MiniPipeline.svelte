<script>
  import { Badge } from '$lib/components/ui/badge/index.js';
  import { ChevronRight } from '@lucide/svelte';
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
    { id: 'PROSPECTING', color: 'bg-gray-500' },
    { id: 'QUALIFICATION', color: 'bg-blue-500' },
    { id: 'PROPOSAL', color: 'bg-purple-500' },
    { id: 'NEGOTIATION', color: 'bg-orange-500' },
    { id: 'CLOSED_WON', color: 'bg-green-500' },
    { id: 'CLOSED_LOST', color: 'bg-red-500' }
  ];
</script>

<div class="overflow-x-auto">
  <div class="flex min-w-max items-center gap-1">
    {#each stages as stage, index}
      {@const data = pipelineData[stage.id] || { count: 0, value: 0, label: stage.id }}
      <a
        href="/opportunities?stage={stage.id}"
        class="group bg-muted/30 hover:border-border/50 hover:bg-muted/50 flex min-w-[120px] flex-col rounded-lg border border-transparent px-3 py-2.5 transition-all"
      >
        <div class="mb-1 flex items-center gap-1.5">
          <div class="h-2 w-2 rounded-full {stage.color}"></div>
          <span class="text-foreground text-xs font-medium">{data.label || stage.id}</span>
          <Badge variant="secondary" class="ml-auto h-5 px-1.5 text-[10px]">{data.count}</Badge>
        </div>
        <p class="text-foreground text-base font-semibold tabular-nums">
          {formatCurrency(data.value, currency, true)}
        </p>
      </a>
      {#if index < stages.length - 1 && index !== 3}
        <ChevronRight class="text-muted-foreground/50 h-4 w-4 flex-shrink-0" />
      {/if}
      {#if index === 3}
        <div class="bg-border mx-1 h-8 w-px flex-shrink-0"></div>
      {/if}
    {/each}
  </div>
</div>
