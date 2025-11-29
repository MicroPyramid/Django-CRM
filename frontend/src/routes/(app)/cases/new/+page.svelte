<script lang="ts">
	import { enhance } from '$app/forms';
	import { FolderOpen } from '@lucide/svelte';
	export let data;
	let title = '';
	let description = '';
	let accountId = data.preSelectedAccountId || '';
	let dueDate = '';
	let assignedId = '';
	let priority = 'Normal';
	let errorMsg = '';
</script>

<div class="h-screen overflow-hidden bg-gray-50/50 dark:bg-gray-900/50">
	<div class="container mx-auto h-full max-w-2xl px-4 py-4">
		<!-- Header -->
		<div class="mb-4">
			<div class="mb-1 flex items-center gap-3">
				<div class="rounded-lg bg-blue-100 p-1.5 dark:bg-blue-900/50">
					<FolderOpen class="h-5 w-5 text-blue-600 dark:text-blue-400" />
				</div>
				<h1 class="text-xl font-bold text-gray-900 dark:text-white">Create New Case</h1>
			</div>
			<p class="text-sm text-gray-600 dark:text-gray-400">
				Create and assign a new support case to track customer issues and requests.
			</p>
		</div>

		<!-- Form Card -->
		<div
			class="overflow-y-auto rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800"
		>
			<form method="POST" action="?/create" use:enhance class="space-y-4 p-4">
				<!-- Case Details Section -->
				<div class="space-y-4">
					<div class="border-b border-gray-100 pb-2 dark:border-gray-700">
						<h2 class="mb-0.5 text-base font-semibold text-gray-900 dark:text-white">
							Case Details
						</h2>
						<p class="text-xs text-gray-500 dark:text-gray-400">Basic information about the case</p>
					</div>

					<!-- Title -->
					<div class="space-y-1">
						<label for="title" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
							Case Title <span class="text-red-500 dark:text-red-400">*</span>
						</label>
						<input
							id="title"
							type="text"
							class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 placeholder-gray-400 transition-colors focus:border-blue-500 focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-500 dark:focus:border-blue-400 dark:focus:ring-blue-400"
							placeholder="Brief description of the issue..."
							required
							bind:value={title}
							name="title"
						/>
					</div>

					<!-- Description -->
					<div class="space-y-1">
						<label
							for="description"
							class="block text-sm font-medium text-gray-700 dark:text-gray-300">Description</label
						>
						<textarea
							id="description"
							class="w-full resize-none rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 placeholder-gray-400 transition-colors focus:border-blue-500 focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-500 dark:focus:border-blue-400 dark:focus:ring-blue-400"
							rows="5"
							placeholder="Detailed description of the case..."
							bind:value={description}
							name="description"
						></textarea>
					</div>

					<!-- Account Selection -->
					<div class="space-y-1">
						<label
							for="accountId"
							class="block text-sm font-medium text-gray-700 dark:text-gray-300"
						>
							Account <span class="text-red-500 dark:text-red-400">*</span>
						</label>
						<select
							id="accountId"
							class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 transition-colors focus:border-blue-500 focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:focus:border-blue-400 dark:focus:ring-blue-400"
							bind:value={accountId}
							name="accountId"
							required
						>
							<option value="" disabled>Select an account...</option>
							{#each data.accounts as acc}
								<option value={acc.id}>{acc.name}</option>
							{/each}
						</select>
					</div>
				</div>

				<!-- Assignment Section -->
				<div class="space-y-4">
					<div class="border-b border-gray-100 pb-2 dark:border-gray-700">
						<h2 class="mb-0.5 text-base font-semibold text-gray-900 dark:text-white">
							Assignment & Priority
						</h2>
						<p class="text-xs text-gray-500 dark:text-gray-400">Set ownership and urgency level</p>
					</div>

					<div class="grid grid-cols-1 gap-4 md:grid-cols-2">
						<!-- Due Date -->
						<div class="space-y-1">
							<label
								for="dueDate"
								class="block text-sm font-medium text-gray-700 dark:text-gray-300">Due Date</label
							>
							<input
								id="dueDate"
								type="date"
								class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 transition-colors focus:border-blue-500 focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:focus:border-blue-400 dark:focus:ring-blue-400"
								bind:value={dueDate}
								name="dueDate"
							/>
						</div>

						<!-- Priority -->
						<div class="space-y-1">
							<label
								for="priority"
								class="block text-sm font-medium text-gray-700 dark:text-gray-300">Priority</label
							>
							<select
								id="priority"
								class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 transition-colors focus:border-blue-500 focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:focus:border-blue-400 dark:focus:ring-blue-400"
								bind:value={priority}
								name="priority"
							>
								<option value="Urgent">🔴 Urgent</option>
								<option value="High">🟠 High</option>
								<option value="Normal">🟡 Normal</option>
								<option value="Low">🟢 Low</option>
							</select>
						</div>
					</div>

					<!-- Assigned To -->
					<div class="space-y-1">
						<label
							for="assignedId"
							class="block text-sm font-medium text-gray-700 dark:text-gray-300"
						>
							Assign To <span class="text-red-500 dark:text-red-400">*</span>
						</label>
						<select
							id="assignedId"
							class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 transition-colors focus:border-blue-500 focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:focus:border-blue-400 dark:focus:ring-blue-400"
							bind:value={assignedId}
							name="assignedId"
							required
						>
							<option value="" disabled>Select a team member...</option>
							{#each data.users as u}
								<option value={u.user.id}>{u.user.name}</option>
							{/each}
						</select>
					</div>
				</div>

				<!-- Error Message -->
				{#if errorMsg}
					<div
						class="rounded-lg border border-red-200 bg-red-50 p-3 dark:border-red-800 dark:bg-red-900/20"
					>
						<p class="text-sm text-red-600 dark:text-red-400">{errorMsg}</p>
					</div>
				{/if}

				<!-- Form Actions -->
				<div
					class="sticky bottom-0 flex flex-col gap-2 border-t border-gray-100 bg-white pt-4 sm:flex-row dark:border-gray-700 dark:bg-gray-800"
				>
					<button
						type="submit"
						class="flex-1 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 sm:flex-none dark:bg-blue-600 dark:hover:bg-blue-500 dark:focus:ring-blue-400 dark:focus:ring-offset-gray-800"
					>
						Create Case
					</button>
					<a
						href="/cases"
						class="flex-1 rounded-lg border border-gray-200 bg-white px-4 py-2 text-center text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 sm:flex-none dark:border-gray-600 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600 dark:focus:ring-gray-400 dark:focus:ring-offset-gray-800"
					>
						Cancel
					</a>
				</div>
			</form>
		</div>
	</div>
</div>
