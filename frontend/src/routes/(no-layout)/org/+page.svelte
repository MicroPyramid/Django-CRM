<script>
	import '../../../app.css';
	import { Building, LogOut, Plus } from '@lucide/svelte';
	import { enhance } from '$app/forms';

	// Get the data from the server load function
	export let data;
	const { orgs } = data;

	let loading = false;
</script>

<div class="min-h-screen bg-gray-50 p-4">
	<div class="mx-auto max-w-6xl">
		<!-- Header -->
		<div class="mb-8 flex items-center justify-between">
			<div>
				<h1 class="mb-2 text-3xl font-bold text-gray-900">Select Organization</h1>
				<p class="text-gray-600">Choose an organization to continue</p>
			</div>
			<a
				href="/logout"
				class="flex items-center gap-2 rounded-lg px-4 py-2 text-gray-600 transition-all duration-200 hover:bg-red-50 hover:text-red-600"
				title="Logout"
			>
				<LogOut class="h-5 w-5" />
				<span class="hidden sm:inline">Logout</span>
			</a>
		</div>

		<!-- Organizations Grid -->
		{#if orgs.length > 0}
			<div class="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
				{#each orgs as org}
					<form
						method="POST"
						action="?/selectOrg"
						use:enhance={() => {
							loading = true;
							return async ({ update }) => {
								await update();
								loading = false;
							};
						}}
						class="group cursor-pointer rounded-xl border border-gray-200 bg-white shadow-sm transition-all duration-200 hover:border-blue-300 hover:shadow-md"
					>
						<input type="hidden" name="org_id" value={org.id} />
						<input type="hidden" name="org_name" value={org.name} />
						<button
							type="submit"
							disabled={loading}
							class="w-full text-left"
							aria-label="Select {org.name} organization"
						>
							<div class="p-6">
								<div class="mb-4 flex items-start justify-between">
									<div class="flex items-center gap-3">
										<div
											class="rounded-lg bg-blue-100 p-3 transition-colors group-hover:bg-blue-200"
										>
											<Building class="h-6 w-6 text-blue-600" />
										</div>
										<div>
											<h3
												class="text-lg font-semibold text-gray-900 transition-colors group-hover:text-blue-600"
											>
												{org.name}
											</h3>
											<p class="text-sm text-gray-500 capitalize">
												{org.role?.toLowerCase() || 'Member'}
											</p>
										</div>
									</div>
								</div>

								<div
									class="w-full rounded-lg bg-blue-600 px-4 py-2.5 text-center font-medium text-white transition-colors duration-200 group-hover:bg-blue-700"
								>
									{loading ? 'Switching...' : 'Select Organization'}
								</div>
							</div>
						</button>
					</form>
				{/each}
			</div>
		{:else}
			<div class="py-16 text-center">
				<div
					class="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-gray-200"
				>
					<Building class="h-8 w-8 text-gray-400" />
				</div>
				<h3 class="mb-2 text-lg font-semibold text-gray-900">No organizations found</h3>
				<p class="mb-6 text-gray-600">Create your first organization to get started</p>
				<a
					href="/org/new"
					class="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-6 py-3 font-medium text-white transition-colors duration-200 hover:bg-blue-700"
				>
					<Plus class="h-5 w-5" />
					Create Organization
				</a>
			</div>
		{/if}

		<!-- Floating Action Button -->
		{#if orgs.length > 0}
			<a
				href="/org/new"
				class="fixed right-6 bottom-6 z-50 flex h-14 w-14 items-center justify-center rounded-full bg-blue-600 text-white shadow-lg transition-all duration-200 hover:bg-blue-700 hover:shadow-xl"
				title="Create New Organization"
			>
				<Plus class="h-6 w-6" />
			</a>
		{/if}
	</div>
</div>
