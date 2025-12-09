<script>
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';

	import { PageHeader } from '$lib/components/layout';
	import { CrmTable } from '$lib/components/ui/crm-table';
	import { FilterBar, SearchInput, DateRangeFilter, SelectFilter } from '$lib/components/ui/filter';
	import { Pagination } from '$lib/components/ui/pagination';
	import { Button } from '$lib/components/ui/button';
	import * as DropdownMenu from '$lib/components/ui/dropdown-menu';
	import { formatCurrency, formatDate } from '$lib/utils/formatting.js';
	import { Plus, Filter, Columns3 } from '@lucide/svelte';

	/** @type {{ data: import('./$types').PageData }} */
	let { data } = $props();

	// Invoice status options
	const INVOICE_STATUSES = [
		{
			value: 'Draft',
			label: 'Draft',
			color: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300'
		},
		{
			value: 'Sent',
			label: 'Sent',
			color: 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300'
		},
		{
			value: 'Viewed',
			label: 'Viewed',
			color: 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900 dark:text-indigo-300'
		},
		{
			value: 'Partially_Paid',
			label: 'Partially Paid',
			color: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300'
		},
		{
			value: 'Paid',
			label: 'Paid',
			color: 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300'
		},
		{
			value: 'Overdue',
			label: 'Overdue',
			color: 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300'
		},
		{
			value: 'Cancelled',
			label: 'Cancelled',
			color: 'bg-gray-200 text-gray-500 dark:bg-gray-700 dark:text-gray-400'
		}
	];

	/**
	 * @typedef {'text' | 'email' | 'number' | 'date' | 'select' | 'checkbox' | 'relation'} ColumnType
	 * @typedef {{ key: string, label: string, type?: ColumnType, width?: string, editable?: boolean, canHide?: boolean, getValue?: (row: any) => any, emptyText?: string, relationIcon?: string, options?: Array<{value: string, label: string, color: string}> }} ColumnDef
	 */

	/** @type {ColumnDef[]} */
	const columns = [
		{
			key: 'invoiceNumber',
			label: 'Invoice #',
			type: 'text',
			width: 'w-28',
			editable: false,
			canHide: false
		},
		{
			key: 'clientName',
			label: 'Client',
			type: 'text',
			width: 'w-40',
			editable: false,
			canHide: false
		},
		{
			key: 'account',
			label: 'Account',
			type: 'relation',
			width: 'w-36',
			relationIcon: 'building',
			canHide: true,
			getValue: (row) => row.account?.name
		},
		{
			key: 'status',
			label: 'Status',
			type: 'select',
			width: 'w-28',
			options: INVOICE_STATUSES,
			canHide: true,
			getValue: (row) => row.status
		},
		{
			key: 'issueDate',
			label: 'Issue Date',
			type: 'date',
			width: 'w-28',
			canHide: true,
			getValue: (row) => row.issueDate
		},
		{
			key: 'dueDate',
			label: 'Due Date',
			type: 'date',
			width: 'w-28',
			canHide: true,
			getValue: (row) => row.dueDate
		},
		{
			key: 'totalAmount',
			label: 'Total',
			type: 'number',
			width: 'w-28',
			canHide: false
		},
		{
			key: 'amountDue',
			label: 'Amount Due',
			type: 'number',
			width: 'w-28',
			canHide: true
		}
	];

	// Default visible columns
	const DEFAULT_VISIBLE_COLUMNS = [
		'invoiceNumber',
		'clientName',
		'status',
		'issueDate',
		'dueDate',
		'totalAmount'
	];

	// Status chip filter definitions
	const STATUS_CHIPS = [
		{ key: 'ALL', label: 'All' },
		{ key: 'OPEN', label: 'Open', statuses: ['Draft', 'Sent', 'Viewed'] },
		{ key: 'PAID', label: 'Paid', statuses: ['Paid', 'Partially_Paid'] },
		{ key: 'OVERDUE', label: 'Overdue', statuses: ['Overdue'] },
		{ key: 'CANCELLED', label: 'Cancelled', statuses: ['Cancelled'] }
	];

	// State
	let filtersExpanded = $state(false);
	let visibleColumns = $state([...DEFAULT_VISIBLE_COLUMNS]);
	let statusChipFilter = $state('ALL');

	// Derived values
	const filters = $derived(data.filters);
	const pagination = $derived(data.pagination);
	const allInvoices = $derived(data.invoices);

	// Filter invoices by chip selection (client-side filtering)
	const invoices = $derived.by(() => {
		if (statusChipFilter === 'ALL') {
			return allInvoices;
		}
		const chip = STATUS_CHIPS.find((c) => c.key === statusChipFilter);
		if (!chip?.statuses) return allInvoices;
		return allInvoices.filter((inv) => chip.statuses.includes(inv.status));
	});

	// Count invoices per chip category
	const chipCounts = $derived.by(() => {
		const counts = { ALL: allInvoices.length };
		STATUS_CHIPS.forEach((chip) => {
			if (chip.statuses) {
				counts[chip.key] = allInvoices.filter((inv) => chip.statuses.includes(inv.status)).length;
			}
		});
		return counts;
	});

	// Count active filters
	const activeFiltersCount = $derived.by(() => {
		let count = 0;
		if (filters.search) count++;
		if (filters.status) count++;
		if (filters.account) count++;
		if (filters.issue_date_gte || filters.issue_date_lte) count++;
		if (filters.due_date_gte || filters.due_date_lte) count++;
		return count;
	});

	// Filter handlers
	async function updateFilters(newFilters) {
		const url = new URL($page.url);

		// Clear existing filter params
		[
			'search',
			'status',
			'account',
			'contact',
			'assigned_to',
			'issue_date_gte',
			'issue_date_lte',
			'due_date_gte',
			'due_date_lte'
		].forEach((key) => url.searchParams.delete(key));

		// Set new params
		Object.entries(newFilters).forEach(([key, value]) => {
			if (Array.isArray(value)) {
				value.forEach((v) => url.searchParams.append(key, v));
			} else if (value) {
				url.searchParams.set(key, value);
			}
		});

		// Reset to page 1 when filters change
		url.searchParams.set('page', '1');

		await goto(url.toString(), { replaceState: true, noScroll: true, invalidateAll: true });
	}

	async function clearFilters() {
		await updateFilters({});
	}

	// Pagination handlers
	async function handlePageChange(newPage) {
		const url = new URL($page.url);
		url.searchParams.set('page', newPage.toString());
		await goto(url.toString(), { replaceState: true, noScroll: true, invalidateAll: true });
	}

	async function handleLimitChange(newLimit) {
		const url = new URL($page.url);
		url.searchParams.set('limit', newLimit.toString());
		url.searchParams.set('page', '1');
		await goto(url.toString(), { replaceState: true, noScroll: true, invalidateAll: true });
	}

	// Row click - navigate to invoice detail
	function handleRowClick(invoice) {
		goto(`/invoices/${invoice.id}`);
	}

	// Create new invoice - navigate to new page
	function createNewInvoice() {
		goto('/invoices/new');
	}

	// Status badge color
	function getStatusColor(status) {
		const statusObj = INVOICE_STATUSES.find((s) => s.value === status);
		return statusObj?.color || 'bg-gray-100 text-gray-700';
	}

	// Column visibility
	function loadColumnConfig() {
		if (typeof window !== 'undefined') {
			const saved = localStorage.getItem('invoices-column-config');
			if (saved) {
				try {
					visibleColumns = JSON.parse(saved);
				} catch (e) {
					visibleColumns = [...DEFAULT_VISIBLE_COLUMNS];
				}
			}
		}
	}

	function saveColumnConfig() {
		if (typeof window !== 'undefined') {
			localStorage.setItem('invoices-column-config', JSON.stringify(visibleColumns));
		}
	}

	function toggleColumn(key) {
		const column = columns.find((c) => c.key === key);
		if (column && !column.canHide) return;

		if (visibleColumns.includes(key)) {
			visibleColumns = visibleColumns.filter((k) => k !== key);
		} else {
			visibleColumns = [...visibleColumns, key];
		}
		saveColumnConfig();
	}

	// Load column config on mount
	$effect(() => {
		loadColumnConfig();
	});
