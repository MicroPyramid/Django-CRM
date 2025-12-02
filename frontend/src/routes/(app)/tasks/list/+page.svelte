<script>
	import { enhance } from '$app/forms';
	import { invalidateAll } from '$app/navigation';
	import { tick } from 'svelte';
	import { toast } from 'svelte-sonner';
	import {
		Plus,
		ChevronLeft,
		ChevronRight,
		CheckSquare,
		Building2,
		Calendar,
		List,
		Flag,
		Circle,
		CheckCircle2,
		Clock,
		RotateCcw,
		Check,
		X,
		Trash2,
		Users,
		User,
		Zap
	} from '@lucide/svelte';
	import { PageHeader, FilterPopover } from '$lib/components/layout';
	import { Button } from '$lib/components/ui/button/index.js';
	import * as Card from '$lib/components/ui/card/index.js';
	import * as DropdownMenu from '$lib/components/ui/dropdown-menu/index.js';
	import * as Sheet from '$lib/components/ui/sheet/index.js';
	import { cn } from '$lib/utils.js';
	import { TASK_STATUSES as statuses, PRIORITIES as priorities } from '$lib/constants/filters.js';
	import { useListFilters } from '$lib/hooks';
	import { NotionTable } from '$lib/components/ui/notion-table';

	// Status and priority options with colors (matching notion style)
	const statusOptions = [
		{ value: 'New', label: 'New', color: 'bg-blue-100 text-blue-700' },
		{ value: 'In Progress', label: 'In Progress', color: 'bg-amber-100 text-amber-700' },
		{ value: 'Completed', label: 'Completed', color: 'bg-emerald-100 text-emerald-700' }
	];

	const priorityOptions = [
		{ value: 'Urgent', label: 'Urgent', color: 'bg-red-100 text-red-700' },
		{ value: 'High', label: 'High', color: 'bg-orange-100 text-orange-700' },
		{ value: 'Normal', label: 'Normal', color: 'bg-blue-100 text-blue-700' },
		{ value: 'Medium', label: 'Medium', color: 'bg-yellow-100 text-yellow-700' },
		{ value: 'Low', label: 'Low', color: 'bg-gray-100 text-gray-600' }
	];

	/**
	 * @typedef {'text' | 'email' | 'number' | 'date' | 'select' | 'checkbox' | 'relation'} ColumnType
	 * @typedef {{ key: string, label: string, type: ColumnType, width?: string, canHide?: boolean, relationIcon?: string, getValue?: (row: any) => any, options?: { value: string, label: string, color: string }[] }} TaskColumn
	 */

	/** @type {TaskColumn[]} */
	const taskColumns = [
		{ key: 'subject', label: 'Task', type: 'text', width: 'w-64', canHide: false },
		{
			key: 'account',
			label: 'Account',
			type: 'relation',
			width: 'w-40',
			relationIcon: 'building',
			getValue: (/** @type {any} */ row) => row.account
		},
		{
			key: 'assignedTo',
			label: 'Assigned To',
			type: 'relation',
			width: 'w-36',
			relationIcon: 'user',
			getValue: (/** @type {any} */ row) => {
				const assigned = row.assignedTo || [];
				if (assigned.length === 0) return null;
				if (assigned.length === 1) return assigned[0];
				return { name: `${assigned.length} users` };
			}
		},
		{ key: 'priority', label: 'Priority', type: 'select', options: priorityOptions, width: 'w-28' },
		{ key: 'status', label: 'Status', type: 'select', options: statusOptions, width: 'w-32' },
		{ key: 'dueDate', label: 'Due Date', type: 'date', width: 'w-36' }
	];

	/** @type {{ data: any }} */
	let { data } = $props();

	// Computed values
	const tasks = $derived(data.tasks || []);
	const accounts = $derived(data.allAccounts || []);
	const users = $derived(data.allUsers || []);
	const contacts = $derived(data.allContacts || []);
	const teams = $derived(data.allTeams || []);

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

	// Local data for optimistic updates
	let localTasks = $state(/** @type {any[]} */ ([]));

	$effect(() => {
		localTasks = [...filteredTasks];
	});


	// Row detail sheet state
	let sheetOpen = $state(false);
	/** @type {string | null} */
	let selectedTaskId = $state(null);


	// View mode state (list or calendar)
	/** @type {'list' | 'calendar'} */
	let viewMode = $state('list');

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
	 * NotionTable callback - handle inline row changes
	 * @param {any} row
	 * @param {string} field
	 * @param {any} value
	 */
	async function handleRowChange(row, field, value) {
		// Optimistically update local state
		localTasks = localTasks.map((t) => (t.id === row.id ? { ...t, [field]: value } : t));

		// Prepare form state and submit to server
		formState.taskId = row.id;
		formState.subject = field === 'subject' ? value : row.subject || '';
		formState.description = row.description || '';
		formState.status = field === 'status' ? value : row.status || 'New';
		formState.priority = field === 'priority' ? value : row.priority || 'Medium';
		formState.dueDate = row.dueDate ? row.dueDate.split('T')[0] : '';
		formState.accountId = row.account?.id || '';
		formState.assignedTo = (row.assignedTo || []).map((/** @type {any} */ a) => a.id);
		formState.contacts = (row.contacts || []).map((/** @type {any} */ c) => c.id);
		formState.teams = (row.teams || []).map((/** @type {any} */ t) => t.id);

		await tick();
		updateForm.requestSubmit();
	}

	/**
	 * NotionTable callback - handle row click to open sheet
	 * @param {any} row
	 */
	function handleRowClick(row) {
		openTaskSheet(row.id);
	}

	/**
	 * NotionTable callback - handle reorder
	 * @param {any[]} newData
	 */
	function handleReorder(newData) {
		localTasks = newData;
	}

	/**
	 * @param {string} dateStr
	 */
	function formatDate(dateStr) {
		if (!dateStr) return '';
		const date = new Date(dateStr);
		return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
	}

	/**
	 * @param {string} value
	 * @param {{ value: string, label: string, color: string }[]} options
	 */
	function getOptionStyle(value, options) {
		const option = options.find((o) => o.value === value);
		return option?.color ?? 'bg-gray-100 text-gray-600';
	}

	/**
	 * @param {string} value
	 * @param {{ value: string, label: string, color: string }[]} options
	 */
	function getOptionLabel(value, options) {
		const option = options.find((o) => o.value === value);
		return option?.label ?? value;
	}

	async function addNewTask() {
		// Open the sheet for creating a new task
		selectedTaskId = null;
		formState = {
			taskId: '',
			subject: '',
			description: '',
			status: 'New',
			priority: 'Medium',
			dueDate: '',
			accountId: '',
			assignedTo: [],
			contacts: [],
			teams: []
		};
		sheetOpen = true;
	}

	// Row detail sheet functions
	/**
	 * @param {string} taskId
	 */
	function openTaskSheet(taskId) {
		selectedTaskId = taskId;
		const task = localTasks.find((t) => t.id === taskId);
		if (task) {
			formState = {
				taskId: task.id,
				subject: task.subject || '',
				description: task.description || '',
				status: task.status || 'New',
				priority: task.priority || 'Medium',
				dueDate: task.dueDate ? task.dueDate.split('T')[0] : '',
				accountId: task.account?.id || '',
				assignedTo: (task.assignedTo || []).map((/** @type {any} */ a) => a.id),
				contacts: (task.contacts || []).map((/** @type {any} */ c) => c.id),
				teams: (task.teams || []).map((/** @type {any} */ t) => t.id)
			};
		}
		sheetOpen = true;
	}

	function closeTaskSheet() {
		sheetOpen = false;
		selectedTaskId = null;
	}

	/**
	 * @param {string} key
	 * @param {any} value
	 */
	function updateSelectedTaskField(key, value) {
		formState = { ...formState, [key]: value };
	}

	async function saveSelectedTask() {
		await tick();
		if (selectedTaskId) {
			updateForm.requestSubmit();
		} else {
			createForm.requestSubmit();
		}
	}

	async function deleteSelectedTask() {
		if (!selectedTaskId) return;
		if (!confirm('Are you sure you want to delete this task?')) return;
		formState.taskId = selectedTaskId;
		await tick();
		deleteForm.requestSubmit();
	}

	async function completeSelectedTask() {
		if (!selectedTaskId) return;
		formState.taskId = selectedTaskId;
		await tick();
		completeForm.requestSubmit();
	}

	async function reopenSelectedTask() {
		if (!selectedTaskId) return;
		formState.taskId = selectedTaskId;
		await tick();
		reopenForm.requestSubmit();
	}

	// Get selected task data
	const selectedTask = $derived(localTasks.find((t) => t.id === selectedTaskId));
	const isCreateMode = $derived(selectedTaskId === null && sheetOpen);
	const isCompleted = $derived(formState.status === 'Completed');

	/**
	 * Create enhance handler for form actions
	 * @param {string} successMessage
	 * @param {boolean} closeSheet
	 */
	function createEnhanceHandler(successMessage, closeSheet = false) {
		return () => {
			return async (/** @type {any} */ { result }) => {
				if (result.type === 'success') {
					toast.success(successMessage);
					if (closeSheet) {
						closeTaskSheet();
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
		for (let d = 1; d <= daysInMonth; d++)
			cal.push(new Date(Date.UTC(calendarYear, calendarMonth, d)));
		while (cal.length % 7 !== 0) cal.push(null);
		return cal;
	});

	// Group filtered tasks by due date for calendar
	const tasksByDate = $derived.by(() => {
		/** @type {Record<string, any[]>} */
		const grouped = {};
		for (const t of filteredTasks) {
			if (!t.dueDate) continue;
			const date = (
				typeof t.dueDate === 'string' ? t.dueDate : t.dueDate?.toISOString?.()
			)?.slice(0, 10);
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

	// Account options for sheet
	const accountOptions = $derived([
		{ value: '', label: 'None' },
		...accounts.map((/** @type {any} */ a) => ({ value: a.id, label: a.name }))
	]);
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

			<Button onclick={addNewTask}>
				<Plus class="mr-2 h-4 w-4" />
				New Task
			</Button>
		</div>
	{/snippet}
</PageHeader>

<div class="flex-1 space-y-4 p-4 md:p-6">
	{#if viewMode === 'list'}
		<NotionTable
			data={localTasks}
			columns={taskColumns}
			storageKey="tasks-table-columns"
			enableDragDrop={true}
			enableColumnToggle={true}
			enableNewRow={true}
			onRowChange={handleRowChange}
			onRowClick={handleRowClick}
			onAddRow={addNewTask}
			onReorder={handleReorder}
		>
			{#snippet emptyState()}
				<div class="flex flex-col items-center justify-center py-16 text-center">
					<CheckSquare class="text-muted-foreground/50 mb-4 h-12 w-12" />
					<h3 class="text-foreground text-lg font-medium">No tasks found</h3>
					<p class="text-muted-foreground mt-1 text-sm">
						Try adjusting your search criteria or create a new task.
					</p>
				</div>
			{/snippet}
		</NotionTable>
	{:else}
		<!-- Calendar View -->
		<div class="grid grid-cols-1 gap-6 lg:grid-cols-3">
			<!-- Calendar Section -->
			<div class="lg:col-span-2">
				<Card.Root>
					<!-- Calendar Header -->
					<Card.Header
						class="bg-primary flex flex-row items-center justify-between space-y-0 rounded-t-lg p-4"
					>
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
								<div
									class="text-muted-foreground border-r p-3 text-center text-sm font-medium last:border-r-0"
								>
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
											formatDateString(date) === selectedDate &&
												'bg-primary text-primary-foreground hover:bg-primary/90',
											isTodayDate(date) &&
												formatDateString(date) !== selectedDate &&
												'bg-primary/10 text-primary',
											!isTodayDate(date) &&
												formatDateString(date) !== selectedDate &&
												'text-foreground'
										)}
									>
										<div class="text-sm font-medium">
											{date.getDate()}
										</div>
										{#if hasTasksOnDate(date)}
											<div
												class={cn(
													'absolute right-1 bottom-1 h-2 w-2 rounded-full',
													formatDateString(date) === selectedDate
														? 'bg-primary-foreground'
														: 'bg-primary'
												)}
											></div>
											<div
												class={cn(
													'absolute bottom-1 left-1 text-xs font-medium',
													formatDateString(date) === selectedDate
														? 'text-primary-foreground'
														: 'text-primary'
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
										onclick={() => openTaskSheet(task.id)}
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
													class="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium {getOptionStyle(
														task.priority,
														priorityOptions
													)}"
												>
													<Flag class="h-3 w-3" />
													{task.priority}
												</span>
											{/if}
											<span
												class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium {getOptionStyle(
													task.status,
													statusOptions
												)}"
											>
												{task.status}
											</span>
										</div>
									</button>
								{/each}
							</div>
						{:else}
							<div class="py-12 text-center">
								<Calendar class="text-muted-foreground/50 mx-auto mb-4 h-12 w-12" />
								<p class="text-muted-foreground text-sm">No tasks scheduled for this date</p>
								<Button onclick={addNewTask} variant="outline" size="sm" class="mt-4">
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

<!-- Task Detail Sheet (Notion-style, same for view and edit) -->
<Sheet.Root bind:open={sheetOpen} onOpenChange={(open) => !open && closeTaskSheet()}>
	<Sheet.Content side="right" class="w-[440px] sm:max-w-[440px] p-0 overflow-hidden">
		<div class="h-full flex flex-col">
			<!-- Header with close button -->
			<div class="flex items-center justify-between px-4 py-3 border-b border-gray-100 dark:border-gray-800">
				<span class="text-sm text-gray-500">{isCreateMode ? 'New Task' : 'Task'}</span>
				<button
					onclick={closeTaskSheet}
					class="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors duration-75"
				>
					<X class="h-4 w-4 text-gray-400" />
				</button>
			</div>

			<!-- Scrollable content -->
			<div class="flex-1 overflow-y-auto">
				<!-- Title section -->
				<div class="px-6 pt-6 pb-4">
					<input
						type="text"
						bind:value={formState.subject}
						placeholder="Task title"
						class="w-full text-2xl font-semibold bg-transparent border-0 outline-none focus:ring-0 placeholder:text-gray-300 dark:placeholder:text-gray-600 {isCompleted
							? 'line-through text-gray-500'
							: ''}"
					/>
				</div>

				<!-- Properties section -->
				<div class="px-4 pb-6">
					<!-- Account property -->
					<div
						class="flex items-center min-h-[36px] px-2 -mx-2 rounded hover:bg-gray-50/60 dark:hover:bg-gray-800/60 transition-colors duration-75 group"
					>
						<div class="w-28 shrink-0 flex items-center gap-2 text-[13px] text-gray-500">
							<Building2 class="h-4 w-4 text-gray-400" />
							Account
						</div>
						<div class="flex-1 min-w-0">
							<select
								bind:value={formState.accountId}
								class="w-full px-2 py-1 text-sm bg-transparent border-0 outline-none focus:bg-gray-50 dark:focus:bg-gray-800 rounded transition-colors cursor-pointer"
							>
								{#each accountOptions as option}
									<option value={option.value}>{option.label}</option>
								{/each}
							</select>
						</div>
					</div>

					<!-- Status property (select) -->
					<div
						class="flex items-center min-h-[36px] px-2 -mx-2 rounded hover:bg-gray-50/60 dark:hover:bg-gray-800/60 transition-colors duration-75 group"
					>
						<div class="w-28 shrink-0 flex items-center gap-2 text-[13px] text-gray-500">
							<Circle class="h-4 w-4 text-gray-400" />
							Status
						</div>
						<div class="flex-1">
							<DropdownMenu.Root>
								<DropdownMenu.Trigger>
									{#snippet child({ props })}
										<button
											{...props}
											type="button"
											class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-sm {getOptionStyle(
												formState.status,
												statusOptions
											)} hover:opacity-90 transition-opacity"
										>
											<span
												class="w-2 h-2 rounded-full {getOptionStyle(formState.status, statusOptions).split(
													' '
												)[0]}"
											></span>
											{getOptionLabel(formState.status, statusOptions)}
										</button>
									{/snippet}
								</DropdownMenu.Trigger>
								<DropdownMenu.Content align="start" class="w-36">
									{#each statusOptions as option (option.value)}
										<DropdownMenu.Item
											onclick={() => updateSelectedTaskField('status', option.value)}
											class="flex items-center gap-2"
										>
											<span class="w-2 h-2 rounded-full {option.color.split(' ')[0]}"></span>
											{option.label}
											{#if formState.status === option.value}
												<Check class="h-4 w-4 ml-auto" />
											{/if}
										</DropdownMenu.Item>
									{/each}
								</DropdownMenu.Content>
							</DropdownMenu.Root>
						</div>
					</div>

					<!-- Priority property (select) -->
					<div
						class="flex items-center min-h-[36px] px-2 -mx-2 rounded hover:bg-gray-50/60 dark:hover:bg-gray-800/60 transition-colors duration-75 group"
					>
						<div class="w-28 shrink-0 flex items-center gap-2 text-[13px] text-gray-500">
							<Zap class="h-4 w-4 text-gray-400" />
							Priority
						</div>
						<div class="flex-1">
							<DropdownMenu.Root>
								<DropdownMenu.Trigger>
									{#snippet child({ props })}
										<button
											{...props}
											type="button"
											class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-sm {getOptionStyle(
												formState.priority,
												priorityOptions
											)} hover:opacity-90 transition-opacity"
										>
											<span
												class="w-2 h-2 rounded-full {getOptionStyle(
													formState.priority,
													priorityOptions
												).split(' ')[0]}"
											></span>
											{getOptionLabel(formState.priority, priorityOptions)}
										</button>
									{/snippet}
								</DropdownMenu.Trigger>
								<DropdownMenu.Content align="start" class="w-36">
									{#each priorityOptions as option (option.value)}
										<DropdownMenu.Item
											onclick={() => updateSelectedTaskField('priority', option.value)}
											class="flex items-center gap-2"
										>
											<span class="w-2 h-2 rounded-full {option.color.split(' ')[0]}"></span>
											{option.label}
											{#if formState.priority === option.value}
												<Check class="h-4 w-4 ml-auto" />
											{/if}
										</DropdownMenu.Item>
									{/each}
								</DropdownMenu.Content>
							</DropdownMenu.Root>
						</div>
					</div>

					<!-- Due Date property -->
					<div
						class="flex items-center min-h-[36px] px-2 -mx-2 rounded hover:bg-gray-50/60 dark:hover:bg-gray-800/60 transition-colors duration-75 group"
					>
						<div class="w-28 shrink-0 flex items-center gap-2 text-[13px] text-gray-500">
							<Calendar class="h-4 w-4 text-gray-400" />
							Due Date
						</div>
						<div class="flex-1 min-w-0">
							<input
								type="date"
								bind:value={formState.dueDate}
								class="w-full px-2 py-1 text-sm bg-transparent border-0 outline-none focus:bg-gray-50 dark:focus:bg-gray-800 rounded transition-colors"
							/>
						</div>
					</div>

					<!-- Assigned To property -->
					<div
						class="flex items-center min-h-[36px] px-2 -mx-2 rounded hover:bg-gray-50/60 dark:hover:bg-gray-800/60 transition-colors duration-75 group"
					>
						<div class="w-28 shrink-0 flex items-center gap-2 text-[13px] text-gray-500">
							<User class="h-4 w-4 text-gray-400" />
							Assigned To
						</div>
						<div class="flex-1 min-w-0">
							<select
								multiple
								bind:value={formState.assignedTo}
								class="w-full px-2 py-1 text-sm bg-transparent border-0 outline-none focus:bg-gray-50 dark:focus:bg-gray-800 rounded transition-colors min-h-[60px]"
							>
								{#each users as user}
									<option value={user.id}>{user.name}</option>
								{/each}
							</select>
						</div>
					</div>

					<!-- Teams property -->
					<div
						class="flex items-center min-h-[36px] px-2 -mx-2 rounded hover:bg-gray-50/60 dark:hover:bg-gray-800/60 transition-colors duration-75 group"
					>
						<div class="w-28 shrink-0 flex items-center gap-2 text-[13px] text-gray-500">
							<Users class="h-4 w-4 text-gray-400" />
							Teams
						</div>
						<div class="flex-1 min-w-0">
							<select
								multiple
								bind:value={formState.teams}
								class="w-full px-2 py-1 text-sm bg-transparent border-0 outline-none focus:bg-gray-50 dark:focus:bg-gray-800 rounded transition-colors min-h-[60px]"
							>
								{#each teams as team}
									<option value={team.id}>{team.name}</option>
								{/each}
							</select>
						</div>
					</div>

					<!-- Description -->
					<div class="mt-4 px-2 -mx-2">
						<div class="text-[13px] text-gray-500 mb-2">Description</div>
						<textarea
							bind:value={formState.description}
							placeholder="Add a description..."
							rows="4"
							class="w-full px-3 py-2 text-sm bg-gray-50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700 rounded-lg outline-none focus:ring-1 focus:ring-blue-300 transition-all resize-none placeholder:text-gray-400"
						></textarea>
					</div>

					<!-- Task metadata (only for existing tasks) -->
					{#if selectedTask && !isCreateMode}
						<div class="mt-6 pt-4 border-t border-gray-100 dark:border-gray-800">
							<div class="text-[13px] text-gray-500 mb-3">Details</div>
							<div class="space-y-2 text-sm">
								{#if selectedTask.createdBy}
									<div class="flex items-center gap-2 text-gray-600 dark:text-gray-400">
										<User class="h-3.5 w-3.5" />
										<span>Created by {selectedTask.createdBy.name}</span>
									</div>
								{/if}
								{#if selectedTask.createdAt}
									<div class="flex items-center gap-2 text-gray-600 dark:text-gray-400">
										<Clock class="h-3.5 w-3.5" />
										<span>Created {formatDate(selectedTask.createdAt)}</span>
									</div>
								{/if}
							</div>
						</div>
					{/if}
				</div>
			</div>

			<!-- Footer with actions -->
			<div class="px-4 py-3 border-t border-gray-100 dark:border-gray-800 mt-auto">
				<div class="flex items-center justify-between">
					{#if !isCreateMode}
						<button
							onclick={deleteSelectedTask}
							class="flex items-center gap-2 px-3 py-1.5 text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition-colors duration-75"
						>
							<Trash2 class="h-4 w-4" />
							Delete
						</button>
					{:else}
						<div></div>
					{/if}
					<div class="flex items-center gap-2">
						{#if !isCreateMode && selectedTask}
							{#if isCompleted}
								<Button variant="outline" size="sm" onclick={reopenSelectedTask}>
									<RotateCcw class="mr-2 h-4 w-4" />
									Reopen
								</Button>
							{:else}
								<Button variant="outline" size="sm" onclick={completeSelectedTask}>
									<CheckCircle2 class="mr-2 h-4 w-4" />
									Complete
								</Button>
							{/if}
						{/if}
						<Button size="sm" onclick={saveSelectedTask}>
							{isCreateMode ? 'Create Task' : 'Save Changes'}
						</Button>
					</div>
				</div>
			</div>
		</div>
	</Sheet.Content>
</Sheet.Root>

<!-- Hidden forms for server actions -->
<form
	method="POST"
	action="?/create"
	bind:this={createForm}
	use:enhance={createEnhanceHandler('Task created successfully', true)}
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
