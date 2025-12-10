<script>
  import { toast } from 'svelte-sonner';
  import KanbanColumn from './KanbanColumn.svelte';
  import { Loader2, TrendingUp, Users, Flame, Zap } from '@lucide/svelte';

  /**
   * @typedef {Object} Column
   * @property {string} id
   * @property {string} name
   * @property {number} order
   * @property {string} color
   * @property {string} stage_type
   * @property {boolean} is_status_column
   * @property {number|null} wip_limit
   * @property {number} [item_count] - Generic count field (lead_count or task_count)
   * @property {Array<any>} items - Generic items array (leads or tasks)
   */

  /**
   * @typedef {Object} KanbanData
   * @property {string} mode
   * @property {Object|null} pipeline
   * @property {Column[]} columns
   * @property {number} [total_items]
   * @property {number} [total_leads] - Legacy support for leads
   * @property {number} [total_tasks] - Legacy support for tasks
   */

  /**
   * @type {{
   *   data: KanbanData | null,
   *   loading?: boolean,
   *   itemName?: string,
   *   itemNamePlural?: string,
   *   onItemMove: (itemId: string, newStatus: string, columnId: string) => Promise<void>,
   *   onCardClick: (item: any) => void,
   *   CardComponent: any,
   *   emptyMessage?: string
   * }}
   */
  let {
    data = null,
    loading = false,
    itemName = 'item',
    itemNamePlural = 'items',
    onItemMove,
    onCardClick,
    CardComponent,
    emptyMessage = 'No data available'
  } = $props();

  // Local mutable copy of columns for optimistic updates
  /** @type {Column[]} */
  let localColumns = $state([]);

  // Sync local columns when data changes from server
  $effect(() => {
    if (data?.columns) {
      localColumns = structuredClone(data.columns);
    }
  });

  // Drag state
  let draggedItem = $state(null);
  let dragSourceColumn = $state(null);
  let dragOverColumn = $state(null);

  // Mobile: Selected column for single-column view
  let mobileActiveColumn = $state('');

  // Set initial mobile column when data loads
  $effect(() => {
    if (localColumns.length > 0 && !mobileActiveColumn) {
      mobileActiveColumn = localColumns[0].id;
    }
  });

  // Calculate pipeline statistics
  const pipelineStats = $derived(() => {
    if (!localColumns || localColumns.length === 0) {
      return { totalValue: 0, hotCount: 0, avgValue: 0 };
    }

    let totalValue = 0;
    let hotCount = 0;
    let itemCount = 0;

    localColumns.forEach(col => {
      col.items?.forEach(item => {
        const amount = parseFloat(String(item.opportunity_amount || item.opportunityAmount || 0));
        if (!isNaN(amount)) totalValue += amount;
        if (item.rating === 'HOT') hotCount++;
        itemCount++;
      });
    });

    return {
      totalValue,
      hotCount,
      avgValue: itemCount > 0 ? totalValue / itemCount : 0
    };
  });

  // Format large numbers
  function formatValue(value) {
    if (value >= 1000000) {
      return `${(value / 1000000).toFixed(1)}M`;
    } else if (value >= 1000) {
      return `${(value / 1000).toFixed(0)}K`;
    }
    return value.toFixed(0);
  }

  /**
   * Handle drag start
   * @param {DragEvent} e
   * @param {any} item
   * @param {string} columnId
   */
  function handleDragStart(e, item, columnId) {
    draggedItem = item;
    dragSourceColumn = columnId;
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', item.id);

    // Add dragging class after a small delay to allow the drag image to be set
    requestAnimationFrame(() => {
      if (e.target instanceof HTMLElement) {
        e.target.style.opacity = '0.5';
      }
    });
  }

  /**
   * Handle drag over a column
   * @param {DragEvent} e
   * @param {string} columnId
   */
  function handleDragOver(e, columnId) {
    e.preventDefault();
    if (dragOverColumn !== columnId) {
      dragOverColumn = columnId;
    }
  }

  /**
   * Handle drag leave
   */
  function handleDragLeave() {
    // Small delay to prevent flicker when moving between cards
    setTimeout(() => {
      dragOverColumn = null;
    }, 50);
  }

  /**
   * Handle drop on column
   * @param {DragEvent} e
   * @param {string} targetColumnId
   */
  async function handleDrop(e, targetColumnId) {
    e.preventDefault();
    dragOverColumn = null;

    if (!draggedItem || dragSourceColumn === targetColumnId) {
      draggedItem = null;
      dragSourceColumn = null;
      return;
    }

    const item = draggedItem;
    const sourceColumnId = dragSourceColumn;

    // Reset drag state
    draggedItem = null;
    dragSourceColumn = null;

    // Optimistic update: move item in local state immediately
    const sourceCol = localColumns.find((c) => c.id === sourceColumnId);
    const targetCol = localColumns.find((c) => c.id === targetColumnId);

    if (sourceCol && targetCol) {
      // Remove from source column
      const itemIndex = sourceCol.items.findIndex((i) => i.id === item.id);
      if (itemIndex !== -1) {
        sourceCol.items.splice(itemIndex, 1);
        sourceCol.item_count--;
      }

      // Add to target column (at the top)
      targetCol.items.unshift({ ...item, status: targetColumnId });
      targetCol.item_count++;

      // Trigger reactivity by reassigning
      localColumns = [...localColumns];
    }

    try {
      // Call the move handler
      await onItemMove(item.id, targetColumnId, targetColumnId);
    } catch (error) {
      console.error(`Failed to move ${itemName}:`, error);
      toast.error(`Failed to move ${itemName}`);

      // Revert optimistic update on error
      if (sourceCol && targetCol) {
        // Remove from target column
        const itemIndex = targetCol.items.findIndex((i) => i.id === item.id);
        if (itemIndex !== -1) {
          targetCol.items.splice(itemIndex, 1);
          targetCol.item_count--;
        }

        // Add back to source column
        sourceCol.items.unshift(item);
        sourceCol.item_count++;

        // Trigger reactivity
        localColumns = [...localColumns];
      }
    }
  }

  /**
   * Handle drag end
   * @param {DragEvent} [e]
   */
  function handleDragEnd(e) {
    if (e?.target instanceof HTMLElement) {
      e.target.style.opacity = '1';
    }
    draggedItem = null;
    dragSourceColumn = null;
    dragOverColumn = null;
  }

  // Get columns sorted by order (use localColumns for optimistic updates)
  const sortedColumns = $derived(
    localColumns.length > 0 ? [...localColumns].sort((a, b) => a.order - b.order) : []
  );

  // Get active column for mobile view
  const activeMobileColumn = $derived(sortedColumns.find((c) => c.id === mobileActiveColumn));

  // Get total count (support both total_items and legacy total_leads/total_tasks)
  const totalCount = $derived(data?.total_items ?? data?.total_leads ?? data?.total_tasks ?? 0);
