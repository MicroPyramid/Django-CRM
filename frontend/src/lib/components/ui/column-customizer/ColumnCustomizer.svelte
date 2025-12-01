<script>
	import { Settings2 } from '@lucide/svelte';
	import { Button } from '$lib/components/ui/button/index.js';
	import * as DropdownMenu from '$lib/components/ui/dropdown-menu/index.js';

	/**
	 * @typedef {Object} ColumnConfig
	 * @property {string} key
	 * @property {string} label
	 * @property {boolean} visible
	 * @property {boolean} [canHide]
	 */

	/**
	 * @type {{
	 *   columns: ColumnConfig[],
	 *   onchange?: (columns: ColumnConfig[]) => void,
	 *   class?: string
	 * }}
	 */
	let {
		columns = [],
		onchange,
		class: className
	} = $props();

	/**
	 * Toggle column visibility
	 * @param {string} key
	 */
	function toggleColumn(key) {
		const updated = columns.map((col) =>
			col.key === key ? { ...col, visible: !col.visible } : col
		);
		onchange?.(updated);
	}

	// Count visible columns
	const visibleCount = $derived(columns.filter((c) => c.visible).length);
	const totalHideable = $derived(columns.filter((c) => c.canHide !== false).length);
</script>

<DropdownMenu.Root>
	<DropdownMenu.Trigger asChild>
		{#snippet child({ props })}
			<Button {...props} variant="outline" size="sm" class={className}>
				<Settings2 class="mr-2 h-4 w-4" />
				Columns
				{#if visibleCount < columns.length}
					<span class="ml-1.5 rounded-full bg-primary/10 px-1.5 py-0.5 text-xs font-medium text-primary">
						{visibleCount}/{columns.length}
					</span>
				{/if}
			</Button>
		{/snippet}
	</DropdownMenu.Trigger>
	<DropdownMenu.Content align="end" class="w-48">
		<DropdownMenu.Label>Toggle columns</DropdownMenu.Label>
		<DropdownMenu.Separator />
		{#each columns as column (column.key)}
			{#if column.canHide !== false}
				<DropdownMenu.CheckboxItem
					class=""
					checked={column.visible}
					onCheckedChange={() => toggleColumn(column.key)}
				>
					{column.label}
				</DropdownMenu.CheckboxItem>
			{/if}
		{/each}
	</DropdownMenu.Content>
</DropdownMenu.Root>
