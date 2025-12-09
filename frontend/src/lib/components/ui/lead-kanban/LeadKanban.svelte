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
	 * @property {number} lead_count
	 * @property {Array<any>} leads
	 */

	/**
	 * @typedef {Object} KanbanData
	 * @property {string} mode
	 * @property {Object|null} pipeline
	 * @property {Column[]} columns
	 * @property {number} total_leads
	 */

	/**
	 * @type {{
	 *   data: KanbanData | null,
	 *   loading?: boolean,
	 *   onStatusChange: (leadId: string, newStatus: string, columnId: string) => Promise<void>,
	 *   onCardClick: (lead: any) => void
	 * }}
	 */
	let { data = null, loading = false, onStatusChange, onCardClick } = $props();

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
	let draggedLead = $state(null);
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
	 * @param {any} lead
	 * @param {string} columnId
	 */
	function handleDragStart(e, lead, columnId) {
		draggedLead = lead;
		dragSourceColumn = columnId;
		e.dataTransfer.effectAllowed = 'move';
		e.dataTransfer.setData('text/plain', lead.id);

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

		if (!draggedLead || dragSourceColumn === targetColumnId) {
			draggedLead = null;
			dragSourceColumn = null;
			return;
		}

		const lead = draggedLead;
		const sourceColumnId = dragSourceColumn;

		// Reset drag state
		draggedLead = null;
		dragSourceColumn = null;

		// Optimistic update: move lead in local state immediately
		const sourceCol = localColumns.find((c) => c.id === sourceColumnId);
		const targetCol = localColumns.find((c) => c.id === targetColumnId);

		if (sourceCol && targetCol) {
			// Remove from source column
			const leadIndex = sourceCol.leads.findIndex((l) => l.id === lead.id);
			if (leadIndex !== -1) {
				sourceCol.leads.splice(leadIndex, 1);
				sourceCol.lead_count--;
			}

			// Add to target column (at the top)
			targetCol.leads.unshift({ ...lead, status: targetColumnId });
			targetCol.lead_count++;

			// Trigger reactivity by reassigning
			localColumns = [...localColumns];
		}

		try {
			// Call the status change handler
			await onStatusChange(lead.id, targetColumnId, targetColumnId);
		} catch (error) {
			console.error('Failed to move lead:', error);
			toast.error('Failed to move lead');

			// Revert optimistic update on error
			if (sourceCol && targetCol) {
				// Remove from target column
				const leadIndex = targetCol.leads.findIndex((l) => l.id === lead.id);
				if (leadIndex !== -1) {
					targetCol.leads.splice(leadIndex, 1);
					targetCol.lead_count--;
				}

				// Add back to source column
				sourceCol.leads.unshift(lead);
				sourceCol.lead_count++;

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
		draggedLead = null;
		dragSourceColumn = null;
		dragOverColumn = null;
	}

	// Get columns sorted by order (use localColumns for optimistic updates)
	const sortedColumns = $derived(
		localColumns.length > 0 ? [...localColumns].sort((a, b) => a.order - b.order) : []
	);

	// Get active column for mobile view
	const activeMobileColumn = $derived(sortedColumns.find((c) => c.id === mobileActiveColumn));
</script>

{#if loading}
	<div class="flex h-64 items-center justify-center">
		<Loader2 class="h-8 w-8 animate-spin text-gray-400" />
	</div>
{:else if !data || sortedColumns.length === 0}
	<div class="flex h-64 flex-col items-center justify-center text-center text-gray-500">
		<p>No kanban data available</p>
	</div>
{:else}
	<!-- Desktop: Horizontal scroll container with all columns -->
	<div class="hidden gap-4 overflow-x-auto pb-4 md:flex" style="min-height: 400px">
		{#each sortedColumns as column (column.id)}
			<KanbanColumn
				{column}
				isDragOver={dragOverColumn === column.id}
				onDragOver={(e) => handleDragOver(e, column.id)}
				onDragLeave={handleDragLeave}
				onDrop={(e) => handleDrop(e, column.id)}
				onCardClick={onCardClick}
				onCardDragStart={(e, lead) => handleDragStart(e, lead, column.id)}
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
					<option value={col.id}>{col.name} ({col.lead_count})</option>
				{/each}
			</select>
		</div>

		<!-- Active column cards -->
		{#if activeMobileColumn}
			<div class="space-y-3">
				{#each activeMobileColumn.leads as lead (lead.id)}
					<div
						class="rounded-lg border border-gray-200 bg-white p-3 dark:border-gray-700 dark:bg-gray-900"
						onclick={() => onCardClick(lead)}
						onkeydown={(e) => (e.key === 'Enter' || e.key === ' ') && onCardClick(lead)}
						role="button"
						tabindex="0"
					>
						<!-- Lead title -->
						<div class="font-medium text-gray-900 dark:text-gray-100">
							{lead.title || lead.full_name || lead.fullName || 'Untitled Lead'}
						</div>

						<!-- Company -->
						{#if lead.company_name || lead.company}
							<div class="mt-1 text-sm text-gray-500 dark:text-gray-400">
								{lead.company_name || lead.company}
							</div>
						{/if}

						<!-- Amount and rating -->
						<div class="mt-2 flex items-center justify-between">
							{#if lead.opportunity_amount || lead.opportunityAmount}
								<span class="text-sm font-medium text-gray-700 dark:text-gray-300">
									{new Intl.NumberFormat('en-US', {
										style: 'currency',
										currency: lead.currency || 'USD',
										minimumFractionDigits: 0
									}).format(parseFloat(lead.opportunity_amount || lead.opportunityAmount))}
								</span>
							{:else}
								<span></span>
							{/if}

							{#if lead.rating}
								<span
									class="rounded-full px-2 py-0.5 text-xs font-medium {lead.rating === 'HOT'
										? 'bg-red-100 text-red-700'
										: lead.rating === 'WARM'
											? 'bg-orange-100 text-orange-700'
											: 'bg-blue-100 text-blue-700'}"
								>
									{lead.rating}
								</span>
							{/if}
						</div>
					</div>
				{/each}

				{#if activeMobileColumn.leads.length === 0}
					<div
						class="flex h-24 items-center justify-center rounded-lg border-2 border-dashed border-gray-300 text-sm text-gray-400"
					>
						No leads in this column
					</div>
				{/if}
			</div>
		{/if}
	</div>

	<!-- Total count footer -->
	<div class="mt-4 text-sm text-gray-500 dark:text-gray-400">
		{data.total_leads} lead{data.total_leads !== 1 ? 's' : ''} total
	</div>
{/if}
