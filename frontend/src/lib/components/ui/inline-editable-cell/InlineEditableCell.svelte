<script>
	import { tick } from 'svelte';
	import { cn } from '$lib/utils.js';

	/**
	 * @typedef {Object} SelectOption
	 * @property {string} value
	 * @property {string} label
	 */

	/**
	 * @type {{
	 *   value?: string,
	 *   type?: 'text' | 'email' | 'phone' | 'url' | 'number' | 'select',
	 *   placeholder?: string,
	 *   options?: SelectOption[],
	 *   onchange?: (value: string) => void,
	 *   onnext?: () => void,
	 *   onprev?: () => void,
	 *   ondown?: () => void,
	 *   disabled?: boolean,
	 *   class?: string,
	 *   children?: import('svelte').Snippet
	 * }}
	 */
	let {
		value = '',
		type = 'text',
		placeholder = '',
		options = [],
		onchange,
		onnext,
		onprev,
		ondown,
		disabled = false,
		class: className,
		children
	} = $props();

	let editing = $state(false);
	let localValue = $state(value);
	/** @type {HTMLInputElement | HTMLSelectElement | null} */
	let inputRef = $state(null);

	// Sync local value when prop changes (and not editing)
	$effect(() => {
		if (!editing) {
			localValue = value;
		}
	});

	/**
	 * Start editing - exposed for external focus management
	 */
	export async function startEditing() {
		if (disabled) return;
		localValue = value;
		editing = true;
		await tick();
		inputRef?.focus();
		if (inputRef && 'select' in inputRef && type !== 'select') {
			inputRef.select();
		}
	}

	/**
	 * Stop editing and optionally save
	 * @param {boolean} save
	 */
	function stopEditing(save = true) {
		if (save && localValue !== value) {
			onchange?.(localValue);
		} else if (!save) {
			localValue = value;
		}
		editing = false;
	}

	/**
	 * Handle keydown for inputs
	 * @param {KeyboardEvent} e
	 */
	function handleKeydown(e) {
		if (e.key === 'Enter') {
			e.preventDefault();
			stopEditing(true);
			ondown?.();
		} else if (e.key === 'Tab') {
			e.preventDefault();
			stopEditing(true);
			if (e.shiftKey) {
				onprev?.();
			} else {
				onnext?.();
			}
		} else if (e.key === 'Escape') {
			e.preventDefault();
			stopEditing(false);
		}
	}

	/**
	 * Handle blur - save on click outside
	 * @param {FocusEvent} e
	 */
	function handleBlur(e) {
		// Small delay to allow click handlers to fire first
		setTimeout(() => {
			if (editing) {
				stopEditing(true);
			}
		}, 100);
	}

	/**
	 * Handle select change - immediate commit for select fields
	 * @param {Event} e
	 */
	function handleSelectChange(e) {
		const target = /** @type {HTMLSelectElement} */ (e.target);
		localValue = target.value;
		onchange?.(localValue);
		editing = false;
	}

	/**
	 * Handle click on cell - start editing
	 * @param {MouseEvent} e
	 */
	function handleCellClick(e) {
		e.stopPropagation();
		if (!disabled && !editing) {
			startEditing();
		}
	}
</script>

<div
	class={cn('inline-editable-cell relative', editing && 'is-editing', className)}
	role="gridcell"
>
	{#if editing}
		{#if type === 'select'}
			<select
				bind:this={inputRef}
				bind:value={localValue}
				onchange={handleSelectChange}
				onkeydown={handleKeydown}
				onblur={handleBlur}
				class="w-full rounded-md border-0 bg-muted/30 px-2 py-1.5 text-sm outline-none ring-2 ring-ring/50 transition-all duration-100 focus:ring-ring"
			>
				{#if placeholder && !localValue}
					<option value="" disabled>{placeholder}</option>
				{/if}
				{#each options as option}
					<option value={option.value}>{option.label}</option>
				{/each}
			</select>
		{:else}
			<input
				bind:this={inputRef}
				bind:value={localValue}
				type={type === 'phone' ? 'tel' : type === 'number' ? 'number' : type}
				{placeholder}
				onkeydown={handleKeydown}
				onblur={handleBlur}
				class="w-full rounded-md border-0 bg-muted/30 px-2 py-1.5 text-sm outline-none ring-2 ring-ring/50 transition-all duration-100 focus:ring-ring placeholder:text-muted-foreground"
			/>
		{/if}
	{:else}
		<button
			type="button"
			onclick={handleCellClick}
			class={cn(
				'w-full text-left rounded-md px-2 py-1.5 -mx-2 -my-1.5 transition-all duration-100',
				!disabled && 'hover:bg-muted/50 cursor-text',
				!disabled && 'focus:outline-none focus:ring-2 focus:ring-ring/30 focus:bg-muted/30',
				disabled && 'cursor-default'
			)}
		>
			{@render children?.()}
		</button>
	{/if}
</div>
