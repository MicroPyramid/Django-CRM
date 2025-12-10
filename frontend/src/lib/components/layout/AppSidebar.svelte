<script>
  import { page } from '$app/stores';
  import { afterNavigate } from '$app/navigation';
  import imgLogo from '$lib/assets/images/logo.png';

  import * as Sidebar from '$lib/components/ui/sidebar/index.js';
  import * as DropdownMenu from '$lib/components/ui/dropdown-menu/index.js';
  import * as Collapsible from '$lib/components/ui/collapsible/index.js';
  import { Button } from '$lib/components/ui/button/index.js';

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
    FileText,
    FileEdit,
    Package,
    RefreshCw,
    FileCode,
    BarChart3,
    Tag,
    Sparkles,
    Search,
    Star,
    Home
  } from '@lucide/svelte';

  /**
   * @typedef {Object} Props
   * @property {Object} user - User object
   * @property {string} [org_name] - Organization name
   */

  /** @type {Props} */
  let { user = {}, org_name = 'BottleCRM' } = $props();

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

  // Auto-open dropdown if a child is active
  $effect(() => {
    navigationItems.forEach((item) => {
      if (item.type === 'dropdown' && item.children && item.key) {
        const hasActiveChild = item.children.some((child) => currentPath === child.href);
        if (hasActiveChild && !openDropdowns[item.key]) {
          openDropdowns[item.key] = true;
        }
      }
    });
  });

  // Close mobile sidebar after navigation
  afterNavigate(() => {
    if (sidebar.isMobile) {
      sidebar.setOpenMobile(false);
    }
  });

  // HubSpot-style navigation structure with sections
  const crmItems = [
    {
      href: '/',
      label: 'Dashboard',
      icon: Home,
      type: 'link',
      preload: 'off'
    },
    {
      href: '/leads',
      label: 'Leads',
      icon: Target,
      type: 'link',
      preload: 'off'
    },
    {
      href: '/contacts',
      label: 'Contacts',
      icon: Users,
      type: 'link',
      preload: 'off'
    },
    {
      href: '/accounts',
      label: 'Companies',
      icon: Building,
      type: 'link',
      preload: 'off'
    },
    {
      href: '/opportunities',
      label: 'Deals',
      icon: Sparkles,
      type: 'link',
      preload: 'off'
    },
    {
      href: '/cases',
      label: 'Tickets',
      icon: Briefcase,
      type: 'link',
      preload: 'off'
    },
    {
      href: '/tasks',
      label: 'Tasks',
      icon: CheckSquare,
      type: 'link',
      preload: 'off'
    }
  ];

  const salesItems = [
    {
      key: 'invoices',
      label: 'Invoices',
      icon: FileText,
      type: 'dropdown',
      children: [
        { href: '/invoices', label: 'All Invoices', icon: FileText, preload: 'off' },
        { href: '/invoices/estimates', label: 'Estimates', icon: FileEdit, preload: 'off' },
        { href: '/invoices/products', label: 'Products', icon: Package, preload: 'off' },
        { href: '/invoices/recurring', label: 'Recurring', icon: RefreshCw, preload: 'off' },
        { href: '/invoices/templates', label: 'Templates', icon: FileCode, preload: 'off' },
        { href: '/invoices/reports', label: 'Reports', icon: BarChart3, preload: 'off' }
      ]
    }
  ];

  const supportItems = [
    {
      href: '/support',
      label: 'Help Desk',
      icon: HelpCircle,
      type: 'link',
      preload: 'off'
    }
  ];

  // Combine for iteration
  const navigationItems = [...crmItems, ...salesItems, ...supportItems];

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
    window.location.href = url;
  };
</script>

