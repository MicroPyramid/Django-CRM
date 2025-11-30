<script>
	import { Loader2, Linkedin } from '@lucide/svelte';
	import SideDrawer from '$lib/components/layout/SideDrawer.svelte';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import { Textarea } from '$lib/components/ui/textarea/index.js';
	import { Separator } from '$lib/components/ui/separator/index.js';
	import * as Select from '$lib/components/ui/select/index.js';
	import { cn } from '$lib/utils.js';
	import { COUNTRIES } from '$lib/constants/countries.js';

	/**
	 * @typedef {Object} ContactFormData
	 * @property {string} [id]
	 * @property {string} first_name
	 * @property {string} last_name
	 * @property {string} email
	 * @property {string} phone
	 * @property {string} organization
	 * @property {string} title
	 * @property {string} department
	 * @property {boolean} do_not_call
	 * @property {string} linked_in_url
	 * @property {string} address_line
	 * @property {string} city
	 * @property {string} state
	 * @property {string} postcode
	 * @property {string} country
	 * @property {string} description
	 */

	/**
	 * @type {{
	 *   open?: boolean,
	 *   onOpenChange?: (open: boolean) => void,
	 *   mode?: 'create' | 'edit',
	 *   initialData?: Partial<ContactFormData> | null,
	 *   loading?: boolean,
	 *   onSubmit?: (data: ContactFormData) => Promise<void>,
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

	/** @type {ContactFormData} */
	let formData = $state({
		first_name: '',
		last_name: '',
		email: '',
		phone: '',
		organization: '',
		title: '',
		department: '',
		do_not_call: false,
		linked_in_url: '',
		address_line: '',
		city: '',
		state: '',
		postcode: '',
		country: '',
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
					first_name: initialData.first_name || '',
					last_name: initialData.last_name || '',
					email: initialData.email || '',
					phone: initialData.phone || '',
					organization: initialData.organization || '',
					title: initialData.title || '',
					department: initialData.department || '',
					do_not_call: initialData.do_not_call || false,
					linked_in_url: initialData.linked_in_url || '',
					address_line: initialData.address_line || '',
					city: initialData.city || '',
					state: initialData.state || '',
					postcode: initialData.postcode || '',
					country: initialData.country || '',
					description: initialData.description || ''
				};
			} else {
				formData = {
					first_name: '',
					last_name: '',
					email: '',
					phone: '',
					organization: '',
					title: '',
					department: '',
					do_not_call: false,
					linked_in_url: '',
					address_line: '',
					city: '',
					state: '',
					postcode: '',
					country: '',
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

		if (!formData.first_name?.trim()) {
			errors.first_name = 'First name is required';
			isValid = false;
		}

		if (!formData.last_name?.trim()) {
			errors.last_name = 'Last name is required';
			isValid = false;
		}

		if (formData.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
			errors.email = 'Please enter a valid email address';
			isValid = false;
		}

		if (formData.linked_in_url && !formData.linked_in_url.match(/^https?:\/\/(www\.)?linkedin\.com\/.+/i)) {
			errors.linked_in_url = 'Please enter a valid LinkedIn URL';
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

	const title = $derived(mode === 'create' ? 'New Contact' : 'Edit Contact');
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
						<div class="grid grid-cols-2 gap-3">
							<div>
								<Label for="first_name" class="text-sm">First Name *</Label>
								<Input
									id="first_name"
									type="text"
									bind:value={formData.first_name}
									class={cn('mt-1.5', errors.first_name && 'border-destructive')}
								/>
								{#if errors.first_name}
									<p class="text-destructive mt-1 text-xs">{errors.first_name}</p>
								{/if}
							</div>
							<div>
								<Label for="last_name" class="text-sm">Last Name *</Label>
								<Input
									id="last_name"
									type="text"
									bind:value={formData.last_name}
									class={cn('mt-1.5', errors.last_name && 'border-destructive')}
								/>
								{#if errors.last_name}
									<p class="text-destructive mt-1 text-xs">{errors.last_name}</p>
								{/if}
							</div>
						</div>

						<div>
							<Label for="organization" class="text-sm">Company</Label>
							<Input
								id="organization"
								type="text"
								bind:value={formData.organization}
								placeholder="e.g., Acme Inc."
								class="mt-1.5"
							/>
						</div>

						<div>
							<Label for="title" class="text-sm">Job Title</Label>
							<Input
								id="title"
								type="text"
								bind:value={formData.title}
								placeholder="e.g., Sales Manager"
								class="mt-1.5"
							/>
						</div>

						<div>
							<Label for="department" class="text-sm">Department</Label>
							<Input
								id="department"
								type="text"
								bind:value={formData.department}
								placeholder="e.g., Marketing"
								class="mt-1.5"
							/>
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
							<Label for="linked_in_url" class="text-sm">LinkedIn URL</Label>
							<div class="relative mt-1.5">
								<Linkedin class="text-muted-foreground absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2" />
								<Input
									id="linked_in_url"
									type="url"
									bind:value={formData.linked_in_url}
									placeholder="https://linkedin.com/in/username"
									class={cn('pl-9', errors.linked_in_url && 'border-destructive')}
								/>
							</div>
							{#if errors.linked_in_url}
								<p class="text-destructive mt-1 text-xs">{errors.linked_in_url}</p>
							{/if}
						</div>

						<div class="flex items-center gap-2">
							<input
								type="checkbox"
								id="do_not_call"
								bind:checked={formData.do_not_call}
								class="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
							/>
							<Label for="do_not_call" class="text-sm font-normal cursor-pointer">
								Do Not Call
							</Label>
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
								<Select.Root
									type="single"
									name="country"
									value={formData.country}
									onValueChange={(v) => (formData.country = v)}
								>
									<Select.Trigger class="mt-1.5 w-full">
										<span class={cn(!formData.country && 'text-muted-foreground')}>
											{formData.country
												? COUNTRIES.find((c) => c.code === formData.country)?.name || formData.country
												: 'Select country'}
										</span>
									</Select.Trigger>
									<Select.Content class="max-h-60">
										{#each COUNTRIES as country}
											<Select.Item value={country.code}>{country.name}</Select.Item>
										{/each}
									</Select.Content>
								</Select.Root>
							</div>
						</div>
					</div>
				</div>

				<Separator class="mb-6" />

				<!-- Additional Information -->
				<div class="mb-6">
					<p class="text-muted-foreground mb-3 text-xs font-medium tracking-wider uppercase">
						Notes
					</p>
					<div>
						<Label for="description" class="text-sm">Description</Label>
						<Textarea
							id="description"
							bind:value={formData.description}
							placeholder="Additional notes about this contact..."
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
			<Button variant="outline" onclick={handleCancel} disabled={isSubmitting || false}>
				Cancel
			</Button>
			<Button onclick={handleSubmit} disabled={isSubmitting || loading || false}>
				{#if isSubmitting}
					<Loader2 class="mr-2 h-4 w-4 animate-spin" />
					{mode === 'create' ? 'Creating...' : 'Saving...'}
				{:else}
					{mode === 'create' ? 'Create Contact' : 'Save Changes'}
				{/if}
			</Button>
		</div>
	{/snippet}
</SideDrawer>
