<script>
	import '../../../app.css';
	import imgLogo from '$lib/assets/images/logo.png';
	import { Building2, LogOut, Plus, ChevronRight, Users, Shield } from '@lucide/svelte';
	import { enhance } from '$app/forms';

	let { data } = $props();
	let orgs = $derived(data.orgs);

	let loading = $state(false);
	let selectedOrgId = $state(null);
</script>

<svelte:head>
	<title>Select Organization | BottleCRM</title>
</svelte:head>

<div class="flex min-h-screen flex-col bg-slate-50">
	<!-- Header -->
	<header class="border-b border-slate-200 bg-white">
		<div class="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
			<div class="flex items-center gap-3">
				<img src={imgLogo} alt="BottleCRM" class="h-8 w-auto" />
				<span class="text-lg font-semibold text-slate-900">BottleCRM</span>
			</div>
			<a
				href="/logout"
				class="flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-100 hover:text-slate-900"
			>
				<LogOut class="h-4 w-4" />
				<span class="hidden sm:inline">Sign out</span>
			</a>
		</div>
	</header>

	<!-- Main Content -->
	<main class="flex flex-1 items-start justify-center px-6 py-12">
		<div class="w-full max-w-2xl">
			<!-- Page Header -->
			<div class="mb-8 text-center">
				<h1 class="text-2xl font-bold text-slate-900">Select an organization</h1>
				<p class="mt-2 text-slate-600">Choose which organization you'd like to work in</p>
			</div>

			<!-- Organizations List -->
			{#if orgs.length > 0}
				<div class="space-y-3">
					{#each orgs as org}
						<form
							method="POST"
							action="?/selectOrg"
							use:enhance={() => {
								loading = true;
								selectedOrgId = org.id;
								return async ({ update }) => {
									await update();
									loading = false;
									selectedOrgId = null;
								};
							}}
						>
							<input type="hidden" name="org_id" value={org.id} />
							<input type="hidden" name="org_name" value={org.name} />
							<button
								type="submit"
								disabled={loading}
								class="group w-full rounded-xl border border-slate-200 bg-white p-5 text-left shadow-sm transition-all hover:border-slate-300 hover:shadow-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-60"
							>
								<div class="flex items-center gap-4">
									<!-- Org Icon -->
									<div class="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg bg-blue-50 text-blue-600 transition-colors group-hover:bg-blue-100">
										<Building2 class="h-6 w-6" />
									</div>

									<!-- Org Info -->
									<div class="flex-1 min-w-0">
										<h3 class="font-semibold text-slate-900 truncate">{org.name}</h3>
										<div class="mt-1 flex items-center gap-3 text-sm text-slate-500">
											<span class="inline-flex items-center gap-1 capitalize">
												<Users class="h-3.5 w-3.5" />
												{org.role?.toLowerCase() || 'Member'}
											</span>
										</div>
									</div>

									<!-- Arrow / Loading -->
									<div class="shrink-0">
										{#if loading && selectedOrgId === org.id}
											<div class="h-5 w-5 animate-spin rounded-full border-2 border-slate-200 border-t-blue-600"></div>
										{:else}
											<ChevronRight class="h-5 w-5 text-slate-400 transition-transform group-hover:translate-x-0.5 group-hover:text-slate-600" />
										{/if}
									</div>
								</div>
							</button>
						</form>
					{/each}
				</div>

				<!-- Create New Org Link -->
				<div class="mt-6">
					<a
						href="/org/new"
						class="flex w-full items-center justify-center gap-2 rounded-xl border-2 border-dashed border-slate-300 bg-slate-50 px-5 py-4 text-sm font-medium text-slate-600 transition-all hover:border-blue-400 hover:bg-blue-50 hover:text-blue-600"
					>
						<Plus class="h-4 w-4" />
						Create new organization
					</a>
				</div>
			{:else}
				<!-- Empty State -->
				<div class="rounded-xl border border-slate-200 bg-white p-12 text-center shadow-sm">
					<div class="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-slate-100">
						<Building2 class="h-8 w-8 text-slate-400" />
					</div>
					<h3 class="text-lg font-semibold text-slate-900">No organizations yet</h3>
					<p class="mt-2 text-slate-600">Create your first organization to get started with BottleCRM</p>
					<a
						href="/org/new"
						class="mt-6 inline-flex items-center gap-2 rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-medium text-white transition-colors hover:bg-blue-700"
					>
						<Plus class="h-4 w-4" />
						Create organization
					</a>
				</div>
			{/if}

			<!-- Trust Signal -->
			<div class="mt-8 flex items-center justify-center gap-2 text-sm text-slate-500">
				<Shield class="h-4 w-4" />
				<span>Your data stays private and secure</span>
			</div>
		</div>
	</main>
</div>
