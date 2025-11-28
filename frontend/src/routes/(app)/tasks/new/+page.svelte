<script>
	import { goto } from '$app/navigation';
	import { enhance } from '$app/forms';
	import { page } from '$app/stores';
	import { X, Calendar, User, Building, FileText, Flag, Clock } from '@lucide/svelte';

	/** @type {{ data: import('./$types').PageData, form?: import('./$types').ActionData }} */
	let { data, form } = $props();

	// Get accountId from URL parameters
	const urlAccountId = $page.url.searchParams.get('accountId');

	// Initialize form fields. If 'form' (from a failed action) exists, use its values.
	// Otherwise, use defaults. These are bound to the inputs.
	let subject = $state(form?.subject ?? '');
	let status = $state(form?.status ?? 'New');
	let priority = $state(form?.priority ?? 'Medium');
	let dueDate = $state(form?.dueDate ?? '');
	let ownerId = $state(form?.ownerId ?? '');
	let accountId = $state(form?.accountId ?? urlAccountId ?? '');
	let description = $state(form?.description ?? '');

	// Form submission state
	let isSubmitting = $state(false);

	// Update local state if 'form' prop changes (e.g., after a failed form submission)
	$effect(() => {
		if (form) {
			subject = form.subject ?? '';
			status = form.status ?? 'New';
			priority = form.priority ?? 'Medium';
			dueDate = form.dueDate ?? '';
			ownerId = form.ownerId ?? '';
			accountId = form.accountId ?? urlAccountId ?? '';
			description = form.description ?? '';
		}
	});

	// Find the selected account name for display
	const selectedAccount = $derived(data.accounts.find((account) => account.id === accountId));

	function handleCancel() {
		// If we came from an account page, go back to it; otherwise go to tasks list
		if (urlAccountId) {
			goto(`/accounts/${urlAccountId}`);
		} else {
			goto('/tasks/list');
		}
	}
</script>

