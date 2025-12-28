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
      label: 'Accounts',
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

<Sidebar.Root
  collapsible="icon"
  class="hubspot-sidebar border-sidebar-border/60 bg-sidebar border-r"
>
  <!-- Header with Logo - HubSpot Style -->
  <Sidebar.Header class="px-3 py-4">
    <Sidebar.Menu>
      <Sidebar.MenuItem>
        <Sidebar.MenuButton size="lg" class="group relative hover:bg-transparent">
          {#snippet child({ props })}
            <a href="/" {...props} class="flex items-center gap-3">
              <!-- Logo Container -->
              <div
                class="flex size-9 items-center justify-center transition-transform duration-200 group-hover:scale-105"
              >
                <img src={imgLogo} alt="Logo" class="size-8" />
              </div>
              <div class="grid flex-1 text-left leading-tight group-data-[collapsible=icon]:hidden">
                <span
                  class="text-sidebar-foreground truncate text-[15px] font-semibold tracking-tight"
                  >{org_name}</span
                >
                <span class="text-sidebar-foreground/50 truncate text-[11px] font-medium">
                  CRM Platform
                </span>
              </div>
            </a>
          {/snippet}
        </Sidebar.MenuButton>
      </Sidebar.MenuItem>
    </Sidebar.Menu>
  </Sidebar.Header>

  <Sidebar.Content class="px-2">
    <!-- CRM Section -->
    <Sidebar.Group>
      <Sidebar.GroupLabel
        class="text-sidebar-foreground/40 mb-1 px-3 text-[10px] font-bold tracking-widest uppercase group-data-[collapsible=icon]:hidden"
      >
        CRM
      </Sidebar.GroupLabel>
      <Sidebar.GroupContent>
        <Sidebar.Menu class="space-y-0.5">
          {#each crmItems as item}
            <Sidebar.MenuItem>
              <Sidebar.MenuButton
                isActive={currentPath === item.href}
                tooltipContent={item.label}
                class="nav-item group/item relative h-9 rounded-lg px-2.5 transition-all duration-200
                  {currentPath === item.href
                  ? 'nav-item-active bg-[var(--color-primary-default)]/[0.08] text-[var(--color-primary-default)] shadow-[inset_0_1px_2px_rgba(0,0,0,0.04)] dark:bg-[var(--color-primary-default)]/15 dark:shadow-none'
                  : 'text-sidebar-foreground/70 hover:bg-sidebar-accent/60 hover:text-sidebar-foreground'}"
              >
                {#snippet child({ props })}
                  <a
                    href={item.href}
                    {...props}
                    data-sveltekit-preload-data={item.preload || 'hover'}
                    class="flex items-center gap-2.5"
                  >
                    <div
                      class="flex size-6 items-center justify-center rounded-md transition-all duration-200
                        {currentPath === item.href
                        ? 'bg-[var(--color-primary-default)] text-white shadow-sm shadow-[var(--color-primary-default)]/25'
                        : 'text-current group-hover/item:bg-sidebar-accent'}"
                    >
                      <item.icon
                        class="size-[15px] transition-transform duration-200 {currentPath === item.href ? 'scale-105' : 'group-hover/item:scale-105'}"
                        strokeWidth={2}
                      />
                    </div>
                    <span class="text-[13px] {currentPath === item.href ? 'font-semibold' : 'font-medium'}">{item.label}</span>
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
      <Sidebar.GroupLabel
        class="text-sidebar-foreground/40 mb-1 px-3 text-[10px] font-bold tracking-widest uppercase group-data-[collapsible=icon]:hidden"
      >
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
                        class="nav-item group/item h-9 rounded-lg px-2.5 transition-all duration-200
                          {hasActiveChild(item.children ?? [])
                          ? 'text-[var(--color-primary-default)]'
                          : 'text-sidebar-foreground/70 hover:bg-sidebar-accent/60 hover:text-sidebar-foreground'}"
                      >
                        <div class="flex w-full items-center gap-2.5">
                          <div
                            class="flex size-6 items-center justify-center rounded-md transition-all duration-200
                              {hasActiveChild(item.children ?? [])
                              ? 'bg-[var(--color-primary-default)]/10 text-[var(--color-primary-default)]'
                              : 'text-current group-hover/item:bg-sidebar-accent'}"
                          >
                            <item.icon class="size-[15px]" strokeWidth={2} />
                          </div>
                          <span class="text-[13px] {hasActiveChild(item.children ?? []) ? 'font-semibold' : 'font-medium'}">{item.label}</span>
                          <ChevronDown
                            class="text-sidebar-foreground/40 ml-auto size-4 transition-transform duration-200 group-data-[state=open]/collapsible:rotate-180"
                          />
                        </div>
                      </Sidebar.MenuButton>
                    {/snippet}
                  </Collapsible.Trigger>
                  <Collapsible.Content>
                    <Sidebar.MenuSub
                      class="mt-1.5 ml-[11px] space-y-0.5 border-l border-sidebar-border/40 py-1 pl-3"
                    >
                      {#each item.children as navChild}
                        <Sidebar.MenuSubItem>
                          <Sidebar.MenuSubButton
                            isActive={currentPath === navChild.href}
                            class="nav-subitem group/subitem relative h-7 rounded-md px-2 transition-all duration-200
                              {currentPath === navChild.href
                              ? 'bg-[var(--color-primary-default)]/[0.08] text-[var(--color-primary-default)] dark:bg-[var(--color-primary-default)]/15'
                              : 'text-sidebar-foreground/60 hover:bg-sidebar-accent/50 hover:text-sidebar-foreground'}"
                          >
                            {#snippet child({ props })}
                              <a href={navChild.href} {...props} class="flex items-center gap-2">
                                <navChild.icon
                                  class="size-3.5 transition-colors duration-200"
                                  strokeWidth={currentPath === navChild.href ? 2.25 : 1.75}
                                />
                                <span class="text-[12px] {currentPath === navChild.href ? 'font-semibold' : 'font-medium'}">{navChild.label}</span>
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
      <Sidebar.GroupLabel
        class="text-sidebar-foreground/40 mb-1 px-3 text-[10px] font-bold tracking-widest uppercase group-data-[collapsible=icon]:hidden"
      >
        Support
      </Sidebar.GroupLabel>
      <Sidebar.GroupContent>
        <Sidebar.Menu class="space-y-0.5">
          {#each supportItems as item}
            <Sidebar.MenuItem>
              <Sidebar.MenuButton
                isActive={currentPath === item.href}
                tooltipContent={item.label}
                class="nav-item group/item relative h-9 rounded-lg px-2.5 transition-all duration-200
                  {currentPath === item.href
                  ? 'nav-item-active bg-[var(--color-primary-default)]/[0.08] text-[var(--color-primary-default)] shadow-[inset_0_1px_2px_rgba(0,0,0,0.04)] dark:bg-[var(--color-primary-default)]/15 dark:shadow-none'
                  : 'text-sidebar-foreground/70 hover:bg-sidebar-accent/60 hover:text-sidebar-foreground'}"
              >
                {#snippet child({ props })}
                  <a
                    href={item.href}
                    {...props}
                    data-sveltekit-preload-data={item.preload || 'hover'}
                    class="flex items-center gap-2.5"
                  >
                    <div
                      class="flex size-6 items-center justify-center rounded-md transition-all duration-200
                        {currentPath === item.href
                        ? 'bg-[var(--color-primary-default)] text-white shadow-sm shadow-[var(--color-primary-default)]/25'
                        : 'text-current group-hover/item:bg-sidebar-accent'}"
                    >
                      <item.icon
                        class="size-[15px] transition-transform duration-200 {currentPath === item.href ? 'scale-105' : 'group-hover/item:scale-105'}"
                        strokeWidth={2}
                      />
                    </div>
                    <span class="text-[13px] {currentPath === item.href ? 'font-semibold' : 'font-medium'}">{item.label}</span>
                  </a>
                {/snippet}
              </Sidebar.MenuButton>
            </Sidebar.MenuItem>
          {/each}
        </Sidebar.Menu>
      </Sidebar.GroupContent>
    </Sidebar.Group>
  </Sidebar.Content>

  <Sidebar.Footer class="border-sidebar-border/60 border-t px-2 py-3">
    <Sidebar.Menu class="space-y-1">
      <!-- Collapse/Expand Toggle - HubSpot Style -->
      <Sidebar.MenuItem class="group-data-[collapsible=icon]:hidden">
        <Sidebar.MenuButton
          onclick={() => sidebar.toggle()}
          tooltipContent="Collapse sidebar"
          class="text-sidebar-foreground/60 hover:bg-sidebar-accent hover:text-sidebar-foreground h-8 rounded-lg px-3 transition-all duration-150"
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
          class="text-sidebar-foreground/60 hover:bg-sidebar-accent hover:text-sidebar-foreground flex h-8 w-full items-center justify-center rounded-lg transition-all duration-150"
        >
          {#snippet child({ props })}
            <button {...props} class="flex items-center justify-center">
              <PanelLeft class="size-4" strokeWidth={1.75} />
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
                class="group/user data-[state=open]:bg-sidebar-accent hover:bg-sidebar-accent h-12 rounded-lg px-2 transition-all duration-150"
              >
                <!-- Avatar with status -->
                <div class="relative">
                  {#if user.profilePhoto && !profileImageError}
                    <img
                      class="ring-sidebar-border/50 size-8 rounded-full object-cover ring-2 transition-all duration-150 group-hover/user:ring-[#ff7a59]/30"
                      src={user.profilePhoto}
                      alt="User avatar"
                      onerror={() => (profileImageError = true)}
                    />
                  {:else}
                    <div
                      class="ring-sidebar-border/50 flex size-8 items-center justify-center rounded-full bg-gradient-to-br from-[#ff7a59] to-[#ff5c35] text-xs font-semibold text-white ring-2 transition-all duration-150 group-hover/user:ring-[#ff7a59]/30"
                    >
                      {getInitials(user.name)}
                    </div>
                  {/if}
                  <!-- Online status indicator -->
                  <div
                    class="border-sidebar absolute -right-0.5 -bottom-0.5 size-2.5 rounded-full border-2 bg-emerald-500"
                  ></div>
                </div>
                <div class="grid flex-1 text-left leading-tight">
                  <span class="text-sidebar-foreground truncate text-[13px] font-semibold"
                    >{user.name}</span
                  >
                  <span class="text-sidebar-foreground/50 truncate text-[11px]">{user.email}</span>
                </div>
                <ChevronsUpDown class="text-sidebar-foreground/40 ml-auto size-4" />
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
                onclick={() => navigateTo('/settings/tags')}
                class="gap-2.5"
              >
                <Tag class="size-4" />
                <span>Tags</span>
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
                class="flex flex-1 flex-col items-center gap-1 rounded-md px-2 py-2 transition-colors {theme === 'light' ? 'bg-[#ff7a59]/10 text-[#ff7a59]' : 'hover:bg-sidebar-accent text-muted-foreground hover:text-foreground'}"
              >
                <Sun class="size-4" />
                <span class="text-[10px] font-medium">Light</span>
              </button>
              <button
                onclick={() => setTheme('dark')}
                class="flex flex-1 flex-col items-center gap-1 rounded-md px-2 py-2 transition-colors {theme === 'dark' ? 'bg-[#ff7a59]/10 text-[#ff7a59]' : 'hover:bg-sidebar-accent text-muted-foreground hover:text-foreground'}"
              >
                <Moon class="size-4" />
                <span class="text-[10px] font-medium">Dark</span>
              </button>
              <button
                onclick={() => setTheme('system')}
                class="flex flex-1 flex-col items-center gap-1 rounded-md px-2 py-2 transition-colors {theme === 'system' ? 'bg-[#ff7a59]/10 text-[#ff7a59]' : 'hover:bg-sidebar-accent text-muted-foreground hover:text-foreground'}"
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

  :global(.hubspot-sidebar [data-slot='sidebar-menu-button']) {
    font-weight: 500;
  }
</style>
