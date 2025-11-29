<script>
	import {
		ArrowLeft,
		Mail,
		Phone,
		Building2,
		Calendar,
		User,
		MapPin,
		Edit,
		Plus,
		ExternalLink,
		Clock,
		DollarSign,
		Target,
		CheckCircle,
		Circle,
		AlertCircle,
		Users,
		Star
	} from '@lucide/svelte';

	/** @type {{ data: import('./$types').PageData }} */
	let { data } = $props();

	const contact = data.contact;

	if (!contact) {
		throw new Error('Contact not found');
	}

	// Get primary account relationship
	const primaryAccountRel = contact.accountRelationships?.find((rel) => rel.isPrimary);
	const hasMultipleAccounts = contact.accountRelationships?.length > 1;

	/** @param {string | Date} dateStr */
	function formatDate(dateStr) {
		if (!dateStr) return 'N/A';
		return new Date(dateStr).toLocaleDateString('en-US', {
			year: 'numeric',
			month: 'short',
			day: 'numeric'
		});
	}

	/** @param {string | Date} dateStr */
	function formatDateTime(dateStr) {
		if (!dateStr) return 'N/A';
		return new Date(dateStr).toLocaleDateString('en-US', {
			year: 'numeric',
			month: 'short',
			day: 'numeric',
			hour: 'numeric',
			minute: '2-digit'
		});
	}

	/** @param {number} amount */
	function formatCurrency(amount) {
		if (!amount) return '$0';
		return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount);
	}

	/** @param {string} status */
	function getStatusColor(status) {
		const colors = {
			Completed: 'text-green-600 bg-green-50 dark:bg-green-900/20',
			'In Progress': 'text-blue-600 bg-blue-50 dark:bg-blue-900/20',
			'Not Started': 'text-gray-600 bg-gray-50 dark:bg-gray-900/20',
			CLOSED_WON: 'text-green-600 bg-green-50 dark:bg-green-900/20',
			CLOSED_LOST: 'text-red-600 bg-red-50 dark:bg-red-900/20',
			NEGOTIATION: 'text-orange-600 bg-orange-50 dark:bg-orange-900/20',
			PROPOSAL: 'text-purple-600 bg-purple-50 dark:bg-purple-900/20'
		};
		return (
			colors[/** @type {keyof typeof colors} */ (status)] ||
			'text-gray-600 bg-gray-50 dark:bg-gray-900/20'
		);
	}

	/** @param {string} priority */
	function getPriorityColor(priority) {
		const colors = {
			High: 'text-red-600 bg-red-50 dark:bg-red-900/20',
			Normal: 'text-blue-600 bg-blue-50 dark:bg-blue-900/20',
			Low: 'text-gray-600 bg-gray-50 dark:bg-gray-900/20'
		};
		return (
			colors[/** @type {keyof typeof colors} */ (priority)] ||
			'text-gray-600 bg-gray-50 dark:bg-gray-900/20'
		);
	}
</script>

