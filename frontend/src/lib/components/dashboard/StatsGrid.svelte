<script>
	import { cn } from '$lib/utils.js';

	/**
	 * @typedef {Object} Props
	 * @property {import('svelte').Snippet} [children] - Child content (KPICards)
	 * @property {string} [class] - Additional classes
	 */

	/** @type {Props & Record<string, any>} */
	let { children, class: className, ...restProps } = $props();
</script>

<!--
	Responsive grid:
	- 1 column on mobile (<640px)
	- 2 columns on sm (640-768px)
	- 3 columns on md (768-1024px)
	- 4 columns on lg (1024-1280px)
	- 6 columns on xl (>1280px) - to fit all 6 metrics
-->
<div
	class={cn(
		'grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6',
		className
	)}
	{...restProps}
>
	{@render children?.()}
</div>
