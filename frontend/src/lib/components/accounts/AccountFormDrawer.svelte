<script>
	import { Loader2 } from '@lucide/svelte';
	import SideDrawer from '$lib/components/layout/SideDrawer.svelte';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import { Textarea } from '$lib/components/ui/textarea/index.js';
	import { Separator } from '$lib/components/ui/separator/index.js';
	import * as Select from '$lib/components/ui/select/index.js';
	import { cn } from '$lib/utils.js';

	/**
	 * @typedef {Object} AccountFormData
	 * @property {string} [id]
	 * @property {string} name
	 * @property {string} industry
	 * @property {string} website
	 * @property {string} phone
	 * @property {string} email
	 * @property {string} address_line
	 * @property {string} city
	 * @property {string} state
	 * @property {string} postcode
	 * @property {string} country
	 * @property {string} annual_revenue
	 * @property {string} number_of_employees
	 * @property {string} description
	 */

	// Industry choices matching Django API (INDCHOICES)
	const INDUSTRIES = [
		{ value: 'ADVERTISING', label: 'Advertising' },
		{ value: 'AGRICULTURE', label: 'Agriculture' },
		{ value: 'APPAREL & ACCESSORIES', label: 'Apparel & Accessories' },
		{ value: 'AUTOMOTIVE', label: 'Automotive' },
		{ value: 'BANKING', label: 'Banking' },
		{ value: 'BIOTECHNOLOGY', label: 'Biotechnology' },
		{ value: 'BUILDING MATERIALS & EQUIPMENT', label: 'Building Materials & Equipment' },
		{ value: 'CHEMICAL', label: 'Chemical' },
		{ value: 'COMPUTER', label: 'Computer' },
		{ value: 'EDUCATION', label: 'Education' },
		{ value: 'ELECTRONICS', label: 'Electronics' },
		{ value: 'ENERGY', label: 'Energy' },
		{ value: 'ENTERTAINMENT & LEISURE', label: 'Entertainment & Leisure' },
		{ value: 'FINANCE', label: 'Finance' },
		{ value: 'FOOD & BEVERAGE', label: 'Food & Beverage' },
		{ value: 'GROCERY', label: 'Grocery' },
		{ value: 'HEALTHCARE', label: 'Healthcare' },
		{ value: 'INSURANCE', label: 'Insurance' },
		{ value: 'LEGAL', label: 'Legal' },
		{ value: 'MANUFACTURING', label: 'Manufacturing' },
		{ value: 'PUBLISHING', label: 'Publishing' },
		{ value: 'REAL ESTATE', label: 'Real Estate' },
		{ value: 'SERVICE', label: 'Service' },
		{ value: 'SOFTWARE', label: 'Software' },
		{ value: 'SPORTS', label: 'Sports' },
		{ value: 'TECHNOLOGY', label: 'Technology' },
		{ value: 'TELECOMMUNICATIONS', label: 'Telecommunications' },
		{ value: 'TELEVISION', label: 'Television' },
		{ value: 'TRANSPORTATION', label: 'Transportation' },
		{ value: 'VENTURE CAPITAL', label: 'Venture Capital' }
	];

	/**
	 * @type {{
	 *   open?: boolean,
	 *   onOpenChange?: (open: boolean) => void,
	 *   mode?: 'create' | 'edit',
	 *   initialData?: Partial<AccountFormData> | null,
	 *   loading?: boolean,
	 *   onSubmit?: (data: AccountFormData) => Promise<void>,
	 *   onCancel?: () => void,
	 * }}
	 */
	let {
		open = $bindable(false),
		onOpenChange,
		mode = 'create',
		initialData = null,
		loading = false,
		onSubmit,
		onCancel
	} = $props();

	/** @type {AccountFormData} */
	let formData = $state({
		name: '',
		industry: '',
		website: '',
		phone: '',
		email: '',
		address_line: '',
		city: '',
		state: '',
		postcode: '',
		country: '',
		annual_revenue: '',
		number_of_employees: '',
		description: ''
	});

	/** @type {Record<string, string>} */
	let errors = $state({});

	let isSubmitting = $state(false);

	// Reset form when drawer opens with new data
	$effect(() => {
		if (open) {
			if (initialData) {
				formData = {
					name: initialData.name || '',
					industry: initialData.industry || '',
					website: initialData.website || '',
					phone: initialData.phone || '',
					email: initialData.email || '',
					address_line: initialData.address_line || '',
					city: initialData.city || '',
					state: initialData.state || '',
					postcode: initialData.postcode || '',
					country: initialData.country || '',
					annual_revenue: initialData.annual_revenue || '',
					number_of_employees: initialData.number_of_employees || '',
					description: initialData.description || ''
				};
			} else {
				formData = {
					name: '',
					industry: '',
					website: '',
					phone: '',
					email: '',
					address_line: '',
					city: '',
					state: '',
					postcode: '',
					country: '',
					annual_revenue: '',
					number_of_employees: '',
					description: ''
				};
			}
			errors = {};
		}
	});

	/**
	 * Validate form
	 */
	function validateForm() {
		errors = {};
		let isValid = true;

		if (!formData.name?.trim()) {
			errors.name = 'Account name is required';
			isValid = false;
		}

		if (formData.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
			errors.email = 'Please enter a valid email address';
			isValid = false;
		}

		if (formData.website && !/^(https?:\/\/)?[\w.-]+\.[a-z]{2,}(\/\S*)?$/i.test(formData.website)) {
			errors.website = 'Please enter a valid website URL';
			isValid = false;
		}

		if (formData.annual_revenue && isNaN(Number(formData.annual_revenue))) {
			errors.annual_revenue = 'Please enter a valid number';
			isValid = false;
		}

		if (formData.number_of_employees && isNaN(Number(formData.number_of_employees))) {
			errors.number_of_employees = 'Please enter a valid number';
			isValid = false;
		}

		return isValid;
	}

	/**
	 * Handle form submission
	 */
	async function handleSubmit() {
		if (!validateForm()) return;

		isSubmitting = true;
		try {
			await onSubmit?.(formData);
		} finally {
			isSubmitting = false;
		}
	}

	/**
	 * Handle cancel
	 */
	function handleCancel() {
		if (onCancel) {
			onCancel();
		} else {
			onOpenChange?.(false);
		}
	}

	const title = $derived(mode === 'create' ? 'New Account' : 'Edit Account');