<div class="min-h-screen bg-gray-50 px-4 py-4 dark:bg-gray-900">
	<div class="mx-auto max-w-4xl">
		<!-- Header -->
		<div class="mb-4">
			<div class="flex items-center justify-between">
				<div>
					<h1 class="text-2xl font-bold text-gray-900 dark:text-white">Create New Task</h1>
					<p class="text-sm text-gray-600 dark:text-gray-300">
						{#if selectedAccount}
							Add a new task for {selectedAccount.name}
						{:else}
							Add a new task to keep track of your work
						{/if}
					</p>
				</div>
				<button
					type="button"
					class="rounded-lg p-2 text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-600 dark:text-gray-500 dark:hover:bg-gray-800 dark:hover:text-gray-300"
					onclick={handleCancel}
					aria-label="Close"
				>
					<X size={20} />
				</button>
			</div>
		</div>

		<!-- Form Card -->
		<div
			class="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800"
		>
			{#if form?.error}
				<div class="border-l-4 border-red-400 bg-red-50 p-3 dark:border-red-500 dark:bg-red-900/20">
					<div class="flex">
						<div class="flex-shrink-0">
							<svg
								class="h-4 w-4 text-red-400 dark:text-red-500"
								viewBox="0 0 20 20"
								fill="currentColor"
							>
								<path
									fill-rule="evenodd"
									d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
									clip-rule="evenodd"
								/>
							</svg>
						</div>
						<div class="ml-2">
							<p class="text-sm font-medium text-red-700 dark:text-red-300">{form.error}</p>
						</div>
					</div>
				</div>
			{/if}

			<form 
				method="POST" 
				use:enhance={() => {
					isSubmitting = true;
					return async ({ update }) => {
						await update();
						isSubmitting = false;
					};
				}}
				class="p-6"
			>
				<!-- Hidden field for pre-selected account -->
				{#if urlAccountId}
					<input type="hidden" name="accountId" value={urlAccountId} />
				{/if}
				
				<div class="space-y-5">
					<!-- Task Details Section -->
					<div>
						<h2
							class="mb-4 flex items-center text-base font-semibold text-gray-900 dark:text-white"
						>
							<FileText size={18} class="mr-2 text-blue-600 dark:text-blue-400" />
							Task Details
						</h2>

						<div class="space-y-4">
							<!-- Subject -->
							<div>
								<label
									for="subject"
									class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300"
								>
									Subject <span class="text-red-500 dark:text-red-400">*</span>
								</label>
								<input
									type="text"
									id="subject"
									name="subject"
									bind:value={subject}
									class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2.5 text-sm text-gray-900 placeholder-gray-400 transition-colors focus:border-blue-500 focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-500 dark:focus:border-blue-400 dark:focus:ring-blue-400"
									placeholder="Enter task subject"
									required
								/>
							</div>

							<!-- Status, Priority, and Due Date in a grid -->
							<div class="grid grid-cols-1 gap-4 md:grid-cols-3">
								<div>
									<label
										for="status"
										class="mb-1 flex items-center text-sm font-medium text-gray-700 dark:text-gray-300"
									>
										<Clock size={14} class="mr-1 text-gray-500 dark:text-gray-400" />
										Status
									</label>
									<select
										id="status"
										name="status"
										bind:value={status}
										class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2.5 text-sm text-gray-900 transition-colors focus:border-blue-500 focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:focus:border-blue-400 dark:focus:ring-blue-400"
									>
										<option value="New">New</option>
										<option value="In Progress">In Progress</option>
										<option value="Completed">Completed</option>
									</select>
								</div>

								<div>
									<label
										for="priority"
										class="mb-1 flex items-center text-sm font-medium text-gray-700 dark:text-gray-300"
									>
										<Flag size={14} class="mr-1 text-gray-500 dark:text-gray-400" />
										Priority
									</label>
									<select
										id="priority"
										name="priority"
										bind:value={priority}
										class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2.5 text-sm text-gray-900 transition-colors focus:border-blue-500 focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:focus:border-blue-400 dark:focus:ring-blue-400"
									>
										<option value="High">High</option>
										<option value="Medium">Medium</option>
										<option value="Low">Low</option>
									</select>
								</div>

								<div>
									<label
										for="dueDate"
										class="mb-1 flex items-center text-sm font-medium text-gray-700 dark:text-gray-300"
									>
										<Calendar size={14} class="mr-1 text-gray-500 dark:text-gray-400" />
										Due Date
									</label>
									<input
										type="date"
										id="dueDate"
										name="dueDate"
										bind:value={dueDate}
										class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2.5 text-sm text-gray-900 transition-colors focus:border-blue-500 focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:focus:border-blue-400 dark:focus:ring-blue-400"
									/>
								</div>
							</div>
						</div>
					</div>

					<!-- Assignment Section -->
					<div class="border-t border-gray-200 pt-5 dark:border-gray-700">
						<h2
							class="mb-4 flex items-center text-base font-semibold text-gray-900 dark:text-white"
						>
							<User size={18} class="mr-2 text-blue-600 dark:text-blue-400" />
							Assignment
						</h2>

						<div class="grid grid-cols-1 gap-4 md:grid-cols-2">
							<!-- Owner -->
							<div>
								<label
									for="ownerId"
									class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300"
								>
									Owner <span class="text-red-500 dark:text-red-400">*</span>
								</label>
								<select
									id="ownerId"
									name="ownerId"
									bind:value={ownerId}
									class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2.5 text-sm text-gray-900 transition-colors focus:border-blue-500 focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:focus:border-blue-400 dark:focus:ring-blue-400"
									required
								>
									<option value="" disabled>Select owner</option>
									{#each data.users as user (user.id)}
										<option value={user.id}>{user.name || user.email}</option>
									{/each}
								</select>
							</div>

							<!-- Related Account -->
							<div>
								<label
									for="accountId"
									class="mb-1 flex items-center text-sm font-medium text-gray-700 dark:text-gray-300"
								>
									<Building size={14} class="mr-1 text-gray-500 dark:text-gray-400" />
									Related Account
								</label>
								{#if urlAccountId}
									<!-- Show disabled select with pre-selected account -->
									<select
										id="accountId"
										class="w-full rounded-lg border border-gray-300 bg-gray-100 px-3 py-2.5 text-sm text-gray-900 dark:border-gray-600 dark:bg-gray-600 dark:text-white"
										disabled
									>
										<option value={urlAccountId} selected>
											{selectedAccount?.name || 'Loading...'}
										</option>
									</select>
									<p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
										Account pre-selected from URL
									</p>
								{:else}
									<!-- Show normal select when no account is pre-selected -->
									<select
										id="accountId"
										name="accountId"
										bind:value={accountId}
										class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2.5 text-sm text-gray-900 transition-colors focus:border-blue-500 focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:focus:border-blue-400 dark:focus:ring-blue-400"
									>
										<option value="">Select account (optional)</option>
										{#each data.accounts as account (account.id)}
											<option value={account.id}>{account.name}</option>
										{/each}
									</select>
								{/if}
							</div>
						</div>
					</div>

					<!-- Description Section -->
					<div class="border-t border-gray-200 pt-5 dark:border-gray-700">
						<div>
							<label
								for="description"
								class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300"
							>
								Description
							</label>
							<textarea
								id="description"
								name="description"
								bind:value={description}
								class="w-full resize-none rounded-lg border border-gray-300 bg-white px-3 py-2.5 text-sm text-gray-900 placeholder-gray-400 transition-colors focus:border-blue-500 focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-500 dark:focus:border-blue-400 dark:focus:ring-blue-400"
								rows="3"
								placeholder="Enter task details and notes..."
							></textarea>
						</div>
					</div>
				</div>

				<!-- Form Actions -->
				<div
					class="mt-5 flex flex-col justify-end gap-3 border-t border-gray-200 pt-5 sm:flex-row dark:border-gray-700"
				>
					<button
						type="button"
						disabled={isSubmitting}
						class="rounded-lg border border-gray-300 bg-white px-5 py-2.5 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 focus:ring-offset-white focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed dark:border-gray-600 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600 dark:focus:ring-gray-400 dark:focus:ring-offset-gray-800"
						onclick={handleCancel}
					>
						Cancel
					</button>
					<button
						type="submit"
						disabled={isSubmitting}
						class="rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-white focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed dark:bg-blue-600 dark:hover:bg-blue-700 dark:focus:ring-blue-400 dark:focus:ring-offset-gray-800"
					>
						{#if isSubmitting}
							<svg class="inline-block w-4 h-4 mr-2 animate-spin" viewBox="0 0 24 24" fill="none">
								<circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" class="opacity-25"/>
								<path fill="currentColor" class="opacity-75" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
							</svg>
							Creating Task...
						{:else}
							Create Task
						{/if}
					</button>
				</div>
			</form>
		</div>
	</div>
</div>

<style>
	/* Add any page-specific styles if needed */
</style>
