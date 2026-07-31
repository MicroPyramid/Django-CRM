<script>
  import '../../app.css';
  import '$lib/v2/styles/v2.css';
  import { page } from '$app/state';
  import Sidebar from '$lib/v2/components/Sidebar.svelte';
  import CommandPalette from '$lib/v2/components/CommandPalette.svelte';
  import { isMigrated } from '$lib/v2/migrated.js';
  import { Radio, Search, Sun, Columns3, LifeBuoy, Receipt, Plus } from '@lucide/svelte';

  /** @type {{ data: { counts: Record<string, number>, org: { name: string } }, children: import('svelte').Snippet }} */
  let { data, children } = $props();

  let paletteOpen = $state(false);

  /**
   * The five things worth a thumb on a phone. Fewer than the sidebar on
   * purpose — a tab bar that scrolls is a menu wearing a tab bar's clothes.
   */
  const TABS = [
    { href: '/v2', label: 'Today', icon: Sun, exact: true },
    { href: '/v2/pipeline', label: 'Pipeline', icon: Columns3 },
    { href: '/v2/tickets', label: 'Tickets', icon: LifeBuoy },
    { href: '/v2/invoices', label: 'Invoices', icon: Receipt }
  ];

  const isActive = (href, exact) =>
    exact ? page.url.pathname === href : page.url.pathname.startsWith(href);

  let live = $derived(isMigrated(page.url.pathname));

  function onkeydown(e) {
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
      e.preventDefault();
      paletteOpen = !paletteOpen;
    }
  }
</script>

<svelte:head>
  <title>BottleCRM v2</title>
  <meta name="robots" content="noindex" />
</svelte:head>

<svelte:window {onkeydown} />

<div class="v2-root v2-shell">
  <Sidebar counts={data.counts} org={data.org} onsearch={() => (paletteOpen = true)} />
  <div class="v2-main">
    <!--
      Shown on the data pages — which is all of them now, except the
      design-system showcase and the static Help page. Those two carry no org
      data, so they get no banner rather than a misleading one. The fixture
      "preview" banner is gone with the fixtures.
    -->
    {#if live}
      <div class="v2-banner v2-banner-live">
        <Radio size={13} />
        <span>
          <b>Live data.</b> This page reads and writes your organisation. Changes are real.
        </span>
        <a href="/" style="margin-left:auto">Back to the live app</a>
      </div>
    {/if}

    <!-- Phone top bar. The sidebar is hidden below 768px; this replaces the
         org mark and the search affordance it carried. -->
    <div class="v2-mobile-top">
      <span class="v2-mark">{data.org.name.slice(0, 1)}</span>
      <h2>{data.org.name}</h2>
      <button
        class="v2-btn v2-btn-quiet"
        type="button"
        style="margin-left:auto"
        onclick={() => (paletteOpen = true)}
        aria-label="Search"
      >
        <Search />
      </button>
    </div>

    {@render children()}

    <nav class="v2-tabbar" aria-label="Sections">
      {#each TABS as tab (tab.href)}
        <a href={tab.href} aria-current={isActive(tab.href, tab.exact) ? 'page' : undefined}>
          <tab.icon />
          {tab.label}
        </a>
      {/each}
    </nav>
  </div>

  <!-- Both live inside .v2-root so they inherit the scoped tokens; both are
       position:fixed, so the shell's overflow:hidden does not clip them. -->
  <a class="v2-fab" href="/v2/pipeline/new" aria-label="New deal"><Plus size={21} /></a>

  <CommandPalette open={paletteOpen} onclose={() => (paletteOpen = false)} />
</div>
