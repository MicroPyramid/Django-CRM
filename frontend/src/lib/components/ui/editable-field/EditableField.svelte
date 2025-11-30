<script>
	import { tick } from 'svelte';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Textarea } from '$lib/components/ui/textarea/index.js';
	import * as Select from '$lib/components/ui/select/index.js';
	import { cn } from '$lib/utils.js';

	/**
	 * @typedef {Object} SelectOption
	 * @property {string} value
	 * @property {string} label
	 */

	/**
	 * @type {{
	 *   label?: string,
	 *   value?: string | boolean,
	 *   type?: 'text' | 'email' | 'phone' | 'url' | 'textarea' | 'select' | 'checkbox' | 'date' | 'number',
	 *   placeholder?: string,
	 *   options?: SelectOption[],
	 *   disabled?: boolean,
	 *   required?: boolean,
	 *   validate?: (value: string) => string | null,
	 *   onchange?: (value: string | boolean) => void,
	 *   icon?: import('svelte').Snippet,
	 *   displayValue?: string,
	 *   emptyText?: string,
	 *   class?: string,
	 *   min?: string | number,
	 *   max?: string | number,
	 *   step?: string | number,
	 * }}
	 */
	let {
		label,
		value = '',
		type = 'text',
		placeholder = '',
		options = [],
		disabled = false,
		required = false,
		validate,
		onchange,
		icon,
		displayValue,
		emptyText = 'Add...',
		class: className,
		min,
		max,
		step
	} = $props();

	let editing = $state(false);
	let localValue = $state(String(value ?? ''));
	let error = $state('');
	/** @type {HTMLInputElement | HTMLTextAreaElement | null} */
	let inputRef = $state(null);

	// Track previous value to detect external changes
	let prevValue = $state(String(value ?? ''));

	// Flag to prevent $effect from resetting localValue right after committing
	let justCommitted = $state(false);

	// Sync local value only when the value prop changes externally (not when editing changes)
	$effect(() => {
		const currentValue = String(value ?? '');
		if (currentValue !== prevValue) {
			prevValue = currentValue;
			// Only sync if not currently editing AND not just committed
			// (justCommitted prevents race condition when clicking between fields)
			if (!editing && !justCommitted && type !== 'checkbox') {
				localValue = currentValue;
			}
		}
	});

	/**
	 * Start editing
	 */
	async function startEdit() {
		if (disabled || type === 'checkbox') return;
		editing = true;
		await tick();
		inputRef?.focus();
		if (inputRef && 'select' in inputRef) {
			inputRef.select();
		}
	}

	/**
	 * Commit the edit
	 */
	function commitEdit() {
		if (validate) {
			const validationError = validate(localValue);
			if (validationError) {
				error = validationError;
				return;
			}
		}
		error = '';
		const hasChanged = localValue !== String(value ?? '');
		if (hasChanged) {
			// Block $effect from resetting localValue during the transition
			justCommitted = true;
			onchange?.(localValue);
			// Reset after microtask to allow parent update to propagate
			queueMicrotask(() => {
				justCommitted = false;
			});
		}
		editing = false;
	}

	/**
	 * Cancel the edit
	 */
	function cancelEdit() {
		localValue = String(value ?? '');
		error = '';
		editing = false;
	}

	/**
	 * Handle keydown
	 * @param {KeyboardEvent} e
	 */
	function handleKeydown(e) {
		if (e.key === 'Enter' && type !== 'textarea') {
			e.preventDefault();
			commitEdit();
		} else if (e.key === 'Escape') {
			cancelEdit();
		}
	}

	/**
	 * Handle checkbox change
	 * @param {Event} e
	 */
	function handleCheckboxChange(e) {
		const target = /** @type {HTMLInputElement} */ (e.target);
		onchange?.(target.checked);
	}

	/**
	 * Handle select change
	 * @param {string} newValue
	 */
	function handleSelectChange(newValue) {
		localValue = newValue;
		onchange?.(newValue);
		editing = false;
	}

	/**
	 * Handle input blur for textarea
	 */
	function handleTextareaBlur() {
		commitEdit();
	}

	/**
	 * Format date for display
	 * @param {string} dateStr
	 */
	function formatDateDisplay(dateStr) {
		if (!dateStr) return '';
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
	 * Get display text
	 */
	function getDisplayText() {
		if (displayValue) return displayValue;
		const strValue = String(value ?? '');
		if (type === 'select' && options.length > 0) {
			const option = options.find((o) => o.value === strValue);
			return option?.label || strValue || emptyText;
		}
		if (type === 'date' && strValue) {
			return formatDateDisplay(strValue);
		}
		return strValue || emptyText;
	}

	// Check if value is empty (works for both string and boolean)
	const isEmpty = $derived(() => {
		if (type === 'checkbox') return false;
		const strValue = String(value ?? '');
		return !strValue;
	});

	// Convert boolean value for checkbox
	const isChecked = $derived(Boolean(value));
</script>

<div class={cn('group', className)}>
	{#if type === 'checkbox'}
		<!-- Checkbox type - always shows checkbox -->
		<label class="flex cursor-pointer items-center gap-2">
			<input
				type="checkbox"
				checked={isChecked}
				onchange={handleCheckboxChange}
				{disabled}
				class="border-input h-4 w-4 rounded text-primary focus:ring-primary"
			/>
			{#if label}
				<span class="text-sm">{label}</span>
			{/if}
		</label>
	{:else if editing}
		<!-- Edit mode -->
		<div class="space-y-1">
			{#if type === 'textarea'}
				<textarea
					bind:this={inputRef}
					bind:value={localValue}
					{placeholder}
					{disabled}
					rows={3}
					onblur={handleTextareaBlur}
					onkeydown={handleKeydown}
					class={cn(
						'border-input bg-background placeholder:text-muted-foreground focus-visible:ring-ring flex min-h-[60px] w-full rounded-md border px-3 py-2 text-sm shadow-xs focus-visible:ring-1 focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-50',
						error && 'border-destructive'
					)}
				></textarea>
			{:else if type === 'select'}
				<Select.Root
					type="single"
					value={localValue}
					onValueChange={handleSelectChange}
					onOpenChange={(open) => {
						if (!open) editing = false;
					}}
				>
					<Select.Trigger class="w-full">
						<span class={cn(!localValue && 'text-muted-foreground')}>
							{options.find((o) => o.value === localValue)?.label || placeholder || 'Select...'}
						</span>
					</Select.Trigger>
					<Select.Content class="max-h-60">
						{#each options as option}
							<Select.Item value={option.value}>{option.label}</Select.Item>
						{/each}
					</Select.Content>
				</Select.Root>
			{:else}
				<input
					bind:this={inputRef}
					bind:value={localValue}
					type={type === 'phone' ? 'tel' : type === 'number' ? 'number' : type}
					{placeholder}
					{disabled}
					min={min}
					max={max}
					step={step}
					onblur={commitEdit}
					onkeydown={handleKeydown}
					class={cn(
						'border-input bg-background file:text-foreground placeholder:text-muted-foreground focus-visible:ring-ring flex h-9 w-full rounded-md border px-3 py-1 text-sm shadow-xs transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium focus-visible:ring-1 focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-50',
						error && 'border-destructive'
					)}
				/>
			{/if}
			{#if error}
				<p class="text-destructive text-xs">{error}</p>
			{/if}
		</div>
	{:else}
		<!-- View mode - clickable to edit -->
		<button
			type="button"
			onclick={startEdit}
			{disabled}
			class={cn(
				'w-full text-left transition-colors',
				'rounded-md px-2 py-1 -mx-2 -my-1',
				!disabled && 'hover:bg-muted/50 cursor-pointer',
				disabled && 'cursor-default',
				isEmpty() && 'text-muted-foreground',
				required && isEmpty() && 'text-destructive'
			)}
		>
			<span class="flex items-center gap-2">
				{#if icon}
					<span class="text-muted-foreground shrink-0">
						{@render icon()}
					</span>
				{/if}
				<span class={cn('truncate', isEmpty() && 'italic')}>
					{getDisplayText()}
				</span>
			</span>
		</button>
	{/if}
</div>
