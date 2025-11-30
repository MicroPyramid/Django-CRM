<script>
	import { Input } from '$lib/components/ui/input/index.js';
	import { cn } from '$lib/utils.js';

	/**
	 * @type {{
	 *   ref?: HTMLInputElement | null,
	 *   value?: string,
	 *   class?: string,
	 *   type?: string,
	 *   [key: string]: any
	 * }}
	 */
	let { ref = $bindable(null), value = $bindable(''), class: className, ...restProps } = $props();
</script>

<Input
	bind:ref
	bind:value
	data-slot="sidebar-input"
	data-sidebar="input"
	class={cn('bg-background h-8 w-full shadow-none', className)}
	{...restProps}
/>
