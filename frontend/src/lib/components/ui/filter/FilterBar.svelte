<script>
	import { Filter, X, ChevronDown, ChevronUp } from '@lucide/svelte';
	import { cn } from '$lib/utils.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';

	/**
	 * @type {{
	 *   activeCount?: number,
	 *   collapsible?: boolean,
	 *   defaultExpanded?: boolean,
	 *   expanded?: boolean,
	 *   minimal?: boolean,
	 *   class?: string,
	 *   onClear?: () => void,
	 *   children?: import('svelte').Snippet,
	 * }}
	 */
	let {
		activeCount = 0,
		collapsible = false,
		defaultExpanded = true,
		expanded: externalExpanded,
		minimal = false,
		class: className,
		onClear,
		children
	} = $props();

	let internalExpanded = $state(defaultExpanded);

	// Use external expanded if provided, otherwise use internal state
	const isExpanded = $derived(externalExpanded !== undefined ? externalExpanded : internalExpanded);
</script>

{#if minimal}
	<!-- Minimal mode: just filter content without header/border -->
	{#if isExpanded}
		<div class={cn('flex flex-wrap items-end gap-3', className)}>
			{@render children?.()}
			{#if activeCount > 0 && onClear}
				<Button variant="ghost" size="sm" onclick={onClear} class="h-8 gap-1 px-2 text-xs">
					<X class="h-3 w-3" />
					Clear
				</Button>
			{/if}
		</div>
	{/if}
{:else}
	<div class={cn('rounded-lg border bg-card', className)}>
		<!-- Header -->
		<div class="flex items-center justify-between px-4 py-2">
			<button
				type="button"
				class="flex items-center gap-2 text-sm font-medium"
				onclick={() => collapsible && (internalExpanded = !internalExpanded)}
				disabled={!collapsible}
			>
				<Filter class="h-4 w-4" />
				<span>Filters</span>
				{#if activeCount > 0}
					<Badge variant="secondary" class="h-5 px-1.5 text-xs">{activeCount}</Badge>
				{/if}
				{#if collapsible}
					{#if isExpanded}
						<ChevronUp class="h-4 w-4" />
					{:else}
						<ChevronDown class="h-4 w-4" />
					{/if}
				{/if}
			</button>
			{#if activeCount > 0 && onClear}
				<Button variant="ghost" size="sm" onclick={onClear} class="h-7 gap-1 px-2 text-xs">
					<X class="h-3 w-3" />
					Clear all
				</Button>
			{/if}
		</div>

		<!-- Filter content -->
		{#if !collapsible || isExpanded}
			<div class="border-t px-4 py-3">
				<div class="flex flex-wrap items-end gap-3">
					{@render children?.()}
				</div>
			</div>
		{/if}
	</div>
{/if}
