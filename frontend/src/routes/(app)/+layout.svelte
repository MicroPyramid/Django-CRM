<script>
	import '../../app.css';
	import Sidebar from './Sidebar.svelte';
	let { data, children } = $props();

	let drawerHidden = $state(true);
</script>

<!-- Mobile menu button for when sidebar is hidden -->
<button
	onclick={() => (drawerHidden = !drawerHidden)}
	class="fixed top-4 left-4 z-50 inline-flex items-center rounded-lg border border-gray-200 bg-white p-2 text-gray-500 shadow-md transition-colors hover:bg-gray-100 focus:ring-2 focus:ring-gray-200 focus:outline-none lg:hidden dark:border-gray-700 dark:bg-gray-900 dark:text-gray-400 dark:hover:bg-gray-800 dark:focus:ring-gray-600"
	class:hidden={!drawerHidden}
	aria-label="Open sidebar menu"
>
	<svg class="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
		<path
			d="M3 12h18M3 6h18M3 18h18"
			stroke="currentColor"
			stroke-width="2"
			stroke-linecap="round"
		/>
	</svg>
</button>

<div class="flex min-h-screen bg-gray-50 dark:bg-gray-900">
	<Sidebar bind:drawerHidden user={data.user} org_name={data.org_name} />
	<main class="flex-1 lg:ml-64">
		<div class="p-6">
			{@render children()}
		</div>
	</main>
</div>
