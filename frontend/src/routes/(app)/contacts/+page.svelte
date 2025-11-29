<script>
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { enhance } from '$app/forms';
	import {
		Search,
		Filter,
		Plus,
		MoreVertical,
		Eye,
		Edit,
		Trash2,
		Users,
		Mail,
		Phone,
		Building,
		Calendar,
		ChevronLeft,
		ChevronRight,
		User
	} from '@lucide/svelte';

	/** @type {{ data: import('./$types').PageData }} */
	let { data } = $props();

	let searchQuery = $state(data.search || '');
	let selectedOwner = $state(data.ownerId || '');
	let showFilters = $state(false);

	// Search functionality
	function handleSearch() {
		const params = new URLSearchParams($page.url.searchParams);
		if (searchQuery) {
			params.set('search', searchQuery);
		} else {
			params.delete('search');
		}
		params.set('page', '1');
		goto(`?${params.toString()}`);
	}

	// Filter functionality
	function applyFilters() {
		const params = new URLSearchParams($page.url.searchParams);
		if (selectedOwner) {
			params.set('owner', selectedOwner);
		} else {
			params.delete('owner');
		}
		params.set('page', '1');
		goto(`?${params.toString()}`);
	}

	function clearFilters() {
		searchQuery = '';
		selectedOwner = '';
		goto('/contacts');
	}

	// Pagination
	/** @param {number} pageNum */
	function goToPage(pageNum) {
		const params = new URLSearchParams($page.url.searchParams);
		params.set('page', pageNum.toString());
		goto(`?${params.toString()}`);
	}

	// Modal functions
	/** @param {any} contact */
	function editContact(contact) {
		goto(`/contacts/${contact.id}/edit`);
	}

	/** @param {string | Date} dateString */
	function formatDate(dateString) {
		return new Date(dateString).toLocaleDateString();
	}

	/** @param {string} phone */
	function formatPhone(phone) {
		if (!phone) return '';
		// Basic phone formatting - can be enhanced
		return phone.replace(/(\d{3})(\d{3})(\d{4})/, '($1) $2-$3');
	}
</script>

<svelte:head>
	<title>Contacts - BottleCRM</title>
</svelte:head>

