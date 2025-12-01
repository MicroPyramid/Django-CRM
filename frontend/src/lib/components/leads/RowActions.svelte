<script>
	import { Pencil, Trash2, Copy } from '@lucide/svelte';
	import { Button } from '$lib/components/ui/button/index.js';
	import * as Tooltip from '$lib/components/ui/tooltip/index.js';
	import { cn } from '$lib/utils.js';

	/**
	 * @type {{
	 *   onEdit?: () => void,
	 *   onDelete?: () => void,
	 *   onDuplicate?: () => void,
	 *   class?: string
	 * }}
	 */
	let {
		onEdit,
		onDelete,
		onDuplicate,
		class: className
	} = $props();

	/**
	 * Handle click with propagation stop
	 * @param {MouseEvent} e
	 * @param {() => void} [handler]
	 */
	function handleClick(e, handler) {
		e.stopPropagation();
		handler?.();
	}
</script>

<div
	class={cn(
		'absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-0.5',
		'bg-background/98 backdrop-blur-sm rounded-lg border border-border/50 shadow-md px-1.5 py-1',
		'opacity-0 scale-95 group-hover:opacity-100 group-hover:scale-100',
		'transition-all duration-200 ease-out',
		'pointer-events-none group-hover:pointer-events-auto',
		className
	)}
>
	<Tooltip.Provider>
		<Tooltip.Root delayDuration={300}>
			<Tooltip.Trigger asChild>
				{#snippet child({ props })}
					<Button
						{...props}
						variant="ghost"
						size="icon"
						class="h-7 w-7 hover:bg-muted/80 transition-colors duration-100"
						onclick={(e) => handleClick(e, onEdit)}
					>
						<Pencil class="h-3.5 w-3.5" />
						<span class="sr-only">Edit</span>
					</Button>
				{/snippet}
			</Tooltip.Trigger>
			<Tooltip.Content>
				<p>Edit</p>
			</Tooltip.Content>
		</Tooltip.Root>

		<Tooltip.Root delayDuration={300}>
			<Tooltip.Trigger asChild>
				{#snippet child({ props })}
					<Button
						{...props}
						variant="ghost"
						size="icon"
						class="h-7 w-7 hover:bg-muted/80 transition-colors duration-100"
						onclick={(e) => handleClick(e, onDuplicate)}
					>
						<Copy class="h-3.5 w-3.5" />
						<span class="sr-only">Duplicate</span>
					</Button>
				{/snippet}
			</Tooltip.Trigger>
			<Tooltip.Content>
				<p>Duplicate</p>
			</Tooltip.Content>
		</Tooltip.Root>

		<Tooltip.Root delayDuration={300}>
			<Tooltip.Trigger asChild>
				{#snippet child({ props })}
					<Button
						{...props}
						variant="ghost"
						size="icon"
						class="h-7 w-7 text-destructive hover:text-destructive hover:bg-destructive/10"
						onclick={(e) => handleClick(e, onDelete)}
					>
						<Trash2 class="h-3.5 w-3.5" />
						<span class="sr-only">Delete</span>
					</Button>
				{/snippet}
			</Tooltip.Trigger>
			<Tooltip.Content>
				<p>Delete</p>
			</Tooltip.Content>
		</Tooltip.Root>
	</Tooltip.Provider>
</div>
