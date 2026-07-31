<script>
  import { page } from '$app/state';
  import {
    Sun,
    Columns3,
    Target,
    Building2,
    Users,
    CircleCheck,
    LifeBuoy,
    BookOpen,
    Receipt,
    Trophy,
    Clock,
    UserCog,
    CircleUser,
    CircleHelp,
    FileText,
    Bell,
    SlidersHorizontal,
    Search,
    Smartphone
  } from '@lucide/svelte';

  /**
   * One flat tree, grouped by what the person is doing rather than by which
   * Django app owns the model. Every label matches the route it lands on and
   * the page title it lands on — "Pipeline" goes to /v2/pipeline, which is
   * titled "Pipeline".
   *
   * v1 had /leads listed twice, as "Pipeline" and as "Leads", and a "Deals"
   * entry pointing at /opportunities while /deals 404'd.
   *
   * @type {{
   *   counts?: Record<string, number>,
   *   org?: { name: string },
   *   onsearch?: () => void
   * }}
   */
  let { counts = {}, org = { name: 'BottleCRM' }, onsearch = () => {} } = $props();

  const GROUPS = [
    {
      label: 'Sell',
      items: [
        { href: '/', label: 'Today', icon: Sun, exact: true },
        { href: '/pipeline', label: 'Pipeline', icon: Columns3, count: 'pipeline' },
        { href: '/leads', label: 'Leads', icon: Target, count: 'leads' },
        { href: '/accounts', label: 'Accounts', icon: Building2 },
        { href: '/contacts', label: 'Contacts', icon: Users },
        { href: '/goals', label: 'Goals', icon: Trophy }
      ]
    },
    {
      label: 'Serve',
      items: [
        { href: '/tasks', label: 'Tasks', icon: CircleCheck, count: 'tasks' },
        // Approvals and Analytics live under Tickets as section tabs. They are
        // not separate destinations, so they do not get separate nav entries —
        // one level of navigation, and the tab strip carries the rest.
        { href: '/tickets', label: 'Tickets', icon: LifeBuoy, count: 'tickets' },
        { href: '/solutions', label: 'Knowledge base', icon: BookOpen },
        { href: '/documents', label: 'Documents', icon: FileText }
      ]
    },
    {
      label: 'Bill',
      items: [
        { href: '/invoices', label: 'Invoices', icon: Receipt, count: 'invoices' },
        { href: '/timesheet', label: 'Timesheet', icon: Clock }
      ]
    },
    {
      // Administration, kept apart from the work. Someone who never touches
      // these should not read past them four times a day.
      label: 'Run',
      items: [
        { href: '/team', label: 'Team and access', icon: UserCog },
        { href: '/settings', label: 'Settings', icon: SlidersHorizontal }
      ]
    }
  ];

  const isActive = (href, exact) =>
    exact ? page.url.pathname === href : page.url.pathname.startsWith(href);
</script>

<nav class="v2-nav" aria-label="Main">
  <div class="v2-org">
    <span class="v2-mark">{org.name.slice(0, 1)}</span>
    <b>{org.name}</b>
  </div>

  <!--
    No entry appears here without a route behind it. v1's "Deals" pointed at
    /opportunities while /deals 404'd; an Inbox link with nothing behind it
    would be the same mistake.
  -->
  {#each GROUPS as group (group.label)}
    <div class="v2-nav-group v2-label">{group.label}</div>
    {#each group.items as item (item.href)}
      <a
        class="v2-link"
        href={item.href}
        aria-current={isActive(item.href, item.exact) ? 'page' : undefined}
      >
        <item.icon />
        {item.label}
        {#if item.count && counts[item.count]}
          <span class="v2-count">{counts[item.count]}</span>
        {/if}
      </a>
    {/each}
  {/each}

  <div class="v2-nav-foot">
    <button class="v2-link v2-nav-search" type="button" onclick={onsearch}>
      <Search />
      Search
      <span class="v2-count">⌘K</span>
    </button>
    <!-- Personal, not work: your own feed sits with your own profile rather
         than in Serve, where it would read as a queue the team shares. -->
    <a
      class="v2-link"
      href="/notifications"
      aria-current={isActive('/notifications', false) ? 'page' : undefined}
    >
      <Bell />
      Notifications
      {#if counts.notifications}
        <span class="v2-count">{counts.notifications}</span>
      {/if}
    </a>
    <a class="v2-link" href="/profile">
      <CircleUser />
      Your profile
    </a>
    <a class="v2-link" href="/support">
      <CircleHelp />
      Help
    </a>
    <!-- The phone app for people on the hosted service. No pulsing dot — a
         download link is not something that needs you right now, and v2 keeps
         attention for the things that do. -->
    <a
      class="v2-link"
      href="https://play.google.com/store/apps/details?id=io.bottlecrm&hl=en"
      target="_blank"
      rel="noopener noreferrer"
    >
      <Smartphone />
      Download app
    </a>
  </div>
</nav>

<style>
  /* Search opens an overlay rather than navigating, so it is a button. It
     borrows .v2-link for everything else — a control that sits in a list of
     links should not look like the odd one out. */
  .v2-nav-search {
    width: 100%;
    background: none;
    border: 0;
    font-family: inherit;
    font-size: inherit;
    text-align: left;
    cursor: pointer;
  }
</style>
