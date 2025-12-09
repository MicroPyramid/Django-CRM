<script>
	import { ChevronDown, Check, X } from '@lucide/svelte';
	import { cn } from '$lib/utils.js';
	import * as Popover from '$lib/components/ui/popover/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { getTagColorClass } from '$lib/constants/colors.js';

	/**
	 * @typedef {{
	 *   id: string,
	 *   name: string,
	 *   color?: string,
	 * }} TagOption
	 */

	/**
	 * @type {{
	 *   tags: TagOption[],
	 *   value?: string[],
	 *   placeholder?: string,
	 *   label?: string,
	 *   class?: string,
	 *   onchange?: (ids: string[]) => void,
	 * }}
	 */
	let {
		tags = [],
		value = $bindable([]),
		placeholder = 'Filter by tags...',
		label = 'Tags',
		class: className,
		onchange
	} = $props();

	let open = $state(false);

	const selectedIds = $derived(Array.isArray(value) ? value : []);

	const displayText = $derived.by(() => {
		if (selectedIds.length === 0) return placeholder;
		if (selectedIds.length === 1) {
			const tag = tags.find((t) => t.id === selectedIds[0]);
			return tag?.name || selectedIds[0];
		}
		return `${selectedIds.length} tags selected`;
	});

	/**
	 * @param {string} tagId
	 */
	function toggleTag(tagId) {
		const newIds = selectedIds.includes(tagId)
			? selectedIds.filter((id) => id !== tagId)
			: [...selectedIds, tagId];
		value = newIds;
		onchange?.(newIds);
	}

	function clearAll() {
		value = [];
		onchange?.([]);
	}

	const selectedTags = $derived(tags.filter((t) => selectedIds.includes(t.id)));
	const hasSelection = $derived(selectedIds.length > 0);
</script>

<div class={cn('flex flex-col gap-1', className)}>
	{#if label}
		<span class="text-muted-foreground text-xs font-medium">{label}</span>
	{/if}
	<Popover.Root bind:open>
		<Popover.Trigger asChild class="">
			{#snippet child({ props })}
				<button
					type="button"
					class={cn(
						'border-input bg-background hover:bg-accent/50 focus-visible:ring-ring flex h-9 w-full items-center justify-between gap-2 rounded-md border px-3 py-2 text-sm shadow-xs transition-colors focus-visible:ring-2 focus-visible:outline-none',
						hasSelection && 'border-primary/50'
					)}
					{...props}
				>
					<span class={cn('truncate', !hasSelection && 'text-muted-foreground')}>
						{displayText}
					</span>
					<div class="flex items-center gap-1">
						{#if hasSelection}
							<!-- svelte-ignore node_invalid_placement_ssr -->
							<span
								role="button"
								tabindex="0"
								onclick={(e) => {
									e.stopPropagation();
									e.preventDefault();
									clearAll();
								}}
								onkeydown={(e) => {
									if (e.key === 'Enter' || e.key === ' ') {
										e.stopPropagation();
										e.preventDefault();
										clearAll();
									}
								}}
								class="hover:bg-muted cursor-pointer rounded p-0.5"
							>
								<X class="h-3 w-3" />
							</span>
						{/if}
						<ChevronDown class="h-4 w-4 opacity-50" />
					</div>
				</button>
			{/snippet}
		</Popover.Trigger>
		<Popover.Content align="start" class="max-h-[300px] w-[250px] overflow-y-auto p-1">
			{#if tags.length === 0}
				<p class="text-muted-foreground px-2 py-1.5 text-sm">No tags available</p>
			{:else}
				{#each tags as tag (tag.id)}
					{@const isSelected = selectedIds.includes(tag.id)}
					<button
						type="button"
						class={cn(
							'hover:bg-accent relative flex w-full cursor-pointer items-center gap-2 rounded-sm px-2 py-1.5 text-sm outline-none',
							isSelected && 'bg-accent'
						)}
						onclick={() => toggleTag(tag.id)}
					>
						{#if isSelected}
							<Check class="h-4 w-4 shrink-0" />
						{:else}
							<span class="w-4 shrink-0"></span>
						{/if}
						<Badge class={cn('text-xs', getTagColorClass(tag.color || 'blue'))}>{tag.name}</Badge>
					</button>
				{/each}
			{/if}
		</Popover.Content>
	</Popover.Root>
</div>

{#if selectedTags.length > 0}
	<div class="mt-1 flex flex-wrap gap-1">
		{#each selectedTags as tag (tag.id)}
			<Badge class={cn('gap-1 text-xs', getTagColorClass(tag.color || 'blue'))}>
				{tag.name}
				<button type="button" onclick={() => toggleTag(tag.id)} class="ml-1 rounded-full hover:bg-black/10">
					<X class="h-3 w-3" />
				</button>
			</Badge>
		{/each}
	</div>
{/if}
