<script>
	import { Building2, Calendar, DollarSign } from '@lucide/svelte';
	import { formatDate, getNameInitials } from '$lib/utils/formatting.js';

	/**
	 * @typedef {Object} Lead
	 * @property {string} id
	 * @property {string} [title]
	 * @property {string} [full_name]
	 * @property {string} [fullName]
	 * @property {string} [company_name]
	 * @property {string} [company]
	 * @property {string} [email]
	 * @property {string} [rating]
	 * @property {number|string} [opportunity_amount]
	 * @property {number|string} [opportunityAmount]
	 * @property {string} [currency]
	 * @property {string} [next_follow_up]
	 * @property {string} [nextFollowUp]
	 * @property {boolean} [is_follow_up_overdue]
	 * @property {boolean} [isFollowUpOverdue]
	 * @property {Array<{id: string, user_details?: {email?: string}, email?: string}>} [assigned_to]
	 * @property {Array<{id: string, user_details?: {email?: string}, email?: string}>} [assignedTo]
	 */

	/** @type {{ item: Lead, onclick?: () => void, ondragstart?: (e: DragEvent) => void, ondragend?: () => void }} */
	let { item, onclick, ondragstart, ondragend } = $props();

	// Rating color mapping
	const ratingColors = {
		HOT: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
		WARM: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
		COLD: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
	};

	// Computed values
	const title = $derived(item.title || item.full_name || item.fullName || 'Untitled Lead');
	const company = $derived(item.company_name || item.company || '');
	const amount = $derived(item.opportunity_amount || item.opportunityAmount);
	const currency = $derived(item.currency || 'USD');
	const followUp = $derived(item.next_follow_up || item.nextFollowUp);
	const isOverdue = $derived(item.is_follow_up_overdue || item.isFollowUpOverdue);
	const rating = $derived(item.rating);
	const assignees = $derived(item.assigned_to || item.assignedTo || []);

	/**
	 * Format currency amount
	 * @param {number|string} value
	 * @param {string} curr
	 */
	function formatAmount(value, curr) {
		const num = typeof value === 'string' ? parseFloat(value) : value;
		if (isNaN(num)) return '';
		return new Intl.NumberFormat('en-US', {
			style: 'currency',
			currency: curr,
			minimumFractionDigits: 0,
			maximumFractionDigits: 0
		}).format(num);
	}

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
	class="lead-card group cursor-pointer rounded-lg border border-gray-200 bg-white p-3 shadow-sm transition-all hover:shadow-md dark:border-gray-700 dark:bg-gray-900"
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

	<!-- Company -->
	{#if company}
		<div class="mt-1 flex items-center gap-1.5 text-sm text-gray-500 dark:text-gray-400">
			<Building2 class="h-3.5 w-3.5 shrink-0" />
			<span class="truncate">{company}</span>
		</div>
	{/if}

	<!-- Amount -->
	{#if amount}
		<div class="mt-1.5 flex items-center gap-1.5 text-sm font-medium text-gray-700 dark:text-gray-300">
			<DollarSign class="h-3.5 w-3.5 shrink-0" />
			{formatAmount(amount, currency)}
		</div>
	{/if}

	<!-- Meta row: Rating + Follow-up -->
	<div class="mt-2 flex items-center justify-between gap-2">
		{#if rating}
			<span class="rounded-full px-2 py-0.5 text-xs font-medium {ratingColors[rating] || 'bg-gray-100 text-gray-600'}">
				{rating}
			</span>
		{:else}
			<span></span>
		{/if}

		{#if followUp}
			<span
				class="flex items-center gap-1 text-xs {isOverdue ? 'font-medium text-red-600 dark:text-red-400' : 'text-gray-500 dark:text-gray-400'}"
			>
				<Calendar class="h-3 w-3" />
				{formatDate(followUp)}
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
	.lead-card:active {
		cursor: grabbing;
		transform: rotate(1deg) scale(1.02);
	}

	.lead-card:focus-visible {
		outline: 2px solid rgb(59 130 246);
		outline-offset: 2px;
	}
</style>
