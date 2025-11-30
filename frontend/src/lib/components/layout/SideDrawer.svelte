<script>
	import { X, ChevronLeft } from '@lucide/svelte/icons';
	import * as Sheet from '$lib/components/ui/sheet/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { cn } from '$lib/utils.js';

	/**
	 * @type {{
	 *   open?: boolean,
	 *   onOpenChange?: (open: boolean) => void,
	 *   title?: string,
	 *   showBackButton?: boolean,
	 *   onBack?: () => void,
	 *   class?: string,
	 *   headerClass?: string,
	 *   contentClass?: string,
	 *   footerClass?: string,
	 *   header?: import('svelte').Snippet,
	 *   children?: import('svelte').Snippet,
	 *   footer?: import('svelte').Snippet,
	 * }}
	 */
	let {
		open = $bindable(false),
		onOpenChange,
		title = '',
		showBackButton = false,
		onBack,
		class: className,
		headerClass,
		contentClass,
		footerClass,
		header,
		children,
		footer
	} = $props();

	function handleOpenChange(value) {
		open = value;
		onOpenChange?.(value);
	}

	function handleBack() {
		if (onBack) {
			onBack();
		} else {
			handleOpenChange(false);
		}
	}

	function handleKeydown(event) {
		if (event.key === 'Escape') {
			handleOpenChange(false);
		}
	}
</script>

<svelte:window onkeydown={handleKeydown} />

<Sheet.Root bind:open onOpenChange={handleOpenChange}>
	<Sheet.Content
		side="right"
		class={cn(
			'flex h-full w-[420px] flex-col gap-0 p-0 sm:w-[420px] sm:max-w-[480px] lg:w-[480px]',
			'data-[state=closed]:duration-200 data-[state=open]:duration-300',
			'data-[state=open]:animate-in data-[state=closed]:animate-out',
			'data-[state=open]:slide-in-from-right data-[state=closed]:slide-out-to-right',
			className
		)}
	>
		<!-- Header -->
		<header
			class={cn(
				'border-border flex h-14 shrink-0 items-center justify-between border-b px-4',
				headerClass
			)}
		>
			<div class="flex items-center gap-2">
				{#if showBackButton}
					<Button variant="ghost" size="icon" class="h-8 w-8" onclick={handleBack}>
						<ChevronLeft class="h-4 w-4" />
						<span class="sr-only">Back</span>
					</Button>
				{/if}
				{#if header}
					{@render header()}
				{:else if title}
					<h2 class="text-foreground text-base font-semibold">{title}</h2>
				{/if}
			</div>
			<Sheet.Close
				class="ring-offset-background focus-visible:ring-ring rounded-md p-1.5 opacity-70 transition-opacity hover:opacity-100 focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:outline-none"
			>
				<X class="h-4 w-4" />
				<span class="sr-only">Close</span>
			</Sheet.Close>
		</header>

		<!-- Scrollable Content -->
		<div class={cn('flex-1 overflow-y-auto', contentClass)}>
			{#if children}
				{@render children()}
			{/if}
		</div>

		<!-- Footer -->
		{#if footer}
			<footer
				class={cn(
					'border-border bg-muted/50 flex h-16 shrink-0 items-center justify-end gap-2 border-t px-4',
					footerClass
				)}
			>
				{@render footer()}
			</footer>
		{/if}
	</Sheet.Content>
</Sheet.Root>
