<script>
  import { TrendingUp, DollarSign } from '@lucide/svelte';

  /**
   * @typedef {Object} Column
   * @property {string} id
   * @property {string} name
   * @property {string} color
   * @property {number} [item_count]
   * @property {number} [lead_count] - Legacy support for leads
   * @property {number} [task_count] - Legacy support for tasks
   * @property {number|null} [wip_limit]
   * @property {Array<any>} items
   */

  /**
   * @type {{
   *   column: Column,
   *   itemName?: string,
   *   isDragOver: boolean,
   *   CardComponent?: any,
   *   onDragOver: (e: DragEvent) => void,
   *   onDragLeave: () => void,
   *   onDrop: (e: DragEvent) => void,
   *   onCardClick: (item: any) => void,
   *   onCardDragStart: (e: DragEvent, item: any) => void,
   *   onCardDragEnd: () => void
   * }}
   */
  let {
    column,
    itemName = 'item',
    isDragOver,
    CardComponent = null,
    onDragOver,
    onDragLeave,
    onDrop,
    onCardClick,
    onCardDragStart,
    onCardDragEnd
  } = $props();

  // Check if column is at WIP limit
  const isAtWipLimit = $derived(
    column.wip_limit !== null &&
      column.wip_limit !== undefined &&
      column.item_count >= column.wip_limit
  );

  // Get item count (supports item_count, lead_count, task_count)
  const itemCount = $derived(
    column.item_count ?? column.lead_count ?? column.task_count ?? column.items?.length ?? 0
  );

  // Calculate total pipeline value for this column
  const columnValue = $derived(() => {
    if (!column.items) return 0;
    return column.items.reduce((sum, item) => {
      const amount = parseFloat(String(item.opportunity_amount || item.opportunityAmount || 0));
      return sum + (isNaN(amount) ? 0 : amount);
    }, 0);
  });

  // Format column value
  function formatColumnValue(value) {
    if (value === 0) return null;
    if (value >= 1000000) {
      return `${(value / 1000000).toFixed(1)}M`;
    } else if (value >= 1000) {
      return `${(value / 1000).toFixed(0)}K`;
    }
    return value.toFixed(0);
  }

  // Get stage-specific gradient based on column color or name
  function getColumnGradient(col) {
    const name = col.name?.toLowerCase() || '';
    const color = col.color?.toLowerCase() || '';

    // Match by common stage names or colors
    if (name.includes('closed') || name.includes('won') || color.includes('green')) {
      return 'from-emerald-500 to-teal-500';
    }
    if (name.includes('lost') || name.includes('reject') || color.includes('red')) {
      return 'from-rose-500 to-red-500';
    }
    if (name.includes('recycl') || name.includes('nurtur') || color.includes('purple')) {
      return 'from-violet-500 to-purple-500';
    }
    if (name.includes('process') || name.includes('qualif') || color.includes('blue')) {
      return 'from-blue-500 to-indigo-500';
    }
    if (name.includes('assign') || name.includes('new') || color.includes('cyan')) {
      return 'from-cyan-500 to-blue-500';
    }
    // Default
    return 'from-slate-500 to-gray-500';
  }

  /**
   * Handle drag over
   * @param {DragEvent} e
   */
  function handleDragOver(e) {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    onDragOver(e);
  }
</script>

<div
  class="kanban-column group flex w-[280px] shrink-0 flex-col rounded-2xl transition-all duration-300"
  class:drag-over={isDragOver}
  class:wip-exceeded={isAtWipLimit}
  ondragover={handleDragOver}
  ondragleave={onDragLeave}
  ondrop={onDrop}
  role="region"
  aria-label="{column.name} column with {itemCount} {itemCount !== 1 ? 'items' : itemName}"
