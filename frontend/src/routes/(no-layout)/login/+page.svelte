<script>
	import '../../../app.css';

	import imgGoogle from '$lib/assets/images/google.svg';
	import imgLogo from '$lib/assets/images/logo.png';
	import {
		Users,
		BarChart3,
		CheckSquare,
		TrendingUp,
		Zap,
		Check,
		Shield,
		Github,
		Star
	} from '@lucide/svelte';

	export let data;

	let isLoading = false;

	const features = [
		{ icon: Users, text: 'Unlimited Contacts' },
		{ icon: BarChart3, text: 'Sales Pipeline' },
		{ icon: CheckSquare, text: 'Task Management' },
		{ icon: TrendingUp, text: 'Analytics & Reports' }
	];

	const benefits = [
		'100% Free Forever',
		'No Credit Card Required',
		'Complete Data Ownership',
		'Self-Hostable Solution'
	];

	function handleGoogleLogin() {
		isLoading = true;
		// The actual navigation will happen via the href
		setTimeout(() => {
			isLoading = false;
		}, 3000);
	}
</script>

<svelte:head>
	<title>Login | BottleCRM - Free Open-Source CRM for Startups</title>
	<meta
		name="description"
		content="Sign in to BottleCRM - the completely free, open-source CRM solution for startups and small businesses. No subscription fees, unlimited users."
	/>
</svelte:head>

<!-- Main Container with Gradient Background -->
<div
	class="relative min-h-screen overflow-hidden bg-gradient-to-br from-blue-600 via-indigo-700 to-purple-800"
