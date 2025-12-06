<script>
	import { Search, X } from '@lucide/svelte';
	import { cn } from '$lib/utils.js';

	/**
	 * @type {{
	 *   value?: string,
	 *   placeholder?: string,
	 *   debounceMs?: number,
	 *   class?: string,
	 *   onchange?: (value: string) => void,
	 *   [key: string]: any
	 * }}
	 */
	let {
		value = $bindable(''),
		placeholder = 'Search...',
		debounceMs = 300,
		class: className,
		onchange,
		...restProps
	} = $props();

	let inputValue = $state(value);
	let timeoutId = $state(/** @type {ReturnType<typeof setTimeout> | null} */ (null));

	// Sync external value changes to internal state
	$effect(() => {
		if (value !== inputValue) {
			inputValue = value;
		}
	});

	/**
	 * @param {Event} e
	 */
	function handleInput(e) {
		const target = /** @type {HTMLInputElement} */ (e.target);
		inputValue = target.value;

		if (timeoutId) {
			clearTimeout(timeoutId);
		}

		timeoutId = setTimeout(() => {
			value = inputValue;
			onchange?.(inputValue);
		}, debounceMs);
	}

	function handleClear() {
		inputValue = '';
		value = '';
		onchange?.('');
	}
</script>

<div class={cn('relative', className)} {...restProps}>
	<Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
	<input
		type="text"
		value={inputValue}
		oninput={handleInput}
		{placeholder}
		class="border-input bg-background placeholder:text-muted-foreground flex h-9 w-full rounded-md border pl-9 pr-9 text-sm shadow-xs transition-colors outline-none focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px] disabled:cursor-not-allowed disabled:opacity-50"
	/>
	{#if inputValue}
		<button
			type="button"
			onclick={handleClear}
			class="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
		>
			<X class="h-4 w-4" />
		</button>
	{/if}
</div>
