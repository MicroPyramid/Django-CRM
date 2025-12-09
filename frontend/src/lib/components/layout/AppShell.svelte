<script>
  import * as Sidebar from '$lib/components/ui/sidebar/index.js';
  import AppSidebar from './AppSidebar.svelte';

  /**
   * @typedef {Object} Props
   * @property {Object} user - User object with name, email, profilePhoto
   * @property {string} [org_name] - Organization name
   * @property {import('svelte').Snippet} [children] - Child content
   */

  /** @type {Props & { children?: import('svelte').Snippet }} */
  let { user = {}, org_name = 'BottleCRM', children } = $props();

  // Get initial sidebar state from cookie (set by server or previous session)
  let defaultOpen = $state(true);

  $effect(() => {
    if (typeof document !== 'undefined') {
      const cookies = document.cookie.split(';');
      const sidebarCookie = cookies.find((c) => c.trim().startsWith('sidebar:state='));
      if (sidebarCookie) {
        const value = sidebarCookie.split('=')[1];
        defaultOpen = value === 'true';
      }
    }
  });
</script>

<Sidebar.Provider open={defaultOpen} class="" style="">
  <AppSidebar {user} {org_name} />
  <Sidebar.Inset class="">
    {@render children?.()}
  </Sidebar.Inset>
</Sidebar.Provider>
