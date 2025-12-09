<script>
	import LeadCard from './LeadCard.svelte';

	/**
	 * @typedef {Object} Column
	 * @property {string} id
	 * @property {string} name
	 * @property {string} color
	 * @property {number} lead_count
	 * @property {number|null} [wip_limit]
	 * @property {Array<any>} leads
	 */

	/**
	 * @type {{
	 *   column: Column,
	 *   isDragOver: boolean,
	 *   onDragOver: (e: DragEvent) => void,
	 *   onDragLeave: () => void,
	 *   onDrop: (e: DragEvent) => void,
	 *   onCardClick: (lead: any) => void,
	 *   onCardDragStart: (e: DragEvent, lead: any) => void,
	 *   onCardDragEnd: () => void
	 * }}
	 */
	let {
		column,
		isDragOver,
		onDragOver,
		onDragLeave,
		onDrop,
		onCardClick,
		onCardDragStart,
		onCardDragEnd
	} = $props();

	// Check if column is at WIP limit
	const isAtWipLimit = $derived(
		column.wip_limit !== null && column.wip_limit !== undefined && column.lead_count >= column.wip_limit
	);

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
	class="kanban-column flex w-72 shrink-0 flex-col rounded-lg bg-gray-100 dark:bg-gray-800/50"
	class:drag-over={isDragOver}
	class:wip-exceeded={isAtWipLimit}
	ondragover={handleDragOver}
	ondragleave={onDragLeave}
	ondrop={onDrop}
	role="region"
	aria-label="{column.name} column with {column.lead_count} leads"
>
	<!-- Column Header -->
	<div
		class="flex items-center justify-between rounded-t-lg border-t-[3px] px-3 py-2"
		style="border-top-color: {column.color}"
	>
		<h3 class="text-sm font-semibold text-gray-900 dark:text-gray-100">
			{column.name}
		</h3>
		<div class="flex items-center gap-2">
			<span
				class="rounded-full bg-gray-200 px-2 py-0.5 text-xs font-medium text-gray-600 dark:bg-gray-700 dark:text-gray-300"
			>
				{column.lead_count}
			</span>
			{#if column.wip_limit}
				<span
					class="rounded-full px-2 py-0.5 text-xs font-medium {isAtWipLimit
						? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
						: 'bg-gray-200 text-gray-500 dark:bg-gray-700 dark:text-gray-400'}"
				>
					/{column.wip_limit}
				</span>
			{/if}
		</div>
	</div>

	<!-- Column Content -->
	<div class="flex-1 space-y-2 overflow-y-auto p-2" style="max-height: calc(100vh - 280px)">
		{#each column.leads as lead (lead.id)}
			<LeadCard
				{lead}
				onclick={() => onCardClick(lead)}
				ondragstart={(e) => onCardDragStart(e, lead)}
				ondragend={onCardDragEnd}
			/>
		{/each}

		{#if column.leads.length === 0}
			<div
				class="flex h-24 items-center justify-center rounded-lg border-2 border-dashed border-gray-300 text-sm text-gray-400 dark:border-gray-600 dark:text-gray-500"
			>
				No leads
			</div>
		{/if}
	</div>
</div>

<style>
	.kanban-column {
		transition:
			background-color 150ms ease,
			box-shadow 150ms ease;
	}

	.kanban-column.drag-over {
		background-color: rgb(239 246 255); /* blue-50 */
		box-shadow:
			inset 0 0 0 2px rgb(59 130 246),
			0 0 12px rgba(59, 130, 246, 0.2);
	}

	:global(.dark) .kanban-column.drag-over {
		background-color: rgba(59, 130, 246, 0.1);
	}

	.kanban-column.wip-exceeded {
		background-color: rgb(254 242 242); /* red-50 */
	}

	:global(.dark) .kanban-column.wip-exceeded {
		background-color: rgba(239, 68, 68, 0.1);
	}
</style>