<Sidebar.Root collapsible="icon" class="hubspot-sidebar border-r border-sidebar-border/60 bg-sidebar">
  <!-- Header with Logo - HubSpot Style -->
  <Sidebar.Header class="px-3 py-4">
    <Sidebar.Menu>
      <Sidebar.MenuItem>
        <Sidebar.MenuButton size="lg" class="group relative hover:bg-transparent">
          {#snippet child({ props })}
            <a href="/" {...props} class="flex items-center gap-3">
              <!-- Logo Container -->
              <div
                class="flex size-9 items-center justify-center rounded-lg bg-gradient-to-br from-[#ff7a59] to-[#ff5c35] shadow-md shadow-[#ff7a59]/20 transition-transform duration-200 group-hover:scale-105"
              >
                <img src={imgLogo} alt="Logo" class="size-5" />
              </div>
              <div class="grid flex-1 text-left leading-tight group-data-[collapsible=icon]:hidden">
                <span class="truncate text-[15px] font-semibold tracking-tight text-sidebar-foreground">{org_name}</span>
                <span class="truncate text-[11px] font-medium text-sidebar-foreground/50">
                  CRM Platform
                </span>
              </div>
            </a>
          {/snippet}
        </Sidebar.MenuButton>
      </Sidebar.MenuItem>
    </Sidebar.Menu>
  </Sidebar.Header>

  <!-- Quick Search Bar - HubSpot Style -->
  <div class="mx-3 mb-3 group-data-[collapsible=icon]:mx-2 group-data-[collapsible=icon]:hidden">
    <button
      class="flex h-9 w-full items-center gap-2 rounded-lg border border-sidebar-border/60 bg-sidebar-accent/30 px-3 text-sm text-sidebar-foreground/60 transition-all hover:border-sidebar-border hover:bg-sidebar-accent/50"
    >
      <Search class="size-4" />
      <span class="flex-1 text-left">Search...</span>
      <kbd class="hidden rounded bg-sidebar-accent px-1.5 py-0.5 text-[10px] font-medium text-sidebar-foreground/50 sm:inline-block">⌘K</kbd>
    </button>
  </div>

  <Sidebar.Content class="px-2">
    <!-- CRM Section -->
    <Sidebar.Group>
      <Sidebar.GroupLabel class="mb-1 px-3 text-[10px] font-bold uppercase tracking-widest text-sidebar-foreground/40 group-data-[collapsible=icon]:hidden">
        CRM
      </Sidebar.GroupLabel>
      <Sidebar.GroupContent>
        <Sidebar.Menu class="space-y-0.5">
          {#each crmItems as item}
            <Sidebar.MenuItem>
              <Sidebar.MenuButton
                isActive={currentPath === item.href}
                tooltipContent={item.label}
                class="hubspot-menu-item group/item relative h-9 rounded-lg px-3 transition-all duration-150
                  {currentPath === item.href
                    ? 'bg-[#fff1ee] text-[#ff5c35] dark:bg-[#ff7a59]/10 dark:text-[#ff7a59]'
                    : 'text-sidebar-foreground/80 hover:bg-sidebar-accent hover:text-sidebar-foreground'}"
              >
                {#snippet child({ props })}
                  <a
                    href={item.href}
                    {...props}
                    data-sveltekit-preload-data={item.preload || 'hover'}
                    class="flex items-center gap-3"
                  >
                    <!-- Active indicator bar - HubSpot style left border -->
                    {#if currentPath === item.href}
                      <div class="absolute left-0 top-1/2 h-5 w-[3px] -translate-y-1/2 rounded-r-full bg-[#ff7a59]"></div>
                    {/if}
                    <div class="flex size-5 items-center justify-center">
                      <item.icon
                        class="size-[18px] transition-colors duration-150"
                        strokeWidth={currentPath === item.href ? 2.25 : 1.75}
                      />
                    </div>
                    <span class="text-[13px] font-medium">{item.label}</span>
                  </a>
                {/snippet}
              </Sidebar.MenuButton>
            </Sidebar.MenuItem>
          {/each}
        </Sidebar.Menu>
      </Sidebar.GroupContent>
    </Sidebar.Group>

    <!-- Sales Section -->
    <Sidebar.Group class="mt-4">
      <Sidebar.GroupLabel class="mb-1 px-3 text-[10px] font-bold uppercase tracking-widest text-sidebar-foreground/40 group-data-[collapsible=icon]:hidden">
        Sales
      </Sidebar.GroupLabel>
      <Sidebar.GroupContent>
        <Sidebar.Menu class="space-y-0.5">
          {#each salesItems as item}
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
                        class="hubspot-menu-item group/item h-9 rounded-lg px-3 transition-all duration-150
                          {hasActiveChild(item.children ?? [])
                            ? 'text-[#ff5c35] dark:text-[#ff7a59]'
                            : 'text-sidebar-foreground/80 hover:bg-sidebar-accent hover:text-sidebar-foreground'}"
                      >
                        <div class="flex w-full items-center gap-3">
                          <div class="flex size-5 items-center justify-center">
                            <item.icon class="size-[18px]" strokeWidth={1.75} />
                          </div>
                          <span class="text-[13px] font-medium">{item.label}</span>
                          <ChevronDown
                            class="ml-auto size-4 text-sidebar-foreground/40 transition-transform duration-200 group-data-[state=open]/collapsible:rotate-180"
                          />
                        </div>
                      </Sidebar.MenuButton>
                    {/snippet}
                  </Collapsible.Trigger>
                  <Collapsible.Content>
                    <Sidebar.MenuSub class="hubspot-submenu mt-1 border-l-2 border-sidebar-border/50 ml-[18px] pl-4 py-1">
                      {#each item.children as navChild}
                        <Sidebar.MenuSubItem>
                          <Sidebar.MenuSubButton
                            isActive={currentPath === navChild.href}
                            class="hubspot-submenu-item group/subitem relative h-8 rounded-md px-2 transition-all duration-150
                              {currentPath === navChild.href
                                ? 'bg-[#fff1ee] text-[#ff5c35] dark:bg-[#ff7a59]/10 dark:text-[#ff7a59]'
                                : 'text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-sidebar-foreground'}"
                          >
                            {#snippet child({ props })}
                              <a href={navChild.href} {...props} class="flex items-center gap-2.5">
                                <div class="flex size-4 items-center justify-center">
                                  <navChild.icon class="size-3.5" strokeWidth={1.75} />
                                </div>
                                <span class="text-[12px] font-medium">{navChild.label}</span>
                              </a>
                            {/snippet}
                          </Sidebar.MenuSubButton>
                        </Sidebar.MenuSubItem>
                      {/each}
                    </Sidebar.MenuSub>
                  </Collapsible.Content>
                </Sidebar.MenuItem>
              </Collapsible.Root>
            {/if}
          {/each}
        </Sidebar.Menu>
      </Sidebar.GroupContent>
    </Sidebar.Group>

    <!-- Support Section -->
    <Sidebar.Group class="mt-4">
      <Sidebar.GroupLabel class="mb-1 px-3 text-[10px] font-bold uppercase tracking-widest text-sidebar-foreground/40 group-data-[collapsible=icon]:hidden">
        Support
      </Sidebar.GroupLabel>
      <Sidebar.GroupContent>
        <Sidebar.Menu class="space-y-0.5">
          {#each supportItems as item}
            <Sidebar.MenuItem>
              <Sidebar.MenuButton
                isActive={currentPath === item.href}
                tooltipContent={item.label}
                class="hubspot-menu-item group/item relative h-9 rounded-lg px-3 transition-all duration-150
                  {currentPath === item.href
                    ? 'bg-[#fff1ee] text-[#ff5c35] dark:bg-[#ff7a59]/10 dark:text-[#ff7a59]'
                    : 'text-sidebar-foreground/80 hover:bg-sidebar-accent hover:text-sidebar-foreground'}"
              >
                {#snippet child({ props })}
                  <a
                    href={item.href}
                    {...props}
                    data-sveltekit-preload-data={item.preload || 'hover'}
                    class="flex items-center gap-3"
                  >
                    {#if currentPath === item.href}
                      <div class="absolute left-0 top-1/2 h-5 w-[3px] -translate-y-1/2 rounded-r-full bg-[#ff7a59]"></div>
                    {/if}
                    <div class="flex size-5 items-center justify-center">
                      <item.icon
                        class="size-[18px] transition-colors duration-150"
                        strokeWidth={currentPath === item.href ? 2.25 : 1.75}
                      />
                    </div>
                    <span class="text-[13px] font-medium">{item.label}</span>
                  </a>
                {/snippet}
              </Sidebar.MenuButton>
            </Sidebar.MenuItem>
          {/each}
        </Sidebar.Menu>
      </Sidebar.GroupContent>
    </Sidebar.Group>
  </Sidebar.Content>

  <Sidebar.Footer class="border-t border-sidebar-border/60 px-2 py-3">
    <Sidebar.Menu class="space-y-1">
      <!-- Collapse/Expand Toggle - HubSpot Style -->
      <Sidebar.MenuItem class="group-data-[collapsible=icon]:hidden">
        <Sidebar.MenuButton
          onclick={() => sidebar.toggle()}
          tooltipContent="Collapse sidebar"
          class="h-8 rounded-lg px-3 text-sidebar-foreground/60 transition-all duration-150 hover:bg-sidebar-accent hover:text-sidebar-foreground"
        >
          {#snippet child({ props })}
            <button {...props} class="flex w-full items-center gap-3">
              <PanelLeftClose class="size-4" strokeWidth={1.75} />
              <span class="text-[12px] font-medium">Collapse</span>
            </button>
          {/snippet}
        </Sidebar.MenuButton>
      </Sidebar.MenuItem>

      <!-- Expand button when collapsed -->
      <Sidebar.MenuItem class="hidden group-data-[collapsible=icon]:block">
        <Sidebar.MenuButton
          onclick={() => sidebar.toggle()}
          tooltipContent="Expand sidebar"
          class="flex h-8 w-full items-center justify-center rounded-lg text-sidebar-foreground/60 transition-all duration-150 hover:bg-sidebar-accent hover:text-sidebar-foreground"
        >
          {#snippet child({ props })}
            <button {...props} class="flex items-center justify-center">
              <PanelLeft class="size-4" strokeWidth={1.75} />
            </button>
          {/snippet}
        </Sidebar.MenuButton>
      </Sidebar.MenuItem>

      <!-- Theme Switcher -->
      <Sidebar.MenuItem>
        <DropdownMenu.Root>
          <DropdownMenu.Trigger>
            {#snippet child({ props })}
              <Sidebar.MenuButton
                {...props}
                tooltipContent="Theme"
                class="h-8 rounded-lg px-3 text-sidebar-foreground/60 transition-all duration-150 hover:bg-sidebar-accent hover:text-sidebar-foreground"
              >
                <div class="flex size-4 items-center justify-center">
                  {#if theme === 'dark'}
                    <Moon class="size-4 text-[#ff7a59]" strokeWidth={1.75} />
                  {:else if theme === 'light'}
                    <Sun class="size-4 text-amber-500" strokeWidth={1.75} />
                  {:else}
                    <Monitor class="size-4" strokeWidth={1.75} />
                  {/if}
                </div>
                <span class="text-[12px] font-medium">Theme</span>
                <span
                  class="ml-auto rounded-md bg-sidebar-accent px-1.5 py-0.5 text-[10px] font-medium capitalize text-sidebar-foreground/50"
                >
                  {theme}
                </span>
              </Sidebar.MenuButton>
            {/snippet}
          </DropdownMenu.Trigger>
          <DropdownMenu.Content side="top" align="start" class="w-44">
            <DropdownMenu.Item inset={false} onclick={() => setTheme('light')} class="gap-2.5">
              <Sun class="size-4 text-amber-500" />
              <span>Light</span>
              {#if theme === 'light'}
                <div class="ml-auto size-2 rounded-full bg-[#ff7a59]"></div>
              {/if}
            </DropdownMenu.Item>
            <DropdownMenu.Item inset={false} onclick={() => setTheme('dark')} class="gap-2.5">
              <Moon class="size-4 text-[#ff7a59]" />
              <span>Dark</span>
              {#if theme === 'dark'}
                <div class="ml-auto size-2 rounded-full bg-[#ff7a59]"></div>
              {/if}
            </DropdownMenu.Item>
            <DropdownMenu.Item inset={false} onclick={() => setTheme('system')} class="gap-2.5">
              <Monitor class="size-4 text-muted-foreground" />
              <span>System</span>
              {#if theme === 'system'}
                <div class="ml-auto size-2 rounded-full bg-[#ff7a59]"></div>
              {/if}
            </DropdownMenu.Item>
          </DropdownMenu.Content>
        </DropdownMenu.Root>
      </Sidebar.MenuItem>

      <!-- Divider -->
      <div class="mx-3 my-2 h-px bg-sidebar-border/50 group-data-[collapsible=icon]:hidden"></div>

      <!-- User Menu - HubSpot Style -->
      <Sidebar.MenuItem>
        <DropdownMenu.Root>
          <DropdownMenu.Trigger>
            {#snippet child({ props })}
              <Sidebar.MenuButton
                size="lg"
                {...props}
                class="group/user h-12 rounded-lg px-2 transition-all duration-150 data-[state=open]:bg-sidebar-accent hover:bg-sidebar-accent"
              >
                <!-- Avatar with status -->
                <div class="relative">
                  {#if user.profilePhoto && !profileImageError}
                    <img
                      class="size-8 rounded-full object-cover ring-2 ring-sidebar-border/50 transition-all duration-150 group-hover/user:ring-[#ff7a59]/30"
                      src={user.profilePhoto}
                      alt="User avatar"
                      onerror={() => profileImageError = true}
                    />
                  {:else}
                    <div class="flex size-8 items-center justify-center rounded-full bg-gradient-to-br from-[#ff7a59] to-[#ff5c35] text-xs font-semibold text-white ring-2 ring-sidebar-border/50 transition-all duration-150 group-hover/user:ring-[#ff7a59]/30">
                      {getInitials(user.name)}
                    </div>
                  {/if}
                  <!-- Online status indicator -->
                  <div class="absolute -bottom-0.5 -right-0.5 size-2.5 rounded-full border-2 border-sidebar bg-emerald-500"></div>
                </div>
                <div class="grid flex-1 text-left leading-tight">
                  <span class="truncate text-[13px] font-semibold text-sidebar-foreground">{user.name}</span>
                  <span class="truncate text-[11px] text-sidebar-foreground/50">{user.email}</span>
                </div>
                <ChevronsUpDown class="ml-auto size-4 text-sidebar-foreground/40" />
              </Sidebar.MenuButton>
            {/snippet}
          </DropdownMenu.Trigger>
          <DropdownMenu.Content
            side="top"
            align="start"
            class="w-[--bits-dropdown-menu-anchor-width] min-w-56"
          >
            <DropdownMenu.Label class="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
              My Account
            </DropdownMenu.Label>
            <DropdownMenu.Separator />
            <DropdownMenu.Group>
              <DropdownMenu.Item inset={false} onclick={() => navigateTo('/profile')} class="gap-2.5">
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
              <DropdownMenu.Item inset={false} onclick={() => navigateTo('/settings/tags')} class="gap-2.5">
                <Tag class="size-4" />
                <span>Tags</span>
              </DropdownMenu.Item>
            </DropdownMenu.Group>
            <DropdownMenu.Separator />
            <DropdownMenu.Item
              class="gap-2.5 text-destructive focus:bg-destructive/10 focus:text-destructive"
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
  /* HubSpot-style sidebar refinements */
  :global(.hubspot-sidebar) {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  }

  :global(.hubspot-sidebar [data-slot="sidebar-menu-button"]) {
    font-weight: 500;
  }

  /* Smooth hover transition for menu items */
  :global(.hubspot-menu-item) {
    position: relative;
  }

  /* Active state animation */
  :global(.hubspot-menu-item::before) {
    content: '';
    position: absolute;
    left: 0;
    top: 50%;
    transform: translateY(-50%);
    width: 0;
    height: 20px;
    background: #ff7a59;
    border-radius: 0 4px 4px 0;
    transition: width 0.15s ease;
  }

  /* Submenu refinements */
  :global(.hubspot-submenu) {
    position: relative;
  }

  :global(.hubspot-submenu::before) {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 2px;
    background: linear-gradient(180deg, transparent, var(--sidebar-border), transparent);
  }
</style>
