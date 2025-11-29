<script>
	import { goto } from '$app/navigation';
	import { enhance } from '$app/forms';
	import { ArrowLeft, Edit3, Calendar, User, Building2, MessageSquare, Send } from '@lucide/svelte';

	export let data;
	/** @type {any} */
	export let form;

	// Reactive assignment for task to allow modifications in edit mode
	/** @type {any} */
	$: task = data.task;
	// Comments are now part of the task object from the server

	let newComment = '';

	// The addComment function is no longer needed here,
	// form submission with `enhance` will handle it.

	// Helper to format date for display, if not already a string
	/**
	 * @param {string | Date | null} dateString - The date to format
	 * @returns {string} Formatted date string
	 */
	function formatDate(dateString) {
		if (!dateString) return 'N/A';
		// If it's already YYYY-MM-DD, it's fine. Otherwise, format it.
		try {
			return new Date(dateString).toLocaleDateString(undefined, {
				year: 'numeric',
				month: 'long',
				day: 'numeric'
			});
		} catch (e) {
			return typeof dateString === 'string' ? dateString : 'N/A'; // Fallback to original string if not a valid date
		}
	}
</script>

<div class="min-h-screen bg-gray-50 dark:bg-gray-900">
	<div class="mx-auto max-w-4xl p-3 sm:p-4 lg:p-6">
		<!-- Header -->
		<div class="mb-6">
			<div class="flex items-center justify-between">
				<div class="flex items-center gap-3">
					<button
						onclick={() => goto('/tasks/list')}
						class="flex h-8 w-8 items-center justify-center rounded-lg border border-gray-200 bg-white text-gray-600 transition-colors hover:bg-gray-50 hover:text-gray-900 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-400 dark:hover:bg-gray-700 dark:hover:text-gray-100"
						aria-label="Back to tasks"
					>
						<ArrowLeft class="h-4 w-4" />
					</button>
					<div>
						<h1 class="text-xl font-bold text-gray-900 sm:text-2xl dark:text-white">
							Task Details
						</h1>
						<p class="text-sm text-gray-600 dark:text-gray-400">View and manage task information</p>
					</div>
				</div>
				<button
					class="flex items-center gap-2 rounded-lg bg-blue-600 px-3 py-2 text-sm font-medium text-white shadow-sm transition-colors hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600"
					onclick={() => task && goto(`/tasks/${task.id}/edit`)}
				>
					<Edit3 class="h-4 w-4" />
					<span class="hidden sm:inline">Edit</span>
				</button>
			</div>
		</div>

		<!-- Task Detail Card -->
		{#if task}
			<div
				class="mb-6 overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800"
			>
				<!-- Task Header -->
				<div class="border-b border-gray-100 p-4 dark:border-gray-700">
					<div class="mb-3 flex flex-wrap items-center gap-2">
						<span
							class="inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium
              {task.status === 'Completed'
								? 'border border-green-200 bg-green-50 text-green-700 dark:border-green-800 dark:bg-green-900/20 dark:text-green-400'
								: ''}
              {task.status === 'In Progress'
								? 'border border-amber-200 bg-amber-50 text-amber-700 dark:border-amber-800 dark:bg-amber-900/20 dark:text-amber-400'
								: ''}
              {task.status === 'New'
								? 'border border-blue-200 bg-blue-50 text-blue-700 dark:border-blue-800 dark:bg-blue-900/20 dark:text-blue-400'
								: ''}"
						>
							{task.status}
						</span>
						<span
							class="inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium
              {task.priority === 'High'
								? 'border border-red-200 bg-red-50 text-red-700 dark:border-red-800 dark:bg-red-900/20 dark:text-red-400'
								: ''}
              {task.priority === 'Medium'
								? 'border border-blue-200 bg-blue-50 text-blue-700 dark:border-blue-800 dark:bg-blue-900/20 dark:text-blue-400'
								: ''}
              {task.priority === 'Low'
								? 'border border-slate-200 bg-slate-50 text-slate-700 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-300'
								: ''}"
						>
							{task.priority}
						</span>
						<div class="ml-auto flex items-center gap-1.5 text-xs text-gray-600 dark:text-gray-400">
							<Calendar class="h-3.5 w-3.5" />
							<span>Due {formatDate(task.dueDate)}</span>
						</div>
					</div>

					<h2 class="mb-2 text-lg font-semibold text-gray-900 sm:text-xl dark:text-white">
						{task.title}
					</h2>

					{#if task.description}
						<p class="text-sm leading-relaxed text-gray-700 dark:text-gray-300">
							{task.description}
						</p>
					{:else}
						<p class="text-sm text-gray-500 italic dark:text-gray-400">No description provided</p>
					{/if}
				</div>

				<!-- Task Meta Information -->
				<div class="bg-gray-50 p-4 dark:bg-gray-700/50">
					<div class="grid grid-cols-1 gap-4 md:grid-cols-2">
						<!-- Owner -->
						<div class="space-y-1.5">
							<div
								class="flex items-center gap-1.5 text-xs font-medium text-gray-600 dark:text-gray-400"
							>
								<User class="h-3.5 w-3.5" />
								<span>Task Owner</span>
							</div>
							<div class="flex items-center gap-2.5">
								{#if task.owner?.profilePhoto}
									<img
										src={task.owner.profilePhoto}
										alt={task.owner.name}
										class="h-8 w-8 rounded-full border border-white shadow-sm dark:border-gray-600"
										referrerpolicy="no-referrer"
									/>
								{:else}
									<div
										class="flex h-8 w-8 items-center justify-center rounded-full border border-white bg-blue-100 shadow-sm dark:border-gray-600 dark:bg-blue-900/30"
									>
										<span class="text-xs font-medium text-blue-700 dark:text-blue-400">
											{task.owner?.name?.charAt(0) || 'U'}
										</span>
									</div>
								{/if}
								<div>
									<div class="text-sm font-medium text-gray-900 dark:text-white">
										{task.owner?.name || 'Unassigned'}
									</div>
									<div class="text-xs text-gray-500 dark:text-gray-400">Owner</div>
								</div>
							</div>
						</div>

						<!-- Account -->
						<div class="space-y-1.5">
							<div
								class="flex items-center gap-1.5 text-xs font-medium text-gray-600 dark:text-gray-400"
							>
								<Building2 class="h-3.5 w-3.5" />
								<span>Related Account</span>
							</div>
							<div class="flex items-center gap-2.5">
								<div
									class="flex h-8 w-8 items-center justify-center rounded-full bg-gray-100 dark:bg-gray-600"
								>
									<Building2 class="h-4 w-4 text-gray-500 dark:text-gray-400" />
								</div>
								<div>
									<div class="text-sm font-medium text-gray-900 dark:text-white">
										{task.account?.name || 'No account assigned'}
									</div>
									<div class="text-xs text-gray-500 dark:text-gray-400">Account</div>
								</div>
							</div>
						</div>
					</div>
				</div>
			</div>

			<!-- Comments Section -->
			<div
				class="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800"
			>
				<div class="border-b border-gray-100 p-4 dark:border-gray-700">
					<div class="flex items-center gap-2">
						<MessageSquare class="h-4 w-4 text-gray-600 dark:text-gray-400" />
						<h2 class="text-base font-semibold text-gray-900 dark:text-white">Comments</h2>
						{#if task.comments && task.comments.length > 0}
							<span class="text-xs text-gray-500 dark:text-gray-400">({task.comments.length})</span>
						{/if}
					</div>
				</div>

				<div class="p-4">
					{#if form?.message}
						<div
							class="mb-4 rounded-lg p-3 {form.success === false
								? 'border border-red-200 bg-red-50 text-red-700 dark:border-red-800 dark:bg-red-900/20 dark:text-red-400'
								: 'border border-green-200 bg-green-50 text-green-700 dark:border-green-800 dark:bg-green-900/20 dark:text-green-400'}"
						>
							<p class="text-xs font-medium">{form.message}</p>
						</div>
					{/if}

					{#if form?.fieldError && Array.isArray(form.fieldError) && form.fieldError.includes('commentBody')}
						{@const formData = /** @type {any} */ (form)}
						{#if 'commentBody' in formData}
							{@const _ = newComment = /** @type {string} */ (formData.commentBody || '')}
						{/if}
					{/if}

					<!-- Comments List -->
					<div class="mb-6 space-y-3">
						{#if task.comments && task.comments.length > 0}
							{#each task.comments as c (c.id || c.createdAt)}
								<div
									class="flex gap-3 rounded-lg border border-gray-100 bg-gray-50 p-3 dark:border-gray-600 dark:bg-gray-700/50"
								>
									{#if c.author.profilePhoto}
										<img
											src={c.author.profilePhoto}
											alt={c.author.name}
											class="h-8 w-8 flex-shrink-0 rounded-full border border-gray-200 dark:border-gray-600"
											referrerpolicy="no-referrer"
										/>
									{:else}
										<div
											class="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full border border-gray-200 bg-blue-100 dark:border-gray-600 dark:bg-blue-900/30"
										>
											<span class="text-xs font-medium text-blue-700 dark:text-blue-400">
												{c.author?.name?.charAt(0) || 'U'}
											</span>
										</div>
									{/if}
									<div class="min-w-0 flex-1">
										<div class="mb-1 flex items-center gap-2">
											<span class="text-sm font-medium text-gray-900 dark:text-white"
												>{c.author.name}</span
											>
											<span class="text-xs text-gray-500 dark:text-gray-400"
												>{new Date(c.createdAt).toLocaleString()}</span
											>
										</div>
										<div class="text-sm leading-relaxed text-gray-700 dark:text-gray-300">
											{c.body}
										</div>
									</div>
								</div>
							{/each}
						{:else}
							<div class="py-6 text-center">
								<MessageSquare class="mx-auto mb-2 h-8 w-8 text-gray-300 dark:text-gray-600" />
								<p class="text-sm font-medium text-gray-500 dark:text-gray-400">No comments yet</p>
								<p class="text-xs text-gray-400 dark:text-gray-500">
									Be the first to add a comment
								</p>
							</div>
						{/if}
					</div>

					<!-- Add Comment Form -->
					<form method="POST" action="?/addComment" use:enhance class="space-y-3">
						<div>
							<label
								for="commentBody"
								class="mb-1.5 block text-xs font-medium text-gray-700 dark:text-gray-300"
							>
								Add a comment
							</label>
							<textarea
								id="commentBody"
								name="commentBody"
								class="w-full resize-none rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 placeholder-gray-500 transition-colors focus:border-transparent focus:ring-2 focus:ring-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 dark:focus:ring-blue-400"
								rows="2"
								placeholder="Share your thoughts or updates..."
								bind:value={newComment}
								required
							></textarea>
						</div>
						<div class="flex justify-end">
							<button
								type="submit"
								class="flex items-center gap-1.5 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-sm transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-blue-500 dark:hover:bg-blue-600"
								disabled={!newComment.trim()}
							>
								<Send class="h-3.5 w-3.5" />
								Add Comment
							</button>
						</div>
					</form>
				</div>
			</div>
		{/if}
	</div>
</div>
