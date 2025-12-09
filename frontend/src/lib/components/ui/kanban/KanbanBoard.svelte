<script>
	import { toast } from 'svelte-sonner';
	import KanbanColumn from './KanbanColumn.svelte';
	import { Loader2 } from '@lucide/svelte';

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
	const totalCount = $derived(
		data?.total_items ?? data?.total_leads ?? data?.total_tasks ?? 0
	);
</script>

{#if loading}
	<div class="flex h-64 items-center justify-center">
		<Loader2 class="h-8 w-8 animate-spin text-gray-400" />
	</div>
{:else if !data || sortedColumns.length === 0}
	<div class="flex h-64 flex-col items-center justify-center text-center text-gray-500">
		<p>{emptyMessage}</p>
	</div>
{:else}
	<!-- Desktop: Horizontal scroll container with all columns -->
	<div class="hidden gap-4 overflow-x-auto pb-4 md:flex" style="min-height: 400px">
		{#each sortedColumns as column (column.id)}
			<KanbanColumn
				{column}
				{itemName}
				{CardComponent}
				isDragOver={dragOverColumn === column.id}
				onDragOver={(e) => handleDragOver(e, column.id)}
				onDragLeave={handleDragLeave}
				onDrop={(e) => handleDrop(e, column.id)}
				onCardClick={onCardClick}
				onCardDragStart={(e, item) => handleDragStart(e, item, column.id)}
				onCardDragEnd={handleDragEnd}
			/>
		{/each}
	</div>

	<!-- Mobile: Tab-based single column view -->
	<div class="md:hidden">
		<!-- Column selector -->
		<div class="mb-4">
			<select
				class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
				bind:value={mobileActiveColumn}
			>
				{#each sortedColumns as col (col.id)}
					<option value={col.id}>{col.name} ({col.item_count})</option>
				{/each}
			</select>
		</div>

		<!-- Active column cards -->
		{#if activeMobileColumn}
			<div class="space-y-3">
				{#each activeMobileColumn.items as item (item.id)}
					{#if CardComponent}
						<svelte:component
							this={CardComponent}
							{item}
							onclick={() => onCardClick(item)}
						/>
					{:else}
						<div
							class="rounded-lg border border-gray-200 bg-white p-3 dark:border-gray-700 dark:bg-gray-900"
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
						class="flex h-24 items-center justify-center rounded-lg border-2 border-dashed border-gray-300 text-sm text-gray-400"
					>
						No {itemNamePlural} in this column
					</div>
				{/if}
			</div>
		{/if}
	</div>

	<!-- Total count footer -->
	<div class="mt-4 text-sm text-gray-500 dark:text-gray-400">
		{totalCount} {totalCount !== 1 ? itemNamePlural : itemName} total
	</div>
{/if}
