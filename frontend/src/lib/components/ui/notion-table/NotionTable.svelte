<script>
	import { onMount, tick } from 'svelte';
	import {
		Check,
		ChevronDown,
		Eye,
		Plus,
		Expand,
		GripVertical,
		Building2,
		User
	} from '@lucide/svelte';
	import * as DropdownMenu from '$lib/components/ui/dropdown-menu/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import {
		calculateDropPosition,
		reorderItems,
		handleDragStart as dndDragStart,
		dragHandleClasses,
		expandButtonClasses,
		dropIndicatorClasses,
		draggedRowClasses
	} from '$lib/utils/drag-drop.js';
	import { getOptionStyle, getOptionLabel, getOptionBgColor } from '$lib/utils/table-helpers.js';

	/**
	 * @typedef {Object} ColumnDef
	 * @property {string} key - Field key in data object
	 * @property {string} label - Display label for column header
	 * @property {'text' | 'email' | 'number' | 'date' | 'select' | 'checkbox' | 'relation'} [type='text']
	 * @property {string} [width] - Tailwind width class
	 * @property {{ value: string, label: string, color: string }[]} [options] - Options for select type
	 * @property {boolean} [editable=true] - Allow inline editing
	 * @property {boolean} [canHide=true] - Allow hiding column
	 * @property {string} [emptyText='Empty'] - Text when value is empty
	 * @property {(value: any) => string} [format] - Custom value formatter
	 * @property {(row: any) => any} [getValue] - Custom value getter for nested data
	 * @property {string} [relationIcon] - Icon type for relation cells ('building' | 'user')
	 */

	/**
	 * @type {{
	 *   data: any[],
	 *   columns: ColumnDef[],
	 *   storageKey: string,
	 *   title?: string,
	 *   subtitle?: string,
	 *   enableDragDrop?: boolean,
	 *   enableColumnToggle?: boolean,
	 *   enableNewRow?: boolean,
	 *   onRowChange?: (row: any, field: string, value: any) => void,
	 *   onRowClick?: (row: any) => void,
	 *   onAddRow?: () => void,
	 *   onReorder?: (rows: any[]) => void,
	 *   emptyState?: import('svelte').Snippet,
	 *   headerActions?: import('svelte').Snippet
	 * }}
	 */
	let {
		data = [],
		columns = [],
		storageKey,
		title = '',
		subtitle = '',
		enableDragDrop = true,
		enableColumnToggle = true,
		enableNewRow = true,
		onRowChange,
		onRowClick,
		onAddRow,
		onReorder,
		emptyState,
		headerActions
	} = $props();

	// Column visibility state
	let visibleColumns = $state(columns.map((c) => c.key));

	// Editing state
	/** @type {{ rowId: string, columnKey: string } | null} */
	let editingCell = $state(null);
	let editValue = $state('');

	// Drag-and-drop state
	/** @type {string | null} */
	let draggedRowId = $state(null);
	/** @type {string | null} */
	let dragOverRowId = $state(null);
	/** @type {'before' | 'after' | null} */
	let dropPosition = $state(null);

	// Load column visibility from localStorage
	onMount(() => {
		const saved = localStorage.getItem(storageKey);
		if (saved) {
			try {
				const parsed = JSON.parse(saved);
				// Only use saved columns that still exist
				visibleColumns = parsed.filter((/** @type {string} */ key) =>
					columns.some((c) => c.key === key)
				);
			} catch (e) {
				console.error('Failed to parse saved columns:', e);
			}
		}
	});

	// Save column visibility when changed
	$effect(() => {
		if (storageKey) {
			localStorage.setItem(storageKey, JSON.stringify(visibleColumns));
		}
	});

	/**
	 * @param {string} key
	 */
	function isColumnVisible(key) {
		return visibleColumns.includes(key);
	}

	/**
	 * @param {string} key
	 */
	function toggleColumn(key) {
		const column = columns.find((c) => c.key === key);
		if (column?.canHide === false) return;

		if (visibleColumns.includes(key)) {
			visibleColumns = visibleColumns.filter((k) => k !== key);
		} else {
			visibleColumns = [...visibleColumns, key];
		}
	}

	/**
	 * Get value from row, using custom getter if provided
	 * @param {any} row
	 * @param {ColumnDef} column
	 */
	function getCellValue(row, column) {
		if (column.getValue) {
			return column.getValue(row);
		}
		return row[column.key];
	}

	/**
	 * Format value for display
	 * @param {any} value
	 * @param {ColumnDef} column
	 */
	function formatValue(value, column) {
		if (value == null || value === '') return null;
		if (column.format) return column.format(value);
		if (column.type === 'number') return formatCurrency(value);
		if (column.type === 'date') return formatDate(value);
		return value;
	}

	/**
	 * @param {number} value
	 */
	function formatCurrency(value) {
		return new Intl.NumberFormat('en-US', {
			style: 'currency',
			currency: 'USD',
			minimumFractionDigits: 0,
			maximumFractionDigits: 0
		}).format(value);
	}

	/**
	 * @param {string} dateStr
	 */
	function formatDate(dateStr) {
		if (!dateStr) return '';
		const date = new Date(dateStr);
		return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
	}

	/**
	 * Start editing a cell
	 * @param {string} rowId
	 * @param {string} columnKey
	 */
	async function startEditing(rowId, columnKey) {
		const row = data.find((r) => r.id === rowId);
		const column = columns.find((c) => c.key === columnKey);

		if (!row || !column) return;
		if (column.editable === false) return;
		// Non-editable types
		if (column.type === 'checkbox' || column.type === 'relation' || column.type === 'select')
			return;

		editingCell = { rowId, columnKey };
		const value = getCellValue(row, column);
		editValue = value?.toString() ?? '';

		await tick();

		const input = document.querySelector(`[data-edit-input="${rowId}-${columnKey}"]`);
		if (input) {
			// @ts-ignore
			input.focus();
			// @ts-ignore
			if (input.select) input.select();
		}
	}

	/**
	 * Stop editing and optionally save
	 * @param {boolean} save
	 */
	function stopEditing(save = true) {
		if (!editingCell) return;

		if (save && onRowChange) {
			const { rowId, columnKey } = editingCell;
			const column = columns.find((c) => c.key === columnKey);
			const row = data.find((r) => r.id === rowId);

			if (row && column) {
				/** @type {string | number} */
				let parsedValue = editValue;
				if (column.type === 'number') {
					parsedValue = parseFloat(editValue) || 0;
				}

				const original = getCellValue(row, column);
				if (parsedValue !== original) {
					onRowChange(row, columnKey, parsedValue);
				}
			}
		}

		editingCell = null;
		editValue = '';
	}

	/**
	 * @param {KeyboardEvent} e
	 */
	function handleKeydown(e) {
		if (e.key === 'Enter') {
			e.preventDefault();
			stopEditing(true);
		} else if (e.key === 'Escape') {
			e.preventDefault();
			stopEditing(false);
		}
	}

	/**
	 * Update select value
	 * @param {string} rowId
	 * @param {string} columnKey
	 * @param {string} value
	 */
	function updateSelectValue(rowId, columnKey, value) {
		const row = data.find((r) => r.id === rowId);
		if (row && onRowChange) {
			onRowChange(row, columnKey, value);
		}
	}

	/**
	 * Toggle checkbox value
	 * @param {string} rowId
	 * @param {string} columnKey
	 */
	function toggleCheckbox(rowId, columnKey) {
		const row = data.find((r) => r.id === rowId);
		const column = columns.find((c) => c.key === columnKey);
		if (row && column && onRowChange) {
			const currentValue = getCellValue(row, column);
			onRowChange(row, columnKey, !currentValue);
		}
	}

	// Drag-and-drop handlers
	/**
	 * @param {DragEvent} e
	 * @param {string} rowId
	 */
	function handleDragStart(e, rowId) {
		draggedRowId = rowId;
		dndDragStart(e, rowId);
	}

	/**
	 * @param {DragEvent} e
	 * @param {string} rowId
	 */
	function handleRowDragOver(e, rowId) {
		e.preventDefault();
		if (draggedRowId === rowId) return;
		dragOverRowId = rowId;
		dropPosition = calculateDropPosition(e);
	}

	function handleRowDragLeave() {
		dragOverRowId = null;
		dropPosition = null;
	}

	/**
	 * @param {DragEvent} e
	 * @param {string} targetRowId
	 */
	function handleRowDrop(e, targetRowId) {
		e.preventDefault();

		if (draggedRowId && targetRowId && onReorder && dropPosition) {
			const newData = reorderItems(data, draggedRowId, targetRowId, dropPosition, (r) => r.id);
			onReorder(newData);
		}

		resetDragState();
	}

	function handleDragEnd() {
		resetDragState();
	}

	function resetDragState() {
		draggedRowId = null;
		dragOverRowId = null;
		dropPosition = null;
	}

	// Derived values
	const visibleColumnDefs = $derived(columns.filter((col) => isColumnVisible(col.key)));
	const columnCounts = $derived({
		visible: visibleColumns.length,
		total: columns.length
	});