>
  <!-- Column Header - Glass with gradient accent -->
  <div class="column-header relative overflow-hidden rounded-t-2xl">
    <!-- Gradient background bar -->
    <div class="absolute inset-x-0 top-0 h-1 bg-gradient-to-r {getColumnGradient(column)}"></div>

    <!-- Glass header content -->
    <div class="relative flex items-center justify-between px-4 py-3 backdrop-blur-sm
      bg-white/60 dark:bg-white/[0.04]
      border border-white/20 dark:border-white/[0.06]
      border-b-0">
      <div class="flex items-center gap-2.5">
        <h3 class="text-sm font-bold tracking-tight text-gray-800 dark:text-white/90">
          {column.name}
        </h3>
        <div class="flex items-center gap-1.5">
          <span
            class="flex h-5 min-w-[20px] items-center justify-center rounded-full bg-gradient-to-r {getColumnGradient(column)} px-1.5 text-[0.65rem] font-bold text-white shadow-sm"
          >
            {itemCount}
          </span>
          {#if column.wip_limit}
            <span
              class="rounded-full px-1.5 py-0.5 text-[0.6rem] font-semibold tracking-wide
                {isAtWipLimit
                  ? 'bg-rose-100 text-rose-600 dark:bg-rose-500/20 dark:text-rose-400'
                  : 'bg-gray-100 text-gray-500 dark:bg-white/5 dark:text-gray-400'}"
            >
              max {column.wip_limit}
            </span>
          {/if}
        </div>
      </div>

      <!-- Column value indicator -->
      {#if columnValue() > 0}
        <div class="flex items-center gap-1 rounded-lg bg-emerald-50 px-2 py-1 dark:bg-emerald-500/10">
          <TrendingUp class="h-3 w-3 text-emerald-600 dark:text-emerald-400" />
          <span class="text-[0.7rem] font-bold text-emerald-700 dark:text-emerald-300">
            {formatColumnValue(columnValue())}
          </span>
        </div>
      {/if}
    </div>
  </div>

  <!-- Column Content - Cards container -->
  <div
    class="column-content flex-1 space-y-2.5 overflow-y-auto px-2 py-3
      bg-gradient-to-b from-gray-50/80 to-gray-100/50
      dark:from-white/[0.02] dark:to-white/[0.01]
      border-x border-white/20 dark:border-white/[0.04]"
    style="max-height: calc(100vh - 280px)"
  >
    {#each column.items as item, index (item.id)}
      <div
        class="card-wrapper animate-in"
        style="animation-delay: {Math.min(index * 40, 300)}ms"
      >
        {#if CardComponent}
          <CardComponent
            {item}
            onclick={() => onCardClick(item)}
            ondragstart={(e) => onCardDragStart(e, item)}
            ondragend={onCardDragEnd}
          />
        {:else}
          <!-- Default card rendering -->
          <div
            class="cursor-pointer rounded-xl border border-white/10 bg-white/80 p-3.5 shadow-sm backdrop-blur-sm transition-all hover:-translate-y-0.5 hover:shadow-md dark:border-white/[0.06] dark:bg-white/[0.03]"
            draggable="true"
            onclick={() => onCardClick(item)}
            onkeydown={(e) => (e.key === 'Enter' || e.key === ' ') && onCardClick(item)}
            ondragstart={(e) => onCardDragStart(e, item)}
            ondragend={onCardDragEnd}
            role="button"
            tabindex="0"
          >
            <div class="font-medium text-gray-900 dark:text-gray-100">
              {item.title || item.name || 'Untitled'}
            </div>
          </div>
        {/if}
      </div>
    {/each}

    {#if column.items.length === 0}
      <div
        class="flex h-28 flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed border-gray-200/60 text-center dark:border-white/[0.06]"
      >
        <div class="text-2xl opacity-30">📭</div>
        <span class="text-xs font-medium text-gray-400 dark:text-gray-500">
          No {itemName}s yet
        </span>
      </div>
    {/if}
  </div>

  <!-- Column Footer - Subtle summary -->
  <div
    class="column-footer flex items-center justify-center rounded-b-2xl px-4 py-2
      bg-white/40 dark:bg-white/[0.02]
      border border-t-0 border-white/20 dark:border-white/[0.04]"
  >
    <span class="text-[0.65rem] font-medium uppercase tracking-wider text-gray-400 dark:text-gray-500">
      {itemCount} {itemCount === 1 ? itemName : itemName + 's'}
    </span>
  </div>
</div>

<style>
  .kanban-column {
    --column-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.05);
    box-shadow: var(--column-shadow);
  }

  :global(.dark) .kanban-column {
    --column-shadow: 0 4px 15px -3px rgba(0, 0, 0, 0.3), 0 2px 6px -2px rgba(0, 0, 0, 0.2);
  }

  /* Drag over state - Glowing effect */
  .kanban-column.drag-over {
    --column-shadow: 0 0 0 2px rgba(34, 211, 238, 0.5), 0 0 30px -5px rgba(34, 211, 238, 0.3);
    transform: scale(1.01);
  }

  .kanban-column.drag-over .column-content {
    background: linear-gradient(
      to bottom,
      rgba(34, 211, 238, 0.08),
      rgba(34, 211, 238, 0.03)
    );
  }

  :global(.dark) .kanban-column.drag-over .column-content {
    background: linear-gradient(
      to bottom,
      rgba(34, 211, 238, 0.1),
      rgba(34, 211, 238, 0.02)
    );
  }

  /* WIP exceeded state */
  .kanban-column.wip-exceeded .column-header {
    background: linear-gradient(
      to right,
      rgba(251, 113, 133, 0.1),
      rgba(251, 113, 133, 0.05)
    );
  }

  :global(.dark) .kanban-column.wip-exceeded .column-header {
    background: linear-gradient(
      to right,
      rgba(251, 113, 133, 0.15),
      rgba(251, 113, 133, 0.05)
    );
  }

  /* Card animation on load */
  .card-wrapper {
    opacity: 0;
    animation: card-fade-in 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards;
  }

  @keyframes card-fade-in {
    from {
      opacity: 0;
      transform: translateY(8px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  /* Scrollbar styling */
  .column-content::-webkit-scrollbar {
    width: 4px;
  }

  .column-content::-webkit-scrollbar-track {
    background: transparent;
  }

  .column-content::-webkit-scrollbar-thumb {
    background: rgba(0, 0, 0, 0.1);
    border-radius: 100px;
  }

  :global(.dark) .column-content::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.1);
  }

  .column-content::-webkit-scrollbar-thumb:hover {
    background: rgba(0, 0, 0, 0.2);
  }

  :global(.dark) .column-content::-webkit-scrollbar-thumb:hover {
    background: rgba(255, 255, 255, 0.2);
  }
</style>
