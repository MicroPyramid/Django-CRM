<script>
	import { onMount, tick } from 'svelte';
	import { Check, ChevronDown, Eye, Plus, Expand, Trash2, X, Mail, Building2, Circle, Zap, DollarSign, Calendar, Star, GripVertical } from '@lucide/svelte';
	import * as DropdownMenu from '$lib/components/ui/dropdown-menu/index.js';
	import * as Sheet from '$lib/components/ui/sheet/index.js';
	import { Button } from '$lib/components/ui/button/index.js';

	const STORAGE_KEY = 'notion-table-columns';

	// Status and priority options with colors
	const statusOptions = [
		{ value: 'active', label: 'Active', color: 'bg-emerald-100 text-emerald-700' },
		{ value: 'inactive', label: 'Inactive', color: 'bg-gray-100 text-gray-600' },
		{ value: 'pending', label: 'Pending', color: 'bg-amber-100 text-amber-700' }
	];

	const priorityOptions = [
		{ value: 'high', label: 'High', color: 'bg-red-100 text-red-700' },
		{ value: 'medium', label: 'Medium', color: 'bg-yellow-100 text-yellow-700' },
		{ value: 'low', label: 'Low', color: 'bg-blue-100 text-blue-700' }
	];

	// Column definitions
	const columns = [
		{ key: 'name', label: 'Name', type: 'text', width: 'w-48' },
		{ key: 'email', label: 'Email', type: 'email', width: 'w-52' },
		{ key: 'company', label: 'Company', type: 'text', width: 'w-40' },
		{ key: 'status', label: 'Status', type: 'select', options: statusOptions, width: 'w-28' },
		{ key: 'priority', label: 'Priority', type: 'select', options: priorityOptions, width: 'w-28' },
		{ key: 'dealValue', label: 'Deal Value', type: 'number', width: 'w-32' },
		{ key: 'lastContact', label: 'Last Contact', type: 'date', width: 'w-36' },
		{ key: 'isVIP', label: 'VIP', type: 'checkbox', width: 'w-16' }
	];

	// Mock data
	let data = $state([
		{ id: '1', name: 'John Smith', email: 'john@acme.com', company: 'Acme Corp', status: 'active', priority: 'high', dealValue: 50000, lastContact: '2024-01-15', isVIP: true },
		{ id: '2', name: 'Sarah Johnson', email: 'sarah@techflow.io', company: 'TechFlow', status: 'active', priority: 'medium', dealValue: 35000, lastContact: '2024-01-18', isVIP: false },
		{ id: '3', name: 'Michael Chen', email: 'mchen@innovate.co', company: 'Innovate Co', status: 'pending', priority: 'high', dealValue: 75000, lastContact: '2024-01-10', isVIP: true },
		{ id: '4', name: 'Emily Davis', email: 'emily@startup.xyz', company: 'StartupXYZ', status: 'inactive', priority: 'low', dealValue: 15000, lastContact: '2023-12-20', isVIP: false },
		{ id: '5', name: 'Robert Wilson', email: 'rwilson@enterprise.com', company: 'Enterprise Inc', status: 'active', priority: 'high', dealValue: 120000, lastContact: '2024-01-22', isVIP: true },
		{ id: '6', name: 'Lisa Anderson', email: 'lisa@cloudtech.io', company: 'CloudTech', status: 'pending', priority: 'medium', dealValue: 45000, lastContact: '2024-01-08', isVIP: false },
		{ id: '7', name: 'David Martinez', email: 'david@global.net', company: 'Global Networks', status: 'active', priority: 'low', dealValue: 28000, lastContact: '2024-01-19', isVIP: false },
		{ id: '8', name: 'Jennifer Brown', email: 'jbrown@fintech.co', company: 'FinTech Solutions', status: 'active', priority: 'high', dealValue: 95000, lastContact: '2024-01-21', isVIP: true },
		{ id: '9', name: 'Chris Taylor', email: 'chris@datawise.com', company: 'DataWise', status: 'inactive', priority: 'medium', dealValue: 22000, lastContact: '2023-11-30', isVIP: false },
		{ id: '10', name: 'Amanda White', email: 'awhite@growthco.io', company: 'GrowthCo', status: 'pending', priority: 'high', dealValue: 68000, lastContact: '2024-01-16', isVIP: true }
	]);

	// Column visibility state
	let visibleColumns = $state(columns.map(c => c.key));

	// Editing state
	let editingCell = $state(null); // { rowId, columnKey }
	let editValue = $state('');

	// Row detail sheet state
	let sheetOpen = $state(false);
	let selectedRowId = $state(null);

	// Drag-and-drop state
	let draggedRowId = $state(null);
	let dragOverRowId = $state(null);
	/** @type {'before' | 'after' | null} */
	let dropPosition = $state(null);

	// Load column visibility from localStorage
	onMount(() => {
		const saved = localStorage.getItem(STORAGE_KEY);
		if (saved) {
			try {
				visibleColumns = JSON.parse(saved);
			} catch (e) {
				console.error('Failed to parse saved columns:', e);
			}
		}
	});

	// Save column visibility when changed
	$effect(() => {
		localStorage.setItem(STORAGE_KEY, JSON.stringify(visibleColumns));
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
		if (visibleColumns.includes(key)) {
			visibleColumns = visibleColumns.filter(k => k !== key);
		} else {
			visibleColumns = [...visibleColumns, key];
		}
	}

	/**
	 * @param {string} rowId
	 * @param {string} columnKey
	 */
	async function startEditing(rowId, columnKey) {
		const row = data.find(r => r.id === rowId);
		if (!row) return;

		editingCell = { rowId, columnKey };
		editValue = row[columnKey]?.toString() ?? '';
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
	 * @param {boolean} save
	 */
	function stopEditing(save = true) {
		if (!editingCell) return;

		if (save) {
			const { rowId, columnKey } = editingCell;
			const column = columns.find(c => c.key === columnKey);

			data = data.map(row => {
				if (row.id === rowId) {
					/** @type {string | number} */
					let value = editValue;
					if (column?.type === 'number') {
						value = parseFloat(editValue) || 0;
					}
					return { ...row, [columnKey]: value };
				}
				return row;
			});
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
	 * @param {string} rowId
	 * @param {string} columnKey
	 * @param {string} value
	 */
	function updateSelectValue(rowId, columnKey, value) {
		data = data.map(row => {
			if (row.id === rowId) {
				return { ...row, [columnKey]: value };
			}
			return row;
		});
	}

	/**
	 * @param {string} rowId
	 */
	function toggleCheckbox(rowId) {
		data = data.map(row => {
			if (row.id === rowId) {
				return { ...row, isVIP: !row.isVIP };
			}
			return row;
		});
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
	 * @param {string} value
	 * @param {{ value: string, label: string, color: string }[]} options
	 */
	function getOptionStyle(value, options) {
		const option = options.find(o => o.value === value);
		return option?.color ?? 'bg-gray-100 text-gray-600';
	}

	/**
	 * @param {string} value
	 * @param {{ value: string, label: string, color: string }[]} options
	 */
	function getOptionLabel(value, options) {
		const option = options.find(o => o.value === value);
		return option?.label ?? value;
	}

	function addNewRow() {
		const newId = (Math.max(...data.map(d => parseInt(d.id))) + 1).toString();
		data = [...data, {
			id: newId,
			name: '',
			email: '',
			company: '',
			status: 'pending',
			priority: 'medium',
			dealValue: 0,
			lastContact: new Date().toISOString().split('T')[0],
			isVIP: false
		}];
	}

	// Row detail sheet functions
	/**
	 * @param {string} rowId
	 */
	function openRowSheet(rowId) {
		selectedRowId = rowId;
		sheetOpen = true;
	}

	function closeRowSheet() {
		sheetOpen = false;
		selectedRowId = null;
	}

	/**
	 * @param {string} key
	 * @param {any} value
	 */
	function updateSelectedRowField(key, value) {
		if (!selectedRowId) return;
		data = data.map(row => {
			if (row.id === selectedRowId) {
				return { ...row, [key]: value };
			}
			return row;
		});
	}

	function deleteSelectedRow() {
		if (!selectedRowId) return;
		data = data.filter(row => row.id !== selectedRowId);
		closeRowSheet();
	}

	// Drag-and-drop handlers
	/**
	 * @param {DragEvent} e
	 * @param {string} rowId
	 */
	function handleDragStart(e, rowId) {
		draggedRowId = rowId;
		if (e.dataTransfer) {
			e.dataTransfer.effectAllowed = 'move';
			e.dataTransfer.setData('text/plain', rowId);
		}
	}

	/**
	 * @param {DragEvent} e
	 * @param {string} rowId
	 */
	function handleRowDragOver(e, rowId) {
		e.preventDefault();
		if (draggedRowId === rowId) return;

		dragOverRowId = rowId;

		// Determine drop position based on mouse position
		const rect = /** @type {HTMLElement} */ (e.currentTarget).getBoundingClientRect();
		const midpoint = rect.top + rect.height / 2;
		dropPosition = e.clientY < midpoint ? 'before' : 'after';
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
		if (!draggedRowId || draggedRowId === targetRowId) {
			resetDragState();
			return;
		}

		const draggedIndex = data.findIndex(r => r.id === draggedRowId);
		const targetIndex = data.findIndex(r => r.id === targetRowId);

		if (draggedIndex === -1 || targetIndex === -1) {
			resetDragState();
			return;
		}

		// Create new array and reorder
		const newData = [...data];
		const [draggedItem] = newData.splice(draggedIndex, 1);

		// Calculate insert position
		let insertIndex = targetIndex;
		if (dropPosition === 'after') {
			insertIndex = draggedIndex < targetIndex ? targetIndex : targetIndex + 1;
		} else {
			insertIndex = draggedIndex < targetIndex ? targetIndex - 1 : targetIndex;
		}

		newData.splice(insertIndex, 0, draggedItem);
		data = newData;

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

	// Get selected row data
	const selectedRow = $derived(data.find(r => r.id === selectedRowId));
</script>

<div class="min-h-screen bg-white">
	<!-- Header -->
	<div class="border-b border-gray-200 px-6 py-4">
		<div class="flex items-center justify-between">
			<div>
				<h1 class="text-2xl font-semibold text-gray-900">Contacts Database</h1>
				<p class="text-sm text-gray-500 mt-1">{data.length} contacts</p>
			</div>
			<div class="flex items-center gap-2">
				<!-- Column Visibility Dropdown -->
				<DropdownMenu.Root>
					<DropdownMenu.Trigger asChild>
						{#snippet child({ props })}
							<Button {...props} variant="outline" size="sm" class="gap-2">
								<Eye class="h-4 w-4" />
								Columns
								{#if visibleColumns.length < columns.length}
									<span class="rounded-full bg-blue-100 px-1.5 py-0.5 text-xs font-medium text-blue-700">
										{visibleColumns.length}/{columns.length}
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
							>
								{column.label}
							</DropdownMenu.CheckboxItem>
						{/each}
					</DropdownMenu.Content>
				</DropdownMenu.Root>

				<Button size="sm" class="gap-2" onclick={addNewRow}>
					<Plus class="h-4 w-4" />
					New
				</Button>
			</div>
		</div>
	</div>

	<!-- Table -->
	<div class="overflow-x-auto">
		<table class="w-full border-collapse">
			<!-- Header -->
			<thead>
				<tr class="border-b border-gray-100/60">
					<!-- Drag handle column -->
					<th class="w-8 px-1"></th>
					<!-- Expand button column -->
					<th class="w-8 px-1"></th>
					{#each columns as column (column.key)}
						{#if isColumnVisible(column.key)}
							<th class="px-4 py-3 text-left text-[13px] font-normal text-gray-400 {column.width}">
								{column.label}
							</th>
						{/if}
					{/each}
				</tr>
			</thead>

			<!-- Body -->
			<tbody>
				{#each data as row (row.id)}
					<!-- Drop indicator line (before row) -->
					{#if dragOverRowId === row.id && dropPosition === 'before'}
						<tr class="h-0">
							<td colspan={visibleColumns.length + 2} class="p-0">
								<div class="h-0.5 bg-blue-400 rounded-full mx-4"></div>
							</td>
						</tr>
					{/if}

					<tr
						class="group hover:bg-gray-50/30 transition-all duration-100 ease-out {draggedRowId === row.id ? 'opacity-40 bg-gray-100' : ''}"
						ondragover={(e) => handleRowDragOver(e, row.id)}
						ondragleave={handleRowDragLeave}
						ondrop={(e) => handleRowDrop(e, row.id)}
					>
						<!-- Drag Handle -->
						<td class="w-8 px-1 py-3">
							<div
								draggable="true"
								ondragstart={(e) => handleDragStart(e, row.id)}
								ondragend={handleDragEnd}
								class="flex items-center justify-center w-6 h-6 rounded opacity-0 group-hover:opacity-40 hover:!opacity-70 hover:bg-gray-200 transition-all cursor-grab active:cursor-grabbing"
								role="button"
								tabindex="0"
								aria-label="Drag to reorder"
							>
								<GripVertical class="h-4 w-4 text-gray-400" />
							</div>
						</td>

						<!-- Expand button -->
						<td class="w-8 px-1 py-3">
							<button
								type="button"
								onclick={() => openRowSheet(row.id)}
								class="flex items-center justify-center w-6 h-6 rounded opacity-0 group-hover:opacity-100 hover:bg-gray-200 transition-all duration-75"
							>
								<Expand class="h-3.5 w-3.5 text-gray-500" />
							</button>
						</td>
						{#each columns as column (column.key)}
							{#if isColumnVisible(column.key)}
								<td class="px-4 py-3 {column.width}">
									<!-- Text / Email cells -->
									{#if column.type === 'text' || column.type === 'email'}
										{#if editingCell?.rowId === row.id && editingCell?.columnKey === column.key}
											<input
												type={column.type === 'email' ? 'email' : 'text'}
												bind:value={editValue}
												onkeydown={handleKeydown}
												onblur={() => stopEditing(true)}
												data-edit-input="{row.id}-{column.key}"
												class="w-full px-2 py-1.5 text-sm bg-white rounded outline-none ring-1 ring-gray-200 focus:ring-blue-300 shadow-sm transition-shadow duration-100"
											/>
										{:else}
											<button
												type="button"
												onclick={() => startEditing(row.id, column.key)}
												class="w-full text-left px-2 py-1.5 -mx-2 -my-1.5 rounded text-sm text-gray-900 hover:bg-gray-100/50 cursor-text transition-colors duration-75"
											>
												{#if row[column.key]}
													{row[column.key]}
												{:else}
													<span class="text-gray-400">Empty</span>
												{/if}
											</button>
										{/if}

									<!-- Number cells -->
									{:else if column.type === 'number'}
										{#if editingCell?.rowId === row.id && editingCell?.columnKey === column.key}
											<input
												type="number"
												bind:value={editValue}
												onkeydown={handleKeydown}
												onblur={() => stopEditing(true)}
												data-edit-input="{row.id}-{column.key}"
												class="w-full px-2 py-1.5 text-sm bg-white rounded outline-none ring-1 ring-gray-200 focus:ring-blue-300 shadow-sm transition-shadow duration-100"
											/>
										{:else}
											<button
												type="button"
												onclick={() => startEditing(row.id, column.key)}
												class="w-full text-left px-2 py-1.5 -mx-2 -my-1.5 rounded text-sm text-gray-900 hover:bg-gray-100/50 cursor-text transition-colors duration-75"
											>
												{formatCurrency(row[column.key])}
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
												class="w-full px-2 py-1.5 text-sm bg-white rounded outline-none ring-1 ring-gray-200 focus:ring-blue-300 shadow-sm transition-shadow duration-100"
											/>
										{:else}
											<button
												type="button"
												onclick={() => startEditing(row.id, column.key)}
												class="w-full text-left px-2 py-1.5 -mx-2 -my-1.5 rounded text-sm text-gray-900 hover:bg-gray-100/50 cursor-text transition-colors duration-75"
											>
												{formatDate(row[column.key])}
											</button>
										{/if}

									<!-- Select cells (Status, Priority) -->
									{:else if column.type === 'select'}
										<DropdownMenu.Root>
											<DropdownMenu.Trigger asChild>
												{#snippet child({ props })}
													<button
														{...props}
														type="button"
														class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium {getOptionStyle(row[column.key], column.options)} hover:opacity-80 transition-opacity"
													>
														{getOptionLabel(row[column.key], column.options)}
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
														<span class="w-2 h-2 rounded-full {option.color.split(' ')[0]}"></span>
														{option.label}
														{#if row[column.key] === option.value}
															<Check class="h-4 w-4 ml-auto" />
														{/if}
													</DropdownMenu.Item>
												{/each}
											</DropdownMenu.Content>
										</DropdownMenu.Root>

									<!-- Checkbox cells -->
									{:else if column.type === 'checkbox'}
										<button
											type="button"
											onclick={() => toggleCheckbox(row.id)}
											class="flex items-center justify-center w-5 h-5 rounded border {row[column.key] ? 'bg-blue-500 border-blue-500' : 'border-gray-300 hover:border-gray-400'} transition-colors"
										>
											{#if row[column.key]}
												<Check class="h-3.5 w-3.5 text-white" />
											{/if}
										</button>
									{/if}
								</td>
							{/if}
						{/each}
					</tr>

					<!-- Drop indicator line (after row) -->
					{#if dragOverRowId === row.id && dropPosition === 'after'}
						<tr class="h-0">
							<td colspan={visibleColumns.length + 2} class="p-0">
								<div class="h-0.5 bg-blue-400 rounded-full mx-4"></div>
							</td>
						</tr>
					{/if}
				{/each}
			</tbody>
		</table>
	</div>

	<!-- Add row button at bottom -->
	<div class="border-t border-gray-100 px-4 py-2">
		<button
			type="button"
			onclick={addNewRow}
			class="flex items-center gap-2 px-2 py-1.5 text-sm text-gray-500 hover:text-gray-700 hover:bg-gray-50 rounded transition-colors"
		>
			<Plus class="h-4 w-4" />
			New row
		</button>
	</div>
</div>

<!-- Row Detail Sheet (Notion-style) -->
<Sheet.Root bind:open={sheetOpen} onOpenChange={(open) => !open && closeRowSheet()}>
	<Sheet.Content side="right" class="w-[440px] sm:max-w-[440px] p-0 overflow-hidden">
		{#if selectedRow}
			<div class="h-full flex flex-col">
				<!-- Header with close button -->
				<div class="flex items-center justify-between px-4 py-3 border-b border-gray-100">
					<span class="text-sm text-gray-500">Contact</span>
					<button onclick={closeRowSheet} class="p-1 rounded hover:bg-gray-100 transition-colors duration-75">
						<X class="h-4 w-4 text-gray-400" />
					</button>
				</div>

				<!-- Scrollable content -->
				<div class="flex-1 overflow-y-auto">
					<!-- Title section -->
					<div class="px-6 pt-6 pb-4">
						<input
							type="text"
							value={selectedRow.name}
							oninput={(e) => updateSelectedRowField('name', /** @type {HTMLInputElement} */ (e.target).value)}
							placeholder="Untitled"
							class="w-full text-2xl font-semibold bg-transparent border-0 outline-none focus:ring-0 placeholder:text-gray-300"
						/>
					</div>

					<!-- Properties section -->
					<div class="px-4 pb-6">
						<!-- Email property -->
						<div class="flex items-center min-h-[36px] px-2 -mx-2 rounded hover:bg-gray-50/60 transition-colors duration-75 group">
							<div class="w-28 shrink-0 flex items-center gap-2 text-[13px] text-gray-500">
								<Mail class="h-4 w-4 text-gray-400" />
								Email
							</div>
							<div class="flex-1 min-w-0">
								<input
									type="email"
									value={selectedRow.email}
									oninput={(e) => updateSelectedRowField('email', /** @type {HTMLInputElement} */ (e.target).value)}
									placeholder="Add email"
									class="w-full px-2 py-1 text-sm bg-transparent border-0 outline-none focus:bg-gray-50 rounded transition-colors placeholder:text-gray-400"
								/>
							</div>
						</div>

						<!-- Company property -->
						<div class="flex items-center min-h-[36px] px-2 -mx-2 rounded hover:bg-gray-50/60 transition-colors duration-75 group">
							<div class="w-28 shrink-0 flex items-center gap-2 text-[13px] text-gray-500">
								<Building2 class="h-4 w-4 text-gray-400" />
								Company
							</div>
							<div class="flex-1 min-w-0">
								<input
									type="text"
									value={selectedRow.company}
									oninput={(e) => updateSelectedRowField('company', /** @type {HTMLInputElement} */ (e.target).value)}
									placeholder="Add company"
									class="w-full px-2 py-1 text-sm bg-transparent border-0 outline-none focus:bg-gray-50 rounded transition-colors placeholder:text-gray-400"
								/>
							</div>
						</div>

						<!-- Status property (select) -->
						<div class="flex items-center min-h-[36px] px-2 -mx-2 rounded hover:bg-gray-50/60 transition-colors duration-75 group">
							<div class="w-28 shrink-0 flex items-center gap-2 text-[13px] text-gray-500">
								<Circle class="h-4 w-4 text-gray-400" />
								Status
							</div>
							<div class="flex-1">
								<DropdownMenu.Root>
									<DropdownMenu.Trigger asChild>
										{#snippet child({ props })}
											<button
												{...props}
												type="button"
												class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-sm {getOptionStyle(selectedRow.status, statusOptions)} hover:opacity-90 transition-opacity"
											>
												<span class="w-2 h-2 rounded-full {getOptionStyle(selectedRow.status, statusOptions).split(' ')[0]}"></span>
												{getOptionLabel(selectedRow.status, statusOptions)}
											</button>
										{/snippet}
									</DropdownMenu.Trigger>
									<DropdownMenu.Content align="start" class="w-36">
										{#each statusOptions as option (option.value)}
											<DropdownMenu.Item
												onclick={() => updateSelectedRowField('status', option.value)}
												class="flex items-center gap-2"
											>
												<span class="w-2 h-2 rounded-full {option.color.split(' ')[0]}"></span>
												{option.label}
												{#if selectedRow.status === option.value}
													<Check class="h-4 w-4 ml-auto" />
												{/if}
											</DropdownMenu.Item>
										{/each}
									</DropdownMenu.Content>
								</DropdownMenu.Root>
							</div>
						</div>

						<!-- Priority property (select) -->
						<div class="flex items-center min-h-[36px] px-2 -mx-2 rounded hover:bg-gray-50/60 transition-colors duration-75 group">
							<div class="w-28 shrink-0 flex items-center gap-2 text-[13px] text-gray-500">
								<Zap class="h-4 w-4 text-gray-400" />
								Priority
							</div>
							<div class="flex-1">
								<DropdownMenu.Root>
									<DropdownMenu.Trigger asChild>
										{#snippet child({ props })}
											<button
												{...props}
												type="button"
												class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-sm {getOptionStyle(selectedRow.priority, priorityOptions)} hover:opacity-90 transition-opacity"
											>
												<span class="w-2 h-2 rounded-full {getOptionStyle(selectedRow.priority, priorityOptions).split(' ')[0]}"></span>
												{getOptionLabel(selectedRow.priority, priorityOptions)}
											</button>
										{/snippet}
									</DropdownMenu.Trigger>
									<DropdownMenu.Content align="start" class="w-36">
										{#each priorityOptions as option (option.value)}
											<DropdownMenu.Item
												onclick={() => updateSelectedRowField('priority', option.value)}
												class="flex items-center gap-2"
											>
												<span class="w-2 h-2 rounded-full {option.color.split(' ')[0]}"></span>
												{option.label}
												{#if selectedRow.priority === option.value}
													<Check class="h-4 w-4 ml-auto" />
												{/if}
											</DropdownMenu.Item>
										{/each}
									</DropdownMenu.Content>
								</DropdownMenu.Root>
							</div>
						</div>

						<!-- Deal Value property -->
						<div class="flex items-center min-h-[36px] px-2 -mx-2 rounded hover:bg-gray-50/60 transition-colors duration-75 group">
							<div class="w-28 shrink-0 flex items-center gap-2 text-[13px] text-gray-500">
								<DollarSign class="h-4 w-4 text-gray-400" />
								Deal Value
							</div>
							<div class="flex-1 min-w-0">
								<div class="flex items-center">
									<span class="text-sm text-gray-500 mr-1">$</span>
									<input
										type="number"
										value={selectedRow.dealValue}
										oninput={(e) => updateSelectedRowField('dealValue', parseFloat(/** @type {HTMLInputElement} */ (e.target).value) || 0)}
										placeholder="0"
										class="w-full px-1 py-1 text-sm bg-transparent border-0 outline-none focus:bg-gray-50 rounded transition-colors placeholder:text-gray-400"
									/>
								</div>
							</div>
						</div>

						<!-- Last Contact property -->
						<div class="flex items-center min-h-[36px] px-2 -mx-2 rounded hover:bg-gray-50/60 transition-colors duration-75 group">
							<div class="w-28 shrink-0 flex items-center gap-2 text-[13px] text-gray-500">
								<Calendar class="h-4 w-4 text-gray-400" />
								Last Contact
							</div>
							<div class="flex-1 min-w-0">
								<input
									type="date"
									value={selectedRow.lastContact}
									oninput={(e) => updateSelectedRowField('lastContact', /** @type {HTMLInputElement} */ (e.target).value)}
									class="w-full px-2 py-1 text-sm bg-transparent border-0 outline-none focus:bg-gray-50 rounded transition-colors"
								/>
							</div>
						</div>

						<!-- VIP property -->
						<div class="flex items-center min-h-[36px] px-2 -mx-2 rounded hover:bg-gray-50/60 transition-colors duration-75 group">
							<div class="w-28 shrink-0 flex items-center gap-2 text-[13px] text-gray-500">
								<Star class="h-4 w-4 text-gray-400" />
								VIP
							</div>
							<div class="flex-1">
								<button
									type="button"
									onclick={() => updateSelectedRowField('isVIP', !selectedRow.isVIP)}
									class="flex items-center justify-center w-5 h-5 rounded border {selectedRow.isVIP ? 'bg-blue-500 border-blue-500' : 'border-gray-300 hover:border-gray-400'} transition-colors duration-75"
								>
									{#if selectedRow.isVIP}
										<Check class="h-3.5 w-3.5 text-white" />
									{/if}
								</button>
							</div>
						</div>
					</div>
				</div>

				<!-- Footer with delete -->
				<div class="px-4 py-3 border-t border-gray-100 mt-auto">
					<button
						onclick={deleteSelectedRow}
						class="flex items-center gap-2 px-3 py-1.5 text-sm text-red-600 hover:bg-red-50 rounded transition-colors duration-75"
					>
						<Trash2 class="h-4 w-4" />
						Delete
					</button>
				</div>
			</div>
		{/if}
	</Sheet.Content>
</Sheet.Root>
