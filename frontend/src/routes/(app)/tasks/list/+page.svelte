<script>
	import { enhance } from '$app/forms';
	import { invalidateAll } from '$app/navigation';
	import { tick, onMount } from 'svelte';
	import { toast } from 'svelte-sonner';
	import {
		Plus,
		ChevronDown,
		ChevronUp,
		ChevronLeft,
		ChevronRight,
		CheckSquare,
		Building2,
		User,
		Calendar,
		List,
		Flag,
		Circle,
		CheckCircle2,
		AlertCircle,
		Clock,
		RotateCcw
	} from '@lucide/svelte';
	import { PageHeader, FilterPopover } from '$lib/components/layout';
	import { TaskDrawer } from '$lib/components/tasks';
	import { Button } from '$lib/components/ui/button/index.js';
	import * as Card from '$lib/components/ui/card/index.js';
	import * as Table from '$lib/components/ui/table/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { cn } from '$lib/utils.js';
	import { formatRelativeDate } from '$lib/utils/formatting.js';
	import { getPriorityClass, getTaskStatusClass, formatStatusDisplay } from '$lib/utils/ui-helpers.js';
	import { TASK_STATUSES as statuses, PRIORITIES as priorities } from '$lib/constants/filters.js';
	import { useDrawerState, useListFilters } from '$lib/hooks';
	import { ColumnCustomizer } from '$lib/components/ui/column-customizer/index.js';

	// Column visibility configuration
	const STORAGE_KEY = 'tasks-column-config';

	/**
	 * @typedef {Object} ColumnConfig
	 * @property {string} key
	 * @property {string} label
	 * @property {boolean} visible
	 * @property {boolean} [canHide]
	 */

	/** @type {ColumnConfig[]} */
	const defaultColumns = [
		{ key: 'task', label: 'Task', visible: true, canHide: false },
		{ key: 'account', label: 'Account', visible: true, canHide: true },
		{ key: 'assignedTo', label: 'Assigned To', visible: true, canHide: true },
		{ key: 'priority', label: 'Priority', visible: true, canHide: true },
		{ key: 'status', label: 'Status', visible: true, canHide: true },
		{ key: 'dueDate', label: 'Due Date', visible: true, canHide: true }
	];

	/**
	 * Load column config from localStorage
	 * @returns {typeof defaultColumns}
	 */
	function loadColumnConfig() {
		if (typeof window === 'undefined') return defaultColumns;
		try {
			const saved = localStorage.getItem(STORAGE_KEY);
			if (saved) {
				const parsed = JSON.parse(saved);
				return defaultColumns.map((def) => {
					const savedCol = parsed.find((/** @type {ColumnConfig} */ p) => p.key === def.key);
					return savedCol ? { ...def, visible: savedCol.visible } : def;
				});
			}
		} catch (e) {
			console.error('Failed to load column config:', e);
		}
		return defaultColumns;
	}

	let columnConfig = $state(defaultColumns);

	onMount(() => {
		columnConfig = loadColumnConfig();
	});

	// Save to localStorage when column config changes
	$effect(() => {
		if (typeof window !== 'undefined' && columnConfig !== defaultColumns) {
			localStorage.setItem(STORAGE_KEY, JSON.stringify(columnConfig));
		}
	});

	/**
	 * Check if a column is visible
	 * @param {string} key
	 */
	function isColumnVisible(key) {
		return columnConfig.find((c) => c.key === key)?.visible ?? true;
	}

	/**
	 * Handle column config change
	 * @param {ColumnConfig[]} newConfig
	 */
	function handleColumnChange(newConfig) {
		columnConfig = newConfig;
	}

	/** @type {{ data: any }} */
	let { data } = $props();

	// Computed values
	const tasks = $derived(data.tasks || []);
	const accounts = $derived(data.allAccounts || []);
	const users = $derived(data.allUsers || []);
	const contacts = $derived(data.allContacts || []);
	const teams = $derived(data.allTeams || []);

	// Drawer state using hook
	const drawer = useDrawerState();

	// Filter/search/sort state using hook
	const list = useListFilters({
		searchFields: ['subject', 'description', 'account.name'],
		filters: [
			{
				key: 'statusFilter',
				defaultValue: 'ALL',
				match: (item, value) => value === 'ALL' || item.status === value
			},
			{
				key: 'priorityFilter',
				defaultValue: 'ALL',
				match: (item, value) => value === 'ALL' || item.priority === value
			}
		],
		defaultSortColumn: 'dueDate',
		defaultSortDirection: 'asc'
	});

	// Filtered tasks
	const filteredTasks = $derived(list.filterAndSort(tasks));
	const activeFiltersCount = $derived(list.getActiveFilterCount());

	// View mode state (list or calendar)
	/** @type {'list' | 'calendar'} */
	let viewMode = $state('list');

	/**
	 * Get status icon for task
	 * @param {string} status
	 */
	function getStatusIcon(status) {
		if (status === 'Completed') return CheckCircle2;
		if (status === 'In Progress') return RotateCcw;
		return AlertCircle;
	}

	// Form references for server actions
	/** @type {HTMLFormElement} */
	let createForm;
	/** @type {HTMLFormElement} */
	let updateForm;
	/** @type {HTMLFormElement} */
	let deleteForm;
	/** @type {HTMLFormElement} */
	let completeForm;
	/** @type {HTMLFormElement} */
	let reopenForm;

	// Form data state
	let formState = $state({
		taskId: '',
		subject: '',
		description: '',
		status: 'New',
		priority: 'Medium',
		dueDate: '',
		accountId: '',
		assignedTo: /** @type {string[]} */ ([]),
		contacts: /** @type {string[]} */ ([]),
		teams: /** @type {string[]} */ ([])
	});

	/**
	 * Handle save from drawer
	 * @param {any} data
	 */
	async function handleSave(data) {
		formState.subject = data.subject || '';
		formState.description = data.description || '';
		formState.status = data.status || 'New';
		formState.priority = data.priority || 'Medium';
		formState.dueDate = data.dueDate || '';
		formState.accountId = data.accountId || '';
		formState.assignedTo = data.assignedTo || [];
		formState.contacts = data.contacts || [];
		formState.teams = data.teams || [];

		await tick();

		if (drawer.mode === 'edit' && drawer.selected) {
			formState.taskId = drawer.selected.id;
			await tick();
			updateForm.requestSubmit();
		} else {
			createForm.requestSubmit();
		}
	}

	/**
	 * Handle task complete
	 * @param {string} taskId
	 * @param {Event} [event]
	 */
	async function handleComplete(taskId, event) {
		event?.stopPropagation();
		formState.taskId = taskId;
		await tick();
		completeForm.requestSubmit();
	}

	/**
	 * Handle task reopen
	 */
	async function handleReopen() {
		if (!drawer.selected) return;
		formState.taskId = drawer.selected.id;
		await tick();
		reopenForm.requestSubmit();
	}

	/**
	 * Handle task delete
	 */
	async function handleDelete() {
		if (!drawer.selected) return;
		if (!confirm(`Are you sure you want to delete "${drawer.selected.subject}"?`)) return;

		formState.taskId = drawer.selected.id;
		await tick();
		deleteForm.requestSubmit();
	}

	/**
	 * Create enhance handler for form actions
	 * @param {string} successMessage
	 * @param {boolean} closeDetailDrawer
	 */
	function createEnhanceHandler(successMessage, closeDetailDrawer = false) {
		return () => {
			return async ({ result }) => {
				if (result.type === 'success') {
					toast.success(successMessage);
					if (closeDetailDrawer) {
						drawer.closeDetail();
					} else {
						drawer.closeForm();
					}
					await invalidateAll();
				} else if (result.type === 'failure') {
					toast.error(result.data?.error || 'Operation failed');
				} else if (result.type === 'error') {
					toast.error('An unexpected error occurred');
				}
			};
		};
	}

	// Form options for drawers
	const formOptions = $derived({
		accounts: accounts.map((/** @type {any} */ acc) => ({ id: acc.id, name: acc.name })),
		users: users.map((/** @type {any} */ user) => ({ id: user.id, name: user.name })),
		contacts: contacts.map((/** @type {any} */ c) => ({ id: c.id, name: c.name })),
		teams: teams.map((/** @type {any} */ t) => ({ id: t.id, name: t.name }))
	});

	// Calendar state
	let today = new Date();
	let currentDate = $state(new Date(today));
	let selectedDate = $state(today.toISOString().slice(0, 10));

	const monthNames = [
		'January',
		'February',
		'March',
		'April',
		'May',
		'June',
		'July',
		'August',
		'September',
		'October',
		'November',
		'December'
	];

	// Calendar computed values
	const calendarYear = $derived(currentDate.getFullYear());
	const calendarMonth = $derived(currentDate.getMonth());
	const monthStart = $derived(new Date(calendarYear, calendarMonth, 1));
	const monthEnd = $derived(new Date(calendarYear, calendarMonth + 1, 0));
	const startDay = $derived(monthStart.getDay());
	const daysInMonth = $derived(monthEnd.getDate());

	const calendar = $derived.by(() => {
		/** @type {(Date | null)[]} */
		let cal = [];
		for (let i = 0; i < startDay; i++) cal.push(null);
		for (let d = 1; d <= daysInMonth; d++) cal.push(new Date(Date.UTC(calendarYear, calendarMonth, d)));
		while (cal.length % 7 !== 0) cal.push(null);
		return cal;
	});

	// Group filtered tasks by due date for calendar
	const tasksByDate = $derived.by(() => {
		/** @type {Record<string, any[]>} */
		const grouped = {};
		for (const t of filteredTasks) {
			if (!t.dueDate) continue;
			const date = (typeof t.dueDate === 'string' ? t.dueDate : t.dueDate?.toISOString?.())?.slice(0, 10);
			if (!date) continue;
			if (!grouped[date]) grouped[date] = [];
			grouped[date].push(t);
		}
		return grouped;
	});

	const selectedTasks = $derived(tasksByDate[selectedDate] || []);

	// Monthly stats for calendar
	const monthlyTaskDates = $derived(
		Object.keys(tasksByDate).filter((dateStr) => {
			const taskDate = new Date(dateStr);
			return taskDate.getFullYear() === calendarYear && taskDate.getMonth() === calendarMonth;
		})
	);

	const totalMonthlyTasks = $derived(
		monthlyTaskDates.reduce((total, dateStr) => total + tasksByDate[dateStr].length, 0)
	);

	/**
	 * Format date to YYYY-MM-DD string
	 * @param {Date} date
	 */
	function formatDateString(date) {
		return date.toISOString().slice(0, 10);
	}

	/**
	 * Check if date is today
	 * @param {Date|null} date
	 */
	function isTodayDate(date) {
		return !!(date && formatDateString(date) === today.toISOString().slice(0, 10));
	}

	/**
	 * Check if date has tasks
	 * @param {Date|null} date
	 */
	function hasTasksOnDate(date) {
		return !!(date && tasksByDate[formatDateString(date)]?.length > 0);
	}

	/**
	 * Select a day on the calendar
	 * @param {Date|null} date
	 */
	function selectDay(date) {
		if (date) {
			selectedDate = formatDateString(date);
		}
	}

	function previousMonth() {
		currentDate = new Date(calendarYear, calendarMonth - 1, 1);
	}

	function nextMonth() {
		currentDate = new Date(calendarYear, calendarMonth + 1, 1);
	}

	function goToToday() {
		currentDate = new Date(today);
		selectedDate = today.toISOString().slice(0, 10);
	}
