<script>
	import { invalidateAll } from '$app/navigation';
	import { toast } from 'svelte-sonner';
	import {
		Search,
		Filter,
		Plus,
		ChevronDown,
		ChevronUp,
		Building2,
		User,
		Calendar,
		DollarSign,
		MoreHorizontal,
		Eye,
		List,
		LayoutGrid,
		Target,
		TrendingUp,
		CheckCircle,
		Percent,
		Briefcase
	} from '@lucide/svelte';
	import PageHeader from '$lib/components/layout/PageHeader.svelte';
	import { KanbanBoard, OpportunityDrawer } from '$lib/components/opportunities';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import * as Card from '$lib/components/ui/card/index.js';
	import * as Table from '$lib/components/ui/table/index.js';
	import * as DropdownMenu from '$lib/components/ui/dropdown-menu/index.js';
	import * as Tabs from '$lib/components/ui/tabs/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { cn } from '$lib/utils.js';
	import { formatRelativeDate, formatCurrency, getInitials } from '$lib/utils/formatting.js';
	import { OPPORTUNITY_STAGES as stages, OPPORTUNITY_TYPES } from '$lib/constants/filters.js';

	/** @type {{ data: any }} */
	let { data } = $props();

	// Options for form drawer
	const formOptions = $derived({
		accounts: data.options?.accounts || [],
		contacts: data.options?.contacts || [],
		tags: data.options?.tags || []
	});

	// State
	let searchQuery = $state('');
	let stageFilter = $state('ALL');
	let sortBy = $state('createdAt');
	let sortOrder = $state('desc');
	let showFilters = $state(false);
	let viewMode = $state(/** @type {'list' | 'kanban'} */ ('list'));

	// Drawer state
	let drawerOpen = $state(false);
	let drawerMode = $state(/** @type {'view' | 'create'} */ ('view'));
	/** @type {any} */
	let selectedOpportunity = $state(null);
	let initialStage = $state('PROSPECTING');
	let isLoading = $state(false);

	// Stage color configurations
	const stageConfig = /** @type {{ [key: string]: { label: string, color: string } }} */ ({
		PROSPECTING: {
			label: 'Prospecting',
			color: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300'
		},
		QUALIFICATION: {
			label: 'Qualification',
			color: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
		},
		PROPOSAL: {
			label: 'Proposal',
			color: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400'
		},
		NEGOTIATION: {
			label: 'Negotiation',
			color: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400'
		},
		CLOSED_WON: {
			label: 'Won',
			color: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
		},
		CLOSED_LOST: {
			label: 'Lost',
			color: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
		}
	});

	// Computed values
	const opportunities = $derived(data.opportunities || []);
	const stats = $derived(data.stats || { total: 0, totalValue: 0, wonValue: 0, pipeline: 0 });

	const filteredOpportunities = $derived.by(() => {
		return opportunities
			.filter((/** @type {any} */ opp) => {
				const matchesSearch =
					searchQuery === '' ||
					opp.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
					opp.account?.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
					opp.owner?.name?.toLowerCase().includes(searchQuery.toLowerCase());

				const matchesStage = stageFilter === 'ALL' || opp.stage === stageFilter;

				return matchesSearch && matchesStage;
			})
			.sort((/** @type {any} */ a, /** @type {any} */ b) => {
				const aValue = a[sortBy];
				const bValue = b[sortBy];
				if (sortOrder === 'asc') {
					return aValue > bValue ? 1 : -1;
				}
				return aValue < bValue ? 1 : -1;
			});
	});

	const activeFiltersCount = $derived(stageFilter !== 'ALL' ? 1 : 0);

	/**
	 * Get stage config
	 * @param {string} stage
	 */
	function getStageConfig(stage) {
		return stageConfig[stage] || stageConfig.PROSPECTING;
	}

	/**
	 * Get opportunity type label
	 * @param {string | null | undefined} type
	 */
	function getTypeLabel(type) {
		if (!type) return null;
		const found = OPPORTUNITY_TYPES.find((t) => t.value === type);
		return found ? found.label : type.replace(/_/g, ' ');
	}

	/**
	 * Toggle sort
	 * @param {string} field
	 */
	function toggleSort(field) {
		if (sortBy === field) {
			sortOrder = sortOrder === 'asc' ? 'desc' : 'asc';
		} else {
			sortBy = field;
			sortOrder = 'desc';
		}
	}

	/**
	 * Clear all filters
	 */
	function clearFilters() {
		searchQuery = '';
		stageFilter = 'ALL';
	}

	/**
	 * Open opportunity detail drawer
	 * @param {any} opportunity
	 */
	function openOpportunityDetail(opportunity) {
		selectedOpportunity = opportunity;
		drawerMode = 'view';
		drawerOpen = true;
	}

	/**
	 * Open create form
	 * @param {string} [stage]
	 */
	function openCreateForm(stage) {
		selectedOpportunity = null;
		drawerMode = 'create';
		initialStage = stage || 'PROSPECTING';
		drawerOpen = true;
	}

	/**
	 * Helper function to update stage via server action
	 * @param {string} opportunityId
	 * @param {string} newStage
	 */
	async function updateStage(opportunityId, newStage) {
		const form = new FormData();
		form.append('opportunityId', opportunityId);
		form.append('stage', newStage);
		const response = await fetch('?/updateStage', { method: 'POST', body: form });
		return response.json();
	}

	/**
	 * Handle save from drawer
	 * @param {any} formData
	 */
	async function handleSave(formData) {
		isLoading = true;
		try {
			const isCreate = drawerMode === 'create';
			const action = isCreate ? '?/create' : '?/update';
			const form = new FormData();

			// Map form data to FormData with all fields
			form.append('name', formData.name || '');
			form.append('amount', formData.amount?.toString() || '');
			form.append('probability', formData.probability?.toString() || '0');
			form.append('stage', formData.stage || 'PROSPECTING');
			form.append('opportunityType', formData.opportunity_type || '');
			form.append('currency', formData.currency || '');
			form.append('leadSource', formData.lead_source || '');
			form.append('closedOn', formData.closed_on || '');
			form.append('description', formData.description || '');
			form.append('accountId', formData.account_id || '');
			form.append('contacts', JSON.stringify(formData.contacts || []));
			form.append('tags', JSON.stringify(formData.tags || []));

			if (!isCreate && selectedOpportunity?.id) {
				form.append('opportunityId', selectedOpportunity.id);
			}

			const response = await fetch(action, { method: 'POST', body: form });
			const result = await response.json();

			if (result.type === 'success' || result.data?.success) {
				toast.success(isCreate ? 'Opportunity created' : 'Opportunity updated');
				drawerOpen = false;
				await invalidateAll();
			} else {
				toast.error(result.data?.message || 'Failed to save opportunity');
			}
		} catch (err) {
			console.error('Form submit error:', err);
			toast.error('An error occurred while saving');
		} finally {
			isLoading = false;
		}
	}

	/**
	 * Handle opportunity delete
	 */
	async function handleDelete() {
		if (!selectedOpportunity?.id) return;

		isLoading = true;
		try {
			const form = new FormData();
			form.append('opportunityId', selectedOpportunity.id);
			const response = await fetch('?/delete', { method: 'POST', body: form });
			const result = await response.json();

			if (result.type === 'success' || result.data?.success) {
				toast.success('Opportunity deleted');
				drawerOpen = false;
				await invalidateAll();
			} else {
				toast.error(result.data?.message || 'Failed to delete opportunity');
			}
		} catch (err) {
			console.error('Delete error:', err);
			toast.error('An error occurred while deleting');
		} finally {
			isLoading = false;
		}
	}

	/**
	 * Handle mark won
	 */
	async function handleMarkWon() {
		if (!selectedOpportunity?.id) return;

		isLoading = true;
		try {
			const result = await updateStage(selectedOpportunity.id, 'CLOSED_WON');

			if (result.type === 'success' || result.data?.success) {
				toast.success('Opportunity marked as won!');
				drawerOpen = false;
				await invalidateAll();
			} else {
				toast.error(result.data?.message || 'Failed to update status');
			}
		} catch (err) {
			console.error('Mark won error:', err);
			toast.error('An error occurred');
		} finally {
			isLoading = false;
		}
	}

	/**
	 * Handle mark lost
	 */
	async function handleMarkLost() {
		if (!selectedOpportunity?.id) return;

		isLoading = true;
		try {
			const result = await updateStage(selectedOpportunity.id, 'CLOSED_LOST');

			if (result.type === 'success' || result.data?.success) {
				toast.success('Opportunity marked as lost');
				drawerOpen = false;
				await invalidateAll();
			} else {
				toast.error(result.data?.message || 'Failed to update status');
			}
		} catch (err) {
			console.error('Mark lost error:', err);
			toast.error('An error occurred');
		} finally {
			isLoading = false;
		}
	}

	/**
	 * Handle stage change from Kanban drag-and-drop
	 * @param {string} opportunityId
	 * @param {string} newStage
	 */
	async function handleStageChange(opportunityId, newStage) {
		try {
			const result = await updateStage(opportunityId, newStage);

			if (result.type === 'success' || result.data?.success) {
				toast.success('Stage updated');
				await invalidateAll();
			} else {
				toast.error(result.data?.message || 'Failed to update stage');
				await invalidateAll(); // Refresh to restore original position
			}
		} catch (err) {
			console.error('Stage change error:', err);
			toast.error('An error occurred');
			await invalidateAll();
		}
	}