<div class="min-h-screen bg-gray-50 dark:bg-gray-900">
	<!-- Header -->
	<div class="border-b border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800">
		<div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
			<div class="flex flex-col py-6 sm:flex-row sm:items-center sm:justify-between">
				<div class="flex items-center gap-4">
					{#if primaryAccountRel}
						<a
							href="/accounts/{primaryAccountRel.account.id}"
							class="flex items-center text-gray-500 transition-colors hover:text-blue-600 dark:text-gray-400 dark:hover:text-blue-400"
						>
							<ArrowLeft class="mr-2 h-5 w-5" />
							Back to {primaryAccountRel.account.name}
						</a>
					{:else}
						<a
							href="/contacts"
							class="flex items-center text-gray-500 transition-colors hover:text-blue-600 dark:text-gray-400 dark:hover:text-blue-400"
						>
							<ArrowLeft class="mr-2 h-5 w-5" />
							Back to Contacts
						</a>
					{/if}
					<div class="flex items-center gap-3">
						<div
							class="flex h-12 w-12 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-purple-600 text-lg font-semibold text-white"
						>
							{contact.firstName?.[0]}{contact.lastName?.[0]}
						</div>
						<div>
							<h1 class="text-2xl font-bold text-gray-900 dark:text-white">
								{contact.firstName}
								{contact.lastName}
							</h1>
							<p class="text-gray-500 dark:text-gray-400">{contact.title || 'Contact'}</p>
						</div>
						{#if primaryAccountRel?.isPrimary}
							<span
								class="flex items-center gap-1 rounded-full bg-blue-100 px-2 py-1 text-xs text-blue-800 dark:bg-blue-900/30 dark:text-blue-300"
							>
								<Star class="h-3 w-3" />
								Primary
							</span>
						{/if}
						{#if hasMultipleAccounts}
							<span
								class="flex items-center gap-1 rounded-full bg-purple-100 px-2 py-1 text-xs text-purple-800 dark:bg-purple-900/30 dark:text-purple-300"
							>
								<Users class="h-3 w-3" />
								{contact.accountRelationships.length} Accounts
							</span>
						{/if}
					</div>
				</div>
				<div class="mt-4 flex gap-3 sm:mt-0">
					<a
						href="/contacts/{contact.id}/edit"
						class="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-white transition-colors hover:bg-blue-700"
					>
						<Edit class="h-4 w-4" />
						Edit
					</a>
				</div>
			</div>
		</div>
	</div>

	<div class="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
		<div class="grid grid-cols-1 gap-8 lg:grid-cols-4">
			<!-- Main Content -->
			<div class="space-y-8 lg:col-span-3">
				<!-- Contact Information -->
				<div
					class="rounded-xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800"
				>
					<h2
						class="mb-6 flex items-center gap-2 text-lg font-semibold text-gray-900 dark:text-white"
					>
						<User class="h-5 w-5" />
						Contact Information
					</h2>
					<div class="grid grid-cols-1 gap-6 md:grid-cols-2">
						<div class="space-y-4">
							<div>
								<span class="text-sm font-medium text-gray-500 dark:text-gray-400">Email</span>
								{#if contact.email}
									<a
										href="mailto:{contact.email}"
										class="mt-1 flex items-center gap-2 text-blue-600 hover:underline dark:text-blue-400"
									>
										<Mail class="h-4 w-4" />
										{contact.email}
									</a>
								{:else}
									<p class="mt-1 text-gray-900 dark:text-white">N/A</p>
								{/if}
							</div>
							<div>
								<span class="text-sm font-medium text-gray-500 dark:text-gray-400">Phone</span>
								{#if contact.phone}
									<a
										href="tel:{contact.phone}"
										class="mt-1 flex items-center gap-2 text-blue-600 hover:underline dark:text-blue-400"
									>
										<Phone class="h-4 w-4" />
										{contact.phone}
									</a>
								{:else}
									<p class="mt-1 text-gray-900 dark:text-white">N/A</p>
								{/if}
							</div>
							<div>
								<span class="text-sm font-medium text-gray-500 dark:text-gray-400">Department</span>
								<p class="mt-1 text-gray-900 dark:text-white">{contact.department || 'N/A'}</p>
							</div>
						</div>
						<div class="space-y-4">
							<div>
								<span class="text-sm font-medium text-gray-500 dark:text-gray-400">Title</span>
								<p class="mt-1 text-gray-900 dark:text-white">{contact.title || 'N/A'}</p>
							</div>
							<div>
								<span class="text-sm font-medium text-gray-500 dark:text-gray-400">Owner</span>
								<p class="mt-1 text-gray-900 dark:text-white">{contact.owner?.name || 'N/A'}</p>
							</div>
							<div>
								<span class="text-sm font-medium text-gray-500 dark:text-gray-400">Created</span>
								<p class="mt-1 flex items-center gap-2 text-gray-900 dark:text-white">
									<Calendar class="h-4 w-4" />
									{formatDate(contact.createdAt)}
								</p>
							</div>
						</div>
					</div>
					{#if contact.description}
						<div class="mt-6 border-t border-gray-200 pt-6 dark:border-gray-700">
							<span class="text-sm font-medium text-gray-500 dark:text-gray-400">Description</span>
							<p class="mt-2 text-gray-900 dark:text-white">{contact.description}</p>
						</div>
					{/if}
				</div>

				<!-- Account Relationships -->
				{#if contact.accountRelationships && contact.accountRelationships.length > 0}
					<div
						class="rounded-xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800"
					>
						<h2
							class="mb-6 flex items-center gap-2 text-lg font-semibold text-gray-900 dark:text-white"
						>
							<Building2 class="h-5 w-5" />
							Account Relationships
							<span class="text-sm font-normal text-gray-500 dark:text-gray-400"
								>({contact.accountRelationships.length})</span
							>
						</h2>
						<div class="space-y-4">
							{#each contact.accountRelationships as relationship}
								<div
									class="flex items-center justify-between rounded-lg border border-gray-200 bg-gray-50 p-4 dark:border-gray-600 dark:bg-gray-700/50"
								>
									<div class="flex-1">
										<div class="flex items-center gap-3">
											<a
												href="/accounts/{relationship.account.id}"
												class="flex items-center gap-2 font-medium text-gray-900 hover:text-blue-600 dark:text-white dark:hover:text-blue-400"
											>
												<Building2 class="h-4 w-4" />
												{relationship.account.name}
											</a>
											{#if relationship.isPrimary}
												<span
													class="flex items-center gap-1 rounded-full bg-blue-100 px-2 py-0.5 text-xs text-blue-800 dark:bg-blue-900/30 dark:text-blue-300"
												>
													<Star class="h-3 w-3" />
													Primary
												</span>
											{/if}
										</div>
										<div
											class="mt-1 flex items-center gap-4 text-sm text-gray-500 dark:text-gray-400"
										>
											{#if relationship.role}
												<span class="flex items-center gap-1">
													<User class="h-3 w-3" />
													{relationship.role}
												</span>
											{/if}
											<span class="flex items-center gap-1">
												<Calendar class="h-3 w-3" />
												Since {formatDate(relationship.startDate)}
											</span>
										</div>
										{#if relationship.description}
											<p class="mt-2 text-sm text-gray-600 dark:text-gray-300">
												{relationship.description}
											</p>
										{/if}
									</div>
									<div class="text-right">
										<span class="text-xs text-gray-500 dark:text-gray-400">
											{relationship.account.type || 'Account'}
										</span>
									</div>
								</div>
							{/each}
						</div>
					</div>
				{/if}

				<!-- Address Information -->
				{#if contact.street || contact.city || contact.state || contact.country}
					<div
						class="rounded-xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800"
					>
						<h2
							class="mb-6 flex items-center gap-2 text-lg font-semibold text-gray-900 dark:text-white"
						>
							<MapPin class="h-5 w-5" />
							Address
						</h2>
						<div class="space-y-2 text-gray-900 dark:text-white">
							{#if contact.street}<p>{contact.street}</p>{/if}
							<p>
								{contact.city || ''}{contact.city && contact.state ? ', ' : ''}{contact.state || ''}
								{contact.postalCode || ''}
							</p>
							{#if contact.country}<p>{contact.country}</p>{/if}
						</div>
					</div>
				{/if}

				<!-- Recent Opportunities -->
				{#if contact.opportunities && contact.opportunities.length > 0}
					<div
						class="rounded-xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800"
					>
						<div class="mb-6 flex items-center justify-between">
							<h2
								class="flex items-center gap-2 text-lg font-semibold text-gray-900 dark:text-white"
							>
								<Target class="h-5 w-5" />
								Opportunities
							</h2>
							<a
								href="/opportunities?contact={contact.id}"
								class="flex items-center gap-1 text-sm text-blue-600 hover:underline dark:text-blue-400"
							>
								View all
								<ExternalLink class="h-3 w-3" />
							</a>
						</div>
						<div class="space-y-4">
							{#each contact.opportunities as opp}
								<div
									class="flex items-center justify-between rounded-lg bg-gray-50 p-4 dark:bg-gray-700/50"
								>
									<div class="flex-1">
										<a
											href="/opportunities/{opp.id}"
											class="font-medium text-gray-900 hover:text-blue-600 dark:text-white dark:hover:text-blue-400"
										>
											{opp.name}
										</a>
										<p class="text-sm text-gray-500 dark:text-gray-400">{opp.account?.name}</p>
									</div>
									<div class="text-right">
										<p class="flex items-center gap-1 font-medium text-gray-900 dark:text-white">
											<DollarSign class="h-4 w-4" />
											{formatCurrency(opp.amount || 0)}
										</p>
										<span
											class="inline-flex rounded-full px-2 py-1 text-xs {getStatusColor(opp.stage)}"
										>
											{opp.stage.replace('_', ' ')}
										</span>
									</div>
								</div>
							{/each}
						</div>
					</div>
				{/if}
			</div>

			<!-- Sidebar -->
			<div class="space-y-8 lg:col-span-1">
				<!-- Recent Tasks -->
				{#if contact.tasks && contact.tasks.length > 0}
					<div
						class="rounded-xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800"
					>
						<div class="mb-6 flex items-center justify-between">
							<h3
								class="flex items-center gap-2 text-lg font-semibold text-gray-900 dark:text-white"
							>
								<CheckCircle class="h-5 w-5" />
								Recent Tasks
							</h3>
							<a
								href="/tasks?contact={contact.id}"
								class="text-sm text-blue-600 hover:underline dark:text-blue-400">View all</a
							>
						</div>
						<div class="space-y-3">
							{#each contact.tasks as task}
								<div class="flex items-start gap-3 rounded-lg bg-gray-50 p-3 dark:bg-gray-700/50">
									{#if task.status === 'Completed'}
										<CheckCircle class="mt-0.5 h-4 w-4 text-green-500" />
									{:else}
										<Circle class="mt-0.5 h-4 w-4 text-gray-400" />
									{/if}
									<div class="min-w-0 flex-1">
										<p class="truncate text-sm font-medium text-gray-900 dark:text-white">
											{task.subject}
										</p>
										<div class="mt-1 flex items-center gap-2">
											<span
												class="inline-flex rounded px-2 py-0.5 text-xs {getPriorityColor(
													task.priority
												)}"
											>
												{task.priority}
											</span>
											{#if task.dueDate}
												<span
													class="flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400"
												>
													<Clock class="h-3 w-3" />
													{formatDate(task.dueDate)}
												</span>
											{/if}
										</div>
									</div>
								</div>
							{/each}
						</div>
					</div>
				{/if}

				<!-- Upcoming Events -->
				{#if contact.events && contact.events.length > 0}
					<div
						class="rounded-xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800"
					>
						<div class="mb-6 flex items-center justify-between">
							<h3
								class="flex items-center gap-2 text-lg font-semibold text-gray-900 dark:text-white"
							>
								<Calendar class="h-5 w-5" />
								Recent Events
							</h3>
							<a
								href="/events?contact={contact.id}"
								class="text-sm text-blue-600 hover:underline dark:text-blue-400">View all</a
							>
						</div>
						<div class="space-y-3">
							{#each contact.events as event}
								<div class="rounded-lg bg-gray-50 p-3 dark:bg-gray-700/50">
									<p class="text-sm font-medium text-gray-900 dark:text-white">{event.subject}</p>
									<p class="mt-1 flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400">
										<Calendar class="h-3 w-3" />
										{formatDateTime(event.startDate)}
									</p>
									{#if event.location}
										<p class="flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400">
											<MapPin class="h-3 w-3" />
											{event.location}
										</p>
									{/if}
								</div>
							{/each}
						</div>
					</div>
				{/if}
			</div>
		</div>
	</div>
</div>
