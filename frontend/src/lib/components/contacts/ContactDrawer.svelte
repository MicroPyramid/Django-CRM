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
	import { COUNTRIES } from '$lib/constants/countries.js';

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
			<div>
				<!-- Header Section -->
				<div class="border-b border-gray-100 px-6 pb-4 pt-6">
					<div class="flex items-center gap-3">
						<div
							class="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-purple-600 text-lg font-medium text-white"
						>
							{getInitials()}
						</div>
						<div class="min-w-0 flex-1">
							<div class="flex gap-2">
								<EditableField
									value={formData.firstName}
									placeholder="First name"
									required
									emptyText="First name"
									onchange={(v) => updateField('firstName', v)}
									class="flex-1 text-xl font-semibold"
								/>
								<EditableField
									value={formData.lastName}
									placeholder="Last name"
									required
									emptyText="Last name"
									onchange={(v) => updateField('lastName', v)}
									class="flex-1 text-xl font-semibold"
								/>
							</div>
							{#if formData.doNotCall}
								<Badge variant="destructive" class="mt-2">
									<PhoneOff class="mr-1 h-3 w-3" />
									Do Not Call
								</Badge>
							{/if}
						</div>
					</div>
				</div>

				<!-- Properties Section (Notion-style) -->
				<div class="px-4 py-4">
					<!-- Title property -->
					<div
						class="group -mx-2 flex min-h-[36px] items-center rounded px-2 transition-colors hover:bg-gray-50/60"
					>
						<div class="flex w-28 shrink-0 items-center gap-2 text-[13px] text-gray-500">
							<Briefcase class="h-4 w-4 text-gray-400" />
							Title
						</div>
						<div class="min-w-0 flex-1">
							<EditableField
								value={formData.title}
								placeholder="Job title"
								emptyText="Add title"
								onchange={(v) => updateField('title', v)}
								class="text-sm"
							/>
						</div>
					</div>

					<!-- Email property -->
					<div
						class="group -mx-2 flex min-h-[36px] items-center rounded px-2 transition-colors hover:bg-gray-50/60"
					>
						<div class="flex w-28 shrink-0 items-center gap-2 text-[13px] text-gray-500">
							<Mail class="h-4 w-4 text-gray-400" />
							Email
						</div>
						<div class="min-w-0 flex-1">
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
								class="text-sm"
							/>
						</div>
					</div>

					<!-- Phone property -->
					<div
						class="group -mx-2 flex min-h-[36px] items-center rounded px-2 transition-colors hover:bg-gray-50/60"
					>
						<div class="flex w-28 shrink-0 items-center gap-2 text-[13px] text-gray-500">
							<Phone class="h-4 w-4 text-gray-400" />
							Phone
						</div>
						<div class="min-w-0 flex-1">
							<EditableField
								value={formData.phone}
								type="phone"
								placeholder="+1 (555) 000-0000"
								emptyText="Add phone"
								onchange={(v) => updateField('phone', v)}
								class="text-sm"
							/>
						</div>
					</div>

					<!-- Company property -->
					<div
						class="group -mx-2 flex min-h-[36px] items-center rounded px-2 transition-colors hover:bg-gray-50/60"
					>
						<div class="flex w-28 shrink-0 items-center gap-2 text-[13px] text-gray-500">
							<Building2 class="h-4 w-4 text-gray-400" />
							Company
						</div>
						<div class="min-w-0 flex-1">
							<EditableField
								value={formData.organization}
								placeholder="Company name"
								emptyText="Add company"
								onchange={(v) => updateField('organization', v)}
								class="text-sm"
							/>
						</div>
					</div>

					<!-- Department property -->
					<div
						class="group -mx-2 flex min-h-[36px] items-center rounded px-2 transition-colors hover:bg-gray-50/60"
					>
						<div class="flex w-28 shrink-0 items-center gap-2 text-[13px] text-gray-500">
							<Briefcase class="h-4 w-4 text-gray-400" />
							Department
						</div>
						<div class="min-w-0 flex-1">
							<EditableField
								value={formData.department}
								placeholder="Department"
								emptyText="Add department"
								onchange={(v) => updateField('department', v)}
								class="text-sm"
							/>
						</div>
					</div>

					<!-- LinkedIn property -->
					<div
						class="group -mx-2 flex min-h-[36px] items-center rounded px-2 transition-colors hover:bg-gray-50/60"
					>
						<div class="flex w-28 shrink-0 items-center gap-2 text-[13px] text-gray-500">
							<Linkedin class="h-4 w-4 text-gray-400" />
							LinkedIn
						</div>
						<div class="min-w-0 flex-1">
							<EditableField
								value={formData.linkedInUrl}
								type="url"
								placeholder="https://linkedin.com/in/..."
								emptyText="Add LinkedIn"
								validate={(v) => {
									if (v && !v.match(/^https?:\/\/(www\.)?linkedin\.com\/.+/i)) {
										return 'Invalid LinkedIn URL';
									}
									return null;
								}}
								onchange={(v) => updateField('linkedInUrl', v)}
								class="text-sm"
							/>
						</div>
					</div>

					<!-- Do Not Call property -->
					<div
						class="group -mx-2 flex min-h-[36px] items-center rounded px-2 transition-colors hover:bg-gray-50/60"
					>
						<div class="flex w-28 shrink-0 items-center gap-2 text-[13px] text-gray-500">
							<PhoneOff class="h-4 w-4 text-gray-400" />
							Do Not Call
						</div>
						<div class="min-w-0 flex-1">
							<EditableField
								type="checkbox"
								value={formData.doNotCall}
								onchange={(v) => updateField('doNotCall', v)}
							/>
						</div>
					</div>

					<!-- Address Section -->
					<div class="mt-4 border-t border-gray-100 pt-4">
						<div
							class="group -mx-2 flex min-h-[36px] items-start rounded px-2 transition-colors hover:bg-gray-50/60"
						>
							<div class="flex w-28 shrink-0 items-center gap-2 pt-1 text-[13px] text-gray-500">
								<MapPin class="h-4 w-4 text-gray-400" />
								Address
							</div>
							<div class="min-w-0 flex-1 space-y-1">
								<EditableField
									value={formData.addressLine}
									placeholder="Street address"
									emptyText="Add street"
									onchange={(v) => updateField('addressLine', v)}
									class="text-sm"
								/>
								<div class="flex gap-2">
									<EditableField
										value={formData.city}
										placeholder="City"
										emptyText="City"
										onchange={(v) => updateField('city', v)}
										class="flex-1 text-sm"
									/>
									<EditableField
										value={formData.state}
										placeholder="State"
										emptyText="State"
										onchange={(v) => updateField('state', v)}
										class="w-20 text-sm"
									/>
								</div>
								<div class="flex gap-2">
									<EditableField
										value={formData.postcode}
										placeholder="Postal code"
										emptyText="Postal"
										onchange={(v) => updateField('postcode', v)}
										class="w-24 text-sm"
									/>
									<EditableField
										value={formData.country}
										type="select"
										options={countryOptions}
										placeholder="Country"
										emptyText="Country"
										onchange={(v) => updateField('country', v)}
										class="flex-1 text-sm"
									/>
								</div>
							</div>
						</div>
					</div>

					<!-- Notes Section -->
					<div class="mt-4 border-t border-gray-100 pt-4">
						<div
							class="group -mx-2 flex min-h-[36px] items-start rounded px-2 transition-colors hover:bg-gray-50/60"
						>
							<div class="flex w-28 shrink-0 items-center gap-2 pt-1 text-[13px] text-gray-500">
								<Tag class="h-4 w-4 text-gray-400" />
								Notes
							</div>
							<div class="min-w-0 flex-1">
								<EditableField
									value={formData.description}
									type="textarea"
									placeholder="Add notes..."
									emptyText="Add notes"
									onchange={(v) => updateField('description', v)}
									class="text-sm"
								/>
							</div>
						</div>
					</div>

					{#if !isCreateMode}
						<!-- Read-only metadata for existing contacts -->
						<div class="mt-4 border-t border-gray-100 pt-4">
							<!-- Owner property -->
							<div
								class="group -mx-2 flex min-h-[36px] items-center rounded px-2 transition-colors hover:bg-gray-50/60"
							>
								<div class="flex w-28 shrink-0 items-center gap-2 text-[13px] text-gray-500">
									<User class="h-4 w-4 text-gray-400" />
									Owner
								</div>
								<div class="min-w-0 flex-1">
									<span class="text-sm text-gray-900">
										{contact?.owner?.name || contact?.owner?.email || 'Unassigned'}
									</span>
								</div>
							</div>

							<!-- Created property -->
							<div
								class="group -mx-2 flex min-h-[36px] items-center rounded px-2 transition-colors hover:bg-gray-50/60"
							>
								<div class="flex w-28 shrink-0 items-center gap-2 text-[13px] text-gray-500">
									<Calendar class="h-4 w-4 text-gray-400" />
									Created
								</div>
								<div class="min-w-0 flex-1">
									<span class="text-sm text-gray-900">{formatDate(contact?.createdAt || '')}</span>
								</div>
							</div>

							<!-- Related Accounts -->
							{#if contact?.relatedAccounts && contact.relatedAccounts.length > 0}
								<div
									class="group -mx-2 flex min-h-[36px] items-center rounded px-2 transition-colors hover:bg-gray-50/60"
								>
									<div class="flex w-28 shrink-0 items-center gap-2 text-[13px] text-gray-500">
										<Building2 class="h-4 w-4 text-gray-400" />
										Accounts
									</div>
									<div class="flex min-w-0 flex-1 flex-wrap gap-1">
										{#each contact.relatedAccounts as rel}
											<a
												href="/accounts/{rel.account.id}"
												class="rounded bg-gray-100 px-2 py-0.5 text-sm text-gray-900 hover:bg-gray-200"
											>
												{rel.account.name}
											</a>
										{/each}
									</div>
								</div>
							{/if}

							<!-- Tags -->
							{#if contact?.tags && contact.tags.length > 0}
								<div
									class="group -mx-2 flex min-h-[36px] items-center rounded px-2 transition-colors hover:bg-gray-50/60"
								>
									<div class="flex w-28 shrink-0 items-center gap-2 text-[13px] text-gray-500">
										<Tag class="h-4 w-4 text-gray-400" />
										Tags
									</div>
									<div class="flex min-w-0 flex-1 flex-wrap gap-1">
										{#each contact.tags as tag}
											<Badge variant="secondary" class="text-xs">{tag.name}</Badge>
										{/each}
									</div>
								</div>
							{/if}

							<!-- Teams -->
							{#if contact?.teams && contact.teams.length > 0}
								<div
									class="group -mx-2 flex min-h-[36px] items-center rounded px-2 transition-colors hover:bg-gray-50/60"
								>
									<div class="flex w-28 shrink-0 items-center gap-2 text-[13px] text-gray-500">
										<User class="h-4 w-4 text-gray-400" />
										Teams
									</div>
									<div class="flex min-w-0 flex-1 flex-wrap gap-1">
										{#each contact.teams as team}
											<Badge variant="outline" class="text-xs">{team.name}</Badge>
										{/each}
									</div>
								</div>
							{/if}

							<!-- Tasks count -->
							{#if contact?._count?.tasks}
								<div
									class="group -mx-2 flex min-h-[36px] items-center rounded px-2 transition-colors hover:bg-gray-50/60"
								>
									<div class="flex w-28 shrink-0 items-center gap-2 text-[13px] text-gray-500">
										Tasks
									</div>
									<div class="min-w-0 flex-1">
										<span class="text-sm text-gray-900">{contact._count.tasks}</span>
									</div>
								</div>
							{/if}

							<!-- Opportunities count -->
							{#if contact?._count?.opportunities}
								<div
									class="group -mx-2 flex min-h-[36px] items-center rounded px-2 transition-colors hover:bg-gray-50/60"
								>
									<div class="flex w-28 shrink-0 items-center gap-2 text-[13px] text-gray-500">
										Opportunities
									</div>
									<div class="min-w-0 flex-1">
										<span class="text-sm text-gray-900">{contact._count.opportunities}</span>
									</div>
								</div>
							{/if}
						</div>
					{/if}
				</div>
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