</script>

<svelte:head>
	<title>Opportunities - BottleCRM</title>
</svelte:head>

<PageHeader title="Opportunities" subtitle="Pipeline: {formatCurrency(stats.pipeline)}">
	{#snippet actions()}
		<div class="flex items-center gap-2">
			<!-- View Toggle -->
			<Tabs.Root bind:value={viewMode} class="hidden sm:block">
				<Tabs.List class="h-9">
					<Tabs.Trigger value="list" class="gap-1.5 px-3">
						<List class="h-4 w-4" />
						<span class="hidden md:inline">List</span>
					</Tabs.Trigger>
					<Tabs.Trigger value="kanban" class="gap-1.5 px-3">
						<LayoutGrid class="h-4 w-4" />
						<span class="hidden md:inline">Kanban</span>
					</Tabs.Trigger>
				</Tabs.List>
			</Tabs.Root>

			<Button onclick={() => openCreateForm()} disabled={false}>
				<Plus class="mr-2 h-4 w-4" />
				New Deal
			</Button>
		</div>
	{/snippet}
</PageHeader>

<div class="flex-1 space-y-4 p-4 md:p-6">
	<!-- Stats Cards -->
	<div class="grid grid-cols-2 gap-4 lg:grid-cols-4">
		<Card.Root>
			<Card.Content class="p-4">
				<div class="flex items-center gap-3">
					<div class="bg-muted flex h-10 w-10 items-center justify-center rounded-lg">
						<Target class="text-muted-foreground h-5 w-5" />
					</div>
					<div>
						<p class="text-muted-foreground text-xs font-medium uppercase">Total Deals</p>
						<p class="text-foreground text-xl font-bold">{stats.total}</p>
					</div>
				</div>
			</Card.Content>
		</Card.Root>
		<Card.Root>
			<Card.Content class="p-4">
				<div class="flex items-center gap-3">
					<div class="bg-muted flex h-10 w-10 items-center justify-center rounded-lg">
						<DollarSign class="text-muted-foreground h-5 w-5" />
					</div>
					<div>
						<p class="text-muted-foreground text-xs font-medium uppercase">Total Value</p>
						<p class="text-foreground text-xl font-bold">{formatCurrency(stats.totalValue)}</p>
					</div>
				</div>
			</Card.Content>
		</Card.Root>
		<Card.Root>
			<Card.Content class="p-4">
				<div class="flex items-center gap-3">
					<div
						class="flex h-10 w-10 items-center justify-center rounded-lg bg-[var(--accent-primary)]/10"
					>
						<TrendingUp class="h-5 w-5 text-[var(--accent-primary)]" />
					</div>
					<div>
						<p class="text-muted-foreground text-xs font-medium uppercase">Pipeline</p>
						<p class="text-xl font-bold text-[var(--accent-primary)]">
							{formatCurrency(stats.pipeline)}
						</p>
					</div>
				</div>
			</Card.Content>
		</Card.Root>
		<Card.Root>
			<Card.Content class="p-4">
				<div class="flex items-center gap-3">
					<div
						class="flex h-10 w-10 items-center justify-center rounded-lg bg-green-100 dark:bg-green-900/30"
					>
						<CheckCircle class="h-5 w-5 text-green-600 dark:text-green-400" />
					</div>
					<div>
						<p class="text-muted-foreground text-xs font-medium uppercase">Won</p>
						<p class="text-xl font-bold text-green-600 dark:text-green-400">
							{formatCurrency(stats.wonValue)}
						</p>
					</div>
				</div>
			</Card.Content>
		</Card.Root>
	</div>

	<!-- Search and Filters -->
	<Card.Root>
		<Card.Content class="p-4">
			<div class="flex flex-col gap-4 sm:flex-row">
				<div class="relative flex-1">
					<Search class="text-muted-foreground absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2" />
					<Input type="text" placeholder="Search deals..." bind:value={searchQuery} class="pl-9" />
				</div>
				<Button
					variant="outline"
					onclick={() => (showFilters = !showFilters)}
					class="shrink-0"
					disabled={false}
				>
					<Filter class="mr-2 h-4 w-4" />
					Filters
					{#if activeFiltersCount > 0}
						<Badge variant="secondary" class="ml-2">{activeFiltersCount}</Badge>
					{/if}
					{#if showFilters}
						<ChevronUp class="ml-2 h-4 w-4" />
					{:else}
						<ChevronDown class="ml-2 h-4 w-4" />
					{/if}
				</Button>

				<!-- Mobile View Toggle -->
				<div class="flex gap-1 sm:hidden">
					<Button
						variant={viewMode === 'list' ? 'default' : 'outline'}
						size="icon"
						onclick={() => (viewMode = 'list')}
						disabled={false}
					>
						<List class="h-4 w-4" />
					</Button>
					<Button
						variant={viewMode === 'kanban' ? 'default' : 'outline'}
						size="icon"
						onclick={() => (viewMode = 'kanban')}
						disabled={false}
					>
						<LayoutGrid class="h-4 w-4" />
					</Button>
				</div>
			</div>

			{#if showFilters}
				<div class="bg-muted/50 mt-4 grid grid-cols-1 gap-4 rounded-lg p-4 sm:grid-cols-3">
					<div>
						<label for="stage-filter" class="mb-1.5 block text-sm font-medium">Stage</label>
						<select
							id="stage-filter"
							bind:value={stageFilter}
							class="border-input bg-background w-full rounded-md border px-3 py-2 text-sm"
						>
							{#each stages as stage}
								<option value={stage.value}>{stage.label}</option>
							{/each}
						</select>
					</div>
					<div></div>
					<div class="flex items-end">
						<Button variant="ghost" onclick={clearFilters} class="w-full" disabled={false}>
							Clear Filters
						</Button>
					</div>
				</div>
			{/if}
		</Card.Content>
	</Card.Root>

	<!-- Content View -->
	{#if viewMode === 'kanban'}
		<!-- Kanban View -->
		<div class="h-[calc(100vh-400px)] min-h-[500px]">
			<KanbanBoard
				opportunities={filteredOpportunities}
				onCardClick={openOpportunityDetail}
				onStageChange={handleStageChange}
				onCreateNew={openCreateForm}
			/>
		</div>
	{:else}
		<!-- List View -->
		<Card.Root>
			<Card.Content class="p-0">
				{#if filteredOpportunities.length === 0}
					<div class="flex flex-col items-center justify-center py-16 text-center">
						<Target class="text-muted-foreground/50 mb-4 h-12 w-12" />
						<h3 class="text-foreground text-lg font-medium">No opportunities found</h3>
						<p class="text-muted-foreground mt-1 text-sm">
							Try adjusting your search criteria or create a new deal.
						</p>
						<Button onclick={() => openCreateForm()} class="mt-4" disabled={false}>
							<Plus class="mr-2 h-4 w-4" />
							Create New Deal
						</Button>
					</div>
				{:else}
					<!-- Desktop Table -->
					<div class="hidden md:block">
						<Table.Root>
							<Table.Header>
								<Table.Row>
									<Table.Head class="w-[200px]">Opportunity</Table.Head>
									<Table.Head>Account</Table.Head>
									<Table.Head>Type</Table.Head>
									<Table.Head>Stage</Table.Head>
									<Table.Head
										class="hover:bg-muted/50 cursor-pointer"
										onclick={() => toggleSort('amount')}
									>
										<div class="flex items-center gap-1">
											Amount
											{#if sortBy === 'amount'}
												{#if sortOrder === 'asc'}
													<ChevronUp class="h-4 w-4" />
												{:else}
													<ChevronDown class="h-4 w-4" />
												{/if}
											{/if}
										</div>
									</Table.Head>
									<Table.Head>Probability</Table.Head>
									<Table.Head>Close Date</Table.Head>
									<Table.Head>Owner</Table.Head>
									<Table.Head class="w-[80px]">Actions</Table.Head>
								</Table.Row>
							</Table.Header>
							<Table.Body>
								{#each filteredOpportunities as opportunity (opportunity.id)}
									{@const config = getStageConfig(opportunity.stage)}
									<Table.Row
										class="hover:bg-muted/50 cursor-pointer"
										onclick={() => openOpportunityDetail(opportunity)}
									>
										<Table.Cell>
											<div class="min-w-0">
												<p class="text-foreground truncate font-medium">
													{opportunity.name}
												</p>
											</div>
										</Table.Cell>
										<Table.Cell>
											{#if opportunity.account?.name}
												<div class="flex items-center gap-1.5 text-sm">
													<Building2 class="text-muted-foreground h-4 w-4" />
													<span class="truncate">{opportunity.account.name}</span>
												</div>
											{:else}
												<span class="text-muted-foreground">-</span>
											{/if}
										</Table.Cell>
										<Table.Cell>
											{#if getTypeLabel(opportunity.opportunityType)}
												<span class="text-sm">{getTypeLabel(opportunity.opportunityType)}</span>
											{:else}
												<span class="text-muted-foreground">-</span>
											{/if}
										</Table.Cell>
										<Table.Cell>
											<span
												class={cn(
													'inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium',
													config.color
												)}
											>
												{config.label}
											</span>
										</Table.Cell>
										<Table.Cell>
											<span class="font-medium text-[var(--accent-primary)]">
												{formatCurrency(opportunity.amount)}
											</span>
										</Table.Cell>
										<Table.Cell>
											{#if opportunity.probability != null}
												<div class="flex items-center gap-1.5 text-sm">
													<Percent class="text-muted-foreground h-3.5 w-3.5" />
													<span>{opportunity.probability}%</span>
												</div>
											{:else}
												<span class="text-muted-foreground">-</span>
											{/if}
										</Table.Cell>
										<Table.Cell>
											{#if opportunity.closedOn}
												<div class="text-muted-foreground flex items-center gap-1.5 text-sm">
													<Calendar class="h-3.5 w-3.5" />
													<span>{formatRelativeDate(opportunity.closedOn)}</span>
												</div>
											{:else}
												<span class="text-muted-foreground">-</span>
											{/if}
										</Table.Cell>
										<Table.Cell>
											{#if opportunity.owner}
												<div
													class="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-blue-600 text-xs font-medium text-white"
													title={opportunity.owner.name}
												>
													{getInitials(opportunity.owner.name)}
												</div>
											{:else}
												<span class="text-muted-foreground">-</span>
											{/if}
										</Table.Cell>
										<Table.Cell onclick={(e) => e.stopPropagation()}>
											<DropdownMenu.Root>
												<DropdownMenu.Trigger>
													<Button variant="ghost" size="icon" class="h-8 w-8" disabled={false}>
														<MoreHorizontal class="h-4 w-4" />
													</Button>
												</DropdownMenu.Trigger>
												<DropdownMenu.Content align="end">
													<DropdownMenu.Item onclick={() => openOpportunityDetail(opportunity)}>
														<Eye class="mr-2 h-4 w-4" />
														View Details
													</DropdownMenu.Item>
													<DropdownMenu.Separator />
													<DropdownMenu.Item class="text-destructive">Delete</DropdownMenu.Item>
												</DropdownMenu.Content>
											</DropdownMenu.Root>
										</Table.Cell>
									</Table.Row>
								{/each}
							</Table.Body>
						</Table.Root>
					</div>

					<!-- Mobile Card View -->
					<div class="divide-y md:hidden">
						{#each filteredOpportunities as opportunity (opportunity.id)}
							{@const config = getStageConfig(opportunity.stage)}
							<button
								type="button"
								class="hover:bg-muted/50 flex w-full items-start gap-4 p-4 text-left"
								onclick={() => openOpportunityDetail(opportunity)}
							>
								<div class="min-w-0 flex-1">
									<div class="flex items-start justify-between gap-2">
										<div>
											<p class="text-foreground font-medium">{opportunity.name}</p>
											{#if opportunity.account?.name}
												<p class="text-muted-foreground text-sm">{opportunity.account.name}</p>
											{/if}
										</div>
										<span
											class={cn(
												'shrink-0 rounded-full px-2 py-0.5 text-xs font-medium',
												config.color
											)}
										>
											{config.label}
										</span>
									</div>
									<div class="mt-2 flex flex-wrap items-center gap-3 text-sm">
										<span class="font-medium text-[var(--accent-primary)]">
											{formatCurrency(opportunity.amount)}
										</span>
										{#if opportunity.closedOn}
											<div class="text-muted-foreground flex items-center gap-1">
												<Calendar class="h-3.5 w-3.5" />
												<span>{formatRelativeDate(opportunity.closedOn)}</span>
											</div>
										{/if}
									</div>
								</div>
							</button>
						{/each}
					</div>
				{/if}
			</Card.Content>
		</Card.Root>
	{/if}
</div>

<!-- Unified Opportunity Drawer -->
<OpportunityDrawer
	bind:open={drawerOpen}
	opportunity={selectedOpportunity}
	mode={drawerMode}
	options={formOptions}
	{initialStage}
	loading={isLoading}
	onSave={handleSave}
	onDelete={handleDelete}
	onMarkWon={handleMarkWon}
	onMarkLost={handleMarkLost}
	onCancel={() => (drawerOpen = false)}
/>
