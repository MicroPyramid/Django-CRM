<script>
  import '../../app.css';
  import { AppShell } from '$lib/components/layout/index.js';
  import { Toaster } from '$lib/components/ui/sonner/index.js';
  import { initOrgSettings } from '$lib/stores/org.js';

  let { data, children } = $props();

  // Initialize org settings store from server data
  $effect(() => {
    if (data.org_settings) {
      initOrgSettings(data.org_settings);
    }
  });
</script>

<AppShell user={data.user} org_name={data.org_name}>
  <main class="flex-1">
    {@render children()}
  </main>
</AppShell>

<Toaster richColors closeButton position="bottom-right" />
