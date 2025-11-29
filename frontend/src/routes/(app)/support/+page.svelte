<script>
	import { Github, Mail, Bug, Lightbulb, Shield, Wrench, Heart, Users } from '@lucide/svelte';

	/** @type {{ data: import('./$types').PageData }} */
	let { data } = $props();
</script>

<div class="min-h-screen bg-gray-50 dark:bg-gray-900">
	<div class="container mx-auto max-w-4xl px-4 py-8">
		<!-- Header Section -->
		<div class="mb-12 text-center">
			<h1 class="mb-4 text-4xl font-bold text-gray-900 dark:text-white">BottleCRM Support</h1>
			<p class="mx-auto max-w-3xl text-xl text-gray-600 dark:text-gray-300">
				Empowering startups with free, open-source CRM solutions. Say goodbye to expensive
				subscription fees.
			</p>
		</div>

		<!-- Mission Statement -->
		<div
			class="mb-8 rounded-xl border border-blue-100 bg-gradient-to-r from-blue-50 to-indigo-50 p-8 dark:border-blue-800 dark:from-blue-900/20 dark:to-indigo-900/20"
		>
			<div class="flex items-start gap-4">
				<div class="flex-shrink-0 rounded-lg bg-blue-100 p-3 dark:bg-blue-800">
					<Heart class="h-6 w-6 text-blue-600 dark:text-blue-300" />
				</div>
				<div>
					<h2 class="mb-3 text-2xl font-semibold text-gray-900 dark:text-white">Our Mission</h2>
					<p class="leading-relaxed text-gray-700 dark:text-gray-300">
						BottleCRM addresses the high subscription costs of commercial CRM alternatives by
						providing a completely free, open-source, and highly customizable solution. Clone it,
						self-host it, and make it yours - forever free.
					</p>
				</div>
			</div>
		</div>

		<!-- Support Grid -->
		<div class="mb-8 grid gap-6 md:grid-cols-2">
			<!-- Community Support -->
			<div
				class="rounded-xl border border-gray-200 bg-white p-6 transition-shadow hover:shadow-lg dark:border-gray-700 dark:bg-gray-800 dark:hover:shadow-xl dark:hover:shadow-gray-900/20"
			>
				<div class="mb-4 flex items-center gap-3">
					<div class="rounded-lg bg-green-100 p-2 dark:bg-green-800">
						<Github class="h-5 w-5 text-green-600 dark:text-green-300" />
					</div>
					<h3 class="text-xl font-semibold text-gray-900 dark:text-white">Community Support</h3>
				</div>
				<p class="mb-4 text-gray-600 dark:text-gray-300">
					Join our open-source community for free support, discussions, and collaboration.
				</p>
				<a
					href="https://github.com/MicroPyramid/Django-CRM"
					target="_blank"
					rel="noopener noreferrer"
					class="inline-flex items-center gap-2 font-medium text-green-600 hover:text-green-700 dark:text-green-400 dark:hover:text-green-300"
				>
					<Github class="h-4 w-4" />
					Visit GitHub Repository
				</a>
			</div>

			<!-- Paid Support -->
			<div
				class="rounded-xl border border-gray-200 bg-white p-6 transition-shadow hover:shadow-lg dark:border-gray-700 dark:bg-gray-800 dark:hover:shadow-xl dark:hover:shadow-gray-900/20"
			>
				<div class="mb-4 flex items-center gap-3">
					<div class="rounded-lg bg-purple-100 p-2 dark:bg-purple-800">
						<Users class="h-5 w-5 text-purple-600 dark:text-purple-300" />
					</div>
					<h3 class="text-xl font-semibold text-gray-900 dark:text-white">Professional Support</h3>
				</div>
				<p class="mb-4 text-gray-600 dark:text-gray-300">
					Get priority support, hosting assistance, and custom development services.
				</p>
				<a
					href="mailto:ashwin@micropyramid.com"
					class="inline-flex items-center gap-2 font-medium text-purple-600 hover:text-purple-700 dark:text-purple-400 dark:hover:text-purple-300"
				>
					<Mail class="h-4 w-4" />
					Contact for Paid Support
				</a>
			</div>
		</div>

		<!-- Feature Requests & Bug Reports -->
		<div
			class="mb-6 rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800"
		>
			<div class="mb-4 flex items-center gap-3">
				<div class="rounded-lg bg-blue-100 p-2 dark:bg-blue-800">
					<Lightbulb class="h-5 w-5 text-blue-600 dark:text-blue-300" />
				</div>
				<h3 class="text-xl font-semibold text-gray-900 dark:text-white">
					Feature Requests & Ideas
				</h3>
			</div>
			<p class="mb-4 text-gray-600 dark:text-gray-300">
				Have an idea to make BottleCRM better? We'd love to hear from you! Share your feature
				requests and help shape the future of open-source CRM.
			</p>
			<a
				href="https://github.com/MicroPyramid/Django-CRM/issues/new?template=feature_request.md"
				target="_blank"
				rel="noopener noreferrer"
				class="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-white transition-colors hover:bg-blue-700 dark:bg-blue-700 dark:hover:bg-blue-600"
			>
				<Lightbulb class="h-4 w-4" />
				Request Feature
			</a>
		</div>

		<!-- Bug Reports -->
		<div
			class="mb-6 rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800"
		>
			<div class="mb-4 flex items-center gap-3">
				<div class="rounded-lg bg-orange-100 p-2 dark:bg-orange-800">
					<Bug class="h-5 w-5 text-orange-600 dark:text-orange-300" />
				</div>
				<h3 class="text-xl font-semibold text-gray-900 dark:text-white">Bug Reports</h3>
			</div>
			<p class="mb-4 text-gray-600 dark:text-gray-300">
				Found a bug? Help us improve BottleCRM by reporting issues. Your feedback helps make the
				platform more stable for everyone.
			</p>
			<a
				href="https://github.com/MicroPyramid/Django-CRM/issues/new?template=bug_report.md"
				target="_blank"
				rel="noopener noreferrer"
				class="inline-flex items-center gap-2 rounded-lg bg-orange-600 px-4 py-2 text-white transition-colors hover:bg-orange-700 dark:bg-orange-700 dark:hover:bg-orange-600"
			>
				<Bug class="h-4 w-4" />
				Report Bug
			</a>
		</div>

		<!-- Security Issues -->
		<div
			class="mb-6 rounded-xl border border-red-200 bg-red-50 p-6 dark:border-red-800 dark:bg-red-900/20"
		>
			<div class="mb-4 flex items-center gap-3">
				<div class="rounded-lg bg-red-100 p-2 dark:bg-red-800">
					<Shield class="h-5 w-5 text-red-600 dark:text-red-300" />
				</div>
				<h3 class="text-xl font-semibold text-gray-900 dark:text-white">Security Issues</h3>
			</div>
			<p class="mb-4 text-gray-600 dark:text-gray-300">
				<strong>Security is our priority.</strong> If you discover any security vulnerabilities, please
				report them privately. Do not create public GitHub issues for security concerns.
			</p>
			<a
				href="mailto:ashwin@micropyramid.com?subject=Security%20Issue%20-%20BottleCRM"
				class="inline-flex items-center gap-2 rounded-lg bg-red-600 px-4 py-2 text-white transition-colors hover:bg-red-700 dark:bg-red-700 dark:hover:bg-red-600"
			>
				<Mail class="h-4 w-4" />
				Report Security Issue
			</a>
		</div>

		<!-- Custom Development -->
		<div
			class="rounded-xl border border-indigo-200 bg-gradient-to-r from-indigo-50 to-purple-50 p-6 dark:border-indigo-800 dark:from-indigo-900/20 dark:to-purple-900/20"
		>
			<div class="mb-4 flex items-center gap-3">
				<div class="rounded-lg bg-indigo-100 p-2 dark:bg-indigo-800">
					<Wrench class="h-5 w-5 text-indigo-600 dark:text-indigo-300" />
				</div>
				<h3 class="text-xl font-semibold text-gray-900 dark:text-white">Custom CRM Development</h3>
			</div>
			<p class="mb-4 text-gray-600 dark:text-gray-300">
				Need BottleCRM tailored to your specific business needs? We offer professional customization
				services including hosting, custom features, integrations, and ongoing support.
			</p>
			<div class="flex flex-col gap-3 sm:flex-row">
				<a
					href="mailto:ashwin@micropyramid.com?subject=Custom%20CRM%20Development%20Inquiry"
					class="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-white transition-colors hover:bg-indigo-700 dark:bg-indigo-700 dark:hover:bg-indigo-600"
				>
					<Mail class="h-4 w-4" />
					Get Custom Quote
				</a>
			</div>
		</div>
	</div>
</div>
