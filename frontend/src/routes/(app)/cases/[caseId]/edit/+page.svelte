<script lang="ts">
	export let data;
	import { enhance } from '$app/forms';
	import { goto } from '$app/navigation';
	import {
		Save,
		X,
		AlertTriangle,
		User,
		Building,
		Calendar,
		Flag,
		FileText,
		Lock,
		Unlock
	} from '@lucide/svelte';

	let title = data.caseItem.subject;
	let description = data.caseItem.description || '';
	let accountId = data.caseItem.accountId;
	let dueDate = '';
	if (data.caseItem.dueDate) {
		const dueDateValue: any = data.caseItem.dueDate;
		if (typeof dueDateValue === 'string') {
			dueDate = dueDateValue.split('T')[0];
		} else if (dueDateValue instanceof Date) {
			dueDate = dueDateValue.toISOString().split('T')[0];
		}
	}
	let assignedId = data.caseItem.ownerId;
	let priority = data.caseItem.priority || 'Normal';
	let errorMsg = '';
	let successMsg = '';
	let loading = false;
	let showCloseConfirmation = false;
	let showReopenConfirmation = false;

	function handleCloseCase() {
		showCloseConfirmation = true;
	}

	function confirmCloseCase() {
		const form = document.getElementById('close-case-form');
		if (form && 'submit' in form && typeof form.submit === 'function') {
			form.submit();
		}
		showCloseConfirmation = false;
	}

	function cancelCloseCase() {
		showCloseConfirmation = false;
	}

	function handleReopenCase() {
		showReopenConfirmation = true;
	}

	function confirmReopenCase() {
		const form = document.getElementById('reopen-case-form');
		if (form && 'submit' in form && typeof form.submit === 'function') {
			form.submit();
		}
		showReopenConfirmation = false;
	}

	function cancelReopenCase() {
		showReopenConfirmation = false;
	}
</script>

