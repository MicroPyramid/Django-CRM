<script>
	import { Calendar, Link, AlertCircle } from '@lucide/svelte';
	import { formatDate } from '$lib/utils/formatting.js';

	/**
	 * @typedef {Object} Task
	 * @property {string} id
	 * @property {string} title
	 * @property {string} status
	 * @property {string} priority
	 * @property {string|null} [due_date]
	 * @property {boolean} [is_overdue]
	 * @property {Array<{id: string, user_details?: {email?: string}, email?: string}>} [assigned_to]
	 * @property {{id: string, name: string, type: string}|null} [related_entity]
	 */

	/** @type {{ item: Task, onclick?: () => void, ondragstart?: (e: DragEvent) => void, ondragend?: () => void }} */
	let { item, onclick, ondragstart, ondragend } = $props();

	// Priority color mapping
	const priorityColors = {
		High: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
		Medium: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
		Low: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
	};

	// Entity type labels
	const entityLabels = {
		account: 'Account',
		lead: 'Lead',
		opportunity: 'Opportunity',
		case: 'Case'
	};

	// Computed values
	const title = $derived(item.title || 'Untitled Task');
	const priority = $derived(item.priority);
	const dueDate = $derived(item.due_date);
	const isOverdue = $derived(item.is_overdue || false);
	const assignees = $derived(item.assigned_to || []);
	const relatedEntity = $derived(item.related_entity);

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
	class="task-card group cursor-pointer rounded-lg border border-gray-200 bg-white p-3 shadow-sm transition-all hover:shadow-md dark:border-gray-700 dark:bg-gray-900"
	class:border-l-red-500={isOverdue}
	class:border-l-[3px]={isOverdue}
	draggable="true"
	onclick={onclick}
	onkeydown={handleKeydown}
	ondragstart={ondragstart}
	ondragend={ondragend}
	role="button"
	tabindex="0"
>
	<!-- Title -->
	<div class="truncate font-medium text-gray-900 dark:text-gray-100">
		{title}
	</div>

	<!-- Related Entity -->
	{#if relatedEntity}
		<div class="mt-1 flex items-center gap-1.5 text-sm text-gray-500 dark:text-gray-400">
			<Link class="h-3.5 w-3.5 shrink-0" />
			<span class="truncate">
				{entityLabels[relatedEntity.type] || relatedEntity.type}: {relatedEntity.name}
			</span>
		</div>
	{/if}

	<!-- Meta row: Priority + Due date -->
	<div class="mt-2 flex items-center justify-between gap-2">
		{#if priority}
			<span
				class="rounded-full px-2 py-0.5 text-xs font-medium {priorityColors[priority] ||
					'bg-gray-100 text-gray-600'}"
			>
				{priority}
			</span>
		{:else}
			<span></span>
		{/if}

		{#if dueDate}
			<span
				class="flex items-center gap-1 text-xs {isOverdue
					? 'font-medium text-red-600 dark:text-red-400'
					: 'text-gray-500 dark:text-gray-400'}"
			>
				{#if isOverdue}
					<AlertCircle class="h-3 w-3" />
				{:else}
					<Calendar class="h-3 w-3" />
				{/if}
				{formatDate(dueDate)}
			</span>
		{/if}
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
	.task-card:active {
		cursor: grabbing;
		transform: rotate(1deg) scale(1.02);
	}

	.task-card:focus-visible {
		outline: 2px solid rgb(59 130 246);
		outline-offset: 2px;
	}
</style>
