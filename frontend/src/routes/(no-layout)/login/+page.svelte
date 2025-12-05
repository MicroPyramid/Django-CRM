<script>
	import '../../../app.css';

	import imgGoogle from '$lib/assets/images/google.svg';
	import imgLogo from '$lib/assets/images/logo.png';
	import {
		Users,
		BarChart3,
		CheckCircle2,
		TrendingUp,
		Shield,
		Lock,
		ArrowRight,
		Sparkles,
		Building2,
		Target,
		PieChart
	} from '@lucide/svelte';

	let { data } = $props();

	let isLoading = $state(false);

	const features = [
		{
			icon: Users,
			title: 'Contact Management',
			description: 'Organize and track all your customer relationships in one place'
		},
		{
			icon: Target,
			title: 'Sales Pipeline',
			description: 'Visualize deals and track progress through custom stages'
		},
		{
			icon: BarChart3,
			title: 'Analytics & Reports',
			description: 'Get insights with powerful dashboards and reporting'
		},
		{
			icon: Building2,
			title: 'Multi-Organization',
			description: 'Manage multiple businesses from a single account'
		}
	];

	const stats = [
		{ value: '10K+', label: 'Active Users' },
		{ value: '500K+', label: 'Contacts Managed' },
		{ value: '99.9%', label: 'Uptime' }
	];

	function handleGoogleLogin() {
		isLoading = true;
	}
</script>

<svelte:head>
	<title>Sign In | BottleCRM - Modern CRM for Growing Teams</title>
	<meta
		name="description"
		content="Sign in to BottleCRM - the open-source CRM solution for startups and growing businesses. Manage contacts, track deals, and grow your business."
	/>
</svelte:head>

