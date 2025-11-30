<script>
	import { cn } from '$lib/utils.js';
	let { ref = $bindable(null), class: className, children, ...restProps } = $props();
</script>

<div
	bind:this={ref}
	data-slot="card-footer"
	class={cn('flex items-center px-6 [.border-t]:pt-6', className)}
	{...restProps}
>
	{@render children?.()}
</div>