</script>

<svelte:head>
	<title>Invoices | BottleCRM</title>
</svelte:head>

<!-- Page Content -->
<div class="flex flex-col">
	<!-- Header -->
	<PageHeader title="Invoices">
		{#snippet actions()}
			<div class="flex items-center gap-2">
				<!-- Status Filter Chips -->
				<div class="flex gap-1">
					{#each STATUS_CHIPS as chip}
						<button
							type="button"
							onclick={() => (statusChipFilter = chip.key)}
							class="inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-medium transition-colors {statusChipFilter ===
							chip.key
								? 'bg-gray-900 text-white dark:bg-white dark:text-gray-900'
								: 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-400 dark:hover:bg-gray-700'}"
						>
							{chip.label}
							<span
								class="rounded-full px-1.5 py-0.5 text-xs {statusChipFilter === chip.key
									? 'bg-gray-700 text-gray-200 dark:bg-gray-200 dark:text-gray-700'
									: 'bg-gray-200 text-gray-500 dark:bg-gray-700 dark:text-gray-500'}"
							>
								{chipCounts[chip.key] || 0}
							</span>
						</button>
					{/each}
				</div>

				<div class="bg-border mx-1 h-6 w-px"></div>

				<!-- Filters Toggle -->
				<Button
					variant="outline"
					size="sm"
					onclick={() => (filtersExpanded = !filtersExpanded)}
					class="gap-2"
				>
					<Filter class="size-4" />
					Filters
					{#if activeFiltersCount > 0}
						<span class="bg-primary text-primary-foreground rounded-full px-2 py-0.5 text-xs">
							{activeFiltersCount}
						</span>
					{/if}
				</Button>

				<!-- Column Visibility -->
				<DropdownMenu.Root>
					<DropdownMenu.Trigger>
						{#snippet child({ props })}
							<Button {...props} variant="outline" size="sm" class="gap-2">
								<Columns3 class="size-4" />
								Columns
							</Button>
						{/snippet}
					</DropdownMenu.Trigger>
					<DropdownMenu.Content align="end" class="w-48">
						{#each columns as column}
							<DropdownMenu.CheckboxItem
								class=""
								checked={visibleColumns.includes(column.key)}
								disabled={!column.canHide}
								onCheckedChange={() => toggleColumn(column.key)}
							>
								{column.label}
							</DropdownMenu.CheckboxItem>
						{/each}
					</DropdownMenu.Content>
				</DropdownMenu.Root>

				<!-- New Invoice -->
				<Button onclick={createNewInvoice} class="gap-2">
					<Plus class="size-4" />
					New Invoice
				</Button>
			</div>
		{/snippet}
	</PageHeader>

	<!-- Filter Bar -->
	<FilterBar
		minimal
		expanded={filtersExpanded}
		activeCount={activeFiltersCount}
		onClear={clearFilters}
	>
		<SearchInput
			value={filters.search}
			placeholder="Search invoices..."
			onchange={(value) => updateFilters({ ...filters, search: value })}
		/>

		<SelectFilter
			label="Status"
			value={filters.status}
			options={INVOICE_STATUSES}
			onchange={(value) => updateFilters({ ...filters, status: value })}
		/>

		<DateRangeFilter
			label="Issue Date"
			startDate={filters.issue_date_gte}
			endDate={filters.issue_date_lte}
			onchange={(start, end) =>
				updateFilters({ ...filters, issue_date_gte: start, issue_date_lte: end })}
		/>

		<DateRangeFilter
			label="Due Date"
			startDate={filters.due_date_gte}
			endDate={filters.due_date_lte}
			onchange={(start, end) =>
				updateFilters({ ...filters, due_date_gte: start, due_date_lte: end })}
		/>
	</FilterBar>

	<!-- Invoice Table -->
	<CrmTable data={invoices} {columns} bind:visibleColumns onRowClick={handleRowClick}>
		{#snippet emptyState()}
			<div class="flex flex-col items-center justify-center py-16 text-center">
				<span class="mb-4 text-6xl">📄</span>
				<h3 class="text-foreground text-lg font-medium">No invoices yet</h3>
				<p class="text-muted-foreground mb-4 text-sm">Create your first invoice to get started</p>
				<Button onclick={createNewInvoice} class="gap-2">
					<Plus class="size-4" />
					Create Invoice
				</Button>
			</div>
		{/snippet}
		{#snippet cellContent(row, column)}
			{#if column.key === 'status'}
				<span
					class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium {getStatusColor(
						row.status
					)}"
				>
					{row.status.replace('_', ' ')}
				</span>
			{:else if column.key === 'issueDate' || column.key === 'dueDate'}
				{row[column.key] ? formatDate(row[column.key]) : '-'}
			{:else if column.key === 'totalAmount' || column.key === 'amountDue'}
				<span
					class={column.key === 'amountDue' && parseFloat(row.amountDue || 0) > 0
						? 'font-medium text-orange-600 dark:text-orange-400'
						: ''}
				>
					{formatCurrency(row[column.key], row.currency)}
				</span>
			{:else if column.key === 'account' || column.key === 'contact'}
				{row[column.key]?.name || '-'}
			{:else}
				{row[column.key] || '-'}
			{/if}
		{/snippet}
	</CrmTable>

	<!-- Pagination -->
	{#if invoices.length > 0}
		<Pagination
			page={pagination.page}
			limit={pagination.limit}
			total={pagination.total}
			limitOptions={[10, 25, 50, 100]}
			onPageChange={handlePageChange}
			onLimitChange={handleLimitChange}
		/>
	{/if}
</div>