<div class="flex min-h-screen">
	<!-- Left Panel - Branding & Features -->
	<div class="relative hidden w-1/2 overflow-hidden bg-slate-900 lg:flex lg:flex-col">
		<!-- Subtle gradient overlay -->
		<div class="absolute inset-0 bg-gradient-to-br from-blue-600/20 via-transparent to-purple-600/20"></div>

		<!-- Grid pattern background -->
		<div class="absolute inset-0 opacity-[0.03]" style="background-image: url(&quot;data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='1'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E&quot;);"></div>

		<!-- Content -->
		<div class="relative z-10 flex flex-1 flex-col justify-between p-12">
			<!-- Top - Logo -->
			<div>
				<div class="flex items-center gap-3">
					<img src={imgLogo} alt="BottleCRM" class="h-10 w-auto" />
					<span class="text-xl font-semibold text-white">BottleCRM</span>
				</div>
			</div>

			<!-- Middle - Features -->
			<div class="space-y-8">
				<div>
					<h1 class="text-4xl font-bold leading-tight text-white">
						The CRM that grows
						<span class="bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
							with your business
						</span>
					</h1>
					<p class="mt-4 text-lg text-slate-400">
						Powerful, intuitive, and completely open-source. Manage your customer relationships without limits.
					</p>
				</div>

				<div class="grid gap-4">
					{#each features as feature}
						<div class="group flex items-start gap-4 rounded-xl border border-slate-800 bg-slate-800/50 p-4 transition-all hover:border-slate-700 hover:bg-slate-800">
							<div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-blue-500/10 text-blue-400">
								{#snippet featureIcon(/** @type {any} */ icon)}
									{@const Icon = icon}
									<Icon class="h-5 w-5" />
								{/snippet}
								{@render featureIcon(feature.icon)}
							</div>
							<div>
								<h3 class="font-semibold text-white">{feature.title}</h3>
								<p class="mt-1 text-sm text-slate-400">{feature.description}</p>
							</div>
						</div>
					{/each}
				</div>
			</div>

			<!-- Bottom - Stats -->
			<div class="border-t border-slate-800 pt-8">
				<div class="grid grid-cols-3 gap-8">
					{#each stats as stat}
						<div>
							<div class="text-2xl font-bold text-white">{stat.value}</div>
							<div class="text-sm text-slate-500">{stat.label}</div>
						</div>
					{/each}
				</div>
			</div>
		</div>
	</div>

	<!-- Right Panel - Login Form -->
	<div class="flex w-full flex-col bg-white lg:w-1/2">
		<!-- Mobile Header -->
		<div class="flex items-center justify-between border-b border-slate-100 p-4 lg:hidden">
			<div class="flex items-center gap-2">
				<img src={imgLogo} alt="BottleCRM" class="h-8 w-auto" />
				<span class="font-semibold text-slate-900">BottleCRM</span>
			</div>
		</div>

		<!-- Login Form Container -->
		<div class="flex flex-1 items-center justify-center p-8">
			<div class="w-full max-w-sm">
				<!-- Header -->
				<div class="mb-8 text-center">
					<div class="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-blue-50">
						<Sparkles class="h-6 w-6 text-blue-600" />
					</div>
					<h2 class="text-2xl font-bold text-slate-900">Welcome back</h2>
					<p class="mt-2 text-slate-600">Sign in to continue to your dashboard</p>
				</div>

				<!-- Login Button -->
				<div class="space-y-4">
					<a
						href={data['google_url']}
						onclick={handleGoogleLogin}
						class="group relative flex w-full items-center justify-center gap-3 rounded-lg border border-slate-200 bg-white px-4 py-3.5 font-medium text-slate-700 shadow-sm transition-all hover:border-slate-300 hover:bg-slate-50 hover:shadow focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
						class:pointer-events-none={isLoading}
					>
						{#if isLoading}
							<div class="h-5 w-5 animate-spin rounded-full border-2 border-slate-300 border-t-blue-600"></div>
							<span>Signing in...</span>
						{:else}
							<img src={imgGoogle} alt="Google" class="h-5 w-5" />
							<span>Continue with Google</span>
							<ArrowRight class="ml-auto h-4 w-4 text-slate-400 transition-transform group-hover:translate-x-0.5" />
						{/if}
					</a>
				</div>

				<!-- Divider -->
				<div class="my-8 flex items-center gap-4">
					<div class="h-px flex-1 bg-slate-200"></div>
					<span class="text-xs font-medium uppercase tracking-wider text-slate-400">Secure login</span>
					<div class="h-px flex-1 bg-slate-200"></div>
				</div>

				<!-- Trust Signals -->
				<div class="space-y-4">
					<div class="flex items-center gap-3 rounded-lg bg-slate-50 p-3">
						<div class="flex h-8 w-8 items-center justify-center rounded-full bg-green-100">
							<Shield class="h-4 w-4 text-green-600" />
						</div>
						<div class="flex-1">
							<p class="text-sm font-medium text-slate-700">Enterprise-grade security</p>
							<p class="text-xs text-slate-500">Your data is encrypted and secure</p>
						</div>
					</div>

					<div class="flex items-center gap-3 rounded-lg bg-slate-50 p-3">
						<div class="flex h-8 w-8 items-center justify-center rounded-full bg-blue-100">
							<Lock class="h-4 w-4 text-blue-600" />
						</div>
						<div class="flex-1">
							<p class="text-sm font-medium text-slate-700">Privacy first</p>
							<p class="text-xs text-slate-500">Self-host for complete data ownership</p>
						</div>
					</div>
				</div>

				<!-- Features for Mobile -->
				<div class="mt-8 lg:hidden">
					<p class="mb-3 text-xs font-medium uppercase tracking-wider text-slate-400">What you get</p>
					<div class="grid grid-cols-2 gap-2">
						{#each ['Unlimited contacts', 'Sales pipeline', 'Task management', 'Team collaboration'] as item}
							<div class="flex items-center gap-2 text-sm text-slate-600">
								<CheckCircle2 class="h-4 w-4 text-green-500" />
								<span>{item}</span>
							</div>
						{/each}
					</div>
				</div>
			</div>
		</div>

		<!-- Footer -->
		<div class="border-t border-slate-100 p-6">
			<div class="flex flex-col items-center justify-between gap-4 text-sm sm:flex-row">
				<p class="text-slate-500">
					Don't have an account?
					<span class="text-slate-700">Sign in with Google to get started</span>
				</p>
				<div class="flex items-center gap-4 text-slate-400">
					<a href="https://github.com/MicroPyramid/Django-CRM" target="_blank" rel="noopener noreferrer" class="hover:text-slate-600">
						GitHub
					</a>
					<span>·</span>
					<a href="/docs" class="hover:text-slate-600">Docs</a>
					<span>·</span>
					<a href="/privacy" class="hover:text-slate-600">Privacy</a>
				</div>
			</div>
		</div>
	</div>
</div>