</script>

<div class="min-h-screen rounded-lg border border-border/40 bg-white dark:bg-gray-950">
	<!-- Header -->
	{#if title || enableColumnToggle || enableNewRow || headerActions}
		<div class="border-b border-gray-200 px-6 py-4 dark:border-gray-800">
			<div class="flex items-center justify-between">
				<div>
					{#if title}
						<h1 class="text-2xl font-semibold text-gray-900 dark:text-gray-100">{title}</h1>
					{/if}
					{#if subtitle}
						<p class="mt-1 text-sm text-gray-500 dark:text-gray-400">{subtitle}</p>
					{:else if data.length > 0}
						<p class="mt-1 text-sm text-gray-500 dark:text-gray-400">{data.length} items</p>
					{/if}
				</div>
				<div class="flex items-center gap-2">
					{#if headerActions}
						{@render headerActions()}
					{/if}

					{#if enableColumnToggle}
						<DropdownMenu.Root>
							<DropdownMenu.Trigger>
								{#snippet child({ props })}
									<Button {...props} variant="outline" size="sm" class="gap-2">
										<Eye class="h-4 w-4" />
										Columns
										{#if columnCounts.visible < columnCounts.total}
											<span
												class="rounded-full bg-blue-100 px-1.5 py-0.5 text-xs font-medium text-blue-700"
											>
												{columnCounts.visible}/{columnCounts.total}
											</span>
										{/if}
									</Button>
								{/snippet}
							</DropdownMenu.Trigger>
							<DropdownMenu.Content align="end" class="w-48">
								<DropdownMenu.Label>Toggle columns</DropdownMenu.Label>
								<DropdownMenu.Separator />
								{#each columns as column (column.key)}
									<DropdownMenu.CheckboxItem
										class=""
										checked={isColumnVisible(column.key)}
										onCheckedChange={() => toggleColumn(column.key)}
										disabled={column.canHide === false}
									>
										{column.label}
									</DropdownMenu.CheckboxItem>
								{/each}
							</DropdownMenu.Content>
						</DropdownMenu.Root>
					{/if}

					{#if enableNewRow && onAddRow}
						<Button size="sm" class="gap-2" onclick={onAddRow}>
							<Plus class="h-4 w-4" />
							New
						</Button>
					{/if}
				</div>
			</div>
		</div>
	{/if}

	<!-- Table -->
	<div class="overflow-x-auto">
		{#if data.length === 0}
			{#if emptyState}
				{@render emptyState()}
			{:else}
				<div class="flex flex-col items-center justify-center py-16 text-center">
					<p class="text-muted-foreground text-sm">No items found</p>
					{#if enableNewRow && onAddRow}
						<Button onclick={onAddRow} class="mt-4">
							<Plus class="mr-2 h-4 w-4" />
							Add New
						</Button>
					{/if}
				</div>
			{/if}
		{:else}
			<table class="w-full border-collapse">
				<!-- Header -->
				<thead>
					<tr class="border-b border-gray-100/60 dark:border-gray-800/60">
						{#if enableDragDrop}
							<th class="w-8 px-1"></th>
						{/if}
						{#if onRowClick}
							<th class="w-8 px-1"></th>
						{/if}
						{#each visibleColumnDefs as column (column.key)}
							<th
								class="px-4 py-3 text-left text-[13px] font-normal text-gray-400 dark:text-gray-500 {column.width ||
									''}"
							>
								{column.label}
							</th>
						{/each}
					</tr>
				</thead>

				<!-- Body -->
				<tbody>
					{#each data as row (row.id)}
						<!-- Drop indicator (before) -->
						{#if dragOverRowId === row.id && dropPosition === 'before'}
							<tr class="h-0">
								<td
									colspan={visibleColumnDefs.length + (enableDragDrop ? 1 : 0) + (onRowClick ? 1 : 0)}
									class="p-0"
								>
									<div class={dropIndicatorClasses}></div>
								</td>
							</tr>
						{/if}

						<tr
							class="group transition-all duration-100 ease-out hover:bg-gray-50/30 dark:hover:bg-gray-900/30 {draggedRowId ===
							row.id
								? draggedRowClasses
								: ''}"
							ondragover={(e) => handleRowDragOver(e, row.id)}
							ondragleave={handleRowDragLeave}
							ondrop={(e) => handleRowDrop(e, row.id)}
						>
							<!-- Drag Handle -->
							{#if enableDragDrop}
								<td class="w-8 px-1 py-3">
									<div
										draggable="true"
										ondragstart={(e) => handleDragStart(e, row.id)}
										ondragend={handleDragEnd}
										class={dragHandleClasses}
										role="button"
										tabindex="0"
										aria-label="Drag to reorder"
									>
										<GripVertical class="h-4 w-4 text-gray-400" />
									</div>
								</td>
							{/if}

							<!-- Expand button -->
							{#if onRowClick}
								<td class="w-8 px-1 py-3">
									<button
										type="button"
										onclick={() => onRowClick(row)}
										class={expandButtonClasses}
									>
										<Expand class="h-3.5 w-3.5 text-gray-500" />
									</button>
								</td>
							{/if}

							<!-- Data cells -->
							{#each visibleColumnDefs as column (column.key)}
								{@const value = getCellValue(row, column)}
								{@const formattedValue = formatValue(value, column)}
								<td class="px-4 py-3 {column.width || ''}">
									<!-- Text / Email / Number cells -->
									{#if column.type === 'text' || column.type === 'email' || column.type === 'number' || !column.type}
										{#if editingCell?.rowId === row.id && editingCell?.columnKey === column.key}
											<input
												type={column.type === 'email'
													? 'email'
													: column.type === 'number'
														? 'number'
														: 'text'}
												bind:value={editValue}
												onkeydown={handleKeydown}
												onblur={() => stopEditing(true)}
												data-edit-input="{row.id}-{column.key}"
												class="w-full rounded px-2 py-1.5 text-sm bg-white dark:bg-gray-900 outline-none ring-1 ring-gray-200 dark:ring-gray-700 focus:ring-blue-300 shadow-sm transition-shadow duration-100"
											/>
										{:else}
											<button
												type="button"
												onclick={() =>
													column.editable !== false
														? startEditing(row.id, column.key)
														: onRowClick?.(row)}
												class="-mx-2 -my-1.5 w-full cursor-text rounded px-2 py-1.5 text-left text-sm text-gray-900 dark:text-gray-100 transition-colors duration-75 hover:bg-gray-100/50 dark:hover:bg-gray-800/50"
											>
												{#if formattedValue}
													{formattedValue}
												{:else}
													<span class="text-gray-400">{column.emptyText || 'Empty'}</span>
												{/if}
											</button>
										{/if}

										<!-- Date cells -->
									{:else if column.type === 'date'}
										{#if editingCell?.rowId === row.id && editingCell?.columnKey === column.key}
											<input
												type="date"
												bind:value={editValue}
												onkeydown={handleKeydown}
												onblur={() => stopEditing(true)}
												data-edit-input="{row.id}-{column.key}"
												class="w-full rounded px-2 py-1.5 text-sm bg-white dark:bg-gray-900 outline-none ring-1 ring-gray-200 dark:ring-gray-700 focus:ring-blue-300 shadow-sm transition-shadow duration-100"
											/>
										{:else}
											<button
												type="button"
												onclick={() =>
													column.editable !== false
														? startEditing(row.id, column.key)
														: onRowClick?.(row)}
												class="-mx-2 -my-1.5 w-full cursor-text rounded px-2 py-1.5 text-left text-sm text-gray-900 dark:text-gray-100 transition-colors duration-75 hover:bg-gray-100/50 dark:hover:bg-gray-800/50"
											>
												{#if formattedValue}
													{formattedValue}
												{:else}
													<span class="text-gray-400">{column.emptyText || 'Empty'}</span>
												{/if}
											</button>
										{/if}

										<!-- Select cells -->
									{:else if column.type === 'select' && column.options}
										<DropdownMenu.Root>
											<DropdownMenu.Trigger>
												{#snippet child({ props })}
													<button
														{...props}
														type="button"
														class="inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium transition-opacity hover:opacity-80 {getOptionStyle(
															value,
															column.options
														)}"
													>
														{getOptionLabel(value, column.options)}
														<ChevronDown class="h-3 w-3 opacity-60" />
													</button>
												{/snippet}
											</DropdownMenu.Trigger>
											<DropdownMenu.Content align="start" class="w-36">
												{#each column.options as option (option.value)}
													<DropdownMenu.Item
														onclick={() => updateSelectValue(row.id, column.key, option.value)}
														class="flex items-center gap-2"
													>
														<span class="h-2 w-2 rounded-full {getOptionBgColor(option.value, [option])}"></span>
														{option.label}
														{#if value === option.value}
															<Check class="ml-auto h-4 w-4" />
														{/if}
													</DropdownMenu.Item>
												{/each}
											</DropdownMenu.Content>
										</DropdownMenu.Root>

										<!-- Checkbox cells -->
									{:else if column.type === 'checkbox'}
										<button
											type="button"
											onclick={() => toggleCheckbox(row.id, column.key)}
											class="flex h-5 w-5 items-center justify-center rounded border transition-colors {value
												? 'border-blue-500 bg-blue-500'
												: 'border-gray-300 hover:border-gray-400'}"
										>
											{#if value}
												<Check class="h-3.5 w-3.5 text-white" />
											{/if}
										</button>

										<!-- Relation cells -->
									{:else if column.type === 'relation'}
										<button
											type="button"
											onclick={() => onRowClick?.(row)}
											class="-mx-2 -my-1.5 w-full cursor-pointer rounded px-2 py-1.5 text-left text-sm text-gray-900 dark:text-gray-100 transition-colors duration-75 hover:bg-gray-100/50 dark:hover:bg-gray-800/50"
										>
											{#if value}
												<div class="flex items-center gap-1.5">
													{#if column.relationIcon === 'user'}
														<User class="h-3.5 w-3.5 text-gray-400" />
													{:else}
														<Building2 class="h-3.5 w-3.5 text-gray-400" />
													{/if}
													<span class="truncate"
														>{typeof value === 'object' ? value.name || value.email : value}</span
													>
												</div>
											{:else}
												<span class="text-gray-400">-</span>
											{/if}
										</button>
									{/if}
								</td>
							{/each}
						</tr>

						<!-- Drop indicator (after) -->
						{#if dragOverRowId === row.id && dropPosition === 'after'}
							<tr class="h-0">
								<td
									colspan={visibleColumnDefs.length + (enableDragDrop ? 1 : 0) + (onRowClick ? 1 : 0)}
									class="p-0"
								>
									<div class={dropIndicatorClasses}></div>
								</td>
							</tr>
						{/if}
					{/each}
				</tbody>
			</table>
		{/if}
	</div>

	<!-- Add row button at bottom -->
	{#if enableNewRow && onAddRow && data.length > 0}
		<div class="border-t border-gray-100 px-4 py-2 dark:border-gray-800">
			<button
				type="button"
				onclick={onAddRow}
				class="flex items-center gap-2 rounded px-2 py-1.5 text-sm text-gray-500 transition-colors hover:bg-gray-50 hover:text-gray-700 dark:hover:bg-gray-800 dark:hover:text-gray-300"
			>
				<Plus class="h-4 w-4" />
				New row
			</button>
		</div>
	{/if}
</div>
