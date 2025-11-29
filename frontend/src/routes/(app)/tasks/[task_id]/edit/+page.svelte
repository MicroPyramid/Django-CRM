<script>
	import { enhance } from '$app/forms';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { X, Save, Calendar, User, Building, AlertCircle, CheckCircle } from '@lucide/svelte';

	/** @type {import('./$types').PageData} */
	export let data;

	/** @type {any} */
	export let form;

	// Reactive task data for the form
	let task = { ...data.task }; // Create a copy to avoid mutating prop directly initially

	// Ensure dueDate is in YYYY-MM-DD for the input, or empty string if null
	let dueDateString = '';
	if (task.dueDate) {
		/** @type {any} */
		const dateValue = task.dueDate;
		if (typeof dateValue === 'string') {
			dueDateString = dateValue.split('T')[0];
		} else if (dateValue instanceof Date) {
			dueDateString = dateValue.toISOString().split('T')[0];
		}
	}
	task = { ...task, dueDate: dueDateString };

	const users = data.users;
	const accounts = data.accounts;

	function handleCancel() {
		goto(`/tasks/${data.task.id}`);
	}
</script>

<div class="min-h-screen bg-gray-50 py-8 dark:bg-gray-900">
	<div class="mx-auto max-w-3xl px-4 sm:px-6 lg:px-8">
		<!-- Header -->
		<div
			class="mb-6 rounded-2xl border border-gray-100 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800"
		>
			<div class="border-b border-gray-100 px-6 py-4 dark:border-gray-700">
				<div class="flex items-center justify-between">
					<div class="flex items-center space-x-3">
						<div
							class="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-100 dark:bg-blue-900"
						>
							<CheckCircle class="h-5 w-5 text-blue-600 dark:text-blue-400" />
						</div>
						<div>
							<h1 class="text-xl font-semibold text-gray-900 dark:text-white">Edit Task</h1>
							<p class="text-sm text-gray-500 dark:text-gray-400">
								Update task details and settings
							</p>
						</div>
					</div>
					<button
						type="button"
						onclick={handleCancel}
						class="flex h-10 w-10 items-center justify-center rounded-xl bg-gray-100 transition-colors duration-200 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600"
						aria-label="Close"
					>
						<X class="h-5 w-5 text-gray-600 dark:text-gray-300" />
					</button>
				</div>
			</div>
		</div>

		<!-- Form -->
		<form method="POST" action="?/update" use:enhance class="space-y-6">
			<!-- Error Messages -->
			{#if form?.message || form?.fieldError}
				<div
					class="rounded-2xl border border-red-200 bg-white shadow-sm dark:border-red-800 dark:bg-gray-800"
				>
					<div class="p-6">
						<div class="flex items-start space-x-3">
							<AlertCircle class="mt-0.5 h-5 w-5 flex-shrink-0 text-red-500 dark:text-red-400" />
							<div class="flex-1">
								{#if form?.message}
									<p class="font-medium text-red-700 dark:text-red-300">{form.message}</p>
								{/if}
								{#if form?.fieldError}
									<p class="text-red-700 dark:text-red-300">
										Error with field '{form.fieldError[0]}': {form.fieldError[1]}
									</p>
								{/if}
							</div>
						</div>
					</div>
				</div>
			{/if}

			<!-- Main Form Content -->
			<div
				class="rounded-2xl border border-gray-100 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800"
			>
				<div class="space-y-6 p-6">
					<!-- Subject -->
					<div class="space-y-2">
						<label
							class="block text-sm font-semibold text-gray-900 dark:text-white"
							for="task-subject"
						>
							Subject <span class="text-red-500 dark:text-red-400">*</span>
						</label>
						<input
							type="text"
							id="task-subject"
							name="subject"
							class="h-12 w-full rounded-xl border border-gray-200 bg-gray-50 px-4 text-gray-900 placeholder-gray-500 transition-all duration-200 focus:border-transparent focus:bg-white focus:ring-2 focus:ring-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 dark:focus:bg-gray-600 dark:focus:ring-blue-400"
							bind:value={task.subject}
							required
							placeholder="Enter task subject"
						/>
					</div>

					<!-- Description -->
					<div class="space-y-2">
						<label
							class="block text-sm font-semibold text-gray-900 dark:text-white"
							for="task-description"
						>
							Description
						</label>
						<textarea
							id="task-description"
							name="description"
							class="w-full resize-none rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 text-gray-900 placeholder-gray-500 transition-all duration-200 focus:border-transparent focus:bg-white focus:ring-2 focus:ring-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 dark:focus:bg-gray-600 dark:focus:ring-blue-400"
							rows="4"
							bind:value={task.description}
							placeholder="Add task description..."
						></textarea>
					</div>

					<!-- Status and Priority -->
					<div class="grid grid-cols-1 gap-6 md:grid-cols-2">
						<div class="space-y-2">
							<label
								class="block text-sm font-semibold text-gray-900 dark:text-white"
								for="task-status"
							>
								Status
							</label>
							<select
								id="task-status"
								name="status"
								class="h-12 w-full rounded-xl border border-gray-200 bg-gray-50 px-4 text-gray-900 transition-all duration-200 focus:border-transparent focus:bg-white focus:ring-2 focus:ring-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:focus:bg-gray-600 dark:focus:ring-blue-400"
								bind:value={task.status}
							>
								<option>New</option>
								<option>In Progress</option>
								<option>Completed</option>
							</select>
						</div>
						<div class="space-y-2">
							<label
								class="block text-sm font-semibold text-gray-900 dark:text-white"
								for="task-priority"
							>
								Priority
							</label>
							<select
								id="task-priority"
								name="priority"
								class="h-12 w-full rounded-xl border border-gray-200 bg-gray-50 px-4 text-gray-900 transition-all duration-200 focus:border-transparent focus:bg-white focus:ring-2 focus:ring-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:focus:bg-gray-600 dark:focus:ring-blue-400"
								bind:value={task.priority}
							>
								<option>High</option>
								<option>Medium</option>
								<option>Low</option>
							</select>
						</div>
					</div>

					<!-- Due Date and Owner -->
					<div class="grid grid-cols-1 gap-6 md:grid-cols-2">
						<div class="space-y-2">
							<label
								class="block text-sm font-semibold text-gray-900 dark:text-white"
								for="task-duedate"
							>
								<div class="flex items-center space-x-2">
									<Calendar class="h-4 w-4" />
									<span>Due Date</span>
								</div>
							</label>
							<input
								type="date"
								id="task-duedate"
								name="dueDate"
								class="h-12 w-full rounded-xl border border-gray-200 bg-gray-50 px-4 text-gray-900 transition-all duration-200 focus:border-transparent focus:bg-white focus:ring-2 focus:ring-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:focus:bg-gray-600 dark:focus:ring-blue-400"
								bind:value={task.dueDate}
							/>
						</div>
						<div class="space-y-2">
							<label
								class="block text-sm font-semibold text-gray-900 dark:text-white"
								for="task-owner"
							>
								<div class="flex items-center space-x-2">
									<User class="h-4 w-4" />
									<span>Owner <span class="text-red-500 dark:text-red-400">*</span></span>
								</div>
							</label>
							<select
								id="task-owner"
								name="ownerId"
								class="h-12 w-full rounded-xl border border-gray-200 bg-gray-50 px-4 text-gray-900 transition-all duration-200 focus:border-transparent focus:bg-white focus:ring-2 focus:ring-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:focus:bg-gray-600 dark:focus:ring-blue-400"
								bind:value={task.ownerId}
								required
							>
								{#each users as user}
									<option value={user.id}>{user.name}</option>
								{/each}
							</select>
						</div>
					</div>

					<!-- Account -->
					<div class="space-y-2">
						<label
							class="block text-sm font-semibold text-gray-900 dark:text-white"
							for="task-account"
						>
							<div class="flex items-center space-x-2">
								<Building class="h-4 w-4" />
								<span>Account</span>
								<span class="text-xs font-normal text-gray-500 dark:text-gray-400">(Optional)</span>
							</div>
						</label>
						<select
							id="task-account"
							name="accountId"
							class="h-12 w-full rounded-xl border border-gray-200 bg-gray-50 px-4 text-gray-900 transition-all duration-200 focus:border-transparent focus:bg-white focus:ring-2 focus:ring-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:focus:bg-gray-600 dark:focus:ring-blue-400"
							bind:value={task.accountId}
						>
							<option value={null}>No account selected</option>
							{#each accounts as acc}
								<option value={acc.id}>{acc.name}</option>
							{/each}
						</select>
					</div>
				</div>
			</div>

			<!-- Action Buttons -->
			<div
				class="rounded-2xl border border-gray-100 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800"
			>
				<div class="px-6 py-4">
					<div class="flex justify-end space-x-3">
						<button
							type="button"
							class="flex h-11 items-center space-x-2 rounded-xl bg-gray-100 px-6 font-medium text-gray-700 transition-colors duration-200 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-200 dark:hover:bg-gray-600"
							onclick={handleCancel}
						>
							<X class="h-4 w-4" />
							<span>Cancel</span>
						</button>
						<button
							type="submit"
							class="flex h-11 items-center space-x-2 rounded-xl bg-blue-600 px-6 font-medium text-white shadow-sm transition-colors duration-200 hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600"
						>
							<Save class="h-4 w-4" />
							<span>Save Changes</span>
						</button>
					</div>
				</div>
			</div>
		</form>
	</div>
</div>
