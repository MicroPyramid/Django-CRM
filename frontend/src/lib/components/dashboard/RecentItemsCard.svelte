<script>
	import * as Card from '$lib/components/ui/card/index.js';

	/**
	 * @typedef {Object} Props
	 * @property {string} title - Card title
	 * @property {boolean} [isEmpty=false] - Whether the card has no items
	 * @property {import('svelte').Snippet} [icon] - Header icon snippet
	 * @property {import('svelte').Snippet} [headerAction] - Header action button snippet
	 * @property {import('svelte').Snippet} [empty] - Empty state content snippet
	 * @property {import('svelte').Snippet} [children] - Card content
	 */

	/** @type {Props} */
	let { title, isEmpty = false, icon, headerAction, empty, children } = $props();
</script>

<Card.Root>
	<Card.Header class="flex flex-row items-center justify-between space-y-0 pb-2">
		<div class="flex items-center gap-2">
			{#if icon}
				<div
					class="bg-muted text-muted-foreground flex h-8 w-8 items-center justify-center rounded-lg"
				>
					{@render icon()}
				</div>
			{/if}
			<Card.Title class="text-base font-semibold">{title}</Card.Title>
		</div>
		{#if headerAction}
			{@render headerAction()}
		{/if}
	</Card.Header>
	<Card.Content>
		{#if isEmpty && empty}
			<div class="flex flex-col items-center justify-center py-8 text-center">
				{@render empty()}
			</div>
		{:else if children}
			{@render children()}
		{/if}
	</Card.Content>
</Card.Root>
