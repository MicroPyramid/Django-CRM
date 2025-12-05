<script>
	import { Check } from '@lucide/svelte';
	import * as DropdownMenu from '$lib/components/ui/dropdown-menu/index.js';
	import { EditableMultiSelect } from '$lib/components/ui/editable-field/index.js';
	import { cn } from '$lib/utils.js';
	import { formatCurrency } from '$lib/utils/formatting.js';

	/**
	 * @type {{
	 *   label: string,
	 *   value?: any,
	 *   type?: 'text' | 'email' | 'number' | 'date' | 'select' | 'checkbox' | 'multiselect' | 'textarea',
	 *   icon?: import('svelte').Component,
	 *   options?: any[],
	 *   placeholder?: string,
	 *   emptyText?: string,
	 *   editable?: boolean,
	 *   prefix?: string,
	 *   onchange?: (value: any) => void,
	 *   class?: string,
	 * }}
	 */
	let {
		label,
		value = '',
		type = 'text',
		icon: Icon,
		options = [],
		placeholder = '',
		emptyText = '',
		editable = true,
		prefix = '',
		onchange,
		class: className
	} = $props();

	/**
	 * Get option style for select
	 * @param {string} val
	 */
	function getOptionStyle(val) {
		if (type !== 'select') return '';
		const opt = options.find((/** @type {any} */ o) => o.value === val);
		return opt?.color || 'bg-gray-100 text-gray-700';
	}

	/**
	 * Get option label for select
	 * @param {string} val
	 */
	function getOptionLabel(val) {
		if (type !== 'select') return val;
		const opt = options.find((/** @type {any} */ o) => o.value === val);
		return opt?.label || val || emptyText || 'Select...';
	}

	/**
	 * Get option background color class (for the dot)
	 * @param {string} val
	 */
	function getOptionBgColor(val) {
		if (type !== 'select') return '';
		const opt = options.find((/** @type {any} */ o) => o.value === val);
		if (!opt?.color) return 'bg-gray-400';
		// Extract bg class from color string (e.g., "bg-emerald-100 text-emerald-700" -> "bg-emerald-500")
		const match = opt.color.match(/bg-(\w+)-\d+/);
		if (match) {
			return `bg-${match[1]}-500`;
		}
		return 'bg-gray-400';
	}

	/**
	 * Format date for display
	 * @param {string} dateStr
	 */
	function formatDate(dateStr) {
		if (!dateStr) return emptyText || 'No date';
		try {
			const date = new Date(dateStr + 'T00:00:00');
			return date.toLocaleDateString('en-US', {
				month: 'short',
				day: 'numeric',
				year: 'numeric'
			});
		} catch {
			return dateStr;
		}
	}

	/**
	 * Format number with optional currency
	 * @param {number | string} val
	 */
	function formatNumber(val) {
		const num = typeof val === 'string' ? parseFloat(val) : val;
		if (isNaN(num)) return emptyText || '0';
		if (prefix === '$') {
			return formatCurrency(num);
		}
		return prefix + num.toLocaleString();
	}

	/**
	 * Handle text input
	 * @param {Event} e
	 */
	function handleInput(e) {
		const target = /** @type {HTMLInputElement} */ (e.target);
		onchange?.(target.value);
	}

	/**
	 * Handle number input
	 * @param {Event} e
	 */
	function handleNumberInput(e) {
		const target = /** @type {HTMLInputElement} */ (e.target);
		onchange?.(parseFloat(target.value) || 0);
	}

	/**
	 * Handle checkbox toggle
	 */
	function handleCheckboxToggle() {
		onchange?.(!value);
	}

	/**
	 * Handle select change
	 * @param {string} newValue
	 */
	function handleSelectChange(newValue) {
		onchange?.(newValue);
	}

	/**
	 * Handle multiselect change
	 * @param {string[]} newValue
	 */
	function handleMultiSelectChange(newValue) {
		onchange?.(newValue);
	}
</script>

<div
	class={cn(
		'group -mx-2 flex min-h-[36px] items-center rounded px-2 transition-colors duration-75 hover:bg-gray-50/60 dark:hover:bg-gray-800/40',
		className
	)}
