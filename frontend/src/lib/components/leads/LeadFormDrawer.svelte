<script>
	import { Loader2 } from '@lucide/svelte';
	import SideDrawer from '$lib/components/layout/SideDrawer.svelte';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import { Textarea } from '$lib/components/ui/textarea/index.js';
	import { Separator } from '$lib/components/ui/separator/index.js';
	import { cn } from '$lib/utils.js';
	import { INDUSTRIES, COUNTRIES } from '$lib/constants/lead-choices.js';

	/**
	 * @typedef {Object} LeadFormData
	 * @property {string} [id]
	 * @property {string} title
	 * @property {string} first_name
	 * @property {string} last_name
	 * @property {string} email
	 * @property {string} phone
	 * @property {string} company
	 * @property {string} contact_title
	 * @property {string} website
	 * @property {string} linkedin_url
	 * @property {string} status
	 * @property {string} source
	 * @property {string} industry
	 * @property {string} rating
	 * @property {string} opportunity_amount
	 * @property {string} probability
	 * @property {string} close_date
	 * @property {string} address_line
	 * @property {string} city
	 * @property {string} state
	 * @property {string} postcode
	 * @property {string} country
	 * @property {string} last_contacted
	 * @property {string} next_follow_up
	 * @property {string} description
	 */

	/**
	 * @typedef {Object} FormOptions
	 * @property {Array<[string, string]>} statuses
	 * @property {Array<[string, string]>} sources
	 */

	/**
	 * @type {{
	 *   open?: boolean,
	 *   onOpenChange?: (open: boolean) => void,
	 *   mode?: 'create' | 'edit',
	 *   initialData?: Partial<LeadFormData> | null,
	 *   options?: FormOptions,
	 *   loading?: boolean,
	 *   onSubmit?: (data: LeadFormData) => Promise<void>,
	 *   onCancel?: () => void,
	 * }}
	 */
	let {
		open = $bindable(false),
		onOpenChange,
		mode = 'create',
		initialData = null,
		options = { statuses: [], sources: [] },
		loading = false,
		onSubmit,
		onCancel
	} = $props();

	/** @type {LeadFormData} */
	let formData = $state({
		// Core Information
		title: '',
		first_name: '',
		last_name: '',
		email: '',
		phone: '',
		company: '',
		contact_title: '',
		website: '',
		linkedin_url: '',
		// Sales Pipeline
		status: 'assigned',
		source: '',
		industry: '',
		rating: '',
		opportunity_amount: '',
		probability: '',
		close_date: '',
		// Address
		address_line: '',
		city: '',
		state: '',
		postcode: '',
		country: '',
		// Activity
		last_contacted: '',
		next_follow_up: '',
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
					// Core Information
					title: initialData.title || '',
					first_name: initialData.first_name || '',
					last_name: initialData.last_name || '',
					email: initialData.email || '',
					phone: initialData.phone || '',
					company: initialData.company || '',
					contact_title: initialData.contact_title || '',
					website: initialData.website || '',
					linkedin_url: initialData.linkedin_url || '',
					// Sales Pipeline
					status: initialData.status || 'assigned',
					source: initialData.source || '',
					industry: initialData.industry || '',
					rating: initialData.rating || '',
					opportunity_amount: initialData.opportunity_amount || '',
					probability: initialData.probability || '',
					close_date: initialData.close_date || '',
					// Address
					address_line: initialData.address_line || '',
					city: initialData.city || '',
					state: initialData.state || '',
					postcode: initialData.postcode || '',
					country: initialData.country || '',
					// Activity
					last_contacted: initialData.last_contacted || '',
					next_follow_up: initialData.next_follow_up || '',
					description: initialData.description || ''
				};
			} else {
				formData = {
					// Core Information
					title: '',
					first_name: '',
					last_name: '',
					email: '',
					phone: '',
					company: '',
					contact_title: '',
					website: '',
					linkedin_url: '',
					// Sales Pipeline
					status: 'assigned',
					source: '',
					industry: '',
					rating: '',
					opportunity_amount: '',
					probability: '',
					close_date: '',
					// Address
					address_line: '',
					city: '',
					state: '',
					postcode: '',
					country: '',
					// Activity
					last_contacted: '',
					next_follow_up: '',
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

		if (!formData.title?.trim()) {
			errors.title = 'Lead title is required';
			isValid = false;
		}

		if (formData.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
			errors.email = 'Please enter a valid email address';
			isValid = false;
		}

		if (formData.probability && (parseInt(formData.probability) < 0 || parseInt(formData.probability) > 100)) {
			errors.probability = 'Probability must be between 0 and 100';
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

	const title = $derived(mode === 'create' ? 'New Lead' : 'Edit Lead');
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
				<!-- Contact Information -->
				<div class="mb-6">
					<p class="text-muted-foreground mb-3 text-xs font-medium tracking-wider uppercase">
						Contact Information
					</p>
					<div class="space-y-4">
						<div>
							<Label for="title" class="text-sm">Lead Title *</Label>
							<Input
								id="title"
								type="text"
								bind:value={formData.title}
								placeholder="e.g., Enterprise Software Deal"
								class={cn('mt-1.5', errors.title && 'border-destructive')}
							/>
							{#if errors.title}
								<p class="text-destructive mt-1 text-xs">{errors.title}</p>
							{/if}
						</div>

						<div class="grid grid-cols-2 gap-3">
							<div>
								<Label for="first_name" class="text-sm">First Name</Label>
								<Input
									id="first_name"
									type="text"
									bind:value={formData.first_name}
									class="mt-1.5"
								/>
							</div>
							<div>
								<Label for="last_name" class="text-sm">Last Name</Label>
								<Input
									id="last_name"
									type="text"
									bind:value={formData.last_name}
									class="mt-1.5"
								/>
							</div>
						</div>

						<div>
							<Label for="email" class="text-sm">Email</Label>
							<Input
								id="email"
								type="email"
								bind:value={formData.email}
								placeholder="email@example.com"
								class={cn('mt-1.5', errors.email && 'border-destructive')}
							/>
							{#if errors.email}
								<p class="text-destructive mt-1 text-xs">{errors.email}</p>
							{/if}
						</div>

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
							<Label for="company" class="text-sm">Company</Label>
							<Input id="company" type="text" bind:value={formData.company} class="mt-1.5" />
						</div>

						<div>
							<Label for="contact_title" class="text-sm">Job Title</Label>
							<Input
								id="contact_title"
								type="text"
								bind:value={formData.contact_title}
								placeholder="e.g., Sales Manager"
								class="mt-1.5"
							/>
						</div>

						<div>
							<Label for="website" class="text-sm">Website</Label>
							<Input
								id="website"
								type="url"
								bind:value={formData.website}
								placeholder="https://example.com"
								class="mt-1.5"
							/>
						</div>

						<div>
							<Label for="linkedin_url" class="text-sm">LinkedIn URL</Label>
							<Input
								id="linkedin_url"
								type="url"
								bind:value={formData.linkedin_url}
								placeholder="https://linkedin.com/in/..."
								class="mt-1.5"
							/>
						</div>
					</div>
				</div>

				<Separator class="mb-6" />

				<!-- Lead Details -->
				<div class="mb-6">
					<p class="text-muted-foreground mb-3 text-xs font-medium tracking-wider uppercase">
						Lead Details
					</p>
					<div class="space-y-4">
						<div>
							<Label for="status" class="text-sm">Status</Label>
							<select
								id="status"
								bind:value={formData.status}
								class="border-input bg-background ring-offset-background focus:ring-ring mt-1.5 w-full rounded-md border px-3 py-2 text-sm focus:ring-2 focus:ring-offset-2 focus:outline-none"
							>
								{#if options.statuses.length > 0}
									{#each options.statuses as [value, label]}
										<option {value}>{label}</option>
									{/each}
								{:else}
									<option value="assigned">Assigned</option>
									<option value="in process">In Process</option>
									<option value="converted">Converted</option>
									<option value="recycled">Recycled</option>
									<option value="closed">Closed</option>
								{/if}
							</select>
						</div>

						<div>
							<Label for="source" class="text-sm">Source</Label>
							<select
								id="source"
								bind:value={formData.source}
								class="border-input bg-background ring-offset-background focus:ring-ring mt-1.5 w-full rounded-md border px-3 py-2 text-sm focus:ring-2 focus:ring-offset-2 focus:outline-none"
							>
								<option value="">Select source</option>
								{#if options.sources.length > 0}
									{#each options.sources as [value, label]}
										<option {value}>{label}</option>
									{/each}
								{:else}
									<option value="call">Call</option>
									<option value="email">Email</option>
									<option value="existing customer">Existing Customer</option>
									<option value="partner">Partner</option>
									<option value="public relations">Public Relations</option>
									<option value="compaign">Campaign</option>
									<option value="other">Other</option>
								{/if}
							</select>
						</div>

						<div>
							<Label for="rating" class="text-sm">Rating</Label>
							<select
								id="rating"
								bind:value={formData.rating}
								class="border-input bg-background ring-offset-background focus:ring-ring mt-1.5 w-full rounded-md border px-3 py-2 text-sm focus:ring-2 focus:ring-offset-2 focus:outline-none"
							>
								<option value="">Select rating</option>
								<option value="HOT">Hot</option>
								<option value="WARM">Warm</option>
								<option value="COLD">Cold</option>
							</select>
						</div>

						<div>
							<Label for="industry" class="text-sm">Industry</Label>
							<select
								id="industry"
								bind:value={formData.industry}
								class="border-input bg-background ring-offset-background focus:ring-ring mt-1.5 w-full rounded-md border px-3 py-2 text-sm focus:ring-2 focus:ring-offset-2 focus:outline-none"
							>
								{#each INDUSTRIES as industry}
									<option value={industry.value}>{industry.label}</option>
								{/each}
							</select>
						</div>

						<div class="grid grid-cols-2 gap-3">
							<div>
								<Label for="opportunity_amount" class="text-sm">Deal Value</Label>
								<Input
									id="opportunity_amount"
									type="number"
									step="0.01"
									bind:value={formData.opportunity_amount}
									placeholder="0.00"
									class="mt-1.5"
								/>
							</div>
							<div>
								<Label for="probability" class="text-sm">Win Probability %</Label>
								<Input
									id="probability"
									type="number"
									min="0"
									max="100"
									bind:value={formData.probability}
									placeholder="0-100"
									class={cn('mt-1.5', errors.probability && 'border-destructive')}
								/>
								{#if errors.probability}
									<p class="text-destructive mt-1 text-xs">{errors.probability}</p>
								{/if}
							</div>
						</div>

						<div>
							<Label for="close_date" class="text-sm">Expected Close Date</Label>
							<Input
								id="close_date"
								type="date"
								bind:value={formData.close_date}
								class="mt-1.5"
							/>
						</div>

						<div>
							<Label for="description" class="text-sm">Description</Label>
							<Textarea
								id="description"
								bind:value={formData.description}
								placeholder="Additional notes about this lead..."
								rows={3}
								class="mt-1.5"
							/>
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
								<Input id="postcode" type="text" bind:value={formData.postcode} class="mt-1.5" />
							</div>
							<div>
								<Label for="country" class="text-sm">Country</Label>
								<select
									id="country"
									bind:value={formData.country}
									class="border-input bg-background ring-offset-background focus:ring-ring mt-1.5 w-full rounded-md border px-3 py-2 text-sm focus:ring-2 focus:ring-offset-2 focus:outline-none"
								>
									{#each COUNTRIES as country}
										<option value={country.value}>{country.label}</option>
									{/each}
								</select>
							</div>
						</div>
					</div>
				</div>

				<Separator class="mb-6" />

				<!-- Activity Tracking -->
				<div class="mb-6">
					<p class="text-muted-foreground mb-3 text-xs font-medium tracking-wider uppercase">
						Activity Tracking
					</p>
					<div class="space-y-4">
						<div>
							<Label for="last_contacted" class="text-sm">Last Contacted</Label>
							<Input
								id="last_contacted"
								type="date"
								bind:value={formData.last_contacted}
								class="mt-1.5"
							/>
						</div>

						<div>
							<Label for="next_follow_up" class="text-sm">Next Follow-up</Label>
							<Input
								id="next_follow_up"
								type="date"
								bind:value={formData.next_follow_up}
								class="mt-1.5"
							/>
						</div>
					</div>
				</div>
			</form>
		{/if}
	{/snippet}

	{#snippet footer()}
		<div class="flex w-full items-center justify-end gap-2">
			<Button variant="outline" onclick={handleCancel} disabled={isSubmitting || false}>
				Cancel
			</Button>
			<Button onclick={handleSubmit} disabled={isSubmitting || loading || false}>
				{#if isSubmitting}
					<Loader2 class="mr-2 h-4 w-4 animate-spin" />
					{mode === 'create' ? 'Creating...' : 'Saving...'}
				{:else}
					{mode === 'create' ? 'Create Lead' : 'Save Changes'}
				{/if}
			</Button>
		</div>
	{/snippet}
</SideDrawer>