</script>

<svelte:head>
	<title>Tasks - BottleCRM</title>
</svelte:head>

<PageHeader title="Tasks" subtitle="{filteredTasks.length} of {tasks.length} tasks">
	{#snippet actions()}
		<div class="flex items-center gap-2">
			<!-- View Toggle -->
			<div class="border-input bg-background inline-flex rounded-lg border p-1">
				<Button
					variant={viewMode === 'list' ? 'secondary' : 'ghost'}
					size="sm"
					onclick={() => (viewMode = 'list')}
					class="h-8 px-3"
				>
					<List class="mr-1.5 h-4 w-4" />
					List
				</Button>
				<Button
					variant={viewMode === 'calendar' ? 'secondary' : 'ghost'}
					size="sm"
					onclick={() => (viewMode = 'calendar')}
					class="h-8 px-3"
				>
					<Calendar class="mr-1.5 h-4 w-4" />
					Calendar
				</Button>
			</div>
			{#if viewMode === 'list'}
				<ColumnCustomizer columns={columnConfig} onchange={handleColumnChange} />
			{/if}
			<FilterPopover activeCount={activeFiltersCount} onClear={list.clearFilters}>
				{#snippet children()}
					<div class="space-y-3">
						<div>
							<label for="status-filter" class="mb-1.5 block text-sm font-medium">Status</label>
							<select
								id="status-filter"
								bind:value={list.filters.statusFilter}
								class="border-input bg-background w-full rounded-md border px-3 py-2 text-sm"
							>
								{#each statuses as status}
									<option value={status.value}>{status.label}</option>
								{/each}
							</select>
						</div>
						<div>
							<label for="priority-filter" class="mb-1.5 block text-sm font-medium">Priority</label>
							<select
								id="priority-filter"
								bind:value={list.filters.priorityFilter}
								class="border-input bg-background w-full rounded-md border px-3 py-2 text-sm"
							>
								{#each priorities as priority}
									<option value={priority.value}>{priority.label}</option>
								{/each}
							</select>
						</div>
					</div>
				{/snippet}
			</FilterPopover>
			<Button onclick={drawer.openCreate}>
				<Plus class="mr-2 h-4 w-4" />
				New Task
			</Button>
		</div>
	{/snippet}
</PageHeader>

<div class="flex-1 space-y-4 p-4 md:p-6">
	{#if viewMode === 'list'}
		<!-- Tasks Table -->
		<Card.Root class="border-0 shadow-sm">
			<Card.Content class="p-0">
				{#if filteredTasks.length === 0}
					<div class="flex flex-col items-center justify-center py-16 text-center">
						<CheckSquare class="text-muted-foreground/50 mb-4 h-12 w-12" />
						<h3 class="text-foreground text-lg font-medium">No tasks found</h3>
						<p class="text-muted-foreground mt-1 text-sm">
							Try adjusting your search criteria or create a new task.
						</p>
						<Button onclick={drawer.openCreate} class="mt-4">
							<Plus class="mr-2 h-4 w-4" />
							Create New Task
						</Button>
					</div>
				{:else}
				<!-- Desktop Table -->
				<div class="hidden md:block">
					<Table.Root>
						<Table.Header>
							<Table.Row class="border-b border-border/40 hover:bg-transparent">
								{#if isColumnVisible('task')}
									<Table.Head class="w-[300px] py-2.5 px-4 text-xs font-normal uppercase tracking-wide text-muted-foreground/70">Task</Table.Head>
								{/if}
								{#if isColumnVisible('account')}
									<Table.Head class="py-2.5 px-4 text-xs font-normal uppercase tracking-wide text-muted-foreground/70">Account</Table.Head>
								{/if}
								{#if isColumnVisible('assignedTo')}
									<Table.Head class="py-2.5 px-4 text-xs font-normal uppercase tracking-wide text-muted-foreground/70">Assigned To</Table.Head>
								{/if}
								{#if isColumnVisible('priority')}
									<Table.Head class="py-2.5 px-4 text-xs font-normal uppercase tracking-wide text-muted-foreground/70">Priority</Table.Head>
								{/if}
								{#if isColumnVisible('status')}
									<Table.Head class="py-2.5 px-4 text-xs font-normal uppercase tracking-wide text-muted-foreground/70">Status</Table.Head>
								{/if}
								{#if isColumnVisible('dueDate')}
									<Table.Head
										class="py-2.5 px-4 text-xs font-normal uppercase tracking-wide text-muted-foreground/70 hover:bg-muted/30 cursor-pointer rounded transition-colors"
										onclick={() => list.toggleSort('dueDate')}
									>
										<div class="flex items-center gap-1">
											Due Date
											{#if list.sortColumn === 'dueDate'}
												{#if list.sortDirection === 'asc'}
													<ChevronUp class="h-3.5 w-3.5" />
												{:else}
													<ChevronDown class="h-3.5 w-3.5" />
												{/if}
											{/if}
										</div>
									</Table.Head>
								{/if}
							</Table.Row>
						</Table.Header>
						<Table.Body>
							{#each filteredTasks as task (task.id)}
								{@const StatusIcon = getStatusIcon(task.status)}
								{@const isOverdue = task.dueDate && task.status !== 'Completed' && new Date(task.dueDate) < new Date()}
								<Table.Row
									class="group relative h-[52px] border-b border-border/30 hover:bg-muted/20 cursor-pointer transition-all duration-150 ease-out"
									onclick={() => drawer.openDetail(task)}
								>
									{#if isColumnVisible('task')}
										<Table.Cell class="py-2 px-4">
											<div class="flex items-center gap-3">
												<div
													class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-purple-500 to-purple-600"
												>
													<CheckSquare class="h-4 w-4 text-white" />
												</div>
												<div class="min-w-0">
													<p class={cn('text-foreground truncate font-medium', task.status === 'Completed' && 'line-through text-muted-foreground')}>
														{task.subject}
													</p>
													{#if task.description}
														<p class="text-muted-foreground line-clamp-1 text-sm">
															{task.description}
														</p>
													{/if}
												</div>
											</div>
										</Table.Cell>
									{/if}
									{#if isColumnVisible('account')}
										<Table.Cell class="py-2 px-4">
											{#if task.account}
												<div class="flex items-center gap-1.5 text-sm">
													<Building2 class="text-muted-foreground h-4 w-4" />
													<span class="truncate">{task.account.name}</span>
												</div>
											{:else}
												<span class="text-muted-foreground">-</span>
											{/if}
										</Table.Cell>
									{/if}
									{#if isColumnVisible('assignedTo')}
										<Table.Cell class="py-2 px-4">
											{#if task.assignedTo && task.assignedTo.length > 0}
												<div class="flex items-center gap-1.5 text-sm">
													<User class="text-muted-foreground h-4 w-4" />
													<span class="truncate">
														{task.assignedTo.length === 1
															? task.assignedTo[0].name
															: `${task.assignedTo.length} users`}
													</span>
												</div>
											{:else}
												<span class="text-muted-foreground">Unassigned</span>
											{/if}
										</Table.Cell>
									{/if}
									{#if isColumnVisible('priority')}
										<Table.Cell class="py-2 px-4">
											{#if task.priority}
												<span
													class={cn(
														'inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium',
														getPriorityClass(task.priority)
													)}
												>
													<Flag class="h-3 w-3" />
													{task.priority}
												</span>
											{:else}
												<span class="text-muted-foreground">-</span>
											{/if}
										</Table.Cell>
									{/if}
									{#if isColumnVisible('status')}
										<Table.Cell class="py-2 px-4">
											<span
												class={cn(
													'inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium',
													getTaskStatusClass(task.status)
												)}
											>
												<StatusIcon class="h-3 w-3" />
												{formatStatusDisplay(task.status)}
											</span>
										</Table.Cell>
									{/if}
									{#if isColumnVisible('dueDate')}
										<Table.Cell class="py-2 px-4">
											{#if task.dueDate}
												<div class={cn(
													'text-muted-foreground flex items-center gap-1.5 text-sm',
													isOverdue && 'font-medium text-red-600 dark:text-red-400'
												)}>
													<Calendar class="h-3.5 w-3.5" />
													<span>{formatRelativeDate(task.dueDate)}</span>
												</div>
											{:else}
												<span class="text-muted-foreground">-</span>
											{/if}
										</Table.Cell>
									{/if}
								</Table.Row>
							{/each}
						</Table.Body>
					</Table.Root>
				</div>

				<!-- Mobile Card View -->
				<div class="divide-y md:hidden">
					{#each filteredTasks as task (task.id)}
						{@const StatusIcon = getStatusIcon(task.status)}
						{@const isOverdue = task.dueDate && task.status !== 'Completed' && new Date(task.dueDate) < new Date()}
						<button
							type="button"
							class="hover:bg-muted/50 flex w-full items-start gap-4 p-4 text-left"
							onclick={() => drawer.openDetail(task)}
						>
							<div
								class="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-purple-500 to-purple-600"
							>
								<CheckSquare class="h-5 w-5 text-white" />
							</div>
							<div class="min-w-0 flex-1">
								<div class="flex items-start justify-between gap-2">
									<div>
										<p class={cn('text-foreground font-medium', task.status === 'Completed' && 'line-through text-muted-foreground')}>
											{task.subject}
										</p>
										{#if task.account}
											<p class="text-muted-foreground text-sm">{task.account.name}</p>
										{/if}
									</div>
									<span
										class={cn(
											'shrink-0 rounded-full px-2 py-0.5 text-xs font-medium',
											getTaskStatusClass(task.status)
										)}
									>
										{formatStatusDisplay(task.status)}
									</span>
								</div>
								<div class="text-muted-foreground mt-2 flex flex-wrap items-center gap-3 text-sm">
									{#if task.priority}
										<span
											class={cn(
												'inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium',
												getPriorityClass(task.priority)
											)}
										>
											<Flag class="h-3 w-3" />
											{task.priority}
										</span>
									{/if}
									{#if task.dueDate}
										<div class={cn(
											'flex items-center gap-1',
											isOverdue && 'font-medium text-red-600 dark:text-red-400'
										)}>
											<Calendar class="h-3.5 w-3.5" />
											<span>{formatRelativeDate(task.dueDate)}</span>
										</div>
									{/if}
									{#if task.assignedTo && task.assignedTo.length > 0}
										<div class="flex items-center gap-1">
											<User class="h-3.5 w-3.5" />
											<span>
												{task.assignedTo.length === 1
													? task.assignedTo[0].name
													: `${task.assignedTo.length} users`}
											</span>
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
	{:else}
		<!-- Calendar View -->
		<div class="grid grid-cols-1 gap-6 lg:grid-cols-3">
			<!-- Calendar Section -->
			<div class="lg:col-span-2">
				<Card.Root>
					<!-- Calendar Header -->
					<Card.Header class="bg-primary flex flex-row items-center justify-between space-y-0 rounded-t-lg p-4">
						<div class="flex items-center gap-4">
							<Button
								variant="ghost"
								size="icon"
								onclick={previousMonth}
								class="hover:bg-primary-foreground/10 text-primary-foreground h-9 w-9"
							>
								<ChevronLeft class="h-5 w-5" />
							</Button>
							<h2 class="text-primary-foreground text-xl font-semibold">
								{monthNames[calendarMonth]}
								{calendarYear}
							</h2>
							<Button
								variant="ghost"
								size="icon"
								onclick={nextMonth}
								class="hover:bg-primary-foreground/10 text-primary-foreground h-9 w-9"
							>
								<ChevronRight class="h-5 w-5" />
							</Button>
						</div>
						<Button
							variant="secondary"
							size="sm"
							onclick={goToToday}
							class="text-primary-foreground bg-primary-foreground/10 hover:bg-primary-foreground/20"
						>
							Today
						</Button>
					</Card.Header>

					<Card.Content class="p-0">
						<!-- Days of Week -->
						<div class="bg-muted/50 grid grid-cols-7 border-b">
							{#each ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'] as day}
								<div class="text-muted-foreground border-r p-3 text-center text-sm font-medium last:border-r-0">
									{day}
								</div>
							{/each}
						</div>

						<!-- Calendar Grid -->
						<div class="grid grid-cols-7">
							{#each calendar as date, i}
								{#if date}
									<button
										onclick={() => selectDay(date)}
										class={cn(
											'relative h-16 border-r border-b p-2 transition-colors last:border-r-0 hover:bg-muted/50 sm:h-20',
											formatDateString(date) === selectedDate && 'bg-primary text-primary-foreground hover:bg-primary/90',
											isTodayDate(date) && formatDateString(date) !== selectedDate && 'bg-primary/10 text-primary',
											!isTodayDate(date) && formatDateString(date) !== selectedDate && 'text-foreground'
										)}
									>
										<div class="text-sm font-medium">
											{date.getDate()}
										</div>
										{#if hasTasksOnDate(date)}
											<div
												class={cn(
													'absolute right-1 bottom-1 h-2 w-2 rounded-full',
													formatDateString(date) === selectedDate ? 'bg-primary-foreground' : 'bg-primary'
												)}
											></div>
											<div
												class={cn(
													'absolute bottom-1 left-1 text-xs font-medium',
													formatDateString(date) === selectedDate ? 'text-primary-foreground' : 'text-primary'
												)}
											>
												{tasksByDate[formatDateString(date)].length}
											</div>
										{/if}
									</button>
								{:else}
									<div class="bg-muted/30 h-16 border-r border-b sm:h-20"></div>
								{/if}
							{/each}
						</div>
					</Card.Content>
				</Card.Root>
			</div>

			<!-- Tasks for Selected Date -->
			<div class="lg:col-span-1">
				<Card.Root class="h-fit">
					<Card.Header class="border-b pb-4">
						<Card.Title class="text-base">
							Tasks for {new Date(selectedDate + 'T00:00:00').toLocaleDateString('en-US', {
								weekday: 'long',
								month: 'long',
								day: 'numeric'
							})}
						</Card.Title>
						<p class="text-muted-foreground text-sm">
							{selectedTasks.length} task{selectedTasks.length !== 1 ? 's' : ''}
						</p>
					</Card.Header>

					<Card.Content class="p-4">
						{#if selectedTasks.length > 0}
							<div class="space-y-3">
								{#each selectedTasks as task}
									<button
										type="button"
										onclick={() => drawer.openDetail(task)}
										class="hover:bg-muted bg-muted/50 block w-full rounded-lg border p-3 text-left transition-colors"
									>
										<div class="mb-2 flex items-start justify-between gap-2">
											<h4 class="text-foreground line-clamp-2 flex-1 font-medium">
												{task.subject}
											</h4>
											{#if task.status === 'Completed'}
												<CheckCircle2 class="text-muted-foreground h-4 w-4 flex-shrink-0" />
											{:else}
												<Circle class="text-muted-foreground h-4 w-4 flex-shrink-0" />
											{/if}
										</div>

										{#if task.description}
											<p class="text-muted-foreground mb-3 line-clamp-2 text-sm">
												{task.description}
											</p>
										{/if}

										<div class="flex flex-wrap items-center gap-2">
											{#if task.priority}
												<span
													class={cn(
														'inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium',
														getPriorityClass(task.priority)
													)}
												>
													<Flag class="h-3 w-3" />
													{task.priority}
												</span>
											{/if}
											<span
												class={cn(
													'inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium',
													getTaskStatusClass(task.status)
												)}
											>
												{formatStatusDisplay(task.status)}
											</span>
										</div>
									</button>
								{/each}
							</div>
						{:else}
							<div class="py-12 text-center">
								<Calendar class="text-muted-foreground/50 mx-auto mb-4 h-12 w-12" />
								<p class="text-muted-foreground text-sm">
									No tasks scheduled for this date
								</p>
								<Button onclick={drawer.openCreate} variant="outline" size="sm" class="mt-4">
									<Plus class="mr-2 h-4 w-4" />
									Add Task
								</Button>
							</div>
						{/if}
					</Card.Content>
				</Card.Root>

				<!-- Monthly Stats -->
				<Card.Root class="mt-4">
					<Card.Header class="pb-2">
						<Card.Title class="text-base">This Month</Card.Title>
					</Card.Header>
					<Card.Content class="space-y-2">
						<div class="flex items-center justify-between">
							<span class="text-muted-foreground text-sm">Total Tasks</span>
							<span class="text-foreground font-medium">{totalMonthlyTasks}</span>
						</div>
						<div class="flex items-center justify-between">
							<span class="text-muted-foreground text-sm">Days with Tasks</span>
							<span class="text-foreground font-medium">{monthlyTaskDates.length}</span>
						</div>
					</Card.Content>
				</Card.Root>
			</div>
		</div>
	{/if}
</div>

<!-- Task Drawer (unified view/edit) -->
<TaskDrawer
	bind:open={drawer.detailOpen}
	task={drawer.selected}
	mode={drawer.mode === 'create' ? 'create' : 'view'}
	loading={drawer.loading}
	options={formOptions}
	onSave={handleSave}
	onComplete={() => drawer.selected && handleComplete(drawer.selected.id)}
	onReopen={handleReopen}
	onDelete={handleDelete}
	onCancel={drawer.closeDetail}
/>

<!-- Hidden forms for server actions -->
<form
	method="POST"
	action="?/create"
	bind:this={createForm}
	use:enhance={createEnhanceHandler('Task created successfully')}
	class="hidden"
>
	<input type="hidden" name="subject" value={formState.subject} />
	<input type="hidden" name="description" value={formState.description} />
	<input type="hidden" name="status" value={formState.status} />
	<input type="hidden" name="priority" value={formState.priority} />
	<input type="hidden" name="dueDate" value={formState.dueDate} />
	<input type="hidden" name="accountId" value={formState.accountId} />
	<input type="hidden" name="assignedTo" value={JSON.stringify(formState.assignedTo)} />
	<input type="hidden" name="contacts" value={JSON.stringify(formState.contacts)} />
	<input type="hidden" name="teams" value={JSON.stringify(formState.teams)} />
</form>

<form
	method="POST"
	action="?/update"
	bind:this={updateForm}
	use:enhance={createEnhanceHandler('Task updated successfully')}
	class="hidden"
>
	<input type="hidden" name="taskId" value={formState.taskId} />
	<input type="hidden" name="subject" value={formState.subject} />
	<input type="hidden" name="description" value={formState.description} />
	<input type="hidden" name="status" value={formState.status} />
	<input type="hidden" name="priority" value={formState.priority} />
	<input type="hidden" name="dueDate" value={formState.dueDate} />
	<input type="hidden" name="accountId" value={formState.accountId} />
	<input type="hidden" name="assignedTo" value={JSON.stringify(formState.assignedTo)} />
	<input type="hidden" name="contacts" value={JSON.stringify(formState.contacts)} />
	<input type="hidden" name="teams" value={JSON.stringify(formState.teams)} />
</form>

<form
	method="POST"
	action="?/delete"
	bind:this={deleteForm}
	use:enhance={createEnhanceHandler('Task deleted successfully', true)}
	class="hidden"
>
	<input type="hidden" name="taskId" value={formState.taskId} />
</form>

<form
	method="POST"
	action="?/complete"
	bind:this={completeForm}
	use:enhance={createEnhanceHandler('Task completed successfully', true)}
	class="hidden"
>
	<input type="hidden" name="taskId" value={formState.taskId} />
</form>

<form
	method="POST"
	action="?/reopen"
	bind:this={reopenForm}
	use:enhance={createEnhanceHandler('Task reopened successfully', true)}
	class="hidden"
>
	<input type="hidden" name="taskId" value={formState.taskId} />
</form>
