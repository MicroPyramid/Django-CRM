<script>
  import { untrack } from 'svelte';
  import { page } from '$app/stores';
  import { afterNavigate, goto } from '$app/navigation';

  import * as Sidebar from '$lib/components/ui/sidebar/index.js';
  import * as DropdownMenu from '$lib/components/ui/dropdown-menu/index.js';
  import * as Collapsible from '$lib/components/ui/collapsible/index.js';
  import { Button } from '$lib/components/ui/button/index.js';
  import { Avatar, AvatarFallback, gradientFor } from '$lib/components/ui/avatar/index.js';

  import {
    LayoutDashboard,
    Target,
    Users,
    Building,
    Briefcase,
    CheckSquare,
    HelpCircle,
    ChevronRight,
    ChevronDown,
    PanelLeftClose,
    PanelLeft,
    Moon,
    Sun,
    Monitor,
    User,
    LogOut,
    ChevronsUpDown,
    Settings,
    Sliders,
    Megaphone,
    Mail,
    Route,
    FileText,
    FileEdit,
    Package,
    RefreshCw,
    FileCode,
    BarChart3,
    Tag,
    Sparkles,
    Home,
    Trophy,
    Cloud,
    RotateCcw,
    Clock,
    MessageSquareQuote,
    ShieldCheck,
    BookOpen,
    Activity,
    Smartphone
  } from '@lucide/svelte';
  import { Bell } from '$lib/components/notifications/index.js';

  /**
   * @typedef {Object} Props
   * @property {Object} user - User object
   * @property {string} [org_name] - Organization name
   * @property {Object} [org_settings] - Org settings (tier, currency, etc.)
   */

  /** @type {Props} */
  let { user = {}, org_name = 'BottleCRM', org_settings = {} } = $props();

  // Tier badge — hidden when JWT doesn't carry one (spec §8 "No tier in JWT")
  const tier = $derived(org_settings?.tier ?? null);

  // Workspace gradient seed — first-letter monogram fallback for the avatar
  const orgInitial = $derived((org_name || 'B').charAt(0).toUpperCase());

  const sidebar = Sidebar.useSidebar();

  /** @type {'light' | 'system' | 'dark'} */
  let theme = $state('system');

  // Initialize theme from localStorage on mount
  $effect(() => {
    if (typeof window !== 'undefined') {
      const savedTheme = localStorage.getItem('theme');
      if (savedTheme === 'dark' || savedTheme === 'light' || savedTheme === 'system') {
        theme = savedTheme;
      }
    }
  });

  // Apply theme whenever it changes
  $effect(() => {
    const currentTheme = theme;
    if (typeof window !== 'undefined') {
      if (currentTheme === 'dark') {
        document.documentElement.classList.add('dark');
      } else if (currentTheme === 'light') {
        document.documentElement.classList.remove('dark');
      } else {
        if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
          document.documentElement.classList.add('dark');
        } else {
          document.documentElement.classList.remove('dark');
        }
      }
    }
  });

  // Listen for system preference changes
  $effect(() => {
    if (typeof window !== 'undefined') {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      const handleChange = () => {
        if (theme === 'system') {
          if (mediaQuery.matches) {
            document.documentElement.classList.add('dark');
          } else {
            document.documentElement.classList.remove('dark');
          }
        }
      };
      mediaQuery.addEventListener('change', handleChange);
      return () => mediaQuery.removeEventListener('change', handleChange);
    }
  });

  /** @param {'light' | 'system' | 'dark'} newTheme */
  const setTheme = (newTheme) => {
    theme = newTheme;
    localStorage.setItem('theme', newTheme);
  };

  let currentPath = $derived($page.url.pathname);

  /** @type {{ [key: string]: boolean }} */
  let openDropdowns = $state({});

  /** Track if profile image failed to load */
  let profileImageError = $state(false);

  /**
   * Get user initials from name
   * @param {string} name
   */
  const getInitials = (name) => {
    if (!name) return '?';
    const parts = name.trim().split(/\s+/);
    if (parts.length >= 2) {
      return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
    }
    return name.slice(0, 2).toUpperCase();
  };

  // Auto-open dropdown if a child route is active. Untrack the openDropdowns
  // read so this effect only re-fires on currentPath changes — otherwise the
  // user's onOpenChange (closing the panel) would re-trigger the effect and
  // immediately re-open it, fighting the click.
  $effect(() => {
    const path = currentPath;
    for (const item of navigationItems) {
      if (item.type !== 'dropdown' || !item.children || !item.key) continue;
      const active = item.children.some(
        (child) => path === child.href || path.startsWith(child.href + '/')
      );
      if (active) {
        untrack(() => {
          if (item.key && !openDropdowns[item.key]) openDropdowns[item.key] = true;
        });
      }
    }
  });

  // Close mobile sidebar after navigation
  afterNavigate(() => {
    if (sidebar.isMobile) {
      sidebar.setOpenMobile(false);
    }
  });

  // Five-section IA per spec §4
  const workspaceItems = [
    { href: '/', label: 'Home', icon: Home, type: 'link', preload: 'off', count: undefined },
    { href: '/leads', label: 'Pipeline', icon: Activity, type: 'link', preload: 'off', count: undefined }
  ];

  const recordsItems = [
    { href: '/leads', label: 'Leads', icon: Target, type: 'link', preload: 'off', count: undefined },
    { href: '/contacts', label: 'Contacts', icon: Users, type: 'link', preload: 'off', count: undefined },
    { href: '/accounts', label: 'Accounts', icon: Building, type: 'link', preload: 'off', count: undefined },
    { href: '/opportunities', label: 'Deals', icon: Sparkles, type: 'link', preload: 'off', count: undefined }
  ];

  const workItems = [
    {
      key: 'tickets',
      label: 'Tickets',
      icon: Briefcase,
      type: 'dropdown',
      count: undefined,
      children: [
        { href: '/tickets', label: 'All tickets', icon: Briefcase, preload: 'off', count: undefined },
        { href: '/tickets/approvals', label: 'Approvals', icon: ShieldCheck, preload: 'off', count: undefined },
        { href: '/tickets/analytics', label: 'Analytics', icon: BarChart3, preload: 'off', count: undefined },
        { href: '/solutions', label: 'Knowledge base', icon: BookOpen, preload: 'off', count: undefined }
      ]
    },
    { href: '/tasks', label: 'Tasks', icon: CheckSquare, type: 'link', preload: 'off', count: undefined },
    { href: '/timesheet', label: 'Timesheet', icon: Clock, type: 'link', preload: 'off', count: undefined },
    { href: '/goals', label: 'Goals', icon: Trophy, type: 'link', preload: 'off', count: undefined }
  ];

  const revenueItems = [
    {
      key: 'invoices',
      label: 'Invoices',
      icon: FileText,
      type: 'dropdown',
      count: undefined,
      children: [
        { href: '/invoices', label: 'All Invoices', icon: FileText, preload: 'off', count: undefined },
        { href: '/invoices/estimates', label: 'Estimates', icon: FileEdit, preload: 'off', count: undefined },
        { href: '/invoices/products', label: 'Products', icon: Package, preload: 'off', count: undefined },
        { href: '/invoices/recurring', label: 'Recurring', icon: RefreshCw, preload: 'off', count: undefined },
        { href: '/invoices/templates', label: 'Templates', icon: FileCode, preload: 'off', count: undefined },
        { href: '/invoices/reports', label: 'Reports', icon: BarChart3, preload: 'off', count: undefined }
      ]
    }
  ];

  const supportItems = [
    { href: '/support', label: 'Help desk', icon: HelpCircle, type: 'link', preload: 'off', count: undefined }
  ];

  // Combine for the auto-open-on-active effect (which scans dropdown items)
  const navigationItems = [...workspaceItems, ...recordsItems, ...workItems, ...revenueItems, ...supportItems];

  /**
   * Check if any child route is active
   * @param {Array<{href: string}>} children
   */
  const hasActiveChild = (children) => {
    return children.some(
      (child) => currentPath === child.href || currentPath.startsWith(child.href + '/')
    );
  };

  /**
   * Navigate to URL
   * @param {string} url
   */
  const navigateTo = (url) => {
    goto(url);
  };