</script>

{#if loading}
  <div class="flex h-96 flex-col items-center justify-center gap-4">
    <div class="relative">
      <div class="absolute inset-0 animate-ping rounded-full bg-cyan-400/30"></div>
      <div class="relative rounded-full bg-gradient-to-r from-cyan-500 to-blue-500 p-3">
        <Loader2 class="h-6 w-6 animate-spin text-white" />
      </div>
    </div>
    <p class="text-sm font-medium text-gray-500 dark:text-gray-400">Loading pipeline...</p>
  </div>
{:else if !data || sortedColumns.length === 0}
  <div class="flex h-96 flex-col items-center justify-center gap-4 text-center">
    <div class="rounded-2xl bg-gray-100 p-6 dark:bg-white/5">
      <Zap class="h-12 w-12 text-gray-300 dark:text-gray-600" />
    </div>
    <div>
      <p class="text-lg font-semibold text-gray-600 dark:text-gray-300">{emptyMessage}</p>
      <p class="mt-1 text-sm text-gray-400 dark:text-gray-500">Add some {itemNamePlural} to get started</p>
    </div>
  </div>
{:else}
  <!-- Desktop: Horizontal scroll container with all columns -->
  <div class="kanban-board hidden md:block">
    <!-- Pipeline Stats Bar -->
    {#if pipelineStats().totalValue > 0}
      <div class="mb-5 flex items-center gap-6 rounded-xl border border-white/10 bg-white/60 px-5 py-3 backdrop-blur-sm dark:border-white/[0.04] dark:bg-white/[0.02]">
        <div class="flex items-center gap-3">
          <div class="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-emerald-500 to-teal-500 shadow-lg shadow-emerald-500/20">
            <TrendingUp class="h-4 w-4 text-white" />
          </div>
          <div>
            <p class="text-[0.65rem] font-medium uppercase tracking-wider text-gray-400 dark:text-gray-500">Pipeline Value</p>
            <p class="text-lg font-bold tracking-tight text-gray-800 dark:text-white">
              AED {formatValue(pipelineStats().totalValue)}
            </p>
          </div>
        </div>

        <div class="h-8 w-px bg-gray-200 dark:bg-white/10"></div>

        <div class="flex items-center gap-3">
          <div class="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-rose-500 to-orange-500 shadow-lg shadow-rose-500/20">
            <Flame class="h-4 w-4 text-white" />
          </div>
          <div>
            <p class="text-[0.65rem] font-medium uppercase tracking-wider text-gray-400 dark:text-gray-500">Hot Leads</p>
            <p class="text-lg font-bold tracking-tight text-gray-800 dark:text-white">
              {pipelineStats().hotCount}
            </p>
          </div>
        </div>

        <div class="h-8 w-px bg-gray-200 dark:bg-white/10"></div>

        <div class="flex items-center gap-3">
          <div class="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-violet-500 to-purple-500 shadow-lg shadow-violet-500/20">
            <Users class="h-4 w-4 text-white" />
          </div>
          <div>
            <p class="text-[0.65rem] font-medium uppercase tracking-wider text-gray-400 dark:text-gray-500">Total {itemNamePlural}</p>
            <p class="text-lg font-bold tracking-tight text-gray-800 dark:text-white">
              {totalCount}
            </p>
          </div>
        </div>
      </div>
    {/if}

    <!-- Kanban Columns -->
    <div class="columns-container flex gap-4 overflow-x-auto pb-4" style="min-height: 400px">
      {#each sortedColumns as column, index (column.id)}
        <div class="column-animate" style="animation-delay: {index * 80}ms">
          <KanbanColumn
            {column}
            {itemName}
            {CardComponent}
            isDragOver={dragOverColumn === column.id}
            onDragOver={(e) => handleDragOver(e, column.id)}
            onDragLeave={handleDragLeave}
            onDrop={(e) => handleDrop(e, column.id)}
            {onCardClick}
            onCardDragStart={(e, item) => handleDragStart(e, item, column.id)}
            onCardDragEnd={handleDragEnd}
          />
        </div>
      {/each}
    </div>
  </div>

  <!-- Mobile: Tab-based single column view -->
  <div class="md:hidden">
    <!-- Column selector - Pill style -->
    <div class="mb-4 overflow-x-auto">
      <div class="flex gap-2 pb-2">
        {#each sortedColumns as col (col.id)}
          <button
            class="shrink-0 rounded-full px-4 py-2 text-sm font-medium transition-all
              {mobileActiveColumn === col.id
                ? 'bg-gradient-to-r from-cyan-500 to-blue-500 text-white shadow-lg shadow-cyan-500/25'
                : 'bg-white/60 text-gray-600 hover:bg-white dark:bg-white/5 dark:text-gray-300 dark:hover:bg-white/10'}"
            onclick={() => mobileActiveColumn = col.id}
          >
            {col.name}
            <span class="ml-1.5 rounded-full bg-white/20 px-1.5 py-0.5 text-xs">
              {col.item_count}
            </span>
          </button>
        {/each}
      </div>
    </div>

    <!-- Active column cards -->
    {#if activeMobileColumn}
      <div class="space-y-3">
        {#each activeMobileColumn.items as item (item.id)}
          {#if CardComponent}
            <CardComponent {item} onclick={() => onCardClick(item)} />
          {:else}
            <div
              class="rounded-xl border border-white/10 bg-white/80 p-4 backdrop-blur-sm dark:border-white/[0.06] dark:bg-white/[0.03]"
              onclick={() => onCardClick(item)}
              onkeydown={(e) => (e.key === 'Enter' || e.key === ' ') && onCardClick(item)}
              role="button"
              tabindex="0"
            >
              <div class="font-medium text-gray-900 dark:text-gray-100">
                {item.title || item.name || 'Untitled'}
              </div>
            </div>
          {/if}
        {/each}

        {#if activeMobileColumn.items.length === 0}
          <div
            class="flex h-32 flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed border-gray-200/60 text-center dark:border-white/[0.06]"
          >
            <div class="text-3xl opacity-30">📭</div>
            <span class="text-sm font-medium text-gray-400 dark:text-gray-500">
              No {itemNamePlural} in this stage
            </span>
          </div>
        {/if}
      </div>
    {/if}
  </div>

  <!-- Total count footer -->
  <div class="mt-6 flex items-center justify-center gap-2 text-sm text-gray-400 dark:text-gray-500">
    <div class="h-px flex-1 bg-gradient-to-r from-transparent via-gray-200 to-transparent dark:via-white/10"></div>
    <span class="px-4 font-medium">
      {totalCount} {totalCount !== 1 ? itemNamePlural : itemName} across {sortedColumns.length} stages
    </span>
    <div class="h-px flex-1 bg-gradient-to-r from-transparent via-gray-200 to-transparent dark:via-white/10"></div>
  </div>
{/if}

<style>
  /* Column entrance animation */
  .column-animate {
    opacity: 0;
    animation: column-slide-in 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards;
  }

  @keyframes column-slide-in {
    from {
      opacity: 0;
      transform: translateY(20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  /* Horizontal scroll with fade indicators */
  .columns-container {
    scrollbar-width: thin;
    scrollbar-color: rgba(0, 0, 0, 0.1) transparent;
  }

  .columns-container::-webkit-scrollbar {
    height: 6px;
  }

  .columns-container::-webkit-scrollbar-track {
    background: transparent;
  }

  .columns-container::-webkit-scrollbar-thumb {
    background: rgba(0, 0, 0, 0.1);
    border-radius: 100px;
  }

  :global(.dark) .columns-container::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.1);
  }

  .columns-container::-webkit-scrollbar-thumb:hover {
    background: rgba(0, 0, 0, 0.2);
  }

  :global(.dark) .columns-container::-webkit-scrollbar-thumb:hover {
    background: rgba(255, 255, 255, 0.2);
  }
</style>
