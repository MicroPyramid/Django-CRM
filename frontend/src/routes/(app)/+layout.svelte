<script>
	import '../../app.css';
	import { AppShell } from '$lib/components/layout/index.js';
	import { Toaster } from '$lib/components/ui/sonner/index.js';

	let { data, children } = $props();
</script>

<AppShell user={data.user} org_name={data.org_name}>
	<main class="flex-1">
		{@render children()}
	</main>
</AppShell>

<Toaster richColors closeButton position="bottom-right" />