>
	<!-- Label with icon -->
	<div class="flex w-28 shrink-0 items-center gap-2 text-[13px] text-gray-500 dark:text-gray-400">
		{#if Icon}
			<Icon class="h-4 w-4 text-gray-400 dark:text-gray-500" />
		{/if}
		{label}
	</div>

	<!-- Value -->
	<div class="min-w-0 flex-1">
		{#if type === 'text' || type === 'email'}
			<input
				type={type}
				{value}
				oninput={handleInput}
				{placeholder}
				disabled={!editable}
				class="w-full rounded border-0 bg-transparent px-2 py-1 text-sm outline-none transition-colors focus:bg-gray-50 dark:focus:bg-gray-800 placeholder:text-gray-400"
			/>
		{:else if type === 'number'}
			<div class="flex items-center">
				{#if prefix}
					<span class="mr-1 text-sm text-gray-500">{prefix}</span>
				{/if}
				<input
					type="number"
					value={value || 0}
					oninput={handleNumberInput}
					{placeholder}
					disabled={!editable}
					class="w-full rounded border-0 bg-transparent px-1 py-1 text-sm outline-none transition-colors focus:bg-gray-50 dark:focus:bg-gray-800 placeholder:text-gray-400"
				/>
			</div>
		{:else if type === 'date'}
			<input
				type="date"
				{value}
				oninput={handleInput}
				disabled={!editable}
				class="w-full rounded border-0 bg-transparent px-2 py-1 text-sm outline-none transition-colors focus:bg-gray-50 dark:focus:bg-gray-800"
			/>
		{:else if type === 'textarea'}
			<textarea
				{value}
				oninput={handleInput}
				{placeholder}
				disabled={!editable}
				rows={2}
				class="w-full rounded border-0 bg-transparent px-2 py-1 text-sm outline-none transition-colors focus:bg-gray-50 dark:focus:bg-gray-800 placeholder:text-gray-400 resize-none"
			></textarea>
		{:else if type === 'select'}
			<DropdownMenu.Root>
				<DropdownMenu.Trigger disabled={!editable}>
					{#snippet child({ props })}
						<button
							{...props}
							type="button"
							class="inline-flex items-center gap-1.5 rounded px-2 py-0.5 text-sm transition-opacity hover:opacity-90 {getOptionStyle(
								value
							)}"
						>
							<span class="h-2 w-2 rounded-full {getOptionBgColor(value)}"></span>
							{getOptionLabel(value)}
						</button>
					{/snippet}
				</DropdownMenu.Trigger>
				<DropdownMenu.Content align="start" class="w-36">
					{#each options as option (option.value)}
						<DropdownMenu.Item
							onclick={() => handleSelectChange(option.value)}
							class="flex items-center gap-2"
						>
							<span class="h-2 w-2 rounded-full {option.color?.split(' ')[0] || 'bg-gray-400'}"></span>
							{option.label}
							{#if value === option.value}
								<Check class="ml-auto h-4 w-4" />
							{/if}
						</DropdownMenu.Item>
					{/each}
				</DropdownMenu.Content>
			</DropdownMenu.Root>
		{:else if type === 'checkbox'}
			<button
				type="button"
				onclick={handleCheckboxToggle}
				disabled={!editable}
				class="flex h-5 w-5 items-center justify-center rounded border transition-colors duration-75 {value
					? 'border-blue-500 bg-blue-500'
					: 'border-gray-300 hover:border-gray-400 dark:border-gray-600'}"
			>
				{#if value}
					<Check class="h-3.5 w-3.5 text-white" />
				{/if}
			</button>
		{:else if type === 'multiselect'}
			<EditableMultiSelect
				value={Array.isArray(value) ? value : []}
				{options}
				{placeholder}
				emptyText={emptyText || 'None selected'}
				disabled={!editable}
				onchange={handleMultiSelectChange}
			/>
		{:else if type === 'readonly'}
			<span class="px-2 py-1 text-sm text-gray-700 dark:text-gray-300">
				{#if value}
					{value}
				{:else}
					<span class="text-gray-400">{emptyText || 'Empty'}</span>
				{/if}
			</span>
		{/if}
	</div>
</div>
