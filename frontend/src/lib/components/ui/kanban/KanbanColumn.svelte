<script>
  import { TrendingUp, Plus } from '@lucide/svelte';

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
   *   draggedItemId?: string | null,
   *   CardComponent?: any,
   *   onDragOver: (e: DragEvent) => void,
   *   onDragLeave: () => void,
   *   onDrop: (e: DragEvent, neighbors: { aboveId: string | null, belowId: string | null }) => void,
   *   onCardClick: (item: any) => void,
   *   onCardDragStart: (e: DragEvent, item: any) => void,
   *   onCardDragEnd: () => void,
   *   onAddItem?: (columnId: string) => void
   * }}
   */
  let {
    column,
    itemName = 'item',
    isDragOver,
    draggedItemId = null,
    CardComponent = null,
    onDragOver,
    onDragLeave,
    onDrop,
    onCardClick,
    onCardDragStart,
    onCardDragEnd,
    onAddItem
  } = $props();

  /** @type {HTMLDivElement | undefined} */
  let cardsEl;
  // Render-index where the dragged card would insert. null = unknown / column empty.
  let dropRenderIdx = $state(/** @type {number | null} */ (null));

  /** @param {number} clientY */
  function computeDropRenderIdx(clientY) {
    if (!cardsEl) return 0;
    const els = /** @type {HTMLElement[]} */ (
      Array.from(cardsEl.querySelectorAll('[data-card-id]'))
    );
    if (els.length === 0) return 0;
    for (let i = 0; i < els.length; i++) {
      const rect = els[i].getBoundingClientRect();
      const mid = rect.top + rect.height / 2;
      if (clientY < mid) return i;
    }
    return els.length;
  }

  const draggedIdxInColumn = $derived(
    draggedItemId ? column.items.findIndex((it) => it.id === draggedItemId) : -1
  );

  /** @param {number} renderIdx */
  function showIndicatorAt(renderIdx) {
    if (!isDragOver || dropRenderIdx !== renderIdx) return false;
    if (draggedIdxInColumn !== -1) {
      // No-op slots: current position or immediately below the dragged card
      if (renderIdx === draggedIdxInColumn || renderIdx === draggedIdxInColumn + 1) return false;
    }
    return true;
  }

  /** @param {number} renderIdx */
  function resolveNeighbors(renderIdx) {
    /** @type {string | null} */
    let aboveId = null;
    /** @type {string | null} */
    let belowId = null;
    for (let i = renderIdx - 1; i >= 0; i--) {
      if (column.items[i].id !== draggedItemId) {
        aboveId = column.items[i].id;
        break;
      }
    }
    for (let i = renderIdx; i < column.items.length; i++) {
      if (column.items[i].id !== draggedItemId) {
        belowId = column.items[i].id;
        break;
      }
    }
    return { aboveId, belowId };
  }

  // WIP limit check
  const isAtWipLimit = $derived(
    column.wip_limit !== null &&
      column.wip_limit !== undefined &&
      column.item_count >= column.wip_limit
  );

  // Item count (supports item_count, lead_count, task_count)
  const itemCount = $derived(
    column.item_count ?? column.lead_count ?? column.task_count ?? column.items?.length ?? 0
  );

  // Sum of opportunity_amount across cards in this column (0 if none)
  const columnValue = $derived.by(() => {
    if (!column.items) return 0;
    return column.items.reduce((sum, item) => {
      const amount = parseFloat(String(item.opportunity_amount || item.opportunityAmount || 0));
      return sum + (isNaN(amount) ? 0 : amount);
    }, 0);
  });

  function formatColumnValue(value) {
    if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`;
    if (value >= 1000) return `${(value / 1000).toFixed(0)}K`;
    return value.toFixed(0);
  }

  /** @param {DragEvent} e */
  function handleDragOver(e) {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    dropRenderIdx = computeDropRenderIdx(e.clientY);
    onDragOver(e);
  }

  function handleColumnDragLeave() {
    dropRenderIdx = null;
    onDragLeave();
  }

  /** @param {DragEvent} e */
  function handleColumnDrop(e) {
    const idx = computeDropRenderIdx(e.clientY);
    dropRenderIdx = null;
    onDrop(e, resolveNeighbors(idx));
  }
</script>

<div
  class="kanban-column flex h-full max-h-full w-[272px] shrink-0 flex-col rounded-xl bg-[var(--surface-sunken,#f1f2f4)] dark:bg-white/[0.04]"
  class:kanban-drag-over={isDragOver}
  class:wip-exceeded={isAtWipLimit}
  ondragover={handleDragOver}
  ondragleave={handleColumnDragLeave}
  ondrop={handleColumnDrop}
  role="region"
  aria-label="{column.name} column with {itemCount} {itemCount !== 1 ? 'items' : itemName}"
>
  <!-- Header: name + count + optional WIP + optional value -->
  <div class="flex items-center justify-between gap-2 px-3 pt-2.5 pb-2">
    <div class="flex min-w-0 items-center gap-2">
      <h3
        class="truncate text-[13px] font-semibold tracking-tight text-gray-700 dark:text-gray-200"
      >
        {column.name}
      </h3>
      <span
        class="rounded-md bg-gray-200/70 px-1.5 py-px text-[11px] font-medium text-gray-500 dark:bg-white/[0.06] dark:text-gray-400"
      >
        {itemCount}
      </span>
      {#if column.wip_limit}
        <span
          class="rounded-md px-1.5 py-px text-[10px] font-medium tracking-wide uppercase
            {isAtWipLimit
            ? 'bg-rose-100 text-rose-600 dark:bg-rose-500/20 dark:text-rose-400'
            : 'bg-gray-200/60 text-gray-500 dark:bg-white/[0.06] dark:text-gray-400'}"
        >
          max {column.wip_limit}
        </span>
      {/if}
    </div>

    {#if columnValue > 0}
      <span
        class="flex items-center gap-1 rounded-md bg-emerald-50 px-1.5 py-px text-[11px] font-semibold text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300"
        title="Column total"
      >
        <TrendingUp class="h-3 w-3" />
        {formatColumnValue(columnValue)}
      </span>
    {/if}
  </div>

  <!-- Cards -->
  <div bind:this={cardsEl} class="kanban-cards min-h-0 flex-1 space-y-2 overflow-y-auto px-2 pb-1">
    {#each column.items as item, i (item.id)}
      {#if showIndicatorAt(i)}
        <div class="drop-indicator" aria-hidden="true"></div>
      {/if}
      <div data-card-id={item.id}>
        {#if CardComponent}
          <CardComponent
            {item}
            onclick={() => onCardClick(item)}
            ondragstart={(e) => onCardDragStart(e, item)}
            ondragend={onCardDragEnd}
          />
        {:else}
          <div
            class="cursor-pointer rounded-lg border border-black/[0.04] bg-white p-2.5 text-sm shadow-[0_1px_0_rgba(9,30,66,0.12)] hover:border-black/10 dark:border-white/[0.06] dark:bg-white/[0.05]"
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
    {#if showIndicatorAt(column.items.length)}
      <div class="drop-indicator" aria-hidden="true"></div>
    {/if}
  </div>

  <!-- Footer: Add a card -->
  {#if onAddItem}
    <button
      type="button"
      onclick={() => onAddItem(column.id)}
      class="m-2 flex items-center gap-2 rounded-md px-2 py-1.5 text-left text-[13px] font-medium text-gray-500 hover:bg-gray-200/70 hover:text-gray-700 dark:text-gray-400 dark:hover:bg-white/[0.06] dark:hover:text-gray-200"
    >
      <Plus class="h-4 w-4" />
      Add a card
    </button>
  {/if}
</div>

<style>
  .kanban-column {
    transition: background-color 0.15s ease;
  }
  .kanban-column.kanban-drag-over {
    background-color: rgba(0, 0, 0, 0.04);
    box-shadow: inset 0 0 0 2px rgba(34, 211, 238, 0.45);
  }
  :global(.dark) .kanban-column.kanban-drag-over {
    background-color: rgba(255, 255, 255, 0.06);
  }
  .kanban-column.wip-exceeded {
    box-shadow: inset 0 0 0 1px rgba(251, 113, 133, 0.4);
  }

  .drop-indicator {
    height: 3px;
    border-radius: 2px;
    background: rgb(34 211 238);
    margin: 2px 0;
  }

  .kanban-cards::-webkit-scrollbar {
    width: 6px;
  }
  .kanban-cards::-webkit-scrollbar-track {
    background: transparent;
  }
  .kanban-cards::-webkit-scrollbar-thumb {
    background: rgba(0, 0, 0, 0.12);
    border-radius: 100px;
  }
  :global(.dark) .kanban-cards::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.12);
  }
</style>
