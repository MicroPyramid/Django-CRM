<script>
  import { resolve } from '$app/paths';
  import { ChevronLeft } from '@lucide/svelte';
</script>

<a href={resolve('settings/automation')}><ChevronLeft size={13} />Automation</a>

<style>
  a {
    display: inline-flex;
    align-items: center;
    gap: 2px;
  }
</style>