>
	<!-- Animated Background Elements -->
	<div class="absolute inset-0 bg-black/10"></div>
	<div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent"></div>

	<!-- Floating Background Shapes -->
	<div class="absolute top-10 left-10 h-72 w-72 rounded-full bg-white/5 blur-3xl"></div>
	<div class="absolute right-10 bottom-10 h-96 w-96 rounded-full bg-blue-400/10 blur-3xl"></div>

	<div class="relative z-10 flex min-h-screen items-center justify-center p-4">
		<div class="mx-auto w-full max-w-6xl">
			<div class="grid items-center gap-12 lg:grid-cols-2">
				<!-- Left Side - Branding & Features -->
				<div class="hidden text-white lg:block">
					<div>
						<div class="mb-8">
							<div
								class="mb-6 inline-flex items-center rounded-full border border-white/20 bg-white/10 px-4 py-2 backdrop-blur-sm"
							>
								<Star class="mr-2 h-4 w-4" />
								<span class="text-sm font-medium">Free & Open Source CRM</span>
							</div>

							<h1 class="mb-6 text-4xl leading-tight font-extrabold xl:text-5xl">
								Welcome to <span class="text-yellow-300">BottleCRM</span>
							</h1>

							<p class="mb-8 text-xl leading-relaxed text-blue-100">
								The completely free, self-hostable CRM solution built specifically for startups and
								growing businesses.
							</p>
						</div>

						<!-- Key Benefits -->
						<div class="mb-8">
							<h3 class="mb-4 text-lg font-semibold">Why Choose BottleCRM?</h3>
							<ul class="space-y-3">
								{#each benefits as benefit}
									<li class="flex items-center">
										<Check class="mr-3 h-5 w-5 flex-shrink-0 text-green-400" />
										<span>{benefit}</span>
									</li>
								{/each}
							</ul>
						</div>

						<!-- Feature Icons -->
						<div class="grid grid-cols-2 gap-4">
							{#each features as feature}
								<div
									class="flex items-center rounded-xl border border-white/20 bg-white/10 p-3 backdrop-blur-sm"
								>
									<div class="mr-3 rounded-lg bg-white/20 p-2">
										{#snippet featureIcon(/** @type {any} */ icon)}
											{@const FeatureIcon = icon}
											<FeatureIcon class="h-5 w-5" />
										{/snippet}
										{@render featureIcon(feature.icon)}
									</div>
									<span class="text-sm font-medium">{feature.text}</span>
								</div>
							{/each}
						</div>

						<!-- Stats -->
						<div class="mt-8 border-t border-white/20 pt-8">
							<div class="grid grid-cols-3 gap-4 text-center">
								<div>
									<div class="text-2xl font-bold text-yellow-300">100%</div>
									<div class="text-sm text-blue-200">Free</div>
								</div>
								<div>
									<div class="text-2xl font-bold text-yellow-300">∞</div>
									<div class="text-sm text-blue-200">Users</div>
								</div>
								<div>
									<div class="text-2xl font-bold text-yellow-300">MIT</div>
									<div class="text-sm text-blue-200">License</div>
								</div>
							</div>
						</div>
					</div>
				</div>

				<!-- Right Side - Login Form -->
				<div class="flex justify-center lg:justify-end">
					<div class="w-full max-w-md">
						<!-- Login Card -->
						<div
							class="relative overflow-hidden rounded-3xl border border-white/20 bg-white/95 p-8 shadow-2xl backdrop-blur-lg"
						>
							<!-- Card Background Pattern -->
							<div class="absolute inset-0 bg-gradient-to-br from-gray-50/50 to-white/50"></div>

							<!-- Card Content -->
							<div class="relative z-10">
								<!-- Logo and Header -->
								<div class="mb-8 text-center">
									<div class="mb-6">
										<img src={imgLogo} alt="BottleCRM Logo" class="mx-auto h-16 w-auto" />
									</div>

									<div>
										<h2 class="mb-2 text-2xl font-bold text-gray-900">Welcome Back</h2>
										<p class="text-sm leading-relaxed text-gray-600">
											Sign in to your free BottleCRM account and start managing your customer
											relationships more effectively.
										</p>
									</div>
								</div>

								<!-- Benefits List for Mobile -->
								<div class="mb-6 lg:hidden">
									<div class="rounded-xl border border-blue-100 bg-blue-50 p-4">
										<div class="mb-3 flex items-center">
											<Zap class="mr-2 h-5 w-5 text-blue-600" />
											<span class="text-sm font-semibold text-blue-900">Free CRM Features</span>
										</div>
										<ul class="space-y-2 text-xs text-blue-700">
											<li class="flex items-center">
												<Check class="mr-2 h-3 w-3 flex-shrink-0" />
												<span>Unlimited contacts & users</span>
											</li>
											<li class="flex items-center">
												<Check class="mr-2 h-3 w-3 flex-shrink-0" />
												<span>Self-hosted solution</span>
											</li>
											<li class="flex items-center">
												<Check class="mr-2 h-3 w-3 flex-shrink-0" />
												<span>No subscription fees</span>
											</li>
										</ul>
									</div>
								</div>

								<!-- Google Sign In Button -->
								<div>
									<a
										href={data['google_url']}
										onclick={handleGoogleLogin}
										class="group relative flex w-full items-center justify-center gap-3 overflow-hidden rounded-xl border-2 border-gray-200 bg-white px-6 py-4 font-semibold text-gray-800 shadow-lg hover:border-blue-300 hover:bg-blue-50 hover:shadow-xl focus:ring-4 focus:ring-blue-200 focus:outline-none"
									>
										<!-- Loading Spinner -->
										{#if isLoading}
											<div
												class="h-5 w-5 animate-spin rounded-full border-2 border-blue-600 border-t-transparent"
											></div>
										{:else}
											<img src={imgGoogle} alt="Google" class="h-5 w-5" />
										{/if}

										<span class="relative z-10">
											{isLoading ? 'Connecting...' : 'Continue with Google'}
										</span>
									</a>
								</div>

								<!-- Security Notice -->
								<div class="mt-6 text-center">
									<div class="mb-3 flex items-center justify-center text-xs text-gray-500">
										<Shield class="mr-1 h-4 w-4" />
										<span>Your data is secure and private</span>
									</div>

									<!-- Footer Links -->
									<div class="flex items-center justify-center space-x-4 text-xs">
										<a
											href="https://github.com/MicroPyramid/Django-CRM"
											target="_blank"
											rel="noopener noreferrer"
											class="flex items-center text-gray-600 hover:text-blue-600"
										>
											<Github class="mr-1 h-3 w-3" />
											<span>Open Source</span>
										</a>
										<span class="text-gray-300">•</span>
										<a href="/features" class="text-gray-600 hover:text-blue-600"> Features </a>
										<span class="text-gray-300">•</span>
										<a href="/contact" class="text-gray-600 hover:text-blue-600"> Support </a>
									</div>
								</div>
							</div>
						</div>

						<!-- Below Card Notice -->
						<div class="mt-6 text-center">
							<p class="text-sm text-blue-100">
								New to BottleCRM?
								<a href="/" class="font-medium text-yellow-300 underline hover:text-yellow-200">
									Learn more about our free CRM
								</a>
							</p>
						</div>
					</div>
				</div>
			</div>
		</div>
	</div>
</div>
