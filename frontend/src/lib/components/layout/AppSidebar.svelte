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
		ChevronsLeft,
		ChevronsRight,
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
		Tag
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

	// Disable prefetch on all nav links - CRM pages load data that shouldn't be prefetched on hover
	const navigationItems = [
		{
			href: '/',
			label: 'Dashboard',
			icon: LayoutDashboard,
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
			label: 'Opportunities',
			icon: Target,
			type: 'link',
			preload: 'off'
		},
		{
			href: '/cases',
			label: 'Cases',
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
		},
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
		},
		{
			href: '/support',
			label: 'Support',
			icon: HelpCircle,
			type: 'link',
			preload: 'off'
		}
	];

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

<Sidebar.Root collapsible="icon" class="border-sidebar-border border-r">
	<Sidebar.Header class="border-sidebar-border border-b">
		<Sidebar.Menu>
			<Sidebar.MenuItem>
				<Sidebar.MenuButton size="lg" class="data-[state=open]:bg-sidebar-accent">
					{#snippet child({ props })}
						<a href="/" {...props}>
							<div
								class="bg-sidebar-primary text-sidebar-primary-foreground flex aspect-square size-8 items-center justify-center rounded-lg"
							>
								<img src={imgLogo} alt="Logo" class="size-6" />
							</div>
							<div class="grid flex-1 text-left text-sm leading-tight">
								<span class="truncate font-semibold">{org_name}</span>
								<span class="text-sidebar-foreground/60 truncate text-xs">CRM</span>
							</div>
						</a>
					{/snippet}
				</Sidebar.MenuButton>
				<!-- Collapse Button (visible when expanded) -->
				<Button
					onclick={() => sidebar.toggle()}
					variant="outline"
					size="icon"
					class="border-sidebar-border bg-sidebar text-sidebar-foreground/60 hover:bg-sidebar-accent hover:text-sidebar-foreground absolute top-1/2 right-1 size-6 -translate-y-1/2 rounded-md shadow-sm transition-all group-data-[collapsible=icon]:hidden hover:shadow-md"
					title="Collapse Sidebar"
				>
					<ChevronsLeft class="size-3.5" />
				</Button>
			</Sidebar.MenuItem>
			<!-- Expand Button (visible when collapsed) -->
			<Sidebar.MenuItem class="hidden group-data-[collapsible=icon]:block">
				<Sidebar.MenuButton
					onclick={() => sidebar.toggle()}
					tooltipContent="Expand Sidebar"
					class="flex items-center justify-center"
				>
					{#snippet child({ props })}
						<button {...props} class="flex w-full items-center justify-center">
							<ChevronsRight class="size-4" />
						</button>
					{/snippet}
				</Sidebar.MenuButton>
			</Sidebar.MenuItem>
		</Sidebar.Menu>
	</Sidebar.Header>

	<Sidebar.Content>
		<Sidebar.Group>
			<Sidebar.GroupContent>
				<Sidebar.Menu>
					{#each navigationItems as item}
						{#if item.type === 'link'}
							<Sidebar.MenuItem>
								<Sidebar.MenuButton
									isActive={currentPath === item.href}
									tooltipContent={item.label}
								>
									{#snippet child({ props })}
										<a
											href={item.href}
											{...props}
											data-sveltekit-preload-data={item.preload || 'hover'}
										>
											<item.icon class="size-4" />
											<span>{item.label}</span>
										</a>
									{/snippet}
								</Sidebar.MenuButton>
							</Sidebar.MenuItem>
						{:else if item.type === 'dropdown' && item.children}
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
											>
												<item.icon class="size-4" />
												<span>{item.label}</span>
												<ChevronRight
													class="ml-auto size-4 transition-transform duration-200 group-data-[state=open]/collapsible:rotate-90"
												/>
											</Sidebar.MenuButton>
										{/snippet}
									</Collapsible.Trigger>
									<Collapsible.Content>
										<Sidebar.MenuSub>
											{#each item.children as navChild}
												<Sidebar.MenuSubItem>
													<Sidebar.MenuSubButton isActive={currentPath === navChild.href}>
														{#snippet child({ props })}
															<a href={navChild.href} {...props}>
																<navChild.icon class="size-4" />
																<span>{navChild.label}</span>
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
	</Sidebar.Content>

	<Sidebar.Footer class="border-sidebar-border border-t">
		<Sidebar.Menu>
			<!-- Theme Switcher -->
			<Sidebar.MenuItem>
				<DropdownMenu.Root>
					<DropdownMenu.Trigger>
						{#snippet child({ props })}
							<Sidebar.MenuButton {...props} tooltipContent="Theme">
								{#if theme === 'dark'}
									<Moon class="size-4" />
								{:else if theme === 'light'}
									<Sun class="size-4" />
								{:else}
									<Monitor class="size-4" />
								{/if}
								<span>Theme</span>
								<span class="text-sidebar-foreground/60 ml-auto text-xs capitalize">{theme}</span>
							</Sidebar.MenuButton>
						{/snippet}
					</DropdownMenu.Trigger>
					<DropdownMenu.Content side="top" align="start" class="w-48">
						<DropdownMenu.Item class="" inset={false} onclick={() => setTheme('light')}>
							<Sun class="mr-2 size-4" />
							<span>Light</span>
						</DropdownMenu.Item>
						<DropdownMenu.Item class="" inset={false} onclick={() => setTheme('dark')}>
							<Moon class="mr-2 size-4" />
							<span>Dark</span>
						</DropdownMenu.Item>
						<DropdownMenu.Item class="" inset={false} onclick={() => setTheme('system')}>
							<Monitor class="mr-2 size-4" />
							<span>System</span>
						</DropdownMenu.Item>
					</DropdownMenu.Content>
				</DropdownMenu.Root>
			</Sidebar.MenuItem>

			<!-- User Menu -->
			<Sidebar.MenuItem>
				<DropdownMenu.Root>
					<DropdownMenu.Trigger>
						{#snippet child({ props })}
							<Sidebar.MenuButton
								size="lg"
								{...props}
								class="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground"
							>
								<img
									class="size-8 rounded-lg object-cover"
									src={user.profilePhoto}
									alt="User avatar"
								/>
								<div class="grid flex-1 text-left text-sm leading-tight">
									<span class="truncate font-semibold">{user.name}</span>
									<span class="text-sidebar-foreground/60 truncate text-xs">{user.email}</span>
								</div>
								<ChevronsUpDown class="ml-auto size-4" />
							</Sidebar.MenuButton>
						{/snippet}
					</DropdownMenu.Trigger>
					<DropdownMenu.Content
						side="top"
						align="start"
						class="w-[--bits-dropdown-menu-anchor-width] min-w-56"
					>
						<DropdownMenu.Label class="">My Account</DropdownMenu.Label>
						<DropdownMenu.Separator class="" />
						<DropdownMenu.Group class="">
							<DropdownMenu.Item class="" inset={false} onclick={() => navigateTo('/profile')}>
								<User class="mr-2 size-4" />
								<span>Profile</span>
							</DropdownMenu.Item>
							<DropdownMenu.Item class="" inset={false} onclick={() => navigateTo('/users')}>
								<Users class="mr-2 size-4" />
								<span>Users & Teams</span>
							</DropdownMenu.Item>
							<DropdownMenu.Item class="" inset={false} onclick={() => navigateTo('/org')}>
								<Building class="mr-2 size-4" />
								<span>Organizations</span>
							</DropdownMenu.Item>
							<DropdownMenu.Item
								class=""
								inset={false}
								onclick={() => navigateTo('/settings/organization')}
							>
								<Settings class="mr-2 size-4" />
								<span>Settings</span>
							</DropdownMenu.Item>
							<DropdownMenu.Item
								class=""
								inset={false}
								onclick={() => navigateTo('/settings/tags')}
							>
								<Tag class="mr-2 size-4" />
								<span>Tags</span>
							</DropdownMenu.Item>
						</DropdownMenu.Group>
						<DropdownMenu.Separator class="" />
						<DropdownMenu.Item
							class="text-destructive focus:text-destructive"
							inset={false}
							onclick={() => navigateTo('/logout')}
						>
							<LogOut class="mr-2 size-4" />
							<span>Sign out</span>
						</DropdownMenu.Item>
					</DropdownMenu.Content>
				</DropdownMenu.Root>
			</Sidebar.MenuItem>
		</Sidebar.Menu>
	</Sidebar.Footer>

	<Sidebar.Rail class="" />
</Sidebar.Root>