</script>

<Sidebar.Root
  collapsible="icon"
  class="hubspot-sidebar border-sidebar-border/60 bg-sidebar border-r"
>
  <!-- Workspace switcher row (spec §5.1) -->
  <Sidebar.Header
    class="border-b border-[color:var(--sidebar-border)] px-3 py-3 group-data-[collapsible=icon]:px-2"
  >
    <div class="flex items-center gap-2">
      <a
        href="/org"
        data-sveltekit-preload-data="off"
        class="flex min-w-0 flex-1 items-center gap-2.5 rounded-md px-1 py-1 transition-colors hover:bg-[color:var(--sidebar-accent)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[color:var(--sidebar-ring)]"
      >
        <Avatar class="size-[26px] shrink-0 rounded-md">
          <AvatarFallback workspace class="rounded-md text-[13px] font-semibold">
            {orgInitial}
          </AvatarFallback>
        </Avatar>
        <div class="flex min-w-0 flex-1 flex-col leading-none group-data-[collapsible=icon]:hidden">
          <div class="flex items-center gap-1.5">
            <span class="truncate text-[14px] font-semibold text-[color:var(--sidebar-foreground)]">
              {org_name}
            </span>
            {#if tier}
              <span
                class="inline-flex shrink-0 items-center rounded-[4px] border border-[color:var(--sidebar-border)] px-1 py-px text-[10px] font-semibold uppercase tracking-wide text-[color:var(--sidebar-subtle)]"
              >
                {tier}
              </span>
            {/if}
          </div>
          <span class="mt-0.5 truncate text-[11px] text-[color:var(--sidebar-subtle)]">
            {user.email ?? ''}
          </span>
        </div>
      </a>
      <div class="shrink-0 group-data-[collapsible=icon]:hidden">
        <Bell />
      </div>
    </div>
  </Sidebar.Header>

  <Sidebar.Content class="px-2 py-3">
    <!-- Workspace Section -->
    <Sidebar.Group>
      <Sidebar.GroupLabel
        class="mb-1 h-auto px-3 text-[10px] font-semibold leading-none text-[color:var(--sidebar-subtle)] [font-variant:small-caps] [text-transform:lowercase] group-data-[collapsible=icon]:hidden"
      >
        Workspace
      </Sidebar.GroupLabel>
      <Sidebar.GroupContent>
        <Sidebar.Menu class="space-y-px">
          {#each workspaceItems as item}
            {#if item.type === 'dropdown' && item.children}
              <Collapsible.Root
                open={openDropdowns[item.key ?? ''] || false}
                onOpenChange={(open) => {
                  if (item.key) openDropdowns[item.key] = open;
                }}
                class="group/collapsible"
              >
                <Sidebar.MenuItem>
                  <Collapsible.Trigger>
                    {#snippet child({ props })}
                      <Sidebar.MenuButton
                        {...props}
                        isActive={hasActiveChild(item.children ?? [])}
                        tooltipContent={item.label}
                        class="nav-item group/item relative h-[30px] rounded-md pl-[18px] pr-[10px] transition-colors duration-150
                          group-data-[collapsible=icon]:size-8 group-data-[collapsible=icon]:rounded-md group-data-[collapsible=icon]:px-0
                          {hasActiveChild(item.children ?? [])
                          ? 'text-[color:var(--sidebar-foreground)] group-data-[collapsible=icon]:bg-[color:var(--sidebar-active-fill)]'
                          : 'text-[color:var(--sidebar-muted)] hover:bg-[color:var(--sidebar-accent)] hover:text-[color:var(--sidebar-foreground)]'}"
                      >
                        {#snippet child({ props: btnProps })}
                          <button {...btnProps}>
                            {#if hasActiveChild(item.children ?? [])}
                              <span
                                aria-hidden="true"
                                class="absolute left-[7px] top-1/2 size-1 -translate-y-1/2 rounded-full bg-[color:var(--sidebar-foreground)] group-data-[collapsible=icon]:hidden"
                              ></span>
                            {/if}
                            <item.icon
                              class="size-[15px] shrink-0 {hasActiveChild(item.children ?? []) ? 'text-[color:var(--sidebar-foreground)]' : 'text-[color:var(--sidebar-subtle)] group-hover/item:text-[color:var(--sidebar-foreground)]'}"
                              strokeWidth={1.6}
                            />
                            <span
                              class="flex-1 truncate text-[14px] group-data-[collapsible=icon]:hidden {hasActiveChild(item.children ?? []) ? 'font-semibold' : 'font-medium'}"
                            >{item.label}</span>
                            {#if item.count !== undefined && item.count !== null}
                              <span
                                class="inline-flex shrink-0 items-center rounded-[4px] px-1.5 text-[11px] font-medium tabular-nums text-[color:var(--sidebar-subtle)] group-data-[collapsible=icon]:hidden"
                              >{item.count}</span>
                            {/if}
                            <ChevronDown
                              class="ml-1 size-3.5 shrink-0 text-[color:var(--sidebar-subtle)] transition-transform duration-150 group-data-[collapsible=icon]:hidden group-data-[state=open]/collapsible:rotate-180"
                            />
                          </button>
                        {/snippet}
                      </Sidebar.MenuButton>
                    {/snippet}
                  </Collapsible.Trigger>
                  <Collapsible.Content>
                    <Sidebar.MenuSub
                      class="ml-0 mt-0.5 mb-1 space-y-px border-none p-0"
                    >
                      {#each item.children as navChild}
                        <Sidebar.MenuSubItem>
                          <Sidebar.MenuSubButton
                            isActive={currentPath === navChild.href}
                            class="group/subitem relative h-[26px] rounded-md pl-[38px] pr-[10px] transition-colors duration-150
                              {currentPath === navChild.href
                              ? 'text-[color:var(--sidebar-foreground)]'
                              : 'text-[color:var(--sidebar-muted)] hover:bg-[color:var(--sidebar-accent)] hover:text-[color:var(--sidebar-foreground)]'}"
                          >
                            {#snippet child({ props })}
                              <a href={navChild.href} {...props}>
                                {#if currentPath === navChild.href}
                                  <span
                                    aria-hidden="true"
                                    class="absolute left-[27px] top-1/2 size-1 -translate-y-1/2 rounded-full bg-[color:var(--sidebar-foreground)]"
                                  ></span>
                                {/if}
                                <span
                                  class="flex-1 truncate text-[13px] {currentPath === navChild.href ? 'font-semibold' : 'font-medium'}"
                                >{navChild.label}</span>
                                {#if navChild.count !== undefined && navChild.count !== null}
                                  <span
                                    class="ml-auto inline-flex shrink-0 items-center rounded-[4px] bg-[color:var(--sidebar-accent)] px-1.5 text-[11px] font-medium tabular-nums text-[color:var(--sidebar-subtle)]"
                                  >{navChild.count}</span>
                                {/if}
                              </a>
                            {/snippet}
                          </Sidebar.MenuSubButton>
                        </Sidebar.MenuSubItem>
                      {/each}
                    </Sidebar.MenuSub>
                  </Collapsible.Content>
                </Sidebar.MenuItem>
              </Collapsible.Root>
            {:else}
              <Sidebar.MenuItem>
                <Sidebar.MenuButton
                  isActive={currentPath === item.href}
                  tooltipContent={item.label}
                  class="nav-item group/item relative h-[30px] rounded-md pl-[18px] pr-[10px] transition-colors duration-150
                    group-data-[collapsible=icon]:size-8 group-data-[collapsible=icon]:rounded-md group-data-[collapsible=icon]:px-0
                    {currentPath === item.href
                    ? 'text-[color:var(--sidebar-foreground)] group-data-[collapsible=icon]:bg-[color:var(--sidebar-active-fill)]'
                    : 'text-[color:var(--sidebar-muted)] hover:bg-[color:var(--sidebar-accent)] hover:text-[color:var(--sidebar-foreground)]'}"
                >
                  {#snippet child({ props })}
                    <a
                      href={item.href}
                      {...props}
                      data-sveltekit-preload-data={item.preload || 'hover'}
                     
                    >
                      {#if currentPath === item.href}
                        <span
                          aria-hidden="true"
                          class="absolute left-[7px] top-1/2 size-1 -translate-y-1/2 rounded-full bg-[color:var(--sidebar-foreground)] group-data-[collapsible=icon]:hidden"
                        ></span>
                      {/if}
                      <item.icon
                        class="size-[15px] shrink-0 {currentPath === item.href ? 'text-[color:var(--sidebar-foreground)]' : 'text-[color:var(--sidebar-subtle)] group-hover/item:text-[color:var(--sidebar-foreground)]'}"
                        strokeWidth={1.6}
                      />
                      <span
                        class="flex-1 truncate text-[14px] group-data-[collapsible=icon]:hidden {currentPath === item.href ? 'font-semibold' : 'font-medium'}"
                      >{item.label}</span>
                      {#if item.count !== undefined && item.count !== null}
                        <span
                          class="ml-auto inline-flex shrink-0 items-center rounded-[4px] px-1.5 text-[11px] font-medium tabular-nums text-[color:var(--sidebar-subtle)] group-data-[collapsible=icon]:hidden"
                        >{item.count}</span>
                      {/if}
                    </a>
                  {/snippet}
                </Sidebar.MenuButton>
              </Sidebar.MenuItem>
            {/if}
          {/each}
        </Sidebar.Menu>
      </Sidebar.GroupContent>
    </Sidebar.Group>

    <!-- Records Section -->
    <Sidebar.Group class="mt-1.5">
      <Sidebar.GroupLabel
        class="mb-1 h-auto px-3 text-[10px] font-semibold leading-none text-[color:var(--sidebar-subtle)] [font-variant:small-caps] [text-transform:lowercase] group-data-[collapsible=icon]:hidden"
      >
        Records
      </Sidebar.GroupLabel>
      <Sidebar.GroupContent>
        <Sidebar.Menu class="space-y-px">
          {#each recordsItems as item}
            {#if item.type === 'dropdown' && item.children}
              <Collapsible.Root
                open={openDropdowns[item.key ?? ''] || false}
                onOpenChange={(open) => {
                  if (item.key) openDropdowns[item.key] = open;
                }}
                class="group/collapsible"
              >
                <Sidebar.MenuItem>
                  <Collapsible.Trigger>
                    {#snippet child({ props })}
                      <Sidebar.MenuButton
                        {...props}
                        isActive={hasActiveChild(item.children ?? [])}
                        tooltipContent={item.label}
                        class="nav-item group/item relative h-[30px] rounded-md pl-[18px] pr-[10px] transition-colors duration-150
                          group-data-[collapsible=icon]:size-8 group-data-[collapsible=icon]:rounded-md group-data-[collapsible=icon]:px-0
                          {hasActiveChild(item.children ?? [])
                          ? 'text-[color:var(--sidebar-foreground)] group-data-[collapsible=icon]:bg-[color:var(--sidebar-active-fill)]'
                          : 'text-[color:var(--sidebar-muted)] hover:bg-[color:var(--sidebar-accent)] hover:text-[color:var(--sidebar-foreground)]'}"
                      >
                        {#snippet child({ props: btnProps })}
                          <button {...btnProps}>
                            {#if hasActiveChild(item.children ?? [])}
                              <span
                                aria-hidden="true"
                                class="absolute left-[7px] top-1/2 size-1 -translate-y-1/2 rounded-full bg-[color:var(--sidebar-foreground)] group-data-[collapsible=icon]:hidden"
                              ></span>
                            {/if}
                            <item.icon
                              class="size-[15px] shrink-0 {hasActiveChild(item.children ?? []) ? 'text-[color:var(--sidebar-foreground)]' : 'text-[color:var(--sidebar-subtle)] group-hover/item:text-[color:var(--sidebar-foreground)]'}"
                              strokeWidth={1.6}
                            />
                            <span
                              class="flex-1 truncate text-[14px] group-data-[collapsible=icon]:hidden {hasActiveChild(item.children ?? []) ? 'font-semibold' : 'font-medium'}"
                            >{item.label}</span>
                            {#if item.count !== undefined && item.count !== null}
                              <span
                                class="inline-flex shrink-0 items-center rounded-[4px] px-1.5 text-[11px] font-medium tabular-nums text-[color:var(--sidebar-subtle)] group-data-[collapsible=icon]:hidden"
                              >{item.count}</span>
                            {/if}
                            <ChevronDown
                              class="ml-1 size-3.5 shrink-0 text-[color:var(--sidebar-subtle)] transition-transform duration-150 group-data-[collapsible=icon]:hidden group-data-[state=open]/collapsible:rotate-180"
                            />
                          </button>
                        {/snippet}
                      </Sidebar.MenuButton>
                    {/snippet}
                  </Collapsible.Trigger>
                  <Collapsible.Content>
                    <Sidebar.MenuSub
                      class="ml-0 mt-0.5 mb-1 space-y-px border-none p-0"
                    >
                      {#each item.children as navChild}
                        <Sidebar.MenuSubItem>
                          <Sidebar.MenuSubButton
                            isActive={currentPath === navChild.href}
                            class="group/subitem relative h-[26px] rounded-md pl-[38px] pr-[10px] transition-colors duration-150
                              {currentPath === navChild.href
                              ? 'text-[color:var(--sidebar-foreground)]'
                              : 'text-[color:var(--sidebar-muted)] hover:bg-[color:var(--sidebar-accent)] hover:text-[color:var(--sidebar-foreground)]'}"
                          >
                            {#snippet child({ props })}
                              <a href={navChild.href} {...props}>
                                {#if currentPath === navChild.href}
                                  <span
                                    aria-hidden="true"
                                    class="absolute left-[27px] top-1/2 size-1 -translate-y-1/2 rounded-full bg-[color:var(--sidebar-foreground)]"
                                  ></span>
                                {/if}
                                <span
                                  class="flex-1 truncate text-[13px] {currentPath === navChild.href ? 'font-semibold' : 'font-medium'}"
                                >{navChild.label}</span>
                                {#if navChild.count !== undefined && navChild.count !== null}
                                  <span
                                    class="ml-auto inline-flex shrink-0 items-center rounded-[4px] bg-[color:var(--sidebar-accent)] px-1.5 text-[11px] font-medium tabular-nums text-[color:var(--sidebar-subtle)]"
                                  >{navChild.count}</span>
                                {/if}
                              </a>
                            {/snippet}
                          </Sidebar.MenuSubButton>
                        </Sidebar.MenuSubItem>
                      {/each}
                    </Sidebar.MenuSub>
                  </Collapsible.Content>
                </Sidebar.MenuItem>
              </Collapsible.Root>
            {:else}
              <Sidebar.MenuItem>
                <Sidebar.MenuButton
                  isActive={currentPath === item.href}
                  tooltipContent={item.label}
                  class="nav-item group/item relative h-[30px] rounded-md pl-[18px] pr-[10px] transition-colors duration-150
                    group-data-[collapsible=icon]:size-8 group-data-[collapsible=icon]:rounded-md group-data-[collapsible=icon]:px-0
                    {currentPath === item.href
                    ? 'text-[color:var(--sidebar-foreground)] group-data-[collapsible=icon]:bg-[color:var(--sidebar-active-fill)]'
                    : 'text-[color:var(--sidebar-muted)] hover:bg-[color:var(--sidebar-accent)] hover:text-[color:var(--sidebar-foreground)]'}"
                >
                  {#snippet child({ props })}
                    <a
                      href={item.href}
                      {...props}
                      data-sveltekit-preload-data={item.preload || 'hover'}
                     
                    >
                      {#if currentPath === item.href}
                        <span
                          aria-hidden="true"
                          class="absolute left-[7px] top-1/2 size-1 -translate-y-1/2 rounded-full bg-[color:var(--sidebar-foreground)] group-data-[collapsible=icon]:hidden"
                        ></span>
                      {/if}
                      <item.icon
                        class="size-[15px] shrink-0 {currentPath === item.href ? 'text-[color:var(--sidebar-foreground)]' : 'text-[color:var(--sidebar-subtle)] group-hover/item:text-[color:var(--sidebar-foreground)]'}"
                        strokeWidth={1.6}
                      />
                      <span
                        class="flex-1 truncate text-[14px] group-data-[collapsible=icon]:hidden {currentPath === item.href ? 'font-semibold' : 'font-medium'}"
                      >{item.label}</span>
                      {#if item.count !== undefined && item.count !== null}
                        <span
                          class="ml-auto inline-flex shrink-0 items-center rounded-[4px] px-1.5 text-[11px] font-medium tabular-nums text-[color:var(--sidebar-subtle)] group-data-[collapsible=icon]:hidden"
                        >{item.count}</span>
                      {/if}
                    </a>
                  {/snippet}
                </Sidebar.MenuButton>
              </Sidebar.MenuItem>
            {/if}
          {/each}
        </Sidebar.Menu>
      </Sidebar.GroupContent>
    </Sidebar.Group>

    <!-- Work Section -->
    <Sidebar.Group class="mt-1.5">
      <Sidebar.GroupLabel
        class="mb-1 h-auto px-3 text-[10px] font-semibold leading-none text-[color:var(--sidebar-subtle)] [font-variant:small-caps] [text-transform:lowercase] group-data-[collapsible=icon]:hidden"
      >
        Work
      </Sidebar.GroupLabel>
      <Sidebar.GroupContent>
        <Sidebar.Menu class="space-y-px">
          {#each workItems as item}
            {#if item.type === 'dropdown' && item.children}
              <Collapsible.Root
                open={openDropdowns[item.key ?? ''] || false}
                onOpenChange={(open) => {
                  if (item.key) openDropdowns[item.key] = open;
                }}
                class="group/collapsible"
              >
                <Sidebar.MenuItem>
                  <Collapsible.Trigger>
                    {#snippet child({ props })}
                      <Sidebar.MenuButton
                        {...props}
                        isActive={hasActiveChild(item.children ?? [])}
                        tooltipContent={item.label}
                        class="nav-item group/item relative h-[30px] rounded-md pl-[18px] pr-[10px] transition-colors duration-150
                          group-data-[collapsible=icon]:size-8 group-data-[collapsible=icon]:rounded-md group-data-[collapsible=icon]:px-0
                          {hasActiveChild(item.children ?? [])
                          ? 'text-[color:var(--sidebar-foreground)] group-data-[collapsible=icon]:bg-[color:var(--sidebar-active-fill)]'
                          : 'text-[color:var(--sidebar-muted)] hover:bg-[color:var(--sidebar-accent)] hover:text-[color:var(--sidebar-foreground)]'}"
                      >
                        {#snippet child({ props: btnProps })}
                          <button {...btnProps}>
                            {#if hasActiveChild(item.children ?? [])}
                              <span
                                aria-hidden="true"
                                class="absolute left-[7px] top-1/2 size-1 -translate-y-1/2 rounded-full bg-[color:var(--sidebar-foreground)] group-data-[collapsible=icon]:hidden"
                              ></span>
                            {/if}
                            <item.icon
                              class="size-[15px] shrink-0 {hasActiveChild(item.children ?? []) ? 'text-[color:var(--sidebar-foreground)]' : 'text-[color:var(--sidebar-subtle)] group-hover/item:text-[color:var(--sidebar-foreground)]'}"
                              strokeWidth={1.6}
                            />
                            <span
                              class="flex-1 truncate text-[14px] group-data-[collapsible=icon]:hidden {hasActiveChild(item.children ?? []) ? 'font-semibold' : 'font-medium'}"
                            >{item.label}</span>
                            {#if item.count !== undefined && item.count !== null}
                              <span
                                class="inline-flex shrink-0 items-center rounded-[4px] px-1.5 text-[11px] font-medium tabular-nums text-[color:var(--sidebar-subtle)] group-data-[collapsible=icon]:hidden"
                              >{item.count}</span>
                            {/if}
                            <ChevronDown
                              class="ml-1 size-3.5 shrink-0 text-[color:var(--sidebar-subtle)] transition-transform duration-150 group-data-[collapsible=icon]:hidden group-data-[state=open]/collapsible:rotate-180"
                            />
                          </button>
                        {/snippet}
                      </Sidebar.MenuButton>
                    {/snippet}
                  </Collapsible.Trigger>
                  <Collapsible.Content>
                    <Sidebar.MenuSub
                      class="ml-0 mt-0.5 mb-1 space-y-px border-none p-0"
                    >
                      {#each item.children as navChild}
                        <Sidebar.MenuSubItem>
                          <Sidebar.MenuSubButton
                            isActive={currentPath === navChild.href}
                            class="group/subitem relative h-[26px] rounded-md pl-[38px] pr-[10px] transition-colors duration-150
                              {currentPath === navChild.href
                              ? 'text-[color:var(--sidebar-foreground)]'
                              : 'text-[color:var(--sidebar-muted)] hover:bg-[color:var(--sidebar-accent)] hover:text-[color:var(--sidebar-foreground)]'}"
                          >
                            {#snippet child({ props })}
                              <a href={navChild.href} {...props}>
                                {#if currentPath === navChild.href}
                                  <span
                                    aria-hidden="true"
                                    class="absolute left-[27px] top-1/2 size-1 -translate-y-1/2 rounded-full bg-[color:var(--sidebar-foreground)]"
                                  ></span>
                                {/if}
                                <span
                                  class="flex-1 truncate text-[13px] {currentPath === navChild.href ? 'font-semibold' : 'font-medium'}"
                                >{navChild.label}</span>
                                {#if navChild.count !== undefined && navChild.count !== null}
                                  <span
                                    class="ml-auto inline-flex shrink-0 items-center rounded-[4px] bg-[color:var(--sidebar-accent)] px-1.5 text-[11px] font-medium tabular-nums text-[color:var(--sidebar-subtle)]"
                                  >{navChild.count}</span>
                                {/if}
                              </a>
                            {/snippet}
                          </Sidebar.MenuSubButton>
                        </Sidebar.MenuSubItem>
                      {/each}
                    </Sidebar.MenuSub>
                  </Collapsible.Content>
                </Sidebar.MenuItem>
              </Collapsible.Root>
            {:else}
              <Sidebar.MenuItem>
                <Sidebar.MenuButton
                  isActive={currentPath === item.href}
                  tooltipContent={item.label}
                  class="nav-item group/item relative h-[30px] rounded-md pl-[18px] pr-[10px] transition-colors duration-150
                    group-data-[collapsible=icon]:size-8 group-data-[collapsible=icon]:rounded-md group-data-[collapsible=icon]:px-0
                    {currentPath === item.href
                    ? 'text-[color:var(--sidebar-foreground)] group-data-[collapsible=icon]:bg-[color:var(--sidebar-active-fill)]'
                    : 'text-[color:var(--sidebar-muted)] hover:bg-[color:var(--sidebar-accent)] hover:text-[color:var(--sidebar-foreground)]'}"
                >
                  {#snippet child({ props })}
                    <a
                      href={item.href}
                      {...props}
                      data-sveltekit-preload-data={item.preload || 'hover'}
                     
                    >
                      {#if currentPath === item.href}
                        <span
                          aria-hidden="true"
                          class="absolute left-[7px] top-1/2 size-1 -translate-y-1/2 rounded-full bg-[color:var(--sidebar-foreground)] group-data-[collapsible=icon]:hidden"
                        ></span>
                      {/if}
                      <item.icon
                        class="size-[15px] shrink-0 {currentPath === item.href ? 'text-[color:var(--sidebar-foreground)]' : 'text-[color:var(--sidebar-subtle)] group-hover/item:text-[color:var(--sidebar-foreground)]'}"
                        strokeWidth={1.6}
                      />
                      <span
                        class="flex-1 truncate text-[14px] group-data-[collapsible=icon]:hidden {currentPath === item.href ? 'font-semibold' : 'font-medium'}"
                      >{item.label}</span>
                      {#if item.count !== undefined && item.count !== null}
                        <span
                          class="ml-auto inline-flex shrink-0 items-center rounded-[4px] px-1.5 text-[11px] font-medium tabular-nums text-[color:var(--sidebar-subtle)] group-data-[collapsible=icon]:hidden"
                        >{item.count}</span>
                      {/if}
                    </a>
                  {/snippet}
                </Sidebar.MenuButton>
              </Sidebar.MenuItem>
            {/if}
          {/each}
        </Sidebar.Menu>
      </Sidebar.GroupContent>
    </Sidebar.Group>

    <!-- Revenue Section -->
    <Sidebar.Group class="mt-1.5">
      <Sidebar.GroupLabel
        class="mb-1 h-auto px-3 text-[10px] font-semibold leading-none text-[color:var(--sidebar-subtle)] [font-variant:small-caps] [text-transform:lowercase] group-data-[collapsible=icon]:hidden"
      >
        Revenue
      </Sidebar.GroupLabel>
      <Sidebar.GroupContent>
        <Sidebar.Menu class="space-y-px">
          {#each revenueItems as item}
            {#if item.type === 'dropdown' && item.children}
              <Collapsible.Root
                open={openDropdowns[item.key ?? ''] || false}
                onOpenChange={(open) => {
                  if (item.key) openDropdowns[item.key] = open;
                }}
                class="group/collapsible"
              >
                <Sidebar.MenuItem>
                  <Collapsible.Trigger>
                    {#snippet child({ props })}
                      <Sidebar.MenuButton
                        {...props}
                        isActive={hasActiveChild(item.children ?? [])}
                        tooltipContent={item.label}
                        class="nav-item group/item relative h-[30px] rounded-md pl-[18px] pr-[10px] transition-colors duration-150
                          group-data-[collapsible=icon]:size-8 group-data-[collapsible=icon]:rounded-md group-data-[collapsible=icon]:px-0
                          {hasActiveChild(item.children ?? [])
                          ? 'text-[color:var(--sidebar-foreground)] group-data-[collapsible=icon]:bg-[color:var(--sidebar-active-fill)]'
                          : 'text-[color:var(--sidebar-muted)] hover:bg-[color:var(--sidebar-accent)] hover:text-[color:var(--sidebar-foreground)]'}"
                      >
                        {#snippet child({ props: btnProps })}
                          <button {...btnProps}>
                            {#if hasActiveChild(item.children ?? [])}
                              <span
                                aria-hidden="true"
                                class="absolute left-[7px] top-1/2 size-1 -translate-y-1/2 rounded-full bg-[color:var(--sidebar-foreground)] group-data-[collapsible=icon]:hidden"
                              ></span>
                            {/if}
                            <item.icon
                              class="size-[15px] shrink-0 {hasActiveChild(item.children ?? []) ? 'text-[color:var(--sidebar-foreground)]' : 'text-[color:var(--sidebar-subtle)] group-hover/item:text-[color:var(--sidebar-foreground)]'}"
                              strokeWidth={1.6}
                            />
                            <span
                              class="flex-1 truncate text-[14px] group-data-[collapsible=icon]:hidden {hasActiveChild(item.children ?? []) ? 'font-semibold' : 'font-medium'}"
                            >{item.label}</span>
                            {#if item.count !== undefined && item.count !== null}
                              <span
                                class="inline-flex shrink-0 items-center rounded-[4px] px-1.5 text-[11px] font-medium tabular-nums text-[color:var(--sidebar-subtle)] group-data-[collapsible=icon]:hidden"
                              >{item.count}</span>
                            {/if}
                            <ChevronDown
                              class="ml-1 size-3.5 shrink-0 text-[color:var(--sidebar-subtle)] transition-transform duration-150 group-data-[collapsible=icon]:hidden group-data-[state=open]/collapsible:rotate-180"
                            />
                          </button>
                        {/snippet}
                      </Sidebar.MenuButton>
                    {/snippet}
                  </Collapsible.Trigger>
                  <Collapsible.Content>
                    <Sidebar.MenuSub
                      class="ml-0 mt-0.5 mb-1 space-y-px border-none p-0"
                    >
                      {#each item.children as navChild}
                        <Sidebar.MenuSubItem>
                          <Sidebar.MenuSubButton
                            isActive={currentPath === navChild.href}
                            class="group/subitem relative h-[26px] rounded-md pl-[38px] pr-[10px] transition-colors duration-150
                              {currentPath === navChild.href
                              ? 'text-[color:var(--sidebar-foreground)]'
                              : 'text-[color:var(--sidebar-muted)] hover:bg-[color:var(--sidebar-accent)] hover:text-[color:var(--sidebar-foreground)]'}"
                          >
                            {#snippet child({ props })}
                              <a href={navChild.href} {...props}>
                                {#if currentPath === navChild.href}
                                  <span
                                    aria-hidden="true"
                                    class="absolute left-[27px] top-1/2 size-1 -translate-y-1/2 rounded-full bg-[color:var(--sidebar-foreground)]"
                                  ></span>
                                {/if}
                                <span
                                  class="flex-1 truncate text-[13px] {currentPath === navChild.href ? 'font-semibold' : 'font-medium'}"
                                >{navChild.label}</span>
                                {#if navChild.count !== undefined && navChild.count !== null}
                                  <span
                                    class="ml-auto inline-flex shrink-0 items-center rounded-[4px] bg-[color:var(--sidebar-accent)] px-1.5 text-[11px] font-medium tabular-nums text-[color:var(--sidebar-subtle)]"
                                  >{navChild.count}</span>
                                {/if}
                              </a>
                            {/snippet}
                          </Sidebar.MenuSubButton>
                        </Sidebar.MenuSubItem>
                      {/each}
                    </Sidebar.MenuSub>
                  </Collapsible.Content>
                </Sidebar.MenuItem>
              </Collapsible.Root>
            {:else}
              <Sidebar.MenuItem>
                <Sidebar.MenuButton
                  isActive={currentPath === item.href}
                  tooltipContent={item.label}
                  class="nav-item group/item relative h-[30px] rounded-md pl-[18px] pr-[10px] transition-colors duration-150
                    group-data-[collapsible=icon]:size-8 group-data-[collapsible=icon]:rounded-md group-data-[collapsible=icon]:px-0
                    {currentPath === item.href
                    ? 'text-[color:var(--sidebar-foreground)] group-data-[collapsible=icon]:bg-[color:var(--sidebar-active-fill)]'
                    : 'text-[color:var(--sidebar-muted)] hover:bg-[color:var(--sidebar-accent)] hover:text-[color:var(--sidebar-foreground)]'}"
                >
                  {#snippet child({ props })}
                    <a
                      href={item.href}
                      {...props}
                      data-sveltekit-preload-data={item.preload || 'hover'}
                     
                    >
                      {#if currentPath === item.href}
                        <span
                          aria-hidden="true"
                          class="absolute left-[7px] top-1/2 size-1 -translate-y-1/2 rounded-full bg-[color:var(--sidebar-foreground)] group-data-[collapsible=icon]:hidden"
                        ></span>
                      {/if}
                      <item.icon
                        class="size-[15px] shrink-0 {currentPath === item.href ? 'text-[color:var(--sidebar-foreground)]' : 'text-[color:var(--sidebar-subtle)] group-hover/item:text-[color:var(--sidebar-foreground)]'}"
                        strokeWidth={1.6}
                      />
                      <span
                        class="flex-1 truncate text-[14px] group-data-[collapsible=icon]:hidden {currentPath === item.href ? 'font-semibold' : 'font-medium'}"
                      >{item.label}</span>
                      {#if item.count !== undefined && item.count !== null}
                        <span
                          class="ml-auto inline-flex shrink-0 items-center rounded-[4px] px-1.5 text-[11px] font-medium tabular-nums text-[color:var(--sidebar-subtle)] group-data-[collapsible=icon]:hidden"
                        >{item.count}</span>
                      {/if}
                    </a>
                  {/snippet}
                </Sidebar.MenuButton>
              </Sidebar.MenuItem>
            {/if}
          {/each}
        </Sidebar.Menu>
      </Sidebar.GroupContent>
    </Sidebar.Group>

    <!-- Support Section -->
    <Sidebar.Group class="mt-1.5">
      <Sidebar.GroupLabel
        class="mb-1 h-auto px-3 text-[10px] font-semibold leading-none text-[color:var(--sidebar-subtle)] [font-variant:small-caps] [text-transform:lowercase] group-data-[collapsible=icon]:hidden"
      >
        Support
      </Sidebar.GroupLabel>
      <Sidebar.GroupContent>
        <Sidebar.Menu class="space-y-px">
          {#each supportItems as item}
            {#if item.type === 'dropdown' && item.children}
              <Collapsible.Root
                open={openDropdowns[item.key ?? ''] || false}
                onOpenChange={(open) => {
                  if (item.key) openDropdowns[item.key] = open;
                }}
                class="group/collapsible"
              >
                <Sidebar.MenuItem>
                  <Collapsible.Trigger>
                    {#snippet child({ props })}
                      <Sidebar.MenuButton
                        {...props}
                        isActive={hasActiveChild(item.children ?? [])}
                        tooltipContent={item.label}
                        class="nav-item group/item relative h-[30px] rounded-md pl-[18px] pr-[10px] transition-colors duration-150
                          group-data-[collapsible=icon]:size-8 group-data-[collapsible=icon]:rounded-md group-data-[collapsible=icon]:px-0
                          {hasActiveChild(item.children ?? [])
                          ? 'text-[color:var(--sidebar-foreground)] group-data-[collapsible=icon]:bg-[color:var(--sidebar-active-fill)]'
                          : 'text-[color:var(--sidebar-muted)] hover:bg-[color:var(--sidebar-accent)] hover:text-[color:var(--sidebar-foreground)]'}"
                      >
                        {#snippet child({ props: btnProps })}
                          <button {...btnProps}>
                            {#if hasActiveChild(item.children ?? [])}
                              <span
                                aria-hidden="true"
                                class="absolute left-[7px] top-1/2 size-1 -translate-y-1/2 rounded-full bg-[color:var(--sidebar-foreground)] group-data-[collapsible=icon]:hidden"
                              ></span>
                            {/if}
                            <item.icon
                              class="size-[15px] shrink-0 {hasActiveChild(item.children ?? []) ? 'text-[color:var(--sidebar-foreground)]' : 'text-[color:var(--sidebar-subtle)] group-hover/item:text-[color:var(--sidebar-foreground)]'}"
                              strokeWidth={1.6}
                            />
                            <span
                              class="flex-1 truncate text-[14px] group-data-[collapsible=icon]:hidden {hasActiveChild(item.children ?? []) ? 'font-semibold' : 'font-medium'}"
                            >{item.label}</span>
                            {#if item.count !== undefined && item.count !== null}
                              <span
                                class="inline-flex shrink-0 items-center rounded-[4px] px-1.5 text-[11px] font-medium tabular-nums text-[color:var(--sidebar-subtle)] group-data-[collapsible=icon]:hidden"
                              >{item.count}</span>
                            {/if}
                            <ChevronDown
                              class="ml-1 size-3.5 shrink-0 text-[color:var(--sidebar-subtle)] transition-transform duration-150 group-data-[collapsible=icon]:hidden group-data-[state=open]/collapsible:rotate-180"
                            />
                          </button>
                        {/snippet}
                      </Sidebar.MenuButton>
                    {/snippet}
                  </Collapsible.Trigger>
                  <Collapsible.Content>
                    <Sidebar.MenuSub
                      class="ml-0 mt-0.5 mb-1 space-y-px border-none p-0"
                    >
                      {#each item.children as navChild}
                        <Sidebar.MenuSubItem>
                          <Sidebar.MenuSubButton
                            isActive={currentPath === navChild.href}
                            class="group/subitem relative h-[26px] rounded-md pl-[38px] pr-[10px] transition-colors duration-150
                              {currentPath === navChild.href
                              ? 'text-[color:var(--sidebar-foreground)]'
                              : 'text-[color:var(--sidebar-muted)] hover:bg-[color:var(--sidebar-accent)] hover:text-[color:var(--sidebar-foreground)]'}"
                          >
                            {#snippet child({ props })}
                              <a href={navChild.href} {...props}>
                                {#if currentPath === navChild.href}
                                  <span
                                    aria-hidden="true"
                                    class="absolute left-[27px] top-1/2 size-1 -translate-y-1/2 rounded-full bg-[color:var(--sidebar-foreground)]"
                                  ></span>
                                {/if}
                                <span
                                  class="flex-1 truncate text-[13px] {currentPath === navChild.href ? 'font-semibold' : 'font-medium'}"
                                >{navChild.label}</span>
                                {#if navChild.count !== undefined && navChild.count !== null}
                                  <span
                                    class="ml-auto inline-flex shrink-0 items-center rounded-[4px] bg-[color:var(--sidebar-accent)] px-1.5 text-[11px] font-medium tabular-nums text-[color:var(--sidebar-subtle)]"
                                  >{navChild.count}</span>
                                {/if}
                              </a>
                            {/snippet}
                          </Sidebar.MenuSubButton>
                        </Sidebar.MenuSubItem>
                      {/each}
                    </Sidebar.MenuSub>
                  </Collapsible.Content>
                </Sidebar.MenuItem>
              </Collapsible.Root>
            {:else}
              <Sidebar.MenuItem>
                <Sidebar.MenuButton
                  isActive={currentPath === item.href}
                  tooltipContent={item.label}
                  class="nav-item group/item relative h-[30px] rounded-md pl-[18px] pr-[10px] transition-colors duration-150
                    group-data-[collapsible=icon]:size-8 group-data-[collapsible=icon]:rounded-md group-data-[collapsible=icon]:px-0
                    {currentPath === item.href
                    ? 'text-[color:var(--sidebar-foreground)] group-data-[collapsible=icon]:bg-[color:var(--sidebar-active-fill)]'
                    : 'text-[color:var(--sidebar-muted)] hover:bg-[color:var(--sidebar-accent)] hover:text-[color:var(--sidebar-foreground)]'}"
                >
                  {#snippet child({ props })}
                    <a
                      href={item.href}
                      {...props}
                      data-sveltekit-preload-data={item.preload || 'hover'}
                     
                    >
                      {#if currentPath === item.href}
                        <span
                          aria-hidden="true"
                          class="absolute left-[7px] top-1/2 size-1 -translate-y-1/2 rounded-full bg-[color:var(--sidebar-foreground)] group-data-[collapsible=icon]:hidden"
                        ></span>
                      {/if}
                      <item.icon
                        class="size-[15px] shrink-0 {currentPath === item.href ? 'text-[color:var(--sidebar-foreground)]' : 'text-[color:var(--sidebar-subtle)] group-hover/item:text-[color:var(--sidebar-foreground)]'}"
                        strokeWidth={1.6}
                      />
                      <span
                        class="flex-1 truncate text-[14px] group-data-[collapsible=icon]:hidden {currentPath === item.href ? 'font-semibold' : 'font-medium'}"
                      >{item.label}</span>
                      {#if item.count !== undefined && item.count !== null}
                        <span
                          class="ml-auto inline-flex shrink-0 items-center rounded-[4px] px-1.5 text-[11px] font-medium tabular-nums text-[color:var(--sidebar-subtle)] group-data-[collapsible=icon]:hidden"
                        >{item.count}</span>
                      {/if}
                    </a>
                  {/snippet}
                </Sidebar.MenuButton>
              </Sidebar.MenuItem>
            {/if}
          {/each}
        </Sidebar.Menu>
      </Sidebar.GroupContent>
    </Sidebar.Group>
  </Sidebar.Content>

  <Sidebar.Footer class="border-t border-[color:var(--sidebar-border)] px-2 py-2">
    <Sidebar.Menu class="space-y-px">
      <!-- Download mobile app -->
      <Sidebar.MenuItem>
        <Sidebar.MenuButton
          tooltipContent="Download mobile app"
          class="h-[30px] rounded-md pl-[18px] pr-[10px] text-[color:var(--sidebar-muted)] transition-colors duration-150 hover:bg-[color:var(--sidebar-accent)] hover:text-[color:var(--sidebar-foreground)]
            group-data-[collapsible=icon]:size-8 group-data-[collapsible=icon]:rounded-md group-data-[collapsible=icon]:px-0"
        >
          {#snippet child({ props })}
            <a
              {...props}
              href="https://play.google.com/store/apps/details?id=io.bottlecrm&hl=en"
              target="_blank"
              rel="noopener noreferrer"
            >
              <span class="relative inline-flex shrink-0">
                <Smartphone
                  class="size-[15px] text-[color:var(--sidebar-subtle)]"
                  strokeWidth={1.6}
                  aria-hidden="true"
                />
                <span class="pointer-events-none absolute -right-0.5 -top-0.5 inline-flex size-1.5">
                  <span class="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75"></span>
                  <span class="relative inline-flex size-1.5 rounded-full bg-emerald-500"></span>
                </span>
              </span>
              <span class="flex-1 text-[13px] font-medium group-data-[collapsible=icon]:hidden">
                Download app
              </span>
            </a>
          {/snippet}
        </Sidebar.MenuButton>
      </Sidebar.MenuItem>

      <!-- Collapse/Expand Toggle -->
      <Sidebar.MenuItem>
        <Sidebar.MenuButton
          onclick={() => sidebar.toggle()}
          tooltipContent={sidebar.state === 'collapsed' ? 'Expand sidebar' : 'Collapse sidebar'}
          class="h-[30px] rounded-md pl-[18px] pr-[10px] text-[color:var(--sidebar-muted)] transition-colors duration-150 hover:bg-[color:var(--sidebar-accent)] hover:text-[color:var(--sidebar-foreground)]
            group-data-[collapsible=icon]:size-8 group-data-[collapsible=icon]:rounded-md group-data-[collapsible=icon]:px-0"
        >
          {#snippet child({ props })}
            <button {...props}>
              {#if sidebar.state === 'collapsed'}
                <PanelLeft class="size-[15px] shrink-0 text-[color:var(--sidebar-subtle)]" strokeWidth={1.6} />
              {:else}
                <PanelLeftClose class="size-[15px] shrink-0 text-[color:var(--sidebar-subtle)]" strokeWidth={1.6} />
              {/if}
              <span class="flex-1 text-[13px] font-medium group-data-[collapsible=icon]:hidden">
                Collapse
              </span>
            </button>
          {/snippet}
        </Sidebar.MenuButton>
      </Sidebar.MenuItem>

      <!-- User Menu - HubSpot Style -->
      <Sidebar.MenuItem>
        <DropdownMenu.Root>
          <DropdownMenu.Trigger>
            {#snippet child({ props })}
              <Sidebar.MenuButton
                size="lg"
                {...props}
                class="group/user h-11 rounded-md px-2 transition-colors duration-150 hover:bg-[color:var(--sidebar-accent)] data-[state=open]:bg-[color:var(--sidebar-accent)]
                  group-data-[collapsible=icon]:size-8 group-data-[collapsible=icon]:rounded-md group-data-[collapsible=icon]:px-0"
              >
                {#if user.profilePhoto && !profileImageError}
                  <img
                    class="size-6 shrink-0 rounded-full object-cover"
                    src={user.profilePhoto}
                    alt="User avatar"
                    onerror={() => (profileImageError = true)}
                  />
                {:else}
                  <Avatar class="size-6 shrink-0 rounded-full">
                    <AvatarFallback gradientSeed={user.email ?? user.name ?? 'user'} class="rounded-full text-[10px] font-semibold">
                      {getInitials(user.name)}
                    </AvatarFallback>
                  </Avatar>
                {/if}
                <div class="flex min-w-0 flex-1 flex-col leading-tight group-data-[collapsible=icon]:hidden">
                  <span class="truncate text-[14px] font-semibold text-[color:var(--sidebar-foreground)]">{user.name}</span>
                  <span class="truncate text-[11px] text-[color:var(--sidebar-subtle)]">{user.email}</span>
                </div>
                <ChevronsUpDown class="ml-auto size-3.5 shrink-0 text-[color:var(--sidebar-subtle)] group-data-[collapsible=icon]:hidden" strokeWidth={1.6} />
              </Sidebar.MenuButton>
            {/snippet}
          </DropdownMenu.Trigger>
          <DropdownMenu.Content
            side="top"
            align="start"
            class="w-[--bits-dropdown-menu-anchor-width] min-w-56"
          >
            <DropdownMenu.Label
              class="text-muted-foreground text-[10px] font-bold tracking-wider uppercase"
            >
              My Account
            </DropdownMenu.Label>
            <DropdownMenu.Separator />
            <DropdownMenu.Group>
              <DropdownMenu.Item
                inset={false}
                onclick={() => navigateTo('/profile')}
                class="gap-2.5"
              >
                <User class="size-4" />
                <span>Profile</span>
              </DropdownMenu.Item>
              <DropdownMenu.Item inset={false} onclick={() => navigateTo('/users')} class="gap-2.5">
                <Users class="size-4" />
                <span>Users & Teams</span>
              </DropdownMenu.Item>
              <DropdownMenu.Item inset={false} onclick={() => navigateTo('/org')} class="gap-2.5">
                <Building class="size-4" />
                <span>Organizations</span>
              </DropdownMenu.Item>
              <DropdownMenu.Item
                inset={false}
                onclick={() => navigateTo('/settings/organization')}
                class="gap-2.5"
              >
                <Settings class="size-4" />
                <span>Settings</span>
              </DropdownMenu.Item>
              <DropdownMenu.Item
                inset={false}
                onclick={() => navigateTo('/settings/salesforce')}
                class="gap-2.5"
              >
                <Cloud class="size-4" />
                <span>Salesforce</span>
              </DropdownMenu.Item>
              <DropdownMenu.Item
                inset={false}
                onclick={() => navigateTo('/settings/tags')}
                class="gap-2.5"
              >
                <Tag class="size-4" />
                <span>Tags</span>
              </DropdownMenu.Item>
              <DropdownMenu.Item
                inset={false}
                onclick={() => navigateTo('/settings/reopen')}
                class="gap-2.5"
              >
                <RotateCcw class="size-4" />
                <span>Reopen Policy</span>
              </DropdownMenu.Item>
              <DropdownMenu.Item
                inset={false}
                onclick={() => navigateTo('/settings/custom-fields')}
                class="gap-2.5"
              >
                <Sliders class="size-4" />
                <span>Custom Fields</span>
              </DropdownMenu.Item>
              <DropdownMenu.Item
                inset={false}
                onclick={() => navigateTo('/settings/routing')}
                class="gap-2.5"
              >
                <Route class="size-4" />
                <span>Auto-Routing</span>
              </DropdownMenu.Item>
              <DropdownMenu.Item
                inset={false}
                onclick={() => navigateTo('/settings/escalation')}
                class="gap-2.5"
              >
                <Megaphone class="size-4" />
                <span>Escalation</span>
              </DropdownMenu.Item>
              <DropdownMenu.Item
                inset={false}
                onclick={() => navigateTo('/settings/ticket-approvals')}
                class="gap-2.5"
              >
                <ShieldCheck class="size-4" />
                <span>Approval Rules</span>
              </DropdownMenu.Item>
              <DropdownMenu.Item
                inset={false}
                onclick={() => navigateTo('/settings/inbound-email')}
                class="gap-2.5"
              >
                <Mail class="size-4" />
                <span>Inbound Email</span>
              </DropdownMenu.Item>
              <DropdownMenu.Item
                inset={false}
                onclick={() => navigateTo('/settings/business-hours')}
                class="gap-2.5"
              >
                <Clock class="size-4" />
                <span>Business Hours</span>
              </DropdownMenu.Item>
              <DropdownMenu.Item
                inset={false}
                onclick={() => navigateTo('/settings/macros')}
                class="gap-2.5"
              >
                <MessageSquareQuote class="size-4" />
                <span>Macros</span>
              </DropdownMenu.Item>
            </DropdownMenu.Group>
            <DropdownMenu.Separator />
            <DropdownMenu.Label
              class="text-muted-foreground text-[10px] font-bold tracking-wider uppercase"
            >
              Theme
            </DropdownMenu.Label>
            <DropdownMenu.Group class="flex gap-1 px-2 py-1.5">
              <button
                onclick={() => setTheme('light')}
                class="flex flex-1 flex-col items-center gap-1 rounded-md px-2 py-2 transition-colors {theme ===
                'light'
                  ? 'bg-[#ff7a59]/10 text-[#ff7a59]'
                  : 'hover:bg-sidebar-accent text-muted-foreground hover:text-foreground'}"
              >
                <Sun class="size-4" />
                <span class="text-[10px] font-medium">Light</span>
              </button>
              <button
                onclick={() => setTheme('dark')}
                class="flex flex-1 flex-col items-center gap-1 rounded-md px-2 py-2 transition-colors {theme ===
                'dark'
                  ? 'bg-[#ff7a59]/10 text-[#ff7a59]'
                  : 'hover:bg-sidebar-accent text-muted-foreground hover:text-foreground'}"
              >
                <Moon class="size-4" />
                <span class="text-[10px] font-medium">Dark</span>
              </button>
              <button
                onclick={() => setTheme('system')}
                class="flex flex-1 flex-col items-center gap-1 rounded-md px-2 py-2 transition-colors {theme ===
                'system'
                  ? 'bg-[#ff7a59]/10 text-[#ff7a59]'
                  : 'hover:bg-sidebar-accent text-muted-foreground hover:text-foreground'}"
              >
                <Monitor class="size-4" />
                <span class="text-[10px] font-medium">System</span>
              </button>
            </DropdownMenu.Group>
            <DropdownMenu.Separator />
            <DropdownMenu.Item
              class="text-destructive focus:bg-destructive/10 focus:text-destructive gap-2.5"
              inset={false}
              onclick={() => navigateTo('/logout')}
            >
              <LogOut class="size-4" />
              <span>Sign out</span>
            </DropdownMenu.Item>
          </DropdownMenu.Content>
        </DropdownMenu.Root>
      </Sidebar.MenuItem>
    </Sidebar.Menu>
  </Sidebar.Footer>

  <Sidebar.Rail />
</Sidebar.Root>

<style>
  /* Refined sidebar typography */
  :global(.hubspot-sidebar) {
    font-family:
      'Geist',
      -apple-system,
      BlinkMacSystemFont,
      'Segoe UI',
      sans-serif;
  }

  :global(.hubspot-sidebar [data-sidebar='menu-button']) {
    font-weight: 500;
    cursor: pointer;
  }
  :global(.hubspot-sidebar [data-sidebar='menu-sub-button']) {
    cursor: pointer;
  }
</style>
