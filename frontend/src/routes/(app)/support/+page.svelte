<script>
	import {
		Github,
		Mail,
		Bug,
		Lightbulb,
		Shield,
		Wrench,
		Heart,
		Users,
		ExternalLink,
		MessageCircle
	} from '@lucide/svelte';
	import PageHeader from '$lib/components/layout/PageHeader.svelte';
	import { Button } from '$lib/components/ui/button/index.js';
	import * as Card from '$lib/components/ui/card/index.js';
	import { Separator } from '$lib/components/ui/separator/index.js';

	/** @type {{ data: import('./$types').PageData }} */
	let { data } = $props();
</script>

<svelte:head>
	<title>Support - BottleCRM</title>
</svelte:head>

<PageHeader title="Help & Support" subtitle="Get help with BottleCRM" />

<div class="flex-1 p-4 md:p-6">
	<div class="mx-auto max-w-4xl space-y-6">
		<!-- Mission Statement -->
		<Card.Root
			class="border-blue-100 bg-gradient-to-r from-blue-50 to-indigo-50 dark:border-blue-800 dark:from-blue-900/20 dark:to-indigo-900/20"
		>
			<Card.Content class="p-6">
				<div class="flex items-start gap-4">
					<div
						class="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg bg-blue-100 dark:bg-blue-800"
					>
						<Heart class="h-6 w-6 text-blue-600 dark:text-blue-300" />
					</div>
					<div>
						<h2 class="text-foreground text-xl font-semibold">Our Mission</h2>
						<p class="text-muted-foreground mt-2 leading-relaxed">
							BottleCRM addresses the high subscription costs of commercial CRM alternatives by
							providing a completely free, open-source, and highly customizable solution. Clone it,
							self-host it, and make it yours - forever free.
						</p>
					</div>
				</div>
			</Card.Content>
		</Card.Root>

		<!-- Support Options Grid -->
		<div class="grid gap-4 md:grid-cols-2">
			<!-- Community Support -->
			<Card.Root class="transition-shadow hover:shadow-md">
				<Card.Header class="">
					<div class="flex items-center gap-3">
						<div
							class="flex h-10 w-10 items-center justify-center rounded-lg bg-green-100 dark:bg-green-900/30"
						>
							<Github class="h-5 w-5 text-green-600 dark:text-green-400" />
						</div>
						<Card.Title class="">Community Support</Card.Title>
					</div>
				</Card.Header>
				<Card.Content>
					<p class="text-muted-foreground mb-4 text-sm">
						Join our open-source community for free support, discussions, and collaboration.
					</p>
					<Button
						variant="outline"
						class="w-full"
						onclick={() => window.open('https://github.com/MicroPyramid/Django-CRM', '_blank')}
					>
						<Github class="mr-2 h-4 w-4" />
						Visit GitHub Repository
						<ExternalLink class="ml-2 h-3 w-3" />
					</Button>
				</Card.Content>
			</Card.Root>

			<!-- Professional Support -->
			<Card.Root class="transition-shadow hover:shadow-md">
				<Card.Header class="">
					<div class="flex items-center gap-3">
						<div
							class="flex h-10 w-10 items-center justify-center rounded-lg bg-purple-100 dark:bg-purple-900/30"
						>
							<Users class="h-5 w-5 text-purple-600 dark:text-purple-400" />
						</div>
						<Card.Title class="">Professional Support</Card.Title>
					</div>
				</Card.Header>
				<Card.Content>
					<p class="text-muted-foreground mb-4 text-sm">
						Get priority support, hosting assistance, and custom development services.
					</p>
					<Button
						variant="outline"
						class="w-full"
						onclick={() => (window.location.href = 'mailto:ashwin@micropyramid.com')}
					>
						<Mail class="mr-2 h-4 w-4" />
						Contact for Paid Support
					</Button>
				</Card.Content>
			</Card.Root>
		</div>

		<!-- Feature Requests -->
		<Card.Root>
			<Card.Header class="">
				<div class="flex items-center gap-3">
					<div
						class="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-100 dark:bg-blue-900/30"
					>
						<Lightbulb class="h-5 w-5 text-blue-600 dark:text-blue-400" />
					</div>
					<div>
						<Card.Title class="">Feature Requests & Ideas</Card.Title>
						<Card.Description class="">Have an idea to make BottleCRM better?</Card.Description>
					</div>
				</div>
			</Card.Header>
			<Card.Content>
				<p class="text-muted-foreground mb-4 text-sm">
					We'd love to hear from you! Share your feature requests and help shape the future of
					open-source CRM.
				</p>
				<Button
					onclick={() =>
						window.open(
							'https://github.com/MicroPyramid/Django-CRM/issues/new?template=feature_request.md',
							'_blank'
						)}
				>
					<Lightbulb class="mr-2 h-4 w-4" />
					Request Feature
					<ExternalLink class="ml-2 h-3 w-3" />
				</Button>
			</Card.Content>
		</Card.Root>

		<!-- Bug Reports -->
		<Card.Root>
			<Card.Header class="">
				<div class="flex items-center gap-3">
					<div
						class="flex h-10 w-10 items-center justify-center rounded-lg bg-orange-100 dark:bg-orange-900/30"
					>
						<Bug class="h-5 w-5 text-orange-600 dark:text-orange-400" />
					</div>
					<div>
						<Card.Title class="">Bug Reports</Card.Title>
						<Card.Description class="">Found a bug? Help us improve BottleCRM</Card.Description>
					</div>
				</div>
			</Card.Header>
			<Card.Content>
				<p class="text-muted-foreground mb-4 text-sm">
					Your feedback helps make the platform more stable for everyone.
				</p>
				<Button
					variant="outline"
					onclick={() =>
						window.open(
							'https://github.com/MicroPyramid/Django-CRM/issues/new?template=bug_report.md',
							'_blank'
						)}
				>
					<Bug class="mr-2 h-4 w-4" />
					Report Bug
					<ExternalLink class="ml-2 h-3 w-3" />
				</Button>
			</Card.Content>
		</Card.Root>

		<!-- Security Issues -->
		<Card.Root class="border-red-200 bg-red-50/50 dark:border-red-800 dark:bg-red-900/10">
			<Card.Header class="">
				<div class="flex items-center gap-3">
					<div
						class="flex h-10 w-10 items-center justify-center rounded-lg bg-red-100 dark:bg-red-900/30"
					>
						<Shield class="h-5 w-5 text-red-600 dark:text-red-400" />
					</div>
					<div>
						<Card.Title class="">Security Issues</Card.Title>
						<Card.Description class="">Report security vulnerabilities privately</Card.Description>
					</div>
				</div>
			</Card.Header>
			<Card.Content>
				<p class="text-muted-foreground mb-4 text-sm">
					<strong>Security is our priority.</strong> If you discover any security vulnerabilities, please
					report them privately. Do not create public GitHub issues for security concerns.
				</p>
				<Button
					variant="destructive"
					onclick={() =>
						(window.location.href =
							'mailto:ashwin@micropyramid.com?subject=Security%20Issue%20-%20BottleCRM')}
				>
					<Mail class="mr-2 h-4 w-4" />
					Report Security Issue
				</Button>
			</Card.Content>
		</Card.Root>

		<!-- Custom Development -->
		<Card.Root
			class="border-indigo-200 bg-gradient-to-r from-indigo-50 to-purple-50 dark:border-indigo-800 dark:from-indigo-900/20 dark:to-purple-900/20"
		>
			<Card.Header class="">
				<div class="flex items-center gap-3">
					<div
						class="flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-100 dark:bg-indigo-900/30"
					>
						<Wrench class="h-5 w-5 text-indigo-600 dark:text-indigo-400" />
					</div>
					<div>
						<Card.Title class="">Custom CRM Development</Card.Title>
						<Card.Description class="">Tailored to your specific business needs</Card.Description>
					</div>
				</div>
			</Card.Header>
			<Card.Content>
				<p class="text-muted-foreground mb-4 text-sm">
					Need BottleCRM tailored to your specific business needs? We offer professional
					customization services including hosting, custom features, integrations, and ongoing
					support.
				</p>
				<Button
					onclick={() =>
						(window.location.href =
							'mailto:ashwin@micropyramid.com?subject=Custom%20CRM%20Development%20Inquiry')}
				>
					<Mail class="mr-2 h-4 w-4" />
					Get Custom Quote
				</Button>
			</Card.Content>
		</Card.Root>

		<!-- Version Info -->
		<div class="text-muted-foreground text-center text-sm">
			<p>BottleCRM v1.0.0</p>
		</div>
	</div>
</div>
