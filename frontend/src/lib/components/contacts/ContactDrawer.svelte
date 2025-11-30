<script>
	import {
		Mail,
		Phone,
		Building2,
		Briefcase,
		Calendar,
		User,
		MapPin,
		Loader2,
		Linkedin,
		PhoneOff,
		Tag
	} from '@lucide/svelte';
	import SideDrawer from '$lib/components/layout/SideDrawer.svelte';
	import { EditableField } from '$lib/components/ui/editable-field/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Separator } from '$lib/components/ui/separator/index.js';
	import { Skeleton } from '$lib/components/ui/skeleton/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { cn } from '$lib/utils.js';
	import { COUNTRIES, getCountryName } from '$lib/constants/countries.js';

	/**
	 * @typedef {Object} Contact
	 * @property {string} [id]
	 * @property {string} firstName
	 * @property {string} lastName
	 * @property {string} [email]
	 * @property {string} [phone]
	 * @property {string} [organization]
	 * @property {string} [title]
	 * @property {string} [department]
	 * @property {boolean} [doNotCall]
	 * @property {string} [linkedInUrl]
	 * @property {string} [description]
	 * @property {string} [addressLine]
	 * @property {string} [city]
	 * @property {string} [state]
	 * @property {string} [postcode]
	 * @property {string} [country]
	 * @property {string} [createdAt]
	 * @property {{id?: string, name: string, email?: string}} [owner]
	 * @property {Array<{account: {id: string, name: string}}>} [relatedAccounts]
	 * @property {Array<{id: string, name: string}>} [teams]
	 * @property {Array<{id: string, name: string}>} [tags]
	 * @property {{tasks: number, opportunities: number}} [_count]
	 */

	/**
	 * @type {{
	 *   open?: boolean,
	 *   onOpenChange?: (open: boolean) => void,
	 *   contact?: Contact | null,
	 *   mode?: 'view' | 'create',
	 *   loading?: boolean,
	 *   onSave?: (data: any) => Promise<void>,
	 *   onDelete?: () => void,
	 *   onCancel?: () => void,
	 * }}
	 */
	let {
		open = $bindable(false),
		onOpenChange,
		contact = null,
		mode = 'view',
		loading = false,
		onSave,
		onDelete,
		onCancel
	} = $props();

	// Create empty contact for create mode
	const emptyContact = {
		firstName: '',
		lastName: '',
		email: '',
		phone: '',
		organization: '',
		title: '',
		department: '',
		doNotCall: false,
		linkedInUrl: '',
		description: '',
		addressLine: '',
		city: '',
		state: '',
		postcode: '',
		country: ''
	};

	// Form data state - editable copy of contact
	let formData = $state(/** @type {Contact} */ ({ ...emptyContact }));
	let originalData = $state(/** @type {Contact} */ ({ ...emptyContact }));
	let isSubmitting = $state(false);

	// Reset form data when contact changes or drawer opens
	$effect(() => {
		if (open) {
			if (mode === 'create') {
				formData = { ...emptyContact };
				originalData = { ...emptyContact };
			} else if (contact) {
				formData = { ...contact };
				originalData = { ...contact };
			}
		}
	});

	// Check if form has changes
	const isDirty = $derived.by(() => {
		return JSON.stringify(formData) !== JSON.stringify(originalData);
	});

	// Check if it's create mode
	const isCreateMode = $derived(mode === 'create');

	// Validation
	const errors = $derived.by(() => {
		/** @type {Record<string, string>} */
		const errs = {};
		if (!formData.firstName?.trim()) {
			errs.firstName = 'First name is required';
		}
		if (!formData.lastName?.trim()) {
			errs.lastName = 'Last name is required';
		}
		if (formData.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
			errs.email = 'Invalid email address';
		}
		if (
			formData.linkedInUrl &&
			!formData.linkedInUrl.match(/^https?:\/\/(www\.)?linkedin\.com\/.+/i)
		) {
			errs.linkedInUrl = 'Invalid LinkedIn URL';
		}
		return errs;
	});

	const isValid = $derived(Object.keys(errors).length === 0);

	/**
	 * Update a field in form data
	 * @param {keyof Contact} field
	 * @param {any} value
	 */
	function updateField(field, value) {
		formData = { ...formData, [field]: value };
	}

	/**
	 * Handle save
	 */
	async function handleSave() {
		if (!isValid) return;

		isSubmitting = true;
		try {
			// Convert to API format (snake_case)
			const apiData = {
				first_name: formData.firstName,
				last_name: formData.lastName,
				email: formData.email || '',
				phone: formData.phone || '',
				organization: formData.organization || '',
				title: formData.title || '',
				department: formData.department || '',
				do_not_call: formData.doNotCall || false,
				linked_in_url: formData.linkedInUrl || '',
				address_line: formData.addressLine || '',
				city: formData.city || '',
				state: formData.state || '',
				postcode: formData.postcode || '',
				country: formData.country || '',
				description: formData.description || ''
			};
			await onSave?.(apiData);
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

	/**
	 * Get full name
	 */
	function getFullName() {
		return `${formData.firstName || ''} ${formData.lastName || ''}`.trim() || 'New Contact';
	}

	/**
	 * Get initials for avatar
	 */
	function getInitials() {
		const first = formData.firstName?.[0] || '';
		const last = formData.lastName?.[0] || '';
		return (first + last).toUpperCase() || '?';
	}

	/**
	 * Format date
	 * @param {string} date
	 */
	function formatDate(date) {
		if (!date) return '';
		return new Date(date).toLocaleDateString('en-US', {
			month: 'short',
			day: 'numeric',
			year: 'numeric'
		});
	}

	/**
	 * Get formatted address
	 */
	function getFormattedAddress() {
		const parts = [];
		if (formData.addressLine) parts.push(formData.addressLine);

		const cityStateZip = [formData.city, formData.state, formData.postcode]
			.filter(Boolean)
			.join(', ');

		if (cityStateZip) parts.push(cityStateZip);
		if (formData.country) parts.push(getCountryName(formData.country));

		return parts.join('\n');
	}

	const title = $derived(isCreateMode ? 'New Contact' : 'Contact');

	// Country options for select
	const countryOptions = COUNTRIES.map((c) => ({ value: c.code, label: c.name }));
</script>

<SideDrawer bind:open {onOpenChange} {title}>
	{#snippet children()}
		{#if loading}
			<!-- Loading skeleton -->
			<div class="space-y-6 p-6">
				<div class="flex items-start gap-4">
					<Skeleton class="h-14 w-14 rounded-full" />
					<div class="flex-1 space-y-2">
						<Skeleton class="h-6 w-48" />
						<Skeleton class="h-4 w-32" />
					</div>
				</div>
				<div class="space-y-4">
					<Skeleton class="h-10 w-full" />
					<Skeleton class="h-10 w-full" />
				</div>
				<Separator class="my-4" />
				<div class="grid grid-cols-2 gap-4">
					{#each { length: 6 } as _}
						<div class="space-y-1">
							<Skeleton class="h-3 w-16" />
							<Skeleton class="h-5 w-24" />
						</div>
					{/each}
				</div>
			</div>
		{:else}
			<div class="p-6">
				<!-- Primary Info Section -->
				<div class="mb-6 flex items-start gap-4">
					<div
						class="flex h-14 w-14 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-purple-600 text-lg font-semibold text-white"
					>
						{getInitials()}
					</div>
					<div class="min-w-0 flex-1 space-y-1">
						<!-- Editable Name -->
						<div class="flex gap-2">
							<EditableField
								value={formData.firstName}
								placeholder="First name"
								required
								emptyText="First name"
								onchange={(v) => updateField('firstName', v)}
								class="flex-1 text-lg font-semibold"
							/>
							<EditableField
								value={formData.lastName}
								placeholder="Last name"
								required
								emptyText="Last name"
								onchange={(v) => updateField('lastName', v)}
								class="flex-1 text-lg font-semibold"
							/>
						</div>
						<!-- Editable Title -->
						<EditableField
							value={formData.title}
							placeholder="Job title"
							emptyText="Add job title"
							onchange={(v) => updateField('title', v)}
							class="text-muted-foreground text-sm"
						/>
						<!-- Do Not Call -->
						{#if formData.doNotCall}
							<Badge variant="destructive" class="mt-2">
								<PhoneOff class="mr-1 h-3 w-3" />
								Do Not Call
							</Badge>
						{/if}
					</div>
				</div>

				<!-- Contact Info Section -->
				<div class="mb-6">
					<p class="text-muted-foreground mb-3 text-xs font-medium tracking-wider uppercase">
						Contact Information
					</p>
					<div class="space-y-2">
						<div class="bg-muted/30 flex items-center gap-3 rounded-lg px-3 py-2">
							<Mail class="text-muted-foreground h-4 w-4 shrink-0" />
							<EditableField
								value={formData.email}
								type="email"
								placeholder="email@example.com"
								emptyText="Add email"
								validate={(v) => {
									if (v && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)) {
										return 'Invalid email';
									}
									return null;
								}}
								onchange={(v) => updateField('email', v)}
								class="flex-1"
							/>
						</div>
						<div class="bg-muted/30 flex items-center gap-3 rounded-lg px-3 py-2">
							<Phone class="text-muted-foreground h-4 w-4 shrink-0" />
							<EditableField
								value={formData.phone}
								type="phone"
								placeholder="+1 (555) 000-0000"
								emptyText="Add phone"
								onchange={(v) => updateField('phone', v)}
								class="flex-1"
							/>
						</div>
						<div class="bg-muted/30 flex items-center gap-3 rounded-lg px-3 py-2">
							<Linkedin class="text-muted-foreground h-4 w-4 shrink-0" />
							<EditableField
								value={formData.linkedInUrl}
								type="url"
								placeholder="https://linkedin.com/in/username"
								emptyText="Add LinkedIn"
								validate={(v) => {
									if (v && !v.match(/^https?:\/\/(www\.)?linkedin\.com\/.+/i)) {
										return 'Invalid LinkedIn URL';
									}
									return null;
								}}
								onchange={(v) => updateField('linkedInUrl', v)}
								class="flex-1"
							/>
						</div>
						<div class="px-1 py-1">
							<EditableField
								type="checkbox"
								label="Do Not Call"
								value={formData.doNotCall}
								onchange={(v) => updateField('doNotCall', v)}
							/>
						</div>
					</div>
				</div>

				<!-- Organization Section -->
				<div class="mb-6">
					<p class="text-muted-foreground mb-3 text-xs font-medium tracking-wider uppercase">
						Organization
					</p>
					<div class="space-y-2">
						<div class="bg-muted/30 flex items-center gap-3 rounded-lg px-3 py-2">
							<Building2 class="text-muted-foreground h-4 w-4 shrink-0" />
							<EditableField
								value={formData.organization}
								placeholder="Company name"
								emptyText="Add company"
								onchange={(v) => updateField('organization', v)}
								class="flex-1"
							/>
						</div>
						<div class="bg-muted/30 flex items-center gap-3 rounded-lg px-3 py-2">
							<Briefcase class="text-muted-foreground h-4 w-4 shrink-0" />
							<EditableField
								value={formData.department}
								placeholder="Department"
								emptyText="Add department"
								onchange={(v) => updateField('department', v)}
								class="flex-1"
							/>
						</div>
					</div>
				</div>

				<!-- Address Section -->
				<div class="mb-6">
					<p class="text-muted-foreground mb-3 text-xs font-medium tracking-wider uppercase">
						Address
					</p>
					<div class="space-y-2">
						<EditableField
							value={formData.addressLine}
							placeholder="Street address"
							emptyText="Add street address"
							onchange={(v) => updateField('addressLine', v)}
						/>
						<div class="grid grid-cols-2 gap-2">
							<EditableField
								value={formData.city}
								placeholder="City"
								emptyText="City"
								onchange={(v) => updateField('city', v)}
							/>
							<EditableField
								value={formData.state}
								placeholder="State/Province"
								emptyText="State"
								onchange={(v) => updateField('state', v)}
							/>
						</div>
						<div class="grid grid-cols-2 gap-2">
							<EditableField
								value={formData.postcode}
								placeholder="Postal code"
								emptyText="Postal code"
								onchange={(v) => updateField('postcode', v)}
							/>
							<EditableField
								value={formData.country}
								type="select"
								options={countryOptions}
								placeholder="Select country"
								emptyText="Country"
								onchange={(v) => updateField('country', v)}
							/>
						</div>
					</div>
				</div>

				<!-- Notes Section -->
				<div class="mb-6">
					<p class="text-muted-foreground mb-3 text-xs font-medium tracking-wider uppercase">
						Notes
					</p>
					<EditableField
						value={formData.description}
						type="textarea"
						placeholder="Add notes about this contact..."
						emptyText="Add notes..."
						onchange={(v) => updateField('description', v)}
					/>
				</div>

				{#if !isCreateMode}
					<Separator class="mb-6" />

					<!-- Read-only sections for existing contacts -->

					<!-- Related Accounts -->
					{#if contact?.relatedAccounts && contact.relatedAccounts.length > 0}
						<div class="mb-6">
							<p class="text-muted-foreground mb-2 text-xs font-medium tracking-wider uppercase">
								Accounts
							</p>
							<div class="space-y-2">
								{#each contact.relatedAccounts as rel}
									<a
										href="/accounts/{rel.account.id}"
										class="bg-muted/50 text-foreground hover:bg-muted flex items-center gap-2 rounded-lg px-3 py-2 text-sm transition-colors"
									>
										<Building2 class="text-muted-foreground h-4 w-4" />
										{rel.account.name}
									</a>
								{/each}
							</div>
						</div>
					{/if}

					<!-- Tags -->
					{#if contact?.tags && contact.tags.length > 0}
						<div class="mb-6">
							<p class="text-muted-foreground mb-2 text-xs font-medium tracking-wider uppercase">
								Tags
							</p>
							<div class="flex flex-wrap gap-2">
								{#each contact.tags as tag}
									<Badge variant="secondary">
										<Tag class="mr-1 h-3 w-3" />
										{tag.name}
									</Badge>
								{/each}
							</div>
						</div>
					{/if}

					<!-- Teams -->
					{#if contact?.teams && contact.teams.length > 0}
						<div class="mb-6">
							<p class="text-muted-foreground mb-2 text-xs font-medium tracking-wider uppercase">
								Teams
							</p>
							<div class="flex flex-wrap gap-2">
								{#each contact.teams as team}
									<Badge variant="outline">{team.name}</Badge>
								{/each}
							</div>
						</div>
					{/if}

					<!-- Metadata -->
					<div class="mb-6">
						<p class="text-muted-foreground mb-3 text-xs font-medium tracking-wider uppercase">
							Details
						</p>
						<div class="grid grid-cols-2 gap-4">
							<div>
								<div class="text-muted-foreground flex items-center gap-1.5 text-xs">
									<User class="h-3.5 w-3.5" />
									<span>Owner</span>
								</div>
								<p class="text-foreground mt-0.5 text-sm font-medium">
									{contact?.owner?.name || 'Unassigned'}
								</p>
							</div>
							<div>
								<div class="text-muted-foreground flex items-center gap-1.5 text-xs">
									<Calendar class="h-3.5 w-3.5" />
									<span>Created</span>
								</div>
								<p class="text-foreground mt-0.5 text-sm font-medium">
									{formatDate(contact?.createdAt || '')}
								</p>
							</div>
							{#if contact?._count?.tasks}
								<div>
									<div class="text-muted-foreground text-xs">Tasks</div>
									<p class="text-foreground mt-0.5 text-sm font-medium">
										{contact._count.tasks}
									</p>
								</div>
							{/if}
							{#if contact?._count?.opportunities}
								<div>
									<div class="text-muted-foreground text-xs">Opportunities</div>
									<p class="text-foreground mt-0.5 text-sm font-medium">
										{contact._count.opportunities}
									</p>
								</div>
							{/if}
						</div>
					</div>
				{/if}
			</div>
		{/if}
	{/snippet}

	{#snippet footer()}
		<div class="flex w-full items-center justify-between">
			{#if !isCreateMode && onDelete}
				<Button
					variant="ghost"
					class="text-destructive hover:text-destructive"
					onclick={onDelete}
					disabled={isSubmitting}
				>
					Delete
				</Button>
			{:else}
				<div></div>
			{/if}
			<div class="flex gap-2">
				<Button variant="outline" onclick={handleCancel} disabled={isSubmitting}>
					Cancel
				</Button>
				{#if isDirty || isCreateMode}
					<Button onclick={handleSave} disabled={isSubmitting || !isValid}>
						{#if isSubmitting}
							<Loader2 class="mr-2 h-4 w-4 animate-spin" />
							{isCreateMode ? 'Creating...' : 'Saving...'}
						{:else}
							{isCreateMode ? 'Create Contact' : 'Save Changes'}
						{/if}
					</Button>
				{/if}
			</div>
		</div>
	{/snippet}
</SideDrawer>