<div class="min-h-screen bg-gray-50 py-8 dark:bg-gray-900">
	<div class="mx-auto max-w-2xl px-4 sm:px-6 lg:px-8">
		<!-- Header -->
		<div class="mb-8">
			<div class="flex items-center justify-between">
				<div>
					<h1 class="text-2xl font-bold text-gray-900 dark:text-white">Edit Case</h1>
					<p class="mt-1 text-sm text-gray-600 dark:text-gray-400">
						Update case details and assignment
					</p>
				</div>
				<div class="flex items-center gap-3">
					<button
						onclick={() => goto(`/cases/${data.caseItem.id}`)}
						class="inline-flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700 dark:focus:ring-offset-gray-900"
					>
						<X size="16" />
						Cancel
					</button>
				</div>
			</div>
		</div>

		<!-- Main Form -->
		<div
			class="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800"
		>
			<form
				method="POST"
				action="?/update"
				use:enhance={({ formData, cancel }) => {
					loading = true;
					errorMsg = '';
					successMsg = '';
					return async ({ result, update }) => {
						loading = false;
						if (result.type === 'failure') {
							errorMsg = (result.data as any)?.error || 'An error occurred';
						} else if (result.type === 'success') {
							successMsg = 'Case updated successfully!';
							// Update the data and reset form values from fresh data
							await update();
							// Re-initialize form values from updated data
							title = data.caseItem.subject;
							description = data.caseItem.description || '';
							accountId = data.caseItem.accountId;
							if (data.caseItem.dueDate) {
								const dueDateValue: any = data.caseItem.dueDate;
								if (typeof dueDateValue === 'string') {
									dueDate = dueDateValue.split('T')[0];
								} else if (dueDateValue instanceof Date) {
									dueDate = dueDateValue.toISOString().split('T')[0];
								}
							} else {
								dueDate = '';
							}
							assignedId = data.caseItem.ownerId;
							priority = data.caseItem.priority || 'Normal';
						} else {
							await update();
						}
					};
				}}
			>
				<!-- Hidden field for status -->
				<input type="hidden" name="status" value={data.caseItem.status} />
				<div class="space-y-6 p-6">
					<!-- Case Title -->
					<div class="space-y-2">
						<label
							for="title"
							class="flex items-center gap-2 text-sm font-medium text-gray-900 dark:text-white"
						>
							<FileText size="16" class="text-gray-500 dark:text-gray-400" />
							Case Title
							<span class="text-red-500 dark:text-red-400">*</span>
						</label>
						<input
							id="title"
							type="text"
							name="title"
							bind:value={title}
							required
							class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2.5 text-sm text-gray-900 placeholder-gray-500 transition-colors focus:border-blue-500 focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 dark:focus:border-blue-500"
							placeholder="Enter case title"
						/>
					</div>

					<!-- Description -->
					<div class="space-y-2">
						<label
							for="description"
							class="flex items-center gap-2 text-sm font-medium text-gray-900 dark:text-white"
						>
							<FileText size="16" class="text-gray-500 dark:text-gray-400" />
							Description
						</label>
						<textarea
							id="description"
							name="description"
							bind:value={description}
							rows="4"
							class="w-full resize-none rounded-lg border border-gray-300 bg-white px-3 py-2.5 text-sm text-gray-900 placeholder-gray-500 transition-colors focus:border-blue-500 focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 dark:focus:border-blue-500"
							placeholder="Describe the case details..."
						></textarea>
					</div>

					<!-- Account Selection -->
					<div class="space-y-2">
						<label
							for="accountId"
							class="flex items-center gap-2 text-sm font-medium text-gray-900 dark:text-white"
						>
							<Building size="16" class="text-gray-500 dark:text-gray-400" />
							Account
							<span class="text-red-500 dark:text-red-400">*</span>
						</label>
						<select
							id="accountId"
							name="accountId"
							bind:value={accountId}
							required
							class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2.5 text-sm text-gray-900 transition-colors focus:border-blue-500 focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:focus:border-blue-500"
						>
							<option value="">Select an account...</option>
							{#each data.accounts as acc}
								<option value={acc.id}>{acc.name}</option>
							{/each}
						</select>
					</div>

					<!-- Due Date and Assignment Row -->
					<div class="grid grid-cols-1 gap-6 md:grid-cols-2">
						<div class="space-y-2">
							<label
								for="dueDate"
								class="flex items-center gap-2 text-sm font-medium text-gray-900 dark:text-white"
							>
								<Calendar size="16" class="text-gray-500 dark:text-gray-400" />
								Due Date
							</label>
							<input
								id="dueDate"
								type="date"
								name="dueDate"
								bind:value={dueDate}
								class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2.5 text-sm text-gray-900 transition-colors focus:border-blue-500 focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:focus:border-blue-500"
							/>
						</div>

						<div class="space-y-2">
							<label
								for="assignedId"
								class="flex items-center gap-2 text-sm font-medium text-gray-900 dark:text-white"
							>
								<User size="16" class="text-gray-500 dark:text-gray-400" />
								Assign To
								<span class="text-red-500 dark:text-red-400">*</span>
							</label>
							<select
								id="assignedId"
								name="assignedId"
								bind:value={assignedId}
								required
								class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2.5 text-sm text-gray-900 transition-colors focus:border-blue-500 focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:focus:border-blue-500"
							>
								<option value="">Select a user...</option>
								{#each data.users as u}
									<option value={u.id}>{u.name}</option>
								{/each}
							</select>
						</div>
					</div>

					<!-- Priority -->
					<div class="space-y-2">
						<label
							for="priority"
							class="flex items-center gap-2 text-sm font-medium text-gray-900 dark:text-white"
						>
							<Flag size="16" class="text-gray-500 dark:text-gray-400" />
							Priority
						</label>
						<select
							id="priority"
							name="priority"
							bind:value={priority}
							class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2.5 text-sm text-gray-900 transition-colors focus:border-blue-500 focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:focus:border-blue-500"
						>
							<option value="Urgent">Urgent</option>
							<option value="High">High</option>
							<option value="Normal">Normal</option>
							<option value="Low">Low</option>
						</select>
					</div>

					<!-- Messages -->
					{#if errorMsg}
						<div
							class="flex items-start gap-3 rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-800 dark:bg-red-900/20"
						>
							<AlertTriangle
								size="20"
								class="mt-0.5 flex-shrink-0 text-red-500 dark:text-red-400"
							/>
							<div class="text-sm text-red-700 dark:text-red-300">{errorMsg}</div>
						</div>
					{/if}

					{#if successMsg}
						<div
							class="flex items-start gap-3 rounded-lg border border-green-200 bg-green-50 p-4 dark:border-green-800 dark:bg-green-900/20"
						>
							<div
								class="mt-0.5 flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full bg-green-500 dark:bg-green-400"
							>
								<div class="h-2 w-2 rounded-full bg-white"></div>
							</div>
							<div class="text-sm text-green-700 dark:text-green-300">{successMsg}</div>
						</div>
					{/if}
				</div>

				<!-- Form Actions -->
				<div
					class="flex flex-col gap-3 border-t border-gray-200 bg-gray-50 px-6 py-4 sm:flex-row dark:border-gray-700 dark:bg-gray-800/50"
				>
					<button
						type="submit"
						disabled={loading || data.caseItem.status === 'CLOSED'}
						class="inline-flex flex-1 items-center justify-center gap-2 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-blue-600 dark:hover:bg-blue-700 dark:focus:ring-offset-gray-800"
					>
						<Save size="16" />
						{loading
							? 'Saving...'
							: data.caseItem.status === 'CLOSED'
								? 'Case is Closed'
								: 'Save Changes'}
					</button>

					{#if data.caseItem.status === 'CLOSED'}
						<button
							type="button"
							onclick={handleReopenCase}
							class="inline-flex items-center justify-center gap-2 rounded-lg border border-green-200 bg-green-50 px-4 py-2.5 text-sm font-medium text-green-700 transition-colors hover:bg-green-100 focus:ring-2 focus:ring-green-500 focus:ring-offset-2 dark:border-green-800 dark:bg-green-900/20 dark:text-green-300 dark:hover:bg-green-900/30 dark:focus:ring-offset-gray-800"
						>
							<Unlock size="16" />
							Reopen Case
						</button>
					{:else}
						<button
							type="button"
							onclick={handleCloseCase}
							class="inline-flex items-center justify-center gap-2 rounded-lg border border-amber-200 bg-amber-50 px-4 py-2.5 text-sm font-medium text-amber-700 transition-colors hover:bg-amber-100 focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 dark:border-amber-800 dark:bg-amber-900/20 dark:text-amber-300 dark:hover:bg-amber-900/30 dark:focus:ring-offset-gray-800"
						>
							<Lock size="16" />
							Close Case
						</button>
					{/if}
				</div>
			</form>
		</div>

		<!-- Hidden Close Case Form -->
		<form id="close-case-form" method="POST" action="?/close" style="display: none;"></form>

		<!-- Hidden Reopen Case Form -->
		<form id="reopen-case-form" method="POST" action="?/reopen" style="display: none;"></form>

		<!-- Close Case Confirmation Modal -->
		{#if showCloseConfirmation}
			<div
				class="bg-opacity-50 dark:bg-opacity-70 fixed inset-0 z-50 flex items-center justify-center bg-black p-4 dark:bg-black"
			>
				<div class="w-full max-w-md rounded-lg bg-white shadow-xl dark:bg-gray-800">
					<div class="p-6">
						<div class="mb-4 flex items-center gap-3">
							<div
								class="flex h-10 w-10 items-center justify-center rounded-full bg-amber-100 dark:bg-amber-900/20"
							>
								<Lock size="20" class="text-amber-600 dark:text-amber-400" />
							</div>
							<div>
								<h3 class="text-lg font-medium text-gray-900 dark:text-white">Close Case</h3>
								<p class="text-sm text-gray-600 dark:text-gray-400">
									Are you sure you want to close this case?
								</p>
							</div>
						</div>
						<p class="mb-6 text-sm text-gray-700 dark:text-gray-300">
							This action will mark the case as closed. You can still view the case details, but it
							will no longer be active.
						</p>
						<div class="flex gap-3">
							<button
								onclick={confirmCloseCase}
								class="flex-1 rounded-lg bg-amber-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-amber-700 focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 dark:bg-amber-600 dark:hover:bg-amber-700 dark:focus:ring-offset-gray-800"
							>
								Close Case
							</button>
							<button
								onclick={cancelCloseCase}
								class="flex-1 rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600 dark:focus:ring-offset-gray-800"
							>
								Cancel
							</button>
						</div>
					</div>
				</div>
			</div>
		{/if}

		<!-- Reopen Case Confirmation Modal -->
		{#if showReopenConfirmation}
			<div
				class="bg-opacity-50 dark:bg-opacity-70 fixed inset-0 z-50 flex items-center justify-center bg-black p-4 dark:bg-black"
			>
				<div class="w-full max-w-md rounded-lg bg-white shadow-xl dark:bg-gray-800">
					<div class="p-6">
						<div class="mb-4 flex items-center gap-3">
							<div
								class="flex h-10 w-10 items-center justify-center rounded-full bg-green-100 dark:bg-green-900/20"
							>
								<Unlock size="20" class="text-green-600 dark:text-green-400" />
							</div>
							<div>
								<h3 class="text-lg font-medium text-gray-900 dark:text-white">Reopen Case</h3>
								<p class="text-sm text-gray-600 dark:text-gray-400">
									Are you sure you want to reopen this case?
								</p>
							</div>
						</div>
						<p class="mb-6 text-sm text-gray-700 dark:text-gray-300">
							This action will mark the case as active again and allow you to continue working on
							it.
						</p>
						<div class="flex gap-3">
							<button
								onclick={confirmReopenCase}
								class="flex-1 rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-green-700 focus:ring-2 focus:ring-green-500 focus:ring-offset-2 dark:bg-green-600 dark:hover:bg-green-700 dark:focus:ring-offset-gray-800"
							>
								Reopen Case
							</button>
							<button
								onclick={cancelReopenCase}
								class="flex-1 rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600 dark:focus:ring-offset-gray-800"
							>
								Cancel
							</button>
						</div>
					</div>
				</div>
			</div>
		{/if}
	</div>
</div>
