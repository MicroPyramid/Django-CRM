<script>
	import { afterNavigate } from '$app/navigation';
	import { page } from '$app/stores';
	import imgLogo from '$lib/assets/images/logo.png';
	import {
		LayoutDashboard,
		Users,
		Building,
		Briefcase,
		CheckSquare,
		HelpCircle,
		ChevronDown,
		UserPlus,
		Plus,
		Calendar,
		List,
		Target,
		LogOut,
		Menu,
		Moon,
		Sun,
		Monitor,
		Settings,
		User,
		X,
		Check
	} from '@lucide/svelte';

	let { drawerHidden = $bindable(false), user = {}, org_name = 'BottleCRM' } = $props();

	/** @type {'light' | 'system' | 'dark'} */
	let theme = $state('system');
	let userDropdownOpen = $state(false);
	let themeDropdownOpen = $state(false);
	let dropdownRef = $state();
	let themeDropdownRef = $state();

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
		// This effect tracks `theme` and re-runs when it changes
		const currentTheme = theme;
		if (typeof window !== 'undefined') {
			if (currentTheme === 'dark') {
				document.documentElement.classList.add('dark');
			} else if (currentTheme === 'light') {
				document.documentElement.classList.remove('dark');
			} else {
				// System preference
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

	const closeDrawer = () => {
		drawerHidden = true;
	};

	const toggleThemeDropdown = () => {
		themeDropdownOpen = !themeDropdownOpen;
		if (themeDropdownOpen) {
			userDropdownOpen = false;
		}
	};

	/** @param {'light' | 'system' | 'dark'} newTheme */
	const setTheme = (newTheme) => {
		theme = newTheme;
		localStorage.setItem('theme', newTheme);
		themeDropdownOpen = false;
	};

	const toggleUserDropdown = () => {
		userDropdownOpen = !userDropdownOpen;
	};

	const handleSettingsLinkClick = (/** @type {any} */ event, /** @type {any} */ href) => {
		event.preventDefault();
		event.stopPropagation();

		// Close the dropdown
		userDropdownOpen = false;

		// Navigate to the intended URL
		window.location.href = href;
	};

	const handleDropdownClick = (/** @type {any} */ event) => {
		// Prevent clicks inside dropdown from bubbling up
		event.stopPropagation();
	};

	const handleClickOutside = (/** @type {any} */ event) => {
		if (userDropdownOpen && dropdownRef && !dropdownRef.contains(event.target)) {
			userDropdownOpen = false;
		}
		if (themeDropdownOpen && themeDropdownRef && !themeDropdownRef.contains(event.target)) {
			themeDropdownOpen = false;
		}
	};

	// Add click outside listener
	$effect(() => {
		if (typeof document !== 'undefined') {
			document.addEventListener('click', handleClickOutside);
			return () => {
				document.removeEventListener('click', handleClickOutside);
			};
		}
	});

	let mainSidebarUrl = $derived($page.url.pathname);
	/** @type {{ [key: string]: boolean }} */
	let openDropdowns = $state({});

	const toggleDropdown = (/** @type {any} */ key) => {
		openDropdowns[key] = !openDropdowns[key];
	};

	afterNavigate((navigation) => {
		document.getElementById('svelte')?.scrollTo({ top: 0 });
		closeDrawer();
	});

	const navigationItems = [
		{
			href: '/',
			label: 'Dashboard',
			icon: LayoutDashboard,
			type: 'link'
		},
		{
			key: 'leads',
			label: 'Leads',
			icon: Target,
			type: 'dropdown',
			children: [
				{ href: '/leads/open', label: 'Open Leads', icon: List },
				{ href: '/leads/new', label: 'Create Lead', icon: Plus }
			]
		},
		{
			key: 'contacts',
			label: 'Contacts',
			icon: Users,
			type: 'dropdown',
			children: [
				{ href: '/contacts', label: 'All Contacts', icon: List },
				{ href: '/contacts/new', label: 'New Contact', icon: UserPlus }
			]
		},
		{
			key: 'accounts',
			label: 'Accounts',
			icon: Building,
			type: 'dropdown',
			children: [
				{ href: '/accounts', label: 'All Accounts', icon: List },
				{ href: '/accounts/new', label: 'New Account', icon: Plus }
			]
		},
		{
			key: 'opportunities',
			label: 'Opportunities',
			icon: Target,
			type: 'dropdown',
			children: [
				{ href: '/opportunities', label: 'All Opportunities', icon: List },
				{ href: '/opportunities/new', label: 'New Opportunity', icon: Plus }
			]
		},
		{
			key: 'cases',
			label: 'Cases',
			icon: Briefcase,
			type: 'dropdown',
			children: [
				{ href: '/cases', label: 'All Cases', icon: List },
				{ href: '/cases/new', label: 'New Case', icon: Plus }
			]
		},
		{
			key: 'tasks',
			label: 'Tasks',
			icon: CheckSquare,
			type: 'dropdown',
			children: [
				{ href: '/tasks/list', label: 'Task List', icon: List },
				{ href: '/tasks/calendar', label: 'Calendar', icon: Calendar }
			]
		},
		{
			href: '/support',
			label: 'Support',
			icon: HelpCircle,
			type: 'link'
		}
	];
</script>

<aside
	class={`fixed inset-0 z-30 h-full w-64 flex-none border-e border-gray-200 lg:block lg:h-auto lg:overflow-y-visible dark:border-gray-600 ${drawerHidden ? 'hidden' : ''}`}
>
	<div class="flex h-full flex-col bg-white dark:bg-gray-900">
		<!-- Header section with logo and mobile close button -->
		<div
			class="flex items-center justify-between border-b border-gray-200 p-4 dark:border-gray-700"
		>
			<a href="/" class="flex items-center gap-3">
				<img src={imgLogo} class="h-8 w-auto" alt="BottleCRM Logo" />
				<span class="text-xl font-bold tracking-tight text-gray-900 dark:text-white">
					{org_name}
				</span>
			</a>

			<!-- Mobile close button -->
			<button
				onclick={closeDrawer}
				class="rounded-lg p-2 text-gray-500 transition-colors hover:bg-gray-100 focus:ring-2 focus:ring-gray-200 focus:outline-none lg:hidden dark:text-gray-400 dark:hover:bg-gray-800 dark:focus:ring-gray-600"
			>
				<X class="h-5 w-5" />
			</button>
		</div>

		<!-- Navigation section -->
		<div class="flex-1 overflow-y-auto px-4 py-4">
			<nav class="space-y-2">
				{#each navigationItems as item}
					{#if item.type === 'link'}
						<a
							href={item.href}
							class={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200 ${
								mainSidebarUrl === item.href
									? 'border-r-2 border-blue-700 bg-blue-50 text-blue-700 dark:border-blue-400 dark:bg-blue-900/20 dark:text-blue-400'
									: 'text-gray-700 hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-gray-800'
							}`}
						>
							<item.icon class="h-5 w-5" />
							<span>{item.label}</span>
						</a>
					{:else if item.type === 'dropdown'}
						<div class="space-y-1">
							<button
								type="button"
								class="flex w-full items-center justify-between rounded-lg px-3 py-2.5 text-sm font-medium text-gray-700 transition-all duration-200 hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-gray-800"
								onclick={() => toggleDropdown(item.key)}
							>
								<div class="flex items-center gap-3">
									<item.icon class="h-5 w-5" />
									<span>{item.label}</span>
								</div>
								<ChevronDown
									class={`h-4 w-4 transition-transform duration-200 ${item.key && openDropdowns[item.key] ? 'rotate-180' : ''}`}
								/>
							</button>

							{#if item.key && openDropdowns[item.key] && item.children}
								<div class="ml-8 space-y-1 border-l-2 border-gray-100 pl-4 dark:border-gray-700">
									{#each item.children as child}
										<a
											href={child.href}
											class={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-all duration-200 ${
												mainSidebarUrl === child.href
													? 'bg-blue-50 font-medium text-blue-700 dark:bg-blue-900/20 dark:text-blue-400'
													: 'text-gray-600 hover:bg-gray-50 hover:text-gray-900 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-300'
											}`}
										>
											<child.icon class="h-4 w-4" />
											<span>{child.label}</span>
										</a>
									{/each}
								</div>
							{/if}
						</div>
					{/if}
				{/each}
			</nav>
		</div>

		<!-- settings section -->
		<div class="border-t border-gray-200 p-4 dark:border-gray-700" bind:this={dropdownRef}>
			<div class="mb-3 flex items-center gap-3">
				<img class="h-10 w-10 rounded-lg object-cover" src={user.profilePhoto} alt="User avatar" />
				<div class="min-w-0 flex-1">
					<div class="truncate text-sm font-medium text-gray-900 dark:text-white">{user.name}</div>
					<div class="truncate text-xs text-gray-500 dark:text-gray-400">{user.email}</div>
				</div>
			</div>

			<!-- Quick actions -->
			<div class="flex items-center justify-between">
				<div class="relative" bind:this={themeDropdownRef}>
					<button
						onclick={toggleThemeDropdown}
						class="rounded-lg p-2 text-gray-500 transition-colors hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800"
						title="Theme"
					>
						{#if theme === 'dark'}
							<Moon class="h-4 w-4" />
						{:else if theme === 'light'}
							<Sun class="h-4 w-4" />
						{:else}
							<Monitor class="h-4 w-4" />
						{/if}
					</button>

					{#if themeDropdownOpen}
						<div
							class="absolute bottom-full left-0 mb-2 w-36 rounded-lg border border-gray-200 bg-white p-1 shadow-lg dark:border-gray-700 dark:bg-gray-800"
						>
							<button
								onclick={() => setTheme('light')}
								class="flex w-full items-center justify-between rounded px-3 py-2 text-sm text-gray-700 transition-colors hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700"
							>
								<span class="flex items-center gap-2">
									<Sun class="h-4 w-4" />
									Light
								</span>
								{#if theme === 'light'}
									<Check class="h-4 w-4 text-blue-500" />
								{/if}
							</button>
							<button
								onclick={() => setTheme('system')}
								class="flex w-full items-center justify-between rounded px-3 py-2 text-sm text-gray-700 transition-colors hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700"
							>
								<span class="flex items-center gap-2">
									<Monitor class="h-4 w-4" />
									System
								</span>
								{#if theme === 'system'}
									<Check class="h-4 w-4 text-blue-500" />
								{/if}
							</button>
							<button
								onclick={() => setTheme('dark')}
								class="flex w-full items-center justify-between rounded px-3 py-2 text-sm text-gray-700 transition-colors hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700"
							>
								<span class="flex items-center gap-2">
									<Moon class="h-4 w-4" />
									Dark
								</span>
								{#if theme === 'dark'}
									<Check class="h-4 w-4 text-blue-500" />
								{/if}
							</button>
						</div>
					{/if}
				</div>

				<button
					onclick={toggleUserDropdown}
					class="rounded-lg p-2 text-gray-500 transition-colors hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800"
					title="User menu"
				>
					<Settings class="h-4 w-4" />
				</button>
			</div>

			<!-- settings dropdown menu -->
			{#if userDropdownOpen}
				<div
					class="mt-3 rounded-lg border border-gray-200 bg-gray-50 p-1 dark:border-gray-700 dark:bg-gray-800"
					onclick={handleDropdownClick}
					onkeydown={(e) => {
						if (e.key === 'Enter' || e.key === ' ') handleDropdownClick(e);
					}}
					tabindex="0"
					role="menu"
				>
					<button
						type="button"
						onclick={(e) => handleSettingsLinkClick(e, '/profile')}
						class="flex w-full items-center gap-3 rounded px-3 py-2 text-left text-sm text-gray-700 transition-colors hover:bg-white dark:text-gray-300 dark:hover:bg-gray-700"
					>
						<User class="h-4 w-4" />
						Profile
					</button>
					<button
						type="button"
						onclick={(e) => handleSettingsLinkClick(e, '/users')}
						class="flex w-full items-center gap-3 rounded px-3 py-2 text-left text-sm text-gray-700 transition-colors hover:bg-white dark:text-gray-300 dark:hover:bg-gray-700"
					>
						<Users class="h-4 w-4" />
						Users
					</button>
					<button
						type="button"
						onclick={(e) => handleSettingsLinkClick(e, '/org')}
						class="flex w-full items-center gap-3 rounded px-3 py-2 text-left text-sm text-gray-700 transition-colors hover:bg-white dark:text-gray-300 dark:hover:bg-gray-700"
					>
						<Building class="h-4 w-4" />
						Organizations
					</button>
					<hr class="my-1 border-gray-200 dark:border-gray-600" />
					<button
						type="button"
						onclick={(e) => handleSettingsLinkClick(e, '/logout')}
						class="flex w-full items-center gap-3 rounded px-3 py-2 text-left text-sm text-red-600 transition-colors hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/20"
					>
						<LogOut class="h-4 w-4" />
						Sign out
					</button>
				</div>
			{/if}
		</div>
	</div>
</aside>

<div
	hidden={drawerHidden}
	class="fixed inset-0 z-20 bg-gray-900/50 lg:hidden dark:bg-gray-900/60"
	onclick={closeDrawer}
	onkeydown={closeDrawer}
	role="presentation"
></div>
