<script lang="ts">
	import {
		Briefcase,
		Edit3,
		Trash2,
		Clock,
		User,
		Building,
		Calendar,
		AlertCircle,
		MessageCircle,
		Send,
		CheckCircle,
		RotateCcw,
		XCircle
	} from '@lucide/svelte';

	export let data;
	let comment = '';
	let errorMsg = '';

	function getPriorityColor(priority: string) {
		switch (priority) {
			case 'Urgent':
				return 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 border-red-200 dark:border-red-800';
			case 'High':
				return 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300 border-orange-200 dark:border-orange-800';
			case 'Normal':
				return 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300 border-yellow-200 dark:border-yellow-800';
			case 'Low':
				return 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 border-green-200 dark:border-green-800';
			default:
				return 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 border-gray-200 dark:border-gray-700';
		}
	}

	function getStatusColor(status: string) {
		switch (status) {
			case 'OPEN':
				return 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 border-blue-200 dark:border-blue-800';
			case 'IN_PROGRESS':
				return 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300 border-orange-200 dark:border-orange-800';
			case 'CLOSED':
				return 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 border-gray-200 dark:border-gray-700';
			default:
				return 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 border-gray-200 dark:border-gray-700';
		}
	}

	function getStatusIcon(status: string) {
		switch (status) {
			case 'OPEN':
				return AlertCircle;
			case 'IN_PROGRESS':
				return RotateCcw;
			case 'CLOSED':
				return CheckCircle;
			default:
				return AlertCircle;
		}
	}

	// Reactive declarations for components
	$: StatusIcon = getStatusIcon(data.caseItem.status);
</script>

