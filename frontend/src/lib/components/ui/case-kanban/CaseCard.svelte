<script>
	import { Building2, AlertTriangle } from '@lucide/svelte';

	/**
	 * @typedef {Object} Case
	 * @property {string} id
	 * @property {string} name
	 * @property {string} status
	 * @property {string} priority
	 * @property {string} [case_type]
	 * @property {string} [account_name]
	 * @property {boolean} [is_sla_breached]
	 * @property {boolean} [is_sla_first_response_breached]
	 * @property {boolean} [is_sla_resolution_breached]
	 * @property {Array<{id: string, user_details?: {email?: string}, email?: string}>} [assigned_to]
	 */

	/** @type {{ item: Case, onclick?: () => void, ondragstart?: (e: DragEvent) => void, ondragend?: () => void }} */
	let { item, onclick, ondragstart, ondragend } = $props();

	// Priority color mapping
	const priorityColors = {
		Urgent: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
		High: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
		Normal: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
		Low: 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400'
	};

	// Case type labels
	const caseTypeLabels = {
		Question: 'Q',
		Incident: 'I',
		Problem: 'P'
	};

	// Computed values
	const name = $derived(item.name || 'Untitled Case');
	const priority = $derived(item.priority);
	const caseType = $derived(item.case_type);
	const accountName = $derived(item.account_name);
	const isSlaBreached = $derived(
		item.is_sla_breached || item.is_sla_first_response_breached || item.is_sla_resolution_breached
	);
	const assignees = $derived(item.assigned_to || []);

	/**
	 * Get initials from assignee
	 * @param {any} assignee
	 */
	function getAssigneeInitials(assignee) {
		const email = assignee?.user_details?.email || assignee?.email || '';
		if (!email) return '?';
		return email.charAt(0).toUpperCase();
	}

	/**
	 * Get assignee display name
	 * @param {any} assignee
	 */
	function getAssigneeName(assignee) {
		return assignee?.user_details?.email || assignee?.email || 'Unknown';
	}

	/**
	 * Handle keyboard events
	 * @param {KeyboardEvent} e
	 */
	function handleKeydown(e) {
		if (e.key === 'Enter' || e.key === ' ') {
			e.preventDefault();
			onclick?.();
		}
	}
</script>

<div
	class="case-card group cursor-pointer rounded-lg border border-gray-200 bg-white p-3 shadow-sm transition-all hover:shadow-md dark:border-gray-700 dark:bg-gray-900"
	class:border-l-red-500={isSlaBreached}
	class:border-l-[3px]={isSlaBreached}
	draggable="true"
	onclick={onclick}
	onkeydown={handleKeydown}
	ondragstart={ondragstart}
	ondragend={ondragend}
	role="button"
	tabindex="0"
>
	<!-- Title + SLA Warning -->
	<div class="flex items-start gap-2">
		<div class="min-w-0 flex-1 truncate font-medium text-gray-900 dark:text-gray-100">
			{name}
		</div>
		{#if isSlaBreached}
			<span title="SLA Breached">
				<AlertTriangle class="h-4 w-4 shrink-0 text-red-500" />
			</span>
		{/if}
	</div>

	<!-- Account -->
	{#if accountName}
		<div class="mt-1 flex items-center gap-1.5 text-sm text-gray-500 dark:text-gray-400">
			<Building2 class="h-3.5 w-3.5 shrink-0" />
			<span class="truncate">{accountName}</span>
		</div>
	{/if}

	<!-- Meta row: Case Type + Priority -->
	<div class="mt-2 flex items-center justify-between gap-2">
		<div class="flex items-center gap-2">
			{#if caseType}
				<span
					class="rounded bg-gray-100 px-1.5 py-0.5 text-xs font-medium text-gray-600 dark:bg-gray-800 dark:text-gray-400"
				>
					{caseTypeLabels[caseType] || caseType}
				</span>
			{/if}
			{#if priority}
				<span
					class="rounded-full px-2 py-0.5 text-xs font-medium {priorityColors[priority] ||
						'bg-gray-100 text-gray-600'}"
				>
					{priority}
				</span>
			{/if}
		</div>
	</div>

	<!-- Assignees -->
	{#if assignees.length > 0}
		<div class="mt-2 flex items-center -space-x-1">
			{#each assignees.slice(0, 3) as assignee (assignee.id)}
				<div
					class="flex h-6 w-6 items-center justify-center rounded-full border-2 border-white bg-gray-200 text-xs font-medium text-gray-600 dark:border-gray-900 dark:bg-gray-700 dark:text-gray-300"
					title={getAssigneeName(assignee)}
				>
					{getAssigneeInitials(assignee)}
				</div>
			{/each}
			{#if assignees.length > 3}
				<div
					class="flex h-6 w-6 items-center justify-center rounded-full border-2 border-white bg-gray-300 text-xs font-medium text-gray-600 dark:border-gray-900 dark:bg-gray-600 dark:text-gray-300"
				>
					+{assignees.length - 3}
				</div>
			{/if}
		</div>
	{/if}
</div>

<style>
	.case-card:active {
		cursor: grabbing;
		transform: rotate(1deg) scale(1.02);
	}

	.case-card:focus-visible {
		outline: 2px solid rgb(59 130 246);
		outline-offset: 2px;
	}
</style>
