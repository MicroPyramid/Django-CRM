<script>
  import { untrack } from 'svelte';
  import { toast } from 'svelte-sonner';
  import KanbanColumn from './KanbanColumn.svelte';
  import { TrendingUp, Users, Flame, Zap } from '@lucide/svelte';

  /**
   * @typedef {Object} Column
   * @property {string} id
   * @property {string} name
   * @property {number} order
   * @property {string} color
   * @property {string} stage_type
   * @property {boolean} is_status_column
   * @property {number|null} wip_limit
   * @property {number} [item_count]
   * @property {Array<any>} items
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
   *   onItemMove: (itemId: string, newStatus: string, columnId: string, aboveId: string | null, belowId: string | null) => Promise<void>,
   *   onCardClick: (item: any) => void,
   *   CardComponent: any,
   *   emptyMessage?: string,
   *   onAddItem?: (columnId: string) => void
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
    emptyMessage = 'No data available',
    onAddItem
  } = $props();

  // Local mutable copy of columns for optimistic updates.
  // Initialize synchronously from props so SSR renders the actual kanban
  // instead of flashing the empty state before $effect runs on hydration.
  /** @type {Column[]} */
  let localColumns = $state(untrack(() => (data?.columns ? structuredClone(data.columns) : [])));

  // Sync local columns when data changes from server (filter/refresh/navigation)
  $effect(() => {
    if (data?.columns) {
      localColumns = structuredClone(data.columns);
    }
  });

  // Drag state
  let draggedItem = $state(null);
  let dragSourceColumn = $state(null);
  let dragOverColumn = $state(null);

  // Mobile: selected column for single-column view
  let mobileActiveColumn = $state('');

  $effect(() => {
    if (localColumns.length > 0 && !mobileActiveColumn) {
      mobileActiveColumn = localColumns[0].id;
    }
  });

  // Pipeline statistics (only show stats bar if there's monetary value)
  const pipelineStats = $derived.by(() => {
    if (!localColumns || localColumns.length === 0) {
      return { totalValue: 0, hotCount: 0 };
    }
    let totalValue = 0;
    let hotCount = 0;
    localColumns.forEach((col) => {
      col.items?.forEach((item) => {
        const amount = parseFloat(String(item.opportunity_amount || item.opportunityAmount || 0));
        if (!isNaN(amount)) totalValue += amount;
        if (item.rating === 'HOT') hotCount++;
      });
    });
    return { totalValue, hotCount };
  });

  function formatValue(value) {
    if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`;
    if (value >= 1000) return `${(value / 1000).toFixed(0)}K`;
    return value.toFixed(0);
  }

  /** @type {HTMLElement | null} */
  let draggedSourceEl = null;

  /**
   * @param {DragEvent} e
   * @param {any} item
   * @param {string} columnId
   */
  function handleDragStart(e, item, columnId) {
    draggedItem = item;
    dragSourceColumn = columnId;
    if (!e.dataTransfer) return;
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', item.id);

    const cardEl = /** @type {HTMLElement | null} */ (
      e.currentTarget instanceof HTMLElement ? e.currentTarget : null
    );
    if (!cardEl) return;

    // Build a crisp, tilted clone for the drag image, the browser default
    // mirrors the source element AFTER our style changes apply, which makes
    // the ghost look washed out. An explicit clone keeps it sharp and tactile.
    const rect = cardEl.getBoundingClientRect();
    const clone = /** @type {HTMLElement} */ (cardEl.cloneNode(true));
    clone.style.position = 'fixed';
    clone.style.top = '-10000px';
    clone.style.left = '-10000px';
    clone.style.width = `${rect.width}px`;
    clone.style.transform = 'rotate(3deg)';
    clone.style.boxShadow = '0 12px 28px rgba(9, 30, 66, 0.25)';
    clone.style.opacity = '1';
    clone.style.pointerEvents = 'none';
    clone.style.zIndex = '9999';
    document.body.appendChild(clone);
    e.dataTransfer.setDragImage(clone, e.clientX - rect.left, e.clientY - rect.top);
    // The browser only needs the node for the next paint; tidy up after.
    setTimeout(() => clone.remove(), 0);

    // Mark the source as a placeholder slot so the column visibly shows
    // where the card came from.
    draggedSourceEl = cardEl;
    requestAnimationFrame(() => {
      cardEl.classList.add('kanban-card-source');
    });
  }

  /**
   * @param {DragEvent} e
   * @param {string} columnId
   */
  function handleDragOver(e, columnId) {
    e.preventDefault();
    if (dragOverColumn !== columnId) {
      dragOverColumn = columnId;
    }
  }

  function handleDragLeave() {
    setTimeout(() => {
      dragOverColumn = null;
    }, 50);
  }

  /**
   * @param {DragEvent} e
   * @param {string} targetColumnId
   * @param {{ aboveId: string | null, belowId: string | null }} neighbors
   */
  async function handleDrop(e, targetColumnId, neighbors) {
    e.preventDefault();
    dragOverColumn = null;

    if (!draggedItem) {
      dragSourceColumn = null;
      return;
    }

    const item = draggedItem;
    const sourceColumnId = dragSourceColumn;
    const { aboveId, belowId } = neighbors;

    draggedItem = null;
    dragSourceColumn = null;

    const sourceCol = localColumns.find((c) => c.id === sourceColumnId);
    const targetCol = localColumns.find((c) => c.id === targetColumnId);
    if (!sourceCol || !targetCol) return;

    // Snapshot for rollback
    const sourceItemsBefore = [...sourceCol.items];
    const targetItemsBefore = [...targetCol.items];
    const sourceCountBefore = sourceCol.item_count;
    const targetCountBefore = targetCol.item_count;

    // Detect no-op: same column AND the dropped position equals current position
    if (sourceColumnId === targetColumnId) {
      const currentIdx = sourceCol.items.findIndex((i) => i.id === item.id);
      const currentAbove = sourceCol.items[currentIdx - 1]?.id ?? null;
      const currentBelow = sourceCol.items[currentIdx + 1]?.id ?? null;
      if (aboveId === currentAbove && belowId === currentBelow) return;
    }

    // Optimistic update: remove from source, insert at resolved position in target
    const srcIdx = sourceCol.items.findIndex((i) => i.id === item.id);
    if (srcIdx !== -1) {
      sourceCol.items.splice(srcIdx, 1);
      sourceCol.item_count--;
    }
    let insertIdx;
    if (belowId) {
      insertIdx = targetCol.items.findIndex((i) => i.id === belowId);
      if (insertIdx === -1) insertIdx = targetCol.items.length;
    } else if (aboveId) {
      const aboveIdx = targetCol.items.findIndex((i) => i.id === aboveId);
      insertIdx = aboveIdx === -1 ? targetCol.items.length : aboveIdx + 1;
    } else {
      insertIdx = targetCol.items.length;
    }
    targetCol.items.splice(insertIdx, 0, { ...item, status: targetColumnId });
    targetCol.item_count++;
    localColumns = [...localColumns];

    try {
      await onItemMove(item.id, targetColumnId, targetColumnId, aboveId, belowId);
    } catch (error) {
      console.error(`Failed to move ${itemName}:`, error);
      toast.error(`Failed to move ${itemName}`);
      sourceCol.items = sourceItemsBefore;
      targetCol.items = targetItemsBefore;
      sourceCol.item_count = sourceCountBefore;
      targetCol.item_count = targetCountBefore;
      localColumns = [...localColumns];
    }
  }

  /** @param {DragEvent} [e] */
  function handleDragEnd(e) {
    if (draggedSourceEl) {
      draggedSourceEl.classList.remove('kanban-card-source');
      draggedSourceEl = null;
    } else if (e?.target instanceof HTMLElement) {
      e.target.classList.remove('kanban-card-source');
    }
    draggedItem = null;
    dragSourceColumn = null;
    dragOverColumn = null;
  }

  const sortedColumns = $derived(
    localColumns.length > 0 ? [...localColumns].sort((a, b) => a.order - b.order) : []
  );

  const activeMobileColumn = $derived(sortedColumns.find((c) => c.id === mobileActiveColumn));

  const totalCount = $derived(data?.total_items ?? data?.total_leads ?? data?.total_tasks ?? 0);
</script>

{#if loading}
  <div class="flex h-full flex-col">
    <div class="columns-container flex min-h-0 flex-1 gap-3 overflow-x-auto pb-3">
      {#each Array.from({ length: 4 }) as _, i (i)}
        <div
          class="flex h-full max-h-full w-[272px] shrink-0 flex-col rounded-xl bg-[var(--surface-sunken,#f1f2f4)] dark:bg-white/[0.04]"
        >
          <div class="flex items-center justify-between px-3 pt-3 pb-2">
            <div class="skeleton h-3.5 w-24 rounded"></div>
            <div class="skeleton h-3.5 w-6 rounded"></div>
          </div>
          <div class="flex flex-col gap-2 px-2 pb-2">
            {#each Array.from({ length: 3 }) as _, j (j)}
              <div
                class="rounded-lg border border-black/[0.04] bg-white p-2.5 shadow-[0_1px_0_rgba(9,30,66,0.12)] dark:border-white/[0.06] dark:bg-white/[0.05]"
              >
                <div class="skeleton mb-1.5 h-1.5 w-10 rounded-sm"></div>
                <div class="skeleton h-3.5 w-[85%] rounded"></div>
                <div class="skeleton mt-1.5 h-3 w-[60%] rounded"></div>
                <div class="mt-2 flex items-center justify-between">
                  <div class="skeleton h-3 w-12 rounded"></div>
                  <div class="flex -space-x-1.5">
                    <div
                      class="skeleton h-6 w-6 rounded-full ring-2 ring-white dark:ring-[#262626]"
                    ></div>
                    <div
                      class="skeleton h-6 w-6 rounded-full ring-2 ring-white dark:ring-[#262626]"
                    ></div>
                  </div>
                </div>
              </div>
            {/each}
          </div>
        </div>
      {/each}
    </div>
  </div>
{:else if !data || sortedColumns.length === 0}
  <div class="flex h-96 flex-col items-center justify-center gap-4 text-center">
    <div class="rounded-xl bg-gray-100 p-6 dark:bg-white/5">
      <Zap class="h-12 w-12 text-gray-300 dark:text-gray-600" />
    </div>
    <div>
      <p class="text-lg font-semibold text-gray-600 dark:text-gray-300">{emptyMessage}</p>
      <p class="mt-1 text-sm text-gray-400 dark:text-gray-500">
        Add some {itemNamePlural} to get started
      </p>
    </div>
  </div>
{:else}
  <div class="flex h-full flex-col">
    <!-- Desktop -->
    <div class="hidden md:flex md:min-h-0 md:flex-1 md:flex-col">
      <!-- Pipeline stats bar (only when monetary value > 0) -->
      {#if pipelineStats.totalValue > 0}
        <div
          class="mb-3 flex items-center gap-5 rounded-lg border border-[var(--border-default)] bg-white px-4 py-2.5 dark:border-white/[0.06] dark:bg-white/[0.02]"
        >
          <div class="flex items-center gap-2">
            <TrendingUp class="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
            <span
              class="text-[11px] font-medium tracking-wider text-gray-500 uppercase dark:text-gray-400"
            >
              Pipeline
            </span>
            <span class="text-sm font-semibold text-gray-800 dark:text-white">
              {formatValue(pipelineStats.totalValue)}
            </span>
          </div>

          <div class="h-4 w-px bg-gray-200 dark:bg-white/10"></div>

          <div class="flex items-center gap-2">
            <Flame class="h-4 w-4 text-rose-500 dark:text-rose-400" />
            <span
              class="text-[11px] font-medium tracking-wider text-gray-500 uppercase dark:text-gray-400"
            >
              Hot
            </span>
            <span class="text-sm font-semibold text-gray-800 dark:text-white">
              {pipelineStats.hotCount}
            </span>
          </div>

          <div class="h-4 w-px bg-gray-200 dark:bg-white/10"></div>

          <div class="flex items-center gap-2">
            <Users class="h-4 w-4 text-gray-500 dark:text-gray-400" />
            <span
              class="text-[11px] font-medium tracking-wider text-gray-500 uppercase dark:text-gray-400"
            >
              Total {itemNamePlural}
            </span>
            <span class="text-sm font-semibold text-gray-800 dark:text-white">
              {totalCount}
            </span>
          </div>
        </div>
      {/if}

      <!-- Columns -->
      <div class="columns-container flex min-h-0 flex-1 gap-3 overflow-x-auto pb-3">
        {#each sortedColumns as column (column.id)}
          <KanbanColumn
            {column}
            {itemName}
            {CardComponent}
            isDragOver={dragOverColumn === column.id}
            draggedItemId={draggedItem?.id ?? null}
            onDragOver={(e) => handleDragOver(e, column.id)}
            onDragLeave={handleDragLeave}
            onDrop={(e, neighbors) => handleDrop(e, column.id, neighbors)}
            {onCardClick}
            onCardDragStart={(e, item) => handleDragStart(e, item, column.id)}
            onCardDragEnd={handleDragEnd}
            {onAddItem}
          />
        {/each}
      </div>
    </div>

    <!-- Mobile: tab-based single-column view -->
    <div class="flex min-h-0 flex-1 flex-col md:hidden">
      <div class="mb-3 overflow-x-auto">
        <div class="flex gap-2 pb-2">
          {#each sortedColumns as col (col.id)}
            <button
              class="shrink-0 rounded-md px-3 py-1.5 text-sm font-medium transition-colors
                {mobileActiveColumn === col.id
                ? 'bg-gray-800 text-white dark:bg-white dark:text-gray-900'
                : 'bg-[var(--surface-sunken,#f1f2f4)] text-gray-700 hover:bg-gray-200 dark:bg-white/[0.06] dark:text-gray-300 dark:hover:bg-white/[0.1]'}"
              onclick={() => (mobileActiveColumn = col.id)}
            >
              {col.name}
              <span
                class="ml-1.5 rounded px-1.5 py-px text-[11px] {mobileActiveColumn === col.id
                  ? 'bg-white/20'
                  : 'bg-gray-200/70 dark:bg-white/[0.08]'}"
              >
                {col.item_count}
              </span>
            </button>
          {/each}
        </div>
      </div>

      {#if activeMobileColumn}
        <div class="space-y-2">
          {#each activeMobileColumn.items as item (item.id)}
            {#if CardComponent}
              <CardComponent {item} onclick={() => onCardClick(item)} />
            {:else}
              <div
                class="rounded-lg border border-black/[0.04] bg-white p-2.5 shadow-[0_1px_0_rgba(9,30,66,0.12)] dark:border-white/[0.06] dark:bg-white/[0.05]"
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

          {#if onAddItem}
            <button
              type="button"
              onclick={() => onAddItem(activeMobileColumn.id)}
              class="flex w-full items-center justify-center gap-2 rounded-md px-2 py-2 text-[13px] font-medium text-gray-500 hover:bg-gray-200/70 hover:text-gray-700 dark:text-gray-400 dark:hover:bg-white/[0.06] dark:hover:text-gray-200"
            >
              Add a card
            </button>
          {/if}
        </div>
      {/if}
    </div>
  </div>
{/if}

<style>
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

  :global(.kanban-card-source) {
    opacity: 0.35 !important;
    filter: grayscale(0.4);
    outline: 2px dashed rgba(34, 211, 238, 0.7);
    outline-offset: -2px;
    border-radius: 0.5rem;
  }

  .skeleton {
    background: linear-gradient(
      90deg,
      rgba(0, 0, 0, 0.06) 0%,
      rgba(0, 0, 0, 0.1) 50%,
      rgba(0, 0, 0, 0.06) 100%
    );
    background-size: 200% 100%;
    animation: shimmer 1.4s ease-in-out infinite;
  }
  :global(.dark) .skeleton {
    background: linear-gradient(
      90deg,
      rgba(255, 255, 255, 0.06) 0%,
      rgba(255, 255, 255, 0.1) 50%,
      rgba(255, 255, 255, 0.06) 100%
    );
    background-size: 200% 100%;
  }
  @keyframes shimmer {
    0% {
      background-position: 200% 0;
    }
    100% {
      background-position: -200% 0;
    }
  }
</style>
