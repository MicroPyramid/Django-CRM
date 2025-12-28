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

  // Pipeline stages using design system tokens
  const stages = [
    {
      id: 'PROSPECTING',
      color: 'bg-[var(--stage-new)]',
      textColor: 'text-[var(--stage-new)]',
      bgColor: 'bg-[var(--stage-new-bg)] dark:bg-[var(--stage-new)]/15',
      borderColor: 'border-[var(--stage-new)]/30',
      glowColor: 'hover:shadow-[var(--stage-new)]/10'
    },
    {
      id: 'QUALIFICATION',
      color: 'bg-[var(--stage-qualified)]',
      textColor: 'text-[var(--stage-qualified)]',
      bgColor: 'bg-[var(--stage-qualified-bg)] dark:bg-[var(--stage-qualified)]/15',
      borderColor: 'border-[var(--stage-qualified)]/30',
      glowColor: 'hover:shadow-[var(--stage-qualified)]/10 dark:hover:shadow-[var(--stage-qualified)]/20'
    },
    {
      id: 'PROPOSAL',
      color: 'bg-[var(--stage-proposal)]',
      textColor: 'text-[var(--stage-proposal)]',
      bgColor: 'bg-[var(--stage-proposal-bg)] dark:bg-[var(--stage-proposal)]/15',
      borderColor: 'border-[var(--stage-proposal)]/30',
      glowColor: 'hover:shadow-[var(--stage-proposal)]/10 dark:hover:shadow-[var(--stage-proposal)]/20'
    },
    {
      id: 'NEGOTIATION',
      color: 'bg-[var(--stage-negotiation)]',
      textColor: 'text-[var(--stage-negotiation)]',
      bgColor: 'bg-[var(--stage-negotiation-bg)] dark:bg-[var(--stage-negotiation)]/15',
      borderColor: 'border-[var(--stage-negotiation)]/30',
      glowColor: 'hover:shadow-[var(--stage-negotiation)]/10 dark:hover:shadow-[var(--stage-negotiation)]/20'
    },
    {
      id: 'CLOSED_WON',
      color: 'bg-[var(--stage-won)]',
      textColor: 'text-[var(--stage-won)]',
      bgColor: 'bg-[var(--stage-won-bg)] dark:bg-[var(--stage-won)]/15',
      borderColor: 'border-[var(--stage-won)]/30',
      glowColor: 'hover:shadow-[var(--stage-won)]/10 dark:hover:shadow-[var(--stage-won)]/20',
      icon: Trophy
    },
    {
      id: 'CLOSED_LOST',
      color: 'bg-[var(--stage-lost)]',
      textColor: 'text-[var(--stage-lost)]',
      bgColor: 'bg-[var(--stage-lost-bg)] dark:bg-[var(--stage-lost)]/15',
      borderColor: 'border-[var(--stage-lost)]/30',
      glowColor: 'hover:shadow-[var(--stage-lost)]/10',
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
        class="group relative min-w-[130px] flex-1 overflow-hidden rounded-[var(--radius-lg)] border px-4 py-3.5 transition-all duration-300 hover:-translate-y-0.5 hover:shadow-lg {stage.borderColor} {stage.bgColor} {stage.glowColor}"
      >
        <!-- Gradient overlay on hover -->
        <div class="pointer-events-none absolute inset-0 bg-gradient-to-br from-white/10 via-transparent to-transparent opacity-0 transition-opacity duration-300 group-hover:opacity-100 dark:from-white/5"></div>

        <div class="relative flex flex-col gap-2">
          <!-- Stage header -->
          <div class="flex items-center justify-between gap-2">
            <div class="flex items-center gap-2">
              <div class="size-2.5 rounded-full {stage.color} shadow-sm"></div>
              <span class="text-[var(--text-primary)] text-xs font-semibold tracking-tight">
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
            <p class="text-[var(--text-primary)] text-lg font-bold tabular-nums tracking-tight">
              {formatCurrency(data.value, currency, true)}
            </p>
          </div>
        </div>
      </a>

      <!-- Connector arrows between active stages -->
      {#if index < 4}
        <div class="flex-shrink-0 px-1">
          <ChevronRight class="size-5 text-[var(--text-tertiary)]/30 transition-colors group-hover:text-[var(--text-tertiary)]/50" />
        </div>
      {/if}

      <!-- Divider before closed stages -->
      {#if index === 3}
        <div class="flex flex-shrink-0 flex-col items-center gap-1 px-2">
          <div class="h-4 w-px bg-[var(--border-default)]/50"></div>
          <span class="text-[var(--text-tertiary)]/50 text-[8px] font-medium uppercase tracking-widest">Closed</span>
          <div class="h-4 w-px bg-[var(--border-default)]/50"></div>
        </div>
      {/if}
    {/each}
  </div>
</div>
