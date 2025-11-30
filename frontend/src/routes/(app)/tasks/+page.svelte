<script>
	import { enhance } from '$app/forms';
	import { Plus, LayoutGrid } from '@lucide/svelte';
	import PageHeader from '$lib/components/layout/PageHeader.svelte';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import * as Card from '$lib/components/ui/card/index.js';

	/** @type {{ data: any }} */
	let { data } = $props();

	let newBoardName = $state('');
	let isCreating = $state(false);
</script>

<svelte:head>
	<title>Task Boards - BottleCRM</title>
</svelte:head>

<PageHeader title="Task Boards" subtitle="Manage your tasks with Kanban boards">
	{#snippet actions()}
		<span class="text-muted-foreground text-sm">
			{data?.boards?.length || 0} board{data?.boards?.length !== 1 ? 's' : ''}
		</span>
	{/snippet}
</PageHeader>

<div class="flex-1 p-4 md:p-6">
	<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
		<!-- Existing Boards -->
		{#if data?.boards?.length}
			{#each data.boards as board}
				<a href="/tasks/board/{board.id}" class="group block">
					<Card.Root
						class="group-hover:border-primary/50 h-full transition-all duration-200 hover:-translate-y-1 hover:shadow-lg"
					>
						<Card.Content class="p-6">
							<div class="flex items-start gap-3">
								<div
									class="bg-primary/10 flex h-10 w-10 shrink-0 items-center justify-center rounded-lg"
								>
									<LayoutGrid class="text-primary h-5 w-5" />
								</div>
								<div class="min-w-0 flex-1">
									<h3 class="text-foreground truncate font-semibold">
										{board.name}
									</h3>
									{#if board.description}
										<p class="text-muted-foreground mt-1 line-clamp-2 text-sm">
											{board.description}
										</p>
									{/if}
								</div>
							</div>
						</Card.Content>
					</Card.Root>
				</a>
			{/each}
		{/if}

		<!-- Create New Board Card -->
		<Card.Root class="hover:border-primary/50 border-2 border-dashed transition-colors">
			<Card.Content class="p-6">
				<form
					method="POST"
					action="?/create"
					use:enhance={() => {
						isCreating = true;
						return async ({ update }) => {
							await update();
							isCreating = false;
							newBoardName = '';
						};
					}}
					class="flex h-full min-h-[100px] flex-col items-center justify-center gap-3"
				>
					<div class="bg-muted flex h-10 w-10 items-center justify-center rounded-lg">
						<Plus class="text-muted-foreground h-5 w-5" />
					</div>
					<div class="w-full space-y-3">
						<Input
							name="name"
							placeholder="New board name"
							bind:value={newBoardName}
							required
							class="text-center"
						/>
						<Button type="submit" class="w-full" disabled={isCreating || !newBoardName.trim()}>
							{#if isCreating}
								<svg class="mr-2 h-4 w-4 animate-spin" viewBox="0 0 24 24">
									<circle
										class="opacity-25"
										cx="12"
										cy="12"
										r="10"
										stroke="currentColor"
										stroke-width="4"
										fill="none"
									/>
									<path
										class="opacity-75"
										fill="currentColor"
										d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
									/>
								</svg>
								Creating...
							{:else}
								<Plus class="mr-2 h-4 w-4" />
								Create Board
							{/if}
						</Button>
					</div>
				</form>
			</Card.Content>
		</Card.Root>
	</div>

	<!-- Empty State -->
	{#if !data?.boards?.length}
		<div class="mt-8 text-center">
			<LayoutGrid class="text-muted-foreground/50 mx-auto h-12 w-12" />
			<h3 class="text-foreground mt-4 text-lg font-medium">No boards yet</h3>
			<p class="text-muted-foreground mt-2 text-sm">
				Create your first board to start organizing tasks with Kanban.
			</p>
		</div>
	{/if}
</div>