<section class="min-h-screen bg-gray-50 dark:bg-gray-900">
	<div class="container mx-auto max-w-5xl p-4">
		<!-- Header -->
		<div
			class="mb-6 rounded-lg border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800"
		>
			<div class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
				<div class="flex items-start gap-4">
					<div class="rounded-lg bg-blue-50 p-3 dark:bg-blue-900/30">
						<Briefcase class="h-6 w-6 text-blue-600 dark:text-blue-400" />
					</div>
					<div>
						<h1 class="mb-2 text-2xl font-bold text-gray-900 dark:text-white">
							{data.caseItem.subject}
						</h1>
						<p class="text-sm text-gray-600 dark:text-gray-400">Case #{data.caseItem.caseNumber}</p>
					</div>
				</div>
				<div class="flex gap-3">
					<a
						href="/cases/{data.caseItem.id}/edit"
						class="inline-flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-700 transition-colors hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-200 dark:hover:bg-gray-600"
					>
						<Edit3 class="h-4 w-4" />
						Edit
					</a>
				</div>
			</div>
		</div>

		<div class="grid grid-cols-1 gap-6 lg:grid-cols-3">
			<!-- Main Content -->
			<div class="space-y-6 lg:col-span-2">
				<!-- Case Details -->
				<div
					class="rounded-lg border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800"
				>
					<h2 class="mb-4 text-lg font-semibold text-gray-900 dark:text-white">Case Information</h2>

					{#if data.caseItem.description}
						<div class="mb-6">
							<h3 class="mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">Description</h3>
							<p class="leading-relaxed text-gray-600 dark:text-gray-400">
								{data.caseItem.description}
							</p>
						</div>
					{/if}

					<div class="grid grid-cols-1 gap-6 md:grid-cols-2">
						<div class="space-y-4">
							<div class="flex items-center gap-3">
								<Building class="h-4 w-4 text-gray-400 dark:text-gray-500" />
								<div>
									<p class="text-sm font-medium text-gray-700 dark:text-gray-300">Account</p>
									<p class="text-gray-900 dark:text-white">
										{data.caseItem.account?.name || 'Not assigned'}
									</p>
								</div>
							</div>

							<div class="flex items-center gap-3">
								<User class="h-4 w-4 text-gray-400 dark:text-gray-500" />
								<div>
									<p class="text-sm font-medium text-gray-700 dark:text-gray-300">Assigned to</p>
									<p class="text-gray-900 dark:text-white">
										{data.caseItem.owner?.name || 'Unassigned'}
									</p>
								</div>
							</div>
						</div>

						<div class="space-y-4">
							{#if data.caseItem.dueDate}
								<div class="flex items-center gap-3">
									<Calendar class="h-4 w-4 text-gray-400 dark:text-gray-500" />
									<div>
										<p class="text-sm font-medium text-gray-700 dark:text-gray-300">Due Date</p>
										<p class="text-gray-900 dark:text-white">
											{new Date(data.caseItem.dueDate).toLocaleDateString()}
										</p>
									</div>
								</div>
							{/if}

							<div class="flex items-center gap-3">
								<Clock class="h-4 w-4 text-gray-400 dark:text-gray-500" />
								<div>
									<p class="text-sm font-medium text-gray-700 dark:text-gray-300">Created</p>
									<p class="text-gray-900 dark:text-white">
										{new Date(data.caseItem.createdAt).toLocaleDateString()}
									</p>
								</div>
							</div>
						</div>
					</div>
				</div>

				<!-- Comments Section -->
				<div
					class="rounded-lg border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800"
				>
					<div class="mb-6 flex items-center gap-2">
						<MessageCircle class="h-5 w-5 text-gray-600 dark:text-gray-400" />
						<h2 class="text-lg font-semibold text-gray-900 dark:text-white">Comments</h2>
						<span class="text-sm text-gray-500 dark:text-gray-400"
							>({data.caseItem.comments?.length || 0})</span
						>
					</div>

					<!-- Comments List -->
					<div class="mb-6 space-y-4">
						{#if data.caseItem.comments && data.caseItem.comments.length}
							{#each data.caseItem.comments as c}
								<div
									class="rounded-lg border border-gray-100 bg-gray-50 p-4 dark:border-gray-600 dark:bg-gray-700/50"
								>
									<div class="flex items-start gap-3">
										<div
											class="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-blue-100 dark:bg-blue-900/30"
										>
											<span class="text-sm font-semibold text-blue-700 dark:text-blue-300">
												{c.author?.name?.[0]?.toUpperCase() || 'U'}
											</span>
										</div>
										<div class="min-w-0 flex-1">
											<div class="mb-1 flex items-center gap-2">
												<p class="font-medium text-gray-900 dark:text-white">
													{c.author?.name || 'Unknown User'}
												</p>
												<span class="text-gray-400 dark:text-gray-500">•</span>
												<p class="text-sm text-gray-500 dark:text-gray-400">
													{new Date(c.createdAt).toLocaleDateString()}
												</p>
											</div>
											<p class="leading-relaxed text-gray-700 dark:text-gray-300">{c.body}</p>
										</div>
									</div>
								</div>
							{/each}
						{:else}
							<div class="py-8 text-center text-gray-500 dark:text-gray-400">
								<MessageCircle class="mx-auto mb-3 h-12 w-12 text-gray-300 dark:text-gray-600" />
								<p>No comments yet. Be the first to add one!</p>
							</div>
						{/if}
					</div>

					<!-- Add Comment Form -->
					<form
						method="POST"
						action="?/comment"
						class="border-t border-gray-200 pt-4 dark:border-gray-600"
					>
						<div class="flex gap-3">
							<input
								type="text"
								name="body"
								bind:value={comment}
								placeholder="Write a comment..."
								required
								class="flex-1 rounded-lg border border-gray-300 bg-white px-4 py-3 text-gray-900 placeholder-gray-500 transition-colors focus:border-blue-500 focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 dark:focus:border-blue-400 dark:focus:ring-blue-400"
							/>
							<button
								type="submit"
								class="flex items-center gap-2 rounded-lg bg-blue-600 px-6 py-3 text-white transition-colors hover:bg-blue-700 dark:bg-blue-700 dark:hover:bg-blue-600"
							>
								<Send class="h-4 w-4" />
								Post
							</button>
						</div>
						{#if errorMsg}
							<p class="mt-2 text-sm text-red-600 dark:text-red-400">{errorMsg}</p>
						{/if}
					</form>
				</div>
			</div>

			<!-- Sidebar -->
			<div class="space-y-6">
				<!-- Status & Priority -->
				<div
					class="rounded-lg border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800"
				>
					<h3 class="mb-4 text-lg font-semibold text-gray-900 dark:text-white">
						Status & Priority
					</h3>

					<div class="space-y-4">
						<div>
							<p class="mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">Status</p>
							<div class="flex items-center gap-2">
								<StatusIcon class="h-4 w-4" />
								<span
									class="rounded-full border px-3 py-1 text-sm font-medium {getStatusColor(
										data.caseItem.status
									)}"
								>
									{data.caseItem.status.replace('_', ' ')}
								</span>
							</div>
						</div>

						<div>
							<p class="mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">Priority</p>
							<span
								class="rounded-full border px-3 py-1 text-sm font-medium {getPriorityColor(
									data.caseItem.priority
								)}"
							>
								{data.caseItem.priority}
							</span>
						</div>
					</div>
				</div>

				<!-- Activity Timeline -->
				<div
					class="rounded-lg border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800"
				>
					<h3 class="mb-4 text-lg font-semibold text-gray-900 dark:text-white">
						Activity Timeline
					</h3>

					<div class="space-y-4">
						<div class="flex items-start gap-3">
							<div
								class="mt-2 h-2 w-2 flex-shrink-0 rounded-full bg-green-500 dark:bg-green-400"
							></div>
							<div class="flex-1">
								<p class="text-sm font-medium text-gray-900 dark:text-white">Case Created</p>
								<p class="text-xs text-gray-500 dark:text-gray-400">
									{new Date(data.caseItem.createdAt).toLocaleDateString()}
								</p>
							</div>
						</div>

						{#if data.caseItem.updatedAt && data.caseItem.updatedAt !== data.caseItem.createdAt}
							<div class="flex items-start gap-3">
								<div
									class="mt-2 h-2 w-2 flex-shrink-0 rounded-full bg-yellow-500 dark:bg-yellow-400"
								></div>
								<div class="flex-1">
									<p class="text-sm font-medium text-gray-900 dark:text-white">Last Updated</p>
									<p class="text-xs text-gray-500 dark:text-gray-400">
										{new Date(data.caseItem.updatedAt).toLocaleDateString()}
									</p>
								</div>
							</div>
						{/if}

						{#if data.caseItem.closedAt}
							<div class="flex items-start gap-3">
								<div
									class="mt-2 h-2 w-2 flex-shrink-0 rounded-full bg-gray-500 dark:bg-gray-400"
								></div>
								<div class="flex-1">
									<p class="text-sm font-medium text-gray-900 dark:text-white">Case Closed</p>
									<p class="text-xs text-gray-500 dark:text-gray-400">
										{new Date(data.caseItem.closedAt).toLocaleDateString()}
									</p>
								</div>
							</div>
						{/if}
					</div>
				</div>
			</div>
		</div>
	</div>
</section>