</script>

<SideDrawer bind:open {onOpenChange} {title}>
	{#snippet children()}
		{#if loading}
			<div class="flex items-center justify-center py-20">
				<Loader2 class="text-muted-foreground h-8 w-8 animate-spin" />
			</div>
		{:else}
			<form
				onsubmit={(e) => {
					e.preventDefault();
					handleSubmit();
				}}
				class="p-6"
			>
				<!-- Basic Information -->
				<div class="mb-6">
					<p class="text-muted-foreground mb-3 text-xs font-medium tracking-wider uppercase">
						Basic Information
					</p>
					<div class="space-y-4">
						<div>
							<Label for="name" class="text-sm">Account Name *</Label>
							<Input
								id="name"
								type="text"
								bind:value={formData.name}
								placeholder="e.g., Acme Corporation"
								class={cn('mt-1.5', errors.name && 'border-destructive')}
							/>
							{#if errors.name}
								<p class="text-destructive mt-1 text-xs">{errors.name}</p>
							{/if}
						</div>

						<div>
							<Label for="industry" class="text-sm">Industry</Label>
							<Select.Root
								type="single"
								name="industry"
								onValueChange={(v) => (formData.industry = v)}
								value={formData.industry}
							>
								<Select.Trigger id="industry" class="mt-1.5 w-full">
									{INDUSTRIES.find((i) => i.value === formData.industry)?.label ||
										'Select industry'}
								</Select.Trigger>
								<Select.Content>
									{#each INDUSTRIES as industry}
										<Select.Item value={industry.value}>{industry.label}</Select.Item>
									{/each}
								</Select.Content>
							</Select.Root>
						</div>
					</div>
				</div>

				<Separator class="mb-6" />

				<!-- Contact Information -->
				<div class="mb-6">
					<p class="text-muted-foreground mb-3 text-xs font-medium tracking-wider uppercase">
						Contact Information
					</p>
					<div class="space-y-4">
						<div>
							<Label for="website" class="text-sm">Website</Label>
							<Input
								id="website"
								type="text"
								bind:value={formData.website}
								placeholder="https://example.com"
								class={cn('mt-1.5', errors.website && 'border-destructive')}
							/>
							{#if errors.website}
								<p class="text-destructive mt-1 text-xs">{errors.website}</p>
							{/if}
						</div>

						<div class="grid grid-cols-2 gap-3">
							<div>
								<Label for="phone" class="text-sm">Phone</Label>
								<Input
									id="phone"
									type="tel"
									bind:value={formData.phone}
									placeholder="+1 (555) 000-0000"
									class="mt-1.5"
								/>
							</div>
							<div>
								<Label for="email" class="text-sm">Email</Label>
								<Input
									id="email"
									type="email"
									bind:value={formData.email}
									placeholder="contact@company.com"
									class={cn('mt-1.5', errors.email && 'border-destructive')}
								/>
								{#if errors.email}
									<p class="text-destructive mt-1 text-xs">{errors.email}</p>
								{/if}
							</div>
						</div>
					</div>
				</div>

				<Separator class="mb-6" />

				<!-- Address -->
				<div class="mb-6">
					<p class="text-muted-foreground mb-3 text-xs font-medium tracking-wider uppercase">
						Address
					</p>
					<div class="space-y-4">
						<div>
							<Label for="address_line" class="text-sm">Street Address</Label>
							<Input
								id="address_line"
								type="text"
								bind:value={formData.address_line}
								placeholder="123 Main St"
								class="mt-1.5"
							/>
						</div>

						<div class="grid grid-cols-2 gap-3">
							<div>
								<Label for="city" class="text-sm">City</Label>
								<Input id="city" type="text" bind:value={formData.city} class="mt-1.5" />
							</div>
							<div>
								<Label for="state" class="text-sm">State/Province</Label>
								<Input id="state" type="text" bind:value={formData.state} class="mt-1.5" />
							</div>
						</div>

						<div class="grid grid-cols-2 gap-3">
							<div>
								<Label for="postcode" class="text-sm">Postal Code</Label>
								<Input
									id="postcode"
									type="text"
									bind:value={formData.postcode}
									class="mt-1.5"
								/>
							</div>
							<div>
								<Label for="country" class="text-sm">Country</Label>
								<Input id="country" type="text" bind:value={formData.country} class="mt-1.5" />
							</div>
						</div>
					</div>
				</div>

				<Separator class="mb-6" />

				<!-- Business Information -->
				<div class="mb-6">
					<p class="text-muted-foreground mb-3 text-xs font-medium tracking-wider uppercase">
						Business Information
					</p>
					<div class="grid grid-cols-2 gap-3">
						<div>
							<Label for="annual_revenue" class="text-sm">Annual Revenue ($)</Label>
							<Input
								id="annual_revenue"
								type="text"
								bind:value={formData.annual_revenue}
								placeholder="1000000"
								class={cn('mt-1.5', errors.annual_revenue && 'border-destructive')}
							/>
							{#if errors.annual_revenue}
								<p class="text-destructive mt-1 text-xs">{errors.annual_revenue}</p>
							{/if}
						</div>
						<div>
							<Label for="number_of_employees" class="text-sm">Employees</Label>
							<Input
								id="number_of_employees"
								type="text"
								bind:value={formData.number_of_employees}
								placeholder="100"
								class={cn('mt-1.5', errors.number_of_employees && 'border-destructive')}
							/>
							{#if errors.number_of_employees}
								<p class="text-destructive mt-1 text-xs">{errors.number_of_employees}</p>
							{/if}
						</div>
					</div>
				</div>

				<Separator class="mb-6" />

				<!-- Additional Information -->
				<div class="mb-6">
					<p class="text-muted-foreground mb-3 text-xs font-medium tracking-wider uppercase">
						Additional Information
					</p>
					<div>
						<Label for="description" class="text-sm">Description</Label>
						<Textarea
							id="description"
							bind:value={formData.description}
							placeholder="Additional notes about this account..."
							rows={3}
							class="mt-1.5"
						/>
					</div>
				</div>
			</form>
		{/if}
	{/snippet}

	{#snippet footer()}
		<div class="flex w-full items-center justify-end gap-2">
			<Button variant="outline" onclick={handleCancel} disabled={isSubmitting}>Cancel</Button>
			<Button onclick={handleSubmit} disabled={isSubmitting || loading}>
				{#if isSubmitting}
					<Loader2 class="mr-2 h-4 w-4 animate-spin" />
					{mode === 'create' ? 'Creating...' : 'Saving...'}
				{:else}
					{mode === 'create' ? 'Create Account' : 'Save Changes'}
				{/if}
			</Button>
		</div>
	{/snippet}
</SideDrawer>
