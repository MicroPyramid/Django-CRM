<script>
  import { page } from '$app/stores';
  import ErrorPage from '$lib/components/ErrorPage.svelte';
</script>

<svelte:head>
  <title>{$page.status} {$page.status === 404 ? 'Not Found' : 'Error'} | BottleCRM</title>
</svelte:head>

<ErrorPage status={$page.status} message={$page.error?.message ?? ''} />