<div class="min-h-screen bg-gray-50 dark:bg-gray-900">
	<!-- Header -->
	<div class="border-b border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800">
		<div class="px-4 py-6 sm:px-6 lg:px-8">
			<div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
				<div class="flex items-center gap-3">
					<div class="rounded-lg bg-blue-100 p-2 dark:bg-blue-900">
						<Users class="h-6 w-6 text-blue-600 dark:text-blue-400" />
					</div>
					<div>
						<h1 class="text-2xl font-bold text-gray-900 dark:text-white">Contacts</h1>
						<p class="text-sm text-gray-500 dark:text-gray-400">
							{data.totalCount} total contacts
						</p>
					</div>
				</div>
				<div class="flex items-center gap-3">
					<button
						onclick={() => (showFilters = !showFilters)}
						class="inline-flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 focus:ring-2 focus:ring-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600"
					>
						<Filter class="h-4 w-4" />
						Filters
					</button>
					<a
						href="/contacts/new"
						class="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:outline-none"
					>
						<Plus class="h-4 w-4" />
						Add Contact
					</a>
				</div>
			</div>

			<!-- Search Bar -->
			<div class="mt-6">
				<div class="relative">
					<Search
						class="absolute top-1/2 left-3 h-5 w-5 -translate-y-1/2 transform text-gray-400"
					/>
					<input
						type="text"
						bind:value={searchQuery}
						placeholder="Search contacts by name, email, phone, title..."
						onkeydown={(e) => e.key === 'Enter' && handleSearch()}
						class="w-full rounded-lg border border-gray-300 bg-white py-3 pr-4 pl-10 text-gray-900 placeholder-gray-500 focus:border-transparent focus:ring-2 focus:ring-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400"
					/>
					{#if searchQuery}
						<button
							onclick={() => {
								searchQuery = '';
								handleSearch();
							}}
							class="absolute top-1/2 right-3 -translate-y-1/2 transform text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
						>
							×
						</button>
					{/if}
				</div>
			</div>

			<!-- Filters Panel -->
			{#if showFilters}
				<div
					class="mt-4 rounded-lg border border-gray-200 bg-gray-50 p-4 dark:border-gray-600 dark:bg-gray-700"
				>
					<div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
						<div>
							<label
								for="ownerSelect"
								class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
							>
								Owner
							</label>
							<select
								id="ownerSelect"
								bind:value={selectedOwner}
								class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-gray-900 focus:ring-2 focus:ring-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-800 dark:text-white"
							>
								<option value="">All owners</option>
								{#each data.owners as owner}
									<option value={owner.id}>{owner.name || owner.email}</option>
								{/each}
							</select>
						</div>
					</div>
					<div class="mt-4 flex gap-2">
						<button
							onclick={applyFilters}
							class="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:outline-none"
						>
							Apply Filters
						</button>
						<button
							onclick={clearFilters}
							class="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 focus:ring-2 focus:ring-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600"
						>
							Clear
						</button>
					</div>
				</div>
			{/if}
		</div>
	</div>

	<!-- Contacts List -->
	<div class="px-4 py-6 sm:px-6 lg:px-8">
		{#if data.contacts.length === 0}
			<div class="py-12 text-center">
				<Users class="mx-auto h-12 w-12 text-gray-400" />
				<h3 class="mt-4 text-lg font-medium text-gray-900 dark:text-white">No contacts found</h3>
				<p class="mt-2 text-gray-500 dark:text-gray-400">
					{data.search
						? 'Try adjusting your search criteria.'
						: 'Get started by creating your first contact.'}
				</p>
				{#if !data.search}
					<a
						href="/contacts/new"
						class="mt-4 inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
					>
						<Plus class="h-4 w-4" />
						Add Contact
					</a>
				{/if}
			</div>
		{:else}
			<!-- Desktop Table View -->
			<div
				class="hidden overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm lg:block dark:border-gray-700 dark:bg-gray-800"
			>
				<table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
					<thead class="bg-gray-50 dark:bg-gray-700">
						<tr>
							<th
								class="px-6 py-3 text-left text-xs font-medium tracking-wider text-gray-500 uppercase dark:text-gray-400"
							>
								Contact
							</th>
							<th
								class="px-6 py-3 text-left text-xs font-medium tracking-wider text-gray-500 uppercase dark:text-gray-400"
							>
								Title & Department
							</th>
							<th
								class="px-6 py-3 text-left text-xs font-medium tracking-wider text-gray-500 uppercase dark:text-gray-400"
							>
								Contact Info
							</th>
							<th
								class="px-6 py-3 text-left text-xs font-medium tracking-wider text-gray-500 uppercase dark:text-gray-400"
							>
								Owner
							</th>
							<th
								class="px-6 py-3 text-left text-xs font-medium tracking-wider text-gray-500 uppercase dark:text-gray-400"
							>
								Activity
							</th>
							<th
								class="px-6 py-3 text-left text-xs font-medium tracking-wider text-gray-500 uppercase dark:text-gray-400"
							>
								Created
							</th>
							<th class="relative px-6 py-3">
								<span class="sr-only">Actions</span>
							</th>
						</tr>
					</thead>
					<tbody class="divide-y divide-gray-200 bg-white dark:divide-gray-700 dark:bg-gray-800">
						{#each data.contacts as contact}
							<tr class="hover:bg-gray-50 dark:hover:bg-gray-700">
								<td class="px-6 py-4 whitespace-nowrap">
									<div class="flex items-center">
										<div class="h-10 w-10 flex-shrink-0">
											<div
												class="flex h-10 w-10 items-center justify-center rounded-full bg-blue-100 dark:bg-blue-900"
											>
												<User class="h-5 w-5 text-blue-600 dark:text-blue-400" />
											</div>
										</div>
										<div class="ml-4">
											<div class="text-sm font-medium text-gray-900 dark:text-white">
												<button
													onclick={() => goto(`/contacts/${contact.id}`)}
													class="text-left hover:text-blue-600 hover:underline dark:hover:text-blue-400"
												>
													{contact.firstName}
													{contact.lastName}
												</button>
											</div>
											{#if contact.relatedAccounts.length > 0}
												<div
													class="flex items-center gap-1 text-sm text-gray-500 dark:text-gray-400"
												>
													<Building class="h-3 w-3" />
													{contact.relatedAccounts[0].account.name}
												</div>
											{/if}
										</div>
									</div>
								</td>
								<td class="px-6 py-4 whitespace-nowrap">
									<div class="text-sm text-gray-900 dark:text-white">{contact.title || '—'}</div>
									<div class="text-sm text-gray-500 dark:text-gray-400">
										{contact.department || '—'}
									</div>
								</td>
								<td class="px-6 py-4 whitespace-nowrap">
									{#if contact.email}
										<div class="flex items-center gap-1 text-sm text-gray-900 dark:text-white">
											<Mail class="h-3 w-3" />
											{contact.email}
										</div>
									{/if}
									{#if contact.phone}
										<div class="flex items-center gap-1 text-sm text-gray-500 dark:text-gray-400">
											<Phone class="h-3 w-3" />
											{formatPhone(contact.phone)}
										</div>
									{/if}
								</td>
								<td class="px-6 py-4 whitespace-nowrap">
									<div class="text-sm text-gray-900 dark:text-white">
										{contact.owner.name || contact.owner.email}
									</div>
								</td>
								<td class="px-6 py-4 whitespace-nowrap">
									<div class="flex gap-2 text-xs">
										{#if contact._count.tasks > 0}
											<span
												class="rounded bg-blue-100 px-2 py-1 text-blue-800 dark:bg-blue-900 dark:text-blue-200"
											>
												{contact._count.tasks} tasks
											</span>
										{/if}
										{#if contact._count.opportunities > 0}
											<span
												class="rounded bg-green-100 px-2 py-1 text-green-800 dark:bg-green-900 dark:text-green-200"
											>
												{contact._count.opportunities} opps
											</span>
										{/if}
									</div>
								</td>
								<td class="px-6 py-4 text-sm whitespace-nowrap text-gray-500 dark:text-gray-400">
									<div class="flex items-center gap-1">
										<Calendar class="h-3 w-3" />
										{formatDate(contact.createdAt)}
									</div>
								</td>
								<td class="px-6 py-4 text-right text-sm font-medium whitespace-nowrap">
									<div class="flex items-center justify-end gap-2">
										<button
											onclick={() => goto(`/contacts/${contact.id}`)}
											class="rounded-md p-1.5 text-gray-600 hover:bg-gray-100 hover:text-blue-600 dark:text-gray-400 dark:hover:bg-gray-700 dark:hover:text-blue-400"
											title="View contact"
										>
											<Eye class="h-4 w-4" />
										</button>
										<button
											onclick={() => editContact(contact)}
											class="rounded-md p-1.5 text-gray-600 hover:bg-gray-100 hover:text-green-600 dark:text-gray-400 dark:hover:bg-gray-700 dark:hover:text-green-400"
											title="Edit contact"
										>
											<Edit class="h-4 w-4" />
										</button>
										<form method="POST" action="?/delete" use:enhance class="inline">
											<input type="hidden" name="contactId" value={contact.id} />
											<button
												type="submit"
												class="rounded-md p-1.5 text-gray-600 hover:bg-gray-100 hover:text-red-600 dark:text-gray-400 dark:hover:bg-gray-700 dark:hover:text-red-400"
												title="Delete contact"
												onclick={(e) => {
													if (!confirm('Are you sure you want to delete this contact?')) {
														e.preventDefault();
													}
												}}
											>
												<Trash2 class="h-4 w-4" />
											</button>
										</form>
									</div>
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>

			<!-- Mobile Card View -->
			<div class="space-y-4 lg:hidden">
				{#each data.contacts as contact}
					<div
						class="rounded-lg border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800"
					>
						<div class="flex items-start justify-between">
							<button
								onclick={() => goto(`/contacts/${contact.id}`)}
								class="flex items-center space-x-3 text-left hover:opacity-75"
							>
								<div
									class="flex h-10 w-10 items-center justify-center rounded-full bg-blue-100 dark:bg-blue-900"
								>
									<User class="h-5 w-5 text-blue-600 dark:text-blue-400" />
								</div>
								<div>
									<h3
										class="text-sm font-medium text-gray-900 hover:text-blue-600 dark:text-white dark:hover:text-blue-400"
									>
										{contact.firstName}
										{contact.lastName}
									</h3>
									<p class="text-sm text-gray-500 dark:text-gray-400">
										{contact.title || 'No title'}
									</p>
								</div>
							</button>
							<button
								onclick={() => goto(`/contacts/${contact.id}`)}
								class="p-1.5 text-gray-600 hover:text-blue-600 dark:text-gray-400 dark:hover:text-blue-400"
							>
								<Eye class="h-4 w-4" />
							</button>
						</div>

						<div class="mt-3 space-y-2">
							{#if contact.email}
								<div class="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
									<Mail class="h-4 w-4" />
									{contact.email}
								</div>
							{/if}
							{#if contact.phone}
								<div class="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
									<Phone class="h-4 w-4" />
									{formatPhone(contact.phone)}
								</div>
							{/if}
							{#if contact.relatedAccounts.length > 0}
								<div class="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
									<Building class="h-4 w-4" />
									{contact.relatedAccounts[0].account.name}
								</div>
							{/if}
						</div>

						<div class="mt-3 flex items-center justify-between">
							<div class="flex gap-2">
								{#if contact._count.tasks > 0}
									<span
										class="rounded bg-blue-100 px-2 py-1 text-xs text-blue-800 dark:bg-blue-900 dark:text-blue-200"
									>
										{contact._count.tasks} tasks
									</span>
								{/if}
								{#if contact._count.opportunities > 0}
									<span
										class="rounded bg-green-100 px-2 py-1 text-xs text-green-800 dark:bg-green-900 dark:text-green-200"
									>
										{contact._count.opportunities} opps
									</span>
								{/if}
							</div>
							<div class="flex gap-2">
								<button
									onclick={() => goto(`/contacts/${contact.id}`)}
									class="p-1.5 text-gray-600 hover:text-blue-600 dark:text-gray-400 dark:hover:text-blue-400"
								>
									<Eye class="h-4 w-4" />
								</button>
								<button
									onclick={() => editContact(contact)}
									class="p-1.5 text-gray-600 hover:text-green-600 dark:text-gray-400 dark:hover:text-green-400"
								>
									<Edit class="h-4 w-4" />
								</button>
							</div>
						</div>
					</div>
				{/each}
			</div>

			<!-- Pagination -->
			{#if data.totalPages > 1}
				<div class="mt-6 flex items-center justify-between">
					<div class="text-sm text-gray-700 dark:text-gray-300">
						Showing {(data.currentPage - 1) * data.limit + 1} to {Math.min(
							data.currentPage * data.limit,
							data.totalCount
						)} of {data.totalCount} contacts
					</div>
					<div class="flex items-center gap-2">
						<button
							onclick={() => goToPage(data.currentPage - 1)}
							disabled={data.currentPage === 1}
							class="p-2 text-gray-600 hover:text-gray-900 disabled:cursor-not-allowed disabled:opacity-50 dark:text-gray-400 dark:hover:text-white"
						>
							<ChevronLeft class="h-4 w-4" />
						</button>

						{#each Array.from({ length: Math.min(5, data.totalPages) }, (_, i) => {
							const start = Math.max(1, data.currentPage - 2);
							return start + i;
						}) as pageNum}
							{#if pageNum <= data.totalPages}
								<button
									onclick={() => goToPage(pageNum)}
									class="px-3 py-1 text-sm {pageNum === data.currentPage
										? 'bg-blue-600 text-white'
										: 'text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white'} rounded"
								>
									{pageNum}
								</button>
							{/if}
						{/each}

						<button
							onclick={() => goToPage(data.currentPage + 1)}
							disabled={data.currentPage === data.totalPages}
							class="p-2 text-gray-600 hover:text-gray-900 disabled:cursor-not-allowed disabled:opacity-50 dark:text-gray-400 dark:hover:text-white"
						>
							<ChevronRight class="h-4 w-4" />
						</button>
					</div>
				</div>
			{/if}
		{/if}
	</div>
</div>
