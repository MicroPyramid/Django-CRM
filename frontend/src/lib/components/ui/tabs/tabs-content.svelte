<script>
	import { Tabs as TabsPrimitive } from 'bits-ui';
	import { cn } from '$lib/utils.js';

	/**
	 * @type {{
	 *   ref?: HTMLElement | null,
	 *   class?: string,
	 *   value: string,
	 *   children?: import('svelte').Snippet,
	 *   [key: string]: any
	 * }}
	 */
	let { ref = $bindable(null), class: className, ...restProps } = $props();
</script>

<TabsPrimitive.Content
	bind:ref
	data-slot="tabs-content"
	class={cn('flex-1 outline-none', className)}
	{...restProps}
/>
