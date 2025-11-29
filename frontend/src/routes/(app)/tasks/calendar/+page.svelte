<script>
	import {
		Calendar,
		ChevronLeft,
		ChevronRight,
		Clock,
		AlertCircle,
		CheckCircle2,
		Circle
	} from '@lucide/svelte';

	export let data;
	let today = new Date();
	let currentDate = new Date(today);
	let selectedDate = today.toISOString().slice(0, 10);

	// Group tasks by due date (YYYY-MM-DD)
	/** @type {Record<string, Array<{id: string, title: string, description: string, type: string, status: string, priority: string}>>} */
	let tasksByDate = {};
	if (data) {
		for (const t of data.tasks) {
			if (!t.dueDate) continue;
			const date = (typeof t.dueDate === 'string' ? t.dueDate : t.dueDate?.toISOString?.())?.slice(
				0,
				10
			);
			if (!date) continue;
			if (!tasksByDate[date]) tasksByDate[date] = [];
			tasksByDate[date].push({
				id: t.id,
				title: t.subject || 'Untitled Task',
				description: t.description || '',
				type: 'CRM',
				status: t.status,
				priority: t.priority
			});
		}
	}

	// Calendar logic
	$: year = currentDate.getFullYear();
	$: month = currentDate.getMonth();
	$: monthStart = new Date(year, month, 1);
	$: monthEnd = new Date(year, month + 1, 0);
	$: startDay = monthStart.getDay();
	$: daysInMonth = monthEnd.getDate();
	$: calendar = (() => {
		let cal = [];
		for (let i = 0; i < startDay; i++) cal.push(null);
		for (let d = 1; d <= daysInMonth; d++) cal.push(new Date(Date.UTC(year, month, d)));
		while (cal.length % 7 !== 0) cal.push(null);
		return cal;
	})();

	$: monthNames = [
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

	/**
	 * Format date to YYYY-MM-DD string
	 * @param {Date} date - Date to format
	 * @returns {string} Formatted date string
	 */
	function formatDate(date) {
		return date.toISOString().slice(0, 10);
	}

	/**
	 * Check if date is today
	 * @param {Date|null} date - Date to check
	 * @returns {boolean} True if date is today
	 */
	function isToday(date) {
		return !!(date && formatDate(date) === today.toISOString().slice(0, 10));
	}

	/**
	 * Check if date has tasks
	 * @param {Date|null} date - Date to check
	 * @returns {boolean} True if date has tasks
	 */
	function hasTasks(date) {
		return !!(date && tasksByDate[formatDate(date)]?.length > 0);
	}

	/**
	 * Select a day on the calendar
	 * @param {Date|null} date - Date to select
	 */
	function selectDay(date) {
		if (date) {
			selectedDate = formatDate(date);
		}
	}

	function previousMonth() {
		currentDate = new Date(year, month - 1, 1);
	}

	function nextMonth() {
		currentDate = new Date(year, month + 1, 1);
	}

	function goToToday() {
		currentDate = new Date(today);
		selectedDate = today.toISOString().slice(0, 10);
	}

	/**
	 * Get priority icon component
	 * @param {string} priority - Task priority
	 * @returns {any} Icon component
	 */
	function getPriorityIcon(priority) {
		switch (priority?.toLowerCase()) {
			case 'high':
				return AlertCircle;
			case 'medium':
				return Clock;
			default:
				return Circle;
		}
	}

	/**
	 * Get status icon component
	 * @param {string} status - Task status
	 * @returns {any} Icon component
	 */
	function getStatusIcon(status) {
		if (status?.toLowerCase() === 'completed') return CheckCircle2;
		return Circle;
	}

	// Calculate monthly stats
	$: monthlyTasks = Object.keys(tasksByDate).filter((dateStr) => {
		const taskDate = new Date(dateStr);
		return taskDate.getFullYear() === year && taskDate.getMonth() === month;
	});

	$: totalMonthlyTasks = monthlyTasks.reduce((total, dateStr) => {
		return total + tasksByDate[dateStr].length;
	}, 0);

	$: selectedTasks = tasksByDate[selectedDate] || [];
</script>

<div
	class="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 p-4 sm:p-6 lg:p-8 dark:from-gray-900 dark:to-gray-800"
>
	<div class="mx-auto max-w-7xl">
		<!-- Header -->
		<div class="mb-8 text-center">
			<div class="mb-4 flex items-center justify-center gap-3">
				<Calendar class="h-8 w-8 text-blue-600 dark:text-blue-400" />
				<h1 class="text-3xl font-bold text-gray-900 dark:text-white">Task Calendar</h1>
			</div>
			<p class="text-gray-600 dark:text-gray-300">Manage and track your tasks with ease</p>
		</div>

		<div class="grid grid-cols-1 gap-8 lg:grid-cols-3">
			<!-- Calendar Section -->
			<div class="lg:col-span-2">
				<div
					class="overflow-hidden rounded-2xl border border-gray-100 bg-white shadow-lg dark:border-gray-700 dark:bg-gray-800"
				>
					<!-- Calendar Header -->
					<div
						class="bg-gradient-to-r from-blue-600 to-blue-700 px-6 py-4 dark:from-blue-700 dark:to-blue-800"
					>
						<div class="flex items-center justify-between">
							<div class="flex items-center gap-4">
								<button
									onclick={previousMonth}
									class="rounded-lg bg-white/10 p-2 transition-colors hover:bg-white/20 dark:bg-white/10 dark:hover:bg-white/20"
								>
									<ChevronLeft class="h-5 w-5 text-white" />
								</button>
								<h2 class="text-xl font-semibold text-white">
									{monthNames[month]}
									{year}
								</h2>
								<button
									onclick={nextMonth}
									class="rounded-lg bg-white/10 p-2 transition-colors hover:bg-white/20 dark:bg-white/10 dark:hover:bg-white/20"
								>
									<ChevronRight class="h-5 w-5 text-white" />
								</button>
							</div>
							<button
								onclick={goToToday}
								class="rounded-lg bg-white/10 px-4 py-2 font-medium text-white transition-colors hover:bg-white/20 dark:bg-white/10 dark:hover:bg-white/20"
							>
								Today
							</button>
						</div>
					</div>

					<!-- Days of Week -->
					<div
						class="grid grid-cols-7 border-b border-gray-200 bg-gray-50 dark:border-gray-600 dark:bg-gray-700"
					>
						{#each ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'] as day}
							<div
								class="border-r border-gray-200 p-4 text-center text-sm font-medium text-gray-600 last:border-r-0 dark:border-gray-600 dark:text-gray-300"
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
									class="group relative h-16 border-r border-b border-gray-200 p-2 transition-colors last:border-r-0
                         hover:bg-blue-50 sm:h-20 dark:border-gray-600 dark:hover:bg-gray-700
                         {formatDate(date) === selectedDate
										? 'bg-blue-600 text-white dark:bg-blue-700'
										: ''}
                         {isToday(date) && formatDate(date) !== selectedDate
										? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300'
										: ''}
                         {!isToday(date) && formatDate(date) !== selectedDate
										? 'text-gray-900 dark:text-gray-100'
										: ''}"
								>
									<div class="text-sm font-medium">
										{date.getDate()}
									</div>
									{#if hasTasks(date)}
										<div
											class="absolute right-1 bottom-1 h-2 w-2 rounded-full
                               {formatDate(date) === selectedDate
												? 'bg-white'
												: 'bg-blue-500 dark:bg-blue-400'}"
										></div>
										<div
											class="absolute bottom-1 left-1 text-xs font-medium
                               {formatDate(date) === selectedDate
												? 'text-white'
												: 'text-blue-600 dark:text-blue-400'}"
										>
											{tasksByDate[formatDate(date)].length}
										</div>
									{/if}
								</button>
							{:else}
								<div
									class="h-16 border-r border-b border-gray-200 bg-gray-50 sm:h-20 dark:border-gray-600 dark:bg-gray-800"
								></div>
							{/if}
						{/each}
					</div>
				</div>
			</div>

			<!-- Tasks Section -->
			<div class="lg:col-span-1">
				<div
					class="h-fit rounded-2xl border border-gray-100 bg-white shadow-lg dark:border-gray-700 dark:bg-gray-800"
				>
					<div class="border-b border-gray-200 p-6 dark:border-gray-600">
						<h3 class="mb-2 text-lg font-semibold text-gray-900 dark:text-white">
							Tasks for {new Date(selectedDate + 'T00:00:00').toLocaleDateString('en-US', {
								weekday: 'long',
								year: 'numeric',
								month: 'long',
								day: 'numeric'
							})}
						</h3>
						<div class="text-sm text-gray-600 dark:text-gray-300">
							{selectedTasks.length} task{selectedTasks.length !== 1 ? 's' : ''}
						</div>
					</div>

					<div class="p-6">
						{#if selectedTasks.length > 0}
							<div class="space-y-4">
								{#each selectedTasks as task}
									<a
										href="/tasks/{task.id}"
										class="block rounded-xl border border-gray-200 bg-gray-50 p-4 transition-colors hover:bg-gray-100 dark:border-gray-600 dark:bg-gray-700 dark:hover:bg-gray-600"
									>
										<div class="mb-2 flex items-start justify-between">
											<h4
												class="overflow-hidden font-medium text-ellipsis text-gray-900 dark:text-white"
												style="display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;"
											>
												{task.title}
											</h4>
											{#snippet statusIcon(/** @type {string} */ status)}
												{@const StatusIcon = getStatusIcon(status)}
												<StatusIcon
													class="ml-2 h-4 w-4 flex-shrink-0 text-gray-400 dark:text-gray-500"
												/>
											{/snippet}
											{@render statusIcon(task.status)}
										</div>

										{#if task.description}
											<p
												class="mb-3 overflow-hidden text-sm text-ellipsis text-gray-600 dark:text-gray-300"
												style="display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;"
											>
												{task.description}
											</p>
										{/if}

										<div class="flex items-center justify-between">
											<div class="flex items-center gap-2">
												<span
													class="inline-flex items-center gap-1 rounded-lg bg-blue-100 px-2 py-1 text-xs font-medium text-blue-700 dark:bg-blue-900 dark:text-blue-300"
												>
													{task.type}
												</span>
												<span
													class="inline-flex items-center gap-1 rounded-lg px-2 py-1 text-xs font-medium
                               {task.priority === 'Urgent'
														? 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300'
														: task.priority === 'High'
															? 'bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-300'
															: task.priority === 'Normal'
																? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300'
																: 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300'}"
												>
													{#snippet priorityIcon(/** @type {string} */ priority)}
														{@const PriorityIcon = getPriorityIcon(priority)}
														<PriorityIcon class="h-3 w-3" />
													{/snippet}
													{@render priorityIcon(task.priority)}
													{task.priority}
												</span>
											</div>
											<span class="text-xs font-medium text-gray-500 dark:text-gray-400"
												>{task.status}</span
											>
										</div>
									</a>
								{/each}
							</div>
						{:else}
							<div class="py-12 text-center">
								<Calendar class="mx-auto mb-4 h-12 w-12 text-gray-300 dark:text-gray-600" />
								<p class="text-sm text-gray-500 dark:text-gray-400">
									No tasks scheduled for this date
								</p>
								<p class="mt-1 text-xs text-gray-400 dark:text-gray-500">
									Select a different date to view tasks
								</p>
							</div>
						{/if}
					</div>
				</div>

				<!-- Quick Stats -->
				<div
					class="mt-6 rounded-2xl border border-gray-100 bg-white p-6 shadow-lg dark:border-gray-700 dark:bg-gray-800"
				>
					<h4 class="mb-4 font-semibold text-gray-900 dark:text-white">This Month</h4>
					<div class="space-y-3">
						<div class="flex items-center justify-between">
							<span class="text-sm text-gray-600 dark:text-gray-300">Total Tasks</span>
							<span class="font-medium text-gray-900 dark:text-white">
								{totalMonthlyTasks}
							</span>
						</div>
						<div class="flex items-center justify-between">
							<span class="text-sm text-gray-600 dark:text-gray-300">Days with Tasks</span>
							<span class="font-medium text-gray-900 dark:text-white">{monthlyTasks.length}</span>
						</div>
					</div>
				</div>
			</div>
		</div>
	</div>
</div>
