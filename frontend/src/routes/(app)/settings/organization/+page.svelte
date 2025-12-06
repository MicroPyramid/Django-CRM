<script>
	import { enhance } from '$app/forms';
	import { invalidateAll } from '$app/navigation';
	import { toast } from 'svelte-sonner';
	import { Settings, Building2, Globe, Banknote } from '@lucide/svelte';
	import { PageHeader } from '$lib/components/layout';
	import { Button } from '$lib/components/ui/button/index.js';
	import * as Card from '$lib/components/ui/card/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import { CURRENCY_CODES } from '$lib/constants/filters.js';

	/** @type {{ data: any, form: any }} */
	let { data, form } = $props();

	const settings = $derived(data.settings || {});
	let isLoading = $state(false);

	// Currency options for select
	const currencyOptions = CURRENCY_CODES.filter((c) => c.value);

	// Country options (simplified list of common countries)
	const countryOptions = [
		{ value: '', label: 'Select Country' },
		{ value: 'US', label: 'United States' },
		{ value: 'GB', label: 'United Kingdom' },
		{ value: 'CA', label: 'Canada' },
		{ value: 'AU', label: 'Australia' },
		{ value: 'DE', label: 'Germany' },
		{ value: 'FR', label: 'France' },
		{ value: 'IN', label: 'India' },
		{ value: 'JP', label: 'Japan' },
		{ value: 'SG', label: 'Singapore' },
		{ value: 'AE', label: 'United Arab Emirates' },
		{ value: 'BR', label: 'Brazil' },
		{ value: 'MX', label: 'Mexico' },
		{ value: 'CH', label: 'Switzerland' },
		{ value: 'NL', label: 'Netherlands' },
		{ value: 'ES', label: 'Spain' },
		{ value: 'IT', label: 'Italy' }
	];

	// Form state - initialized from settings via $effect
	let formName = $state('');
	let formDomain = $state('');
	let formDescription = $state('');
	let formCurrency = $state('USD');
	let formCountry = $state('');

	// Update form state when settings change
	$effect(() => {
		formName = settings.name || '';
		formDomain = settings.domain || '';
		formDescription = settings.description || '';
		formCurrency = settings.default_currency || 'USD';
		formCountry = settings.default_country || '';
	});

	// Handle form result
	$effect(() => {
		if (form?.success) {
			toast.success('Organization settings updated');
			invalidateAll();
		} else if (form?.error) {
			toast.error(form.error);
		}
	});
</script>

<svelte:head>
	<title>Organization Settings - BottleCRM</title>
</svelte:head>

<PageHeader title="Organization Settings" subtitle="Manage your organization preferences">
	{#snippet actions()}
		<div class="flex items-center gap-2">
			<Settings class="text-muted-foreground h-5 w-5" />
		</div>
	{/snippet}
</PageHeader>

<div class="flex-1 space-y-6 p-4 md:p-6">
	<form
		method="POST"
		action="?/update"
		use:enhance={() => {
			isLoading = true;
			return async ({ update }) => {
				await update();
				isLoading = false;
			};
		}}
	>
		<!-- Organization Details -->
		<Card.Root class="mb-6">
			<Card.Header class="pb-4">
				<Card.Title class="flex items-center gap-2 text-lg">
					<Building2 class="h-5 w-5" />
					Organization Details
				</Card.Title>
				<Card.Description class="">Basic information about your organization</Card.Description>
			</Card.Header>
			<Card.Content class="space-y-4">
				<div class="grid gap-4 md:grid-cols-2">
					<div class="grid gap-2">
						<Label class="" for="name">Organization Name</Label>
						<Input
							id="name"
							name="name"
							type="text"
							bind:value={formName}
							placeholder="Enter organization name"
						/>
					</div>
					<div class="grid gap-2">
						<Label class="" for="domain">Domain</Label>
						<div class="relative">
							<Globe class="text-muted-foreground absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2" />
							<Input
								id="domain"
								name="domain"
								type="text"
								bind:value={formDomain}
								placeholder="yourcompany.com"
								class="pl-10"
							/>
						</div>
					</div>
				</div>
				<div class="grid gap-2">
					<Label class="" for="description">Description</Label>
					<textarea
						id="description"
						name="description"
						rows="3"
						bind:value={formDescription}
						placeholder="Describe your organization..."
						class="border-input bg-background ring-offset-background placeholder:text-muted-foreground focus-visible:ring-ring flex min-h-[80px] w-full rounded-md border px-3 py-2 text-sm focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-50"
					></textarea>
				</div>
			</Card.Content>
		</Card.Root>

		<!-- Locale Settings -->
		<Card.Root class="mb-6">
			<Card.Header class="pb-4">
				<Card.Title class="flex items-center gap-2 text-lg">
					<Globe class="h-5 w-5" />
					Locale Settings
				</Card.Title>
				<Card.Description class="">
					Configure default currency and country for your organization
				</Card.Description>
			</Card.Header>
			<Card.Content class="space-y-4">
				<div class="grid gap-4 md:grid-cols-2">
					<div class="grid gap-2">
						<Label class="" for="default_currency">Default Currency</Label>
						<div class="relative">
							<Banknote class="text-muted-foreground absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2" />
							<select
								id="default_currency"
								name="default_currency"
								bind:value={formCurrency}
								class="border-input bg-background w-full rounded-md border py-2 pl-10 pr-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
							>
								{#each currencyOptions as currency}
									<option value={currency.value}>{currency.label}</option>
								{/each}
							</select>
						</div>
						<p class="text-muted-foreground text-xs">
							This will be the default currency for new opportunities, leads, and invoices.
						</p>
					</div>

					<div class="grid gap-2">
						<Label class="" for="default_country">Default Country</Label>
						<div class="relative">
							<Globe class="text-muted-foreground absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2" />
							<select
								id="default_country"
								name="default_country"
								bind:value={formCountry}
								class="border-input bg-background w-full rounded-md border py-2 pl-10 pr-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
							>
								{#each countryOptions as country}
									<option value={country.value}>{country.label}</option>
								{/each}
							</select>
						</div>
						<p class="text-muted-foreground text-xs">
							Default country for addresses and locale formatting.
						</p>
					</div>
				</div>

				<!-- Preview -->
				{#if formCurrency}
					<div class="bg-muted/50 rounded-lg p-4">
						<p class="text-muted-foreground mb-2 text-sm font-medium">Preview</p>
						<p class="text-foreground text-lg font-semibold">
							{new Intl.NumberFormat('en-US', {
								style: 'currency',
								currency: formCurrency
							}).format(12345.67)}
						</p>
					</div>
				{/if}
			</Card.Content>
		</Card.Root>

		<!-- Save Button -->
		<div class="flex justify-end">
			<Button type="submit" disabled={isLoading}>
				{isLoading ? 'Saving...' : 'Save Changes'}
			</Button>
		</div>
	</form>
</div>
