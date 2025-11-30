<script>
	import { untrack } from 'svelte';
	import {
		Mail,
		Phone,
		Building2,
		Briefcase,
		Calendar,
		Target,
		User,
		Star,
		Globe,
		Linkedin,
		DollarSign,
		Percent,
		Activity,
		MessageSquare,
		Loader2,
		ArrowRightCircle
	} from '@lucide/svelte';
	import SideDrawer from '$lib/components/layout/SideDrawer.svelte';
	import { EditableField } from '$lib/components/ui/editable-field/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Separator } from '$lib/components/ui/separator/index.js';
	import { Skeleton } from '$lib/components/ui/skeleton/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { cn } from '$lib/utils.js';
	import { INDUSTRIES, COUNTRIES } from '$lib/constants/lead-choices.js';

	/**
	 * @typedef {Object} Lead
	 * @property {string} [id]
	 * @property {string} title
	 * @property {string} firstName
	 * @property {string} lastName
	 * @property {string} [email]
	 * @property {string} [phone]
	 * @property {string | {id: string, name: string}} [company]
	 * @property {string} [contactTitle]
	 * @property {string} [website]
	 * @property {string} [linkedinUrl]
	 * @property {string} status
	 * @property {string} [leadSource]
	 * @property {string} [rating]
	 * @property {string} [industry]
	 * @property {string} [opportunityAmount]
	 * @property {number | string} [probability]
	 * @property {string} [closeDate]
	 * @property {string} [addressLine]
	 * @property {string} [city]
	 * @property {string} [state]
	 * @property {string} [postcode]
	 * @property {string} [country]
	 * @property {string} [lastContacted]
	 * @property {string} [nextFollowUp]
	 * @property {string} [description]
	 * @property {string} [createdAt]
	 * @property {{id?: string, name: string, email?: string}} [owner]
	 * @property {Array<{id: string, body: string, createdAt: string, author?: {name: string}}>} [comments]
	 */

	/**
	 * @typedef {Object} FormOptions
	 * @property {Array<{value: string, label: string}>} statuses
	 * @property {Array<{value: string, label: string}>} sources
	 */

	/**
	 * @type {{
	 *   open?: boolean,
	 *   onOpenChange?: (open: boolean) => void,
	 *   lead?: Lead | null,
	 *   mode?: 'view' | 'create',
	 *   loading?: boolean,
	 *   options?: FormOptions,
	 *   onSave?: (data: any) => Promise<void>,
	 *   onDelete?: () => void,
	 *   onConvert?: () => void,
	 *   onCancel?: () => void,
	 * }}
	 */
	let {
		open = $bindable(false),
		onOpenChange,
		lead = null,
		mode = 'view',
		loading = false,
		options = { statuses: [], sources: [] },
		onSave,
		onDelete,
		onConvert,
		onCancel
	} = $props();

	// Empty lead template
	const emptyLead = {
		title: '',
		firstName: '',
		lastName: '',
		email: '',
		phone: '',
		company: '',
		contactTitle: '',
		website: '',
		linkedinUrl: '',
		status: 'assigned',
		leadSource: '',
		rating: '',
		industry: '',
		opportunityAmount: '',
		probability: '',
		closeDate: '',
		addressLine: '',
		city: '',
		state: '',
		postcode: '',
		country: '',
		lastContacted: '',
		nextFollowUp: '',
		description: ''
	};

	// Form data state
	let formData = $state(/** @type {Lead} */ ({ ...emptyLead }));
	let originalData = $state(/** @type {Lead} */ ({ ...emptyLead }));
	let isSubmitting = $state(false);

	// Reset form data when lead changes or drawer opens
	$effect(() => {
		if (open) {
			if (mode === 'create') {
				formData = { ...emptyLead };
				originalData = { ...emptyLead };
			} else if (lead) {
				// Use untrack to prevent nested property access from creating fine-grained dependencies
				// This prevents the effect from re-running when editing fields
				const leadData = untrack(() => {
					const companyName = typeof lead.company === 'object' ? lead.company?.name : lead.company;
					return {
						...lead,
						company: companyName || '',
						status: lead.status?.toLowerCase().replace('_', ' ') || 'assigned'
					};
				});
				formData = leadData;
				originalData = { ...leadData };
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
		if (!formData.title?.trim()) {
			errs.title = 'Lead title is required';
		}
		if (formData.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
			errs.email = 'Invalid email address';
		}
		const prob = parseInt(String(formData.probability || '0'));
		if (formData.probability && (prob < 0 || prob > 100)) {
			errs.probability = 'Probability must be 0-100';
		}
		return errs;
	});

	const isValid = $derived(Object.keys(errors).length === 0);

	/**
	 * Update a field in form data
	 * @param {keyof Lead} field
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
				title: formData.title || '',
				first_name: formData.firstName || '',
				last_name: formData.lastName || '',
				email: formData.email || '',
				phone: formData.phone || '',
				company: formData.company || '',
				contact_title: formData.contactTitle || '',
				website: formData.website || '',
				linkedin_url: formData.linkedinUrl || '',
				status: formData.status || 'assigned',
				source: formData.leadSource || '',
				industry: formData.industry || '',
				rating: formData.rating || '',
				opportunity_amount: formData.opportunityAmount || '',
				probability: formData.probability || '',
				close_date: formData.closeDate || '',
				address_line: formData.addressLine || '',
				city: formData.city || '',
				state: formData.state || '',
				postcode: formData.postcode || '',
				country: formData.country || '',
				last_contacted: formData.lastContacted || '',
				next_follow_up: formData.nextFollowUp || '',
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
		return `${formData.firstName || ''} ${formData.lastName || ''}`.trim() || 'New Lead';
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
	 * Get status badge classes
	 * @param {string} status
	 */
	function getStatusClass(status) {
		const classes = /** @type {{ [key: string]: string }} */ ({
			new: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
			assigned: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
			'in process': 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
			pending: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
			contacted: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
			qualified: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
			converted: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400',
			recycled: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
			closed: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
		});
		return classes[status?.toLowerCase()] || classes.assigned;
	}

	/**
	 * Get rating config
	 * @param {string | undefined} rating
	 */
	function getRatingConfig(rating) {
		const configs = /** @type {{ [key: string]: { color: string, bgColor: string, dots: number } }} */ ({
			HOT: { color: 'text-red-500', bgColor: 'bg-red-500', dots: 3 },
			WARM: { color: 'text-orange-500', bgColor: 'bg-orange-500', dots: 2 },
			COLD: { color: 'text-blue-500', bgColor: 'bg-blue-500', dots: 1 }
		});
		return configs[rating?.toUpperCase() || ''] || { color: 'text-gray-400', bgColor: 'bg-gray-400', dots: 0 };
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
	 * Format relative time
	 * @param {string} date
	 */
	function formatRelativeTime(date) {
		const now = new Date();
		const then = new Date(date);
		const diff = now.getTime() - then.getTime();
		const days = Math.floor(diff / (1000 * 60 * 60 * 24));

		if (days === 0) return 'Today';
		if (days === 1) return 'Yesterday';
		if (days < 7) return `${days} days ago`;
		if (days < 30) return `${Math.floor(days / 7)} weeks ago`;
		return formatDate(date);
	}

	/**
	 * Format currency
	 * @param {string | number | undefined} amount
	 */
	function formatCurrency(amount) {
		if (!amount) return '';
		const num = parseFloat(String(amount));
		if (isNaN(num)) return '';
		return '$' + num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
	}

	const title = $derived(isCreateMode ? 'New Lead' : 'Lead');

	// Status options for select
	const statusOptions = $derived(
		options.statuses.length > 0
			? options.statuses
			: [
					{ value: 'assigned', label: 'Assigned' },
					{ value: 'in process', label: 'In Process' },
					{ value: 'converted', label: 'Converted' },
					{ value: 'recycled', label: 'Recycled' },
					{ value: 'closed', label: 'Closed' }
				]
	);

	// Source options for select
	const sourceOptions = $derived(
		options.sources.length > 0
			? options.sources
			: [
					{ value: '', label: 'Select source' },
					{ value: 'call', label: 'Call' },
					{ value: 'email', label: 'Email' },
					{ value: 'existing customer', label: 'Existing Customer' },
					{ value: 'partner', label: 'Partner' },
					{ value: 'public relations', label: 'Public Relations' },
					{ value: 'campaign', label: 'Campaign' },
					{ value: 'other', label: 'Other' }
				]
	);

	// Rating options
	const ratingOptions = [
		{ value: '', label: 'Select rating' },
		{ value: 'HOT', label: 'Hot' },
		{ value: 'WARM', label: 'Warm' },
		{ value: 'COLD', label: 'Cold' }
	];

	// Industry options (prepend empty option)
	const industryOptions = INDUSTRIES;

	// Country options
	const countryOptions = COUNTRIES;

	// Check if lead is converted
	const isConverted = $derived(formData.status?.toLowerCase() === 'converted');
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
						class="flex h-14 w-14 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-blue-600 text-lg font-semibold text-white"
					>
						{getInitials()}
					</div>
					<div class="min-w-0 flex-1 space-y-1">
						<!-- Lead Title -->
						<EditableField
							value={formData.title}
							placeholder="Lead title"
							required
							emptyText="Add lead title"
							onchange={(v) => updateField('title', v)}
							class="text-lg font-semibold"
						/>
						<!-- Editable Name -->
						<div class="flex gap-2">
							<EditableField
								value={formData.firstName}
								placeholder="First name"
								emptyText="First name"
								onchange={(v) => updateField('firstName', v)}
								class="flex-1 text-sm"
							/>
							<EditableField
								value={formData.lastName}
								placeholder="Last name"
								emptyText="Last name"
								onchange={(v) => updateField('lastName', v)}
								class="flex-1 text-sm"
							/>
						</div>
						<!-- Job Title -->
						<EditableField
							value={formData.contactTitle}
							placeholder="Job title"
							emptyText="Add job title"
							onchange={(v) => updateField('contactTitle', v)}
							class="text-muted-foreground text-sm"
						/>
						<!-- Status Badge -->
						<div class="mt-2 flex items-center gap-2">
							<span
								class={cn(
									'inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium capitalize',
									getStatusClass(formData.status || '')
								)}
							>
								{formData.status || 'assigned'}
							</span>
							{#if formData.rating}
								{@const ratingConfig = getRatingConfig(formData.rating)}
								<div class="flex items-center gap-1">
									{#each { length: ratingConfig.dots } as _}
										<div class={cn('h-2 w-2 rounded-full', ratingConfig.bgColor)}></div>
									{/each}
									<span class={cn('text-xs font-medium', ratingConfig.color)}>
										{formData.rating}
									</span>
								</div>
							{/if}
						</div>
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
							<Building2 class="text-muted-foreground h-4 w-4 shrink-0" />
							<EditableField
								value={typeof formData.company === 'object' ? formData.company?.name : formData.company || ''}
								placeholder="Company name"
								emptyText="Add company"
								onchange={(v) => updateField('company', v)}
								class="flex-1"
							/>
						</div>
						<div class="bg-muted/30 flex items-center gap-3 rounded-lg px-3 py-2">
							<Globe class="text-muted-foreground h-4 w-4 shrink-0" />
							<EditableField
								value={formData.website}
								type="url"
								placeholder="https://example.com"
								emptyText="Add website"
								onchange={(v) => updateField('website', v)}
								class="flex-1"
							/>
						</div>
						<div class="bg-muted/30 flex items-center gap-3 rounded-lg px-3 py-2">
							<Linkedin class="text-muted-foreground h-4 w-4 shrink-0" />
							<EditableField
								value={formData.linkedinUrl}
								type="url"
								placeholder="https://linkedin.com/in/username"
								emptyText="Add LinkedIn"
								onchange={(v) => updateField('linkedinUrl', v)}
								class="flex-1"
							/>
						</div>
					</div>
				</div>

				<!-- Lead Details Section -->
				<div class="mb-6">
					<p class="text-muted-foreground mb-3 text-xs font-medium tracking-wider uppercase">
						Lead Details
					</p>
					<div class="space-y-2">
						<div class="bg-muted/30 flex items-center gap-3 rounded-lg px-3 py-2">
							<Activity class="text-muted-foreground h-4 w-4 shrink-0" />
							<div class="flex-1">
								<span class="text-muted-foreground mr-2 text-xs">Status</span>
								<EditableField
									value={formData.status}
									type="select"
									options={statusOptions}
									emptyText="Select status"
									onchange={(v) => updateField('status', v)}
									class="inline"
								/>
							</div>
						</div>
						<div class="bg-muted/30 flex items-center gap-3 rounded-lg px-3 py-2">
							<Target class="text-muted-foreground h-4 w-4 shrink-0" />
							<div class="flex-1">
								<span class="text-muted-foreground mr-2 text-xs">Source</span>
								<EditableField
									value={formData.leadSource}
									type="select"
									options={sourceOptions}
									emptyText="Select source"
									onchange={(v) => updateField('leadSource', v)}
									class="inline"
								/>
							</div>
						</div>
						<div class="bg-muted/30 flex items-center gap-3 rounded-lg px-3 py-2">
							<Star class="text-muted-foreground h-4 w-4 shrink-0" />
							<div class="flex-1">
								<span class="text-muted-foreground mr-2 text-xs">Rating</span>
								<EditableField
									value={formData.rating}
									type="select"
									options={ratingOptions}
									emptyText="Select rating"
									onchange={(v) => updateField('rating', v)}
									class="inline"
								/>
							</div>
						</div>
						<div class="bg-muted/30 flex items-center gap-3 rounded-lg px-3 py-2">
							<Briefcase class="text-muted-foreground h-4 w-4 shrink-0" />
							<div class="flex-1">
								<span class="text-muted-foreground mr-2 text-xs">Industry</span>
								<EditableField
									value={formData.industry}
									type="select"
									options={industryOptions}
									emptyText="Select industry"
									onchange={(v) => updateField('industry', v)}
									class="inline"
								/>
							</div>
						</div>
					</div>
				</div>

				<!-- Deal Information Section -->
				<div class="mb-6">
					<p class="text-muted-foreground mb-3 text-xs font-medium tracking-wider uppercase">
						Deal Information
					</p>
					<div class="space-y-2">
						<div class="bg-muted/30 flex items-center gap-3 rounded-lg px-3 py-2">
							<DollarSign class="text-muted-foreground h-4 w-4 shrink-0" />
							<div class="flex-1">
								<span class="text-muted-foreground mr-2 text-xs">Deal Value</span>
								<EditableField
									value={formData.opportunityAmount}
									type="number"
									step="0.01"
									placeholder="0.00"
									emptyText="Add amount"
									displayValue={formatCurrency(formData.opportunityAmount)}
									onchange={(v) => updateField('opportunityAmount', v)}
									class="inline"
								/>
							</div>
						</div>
						<div class="bg-muted/30 flex items-center gap-3 rounded-lg px-3 py-2">
							<Percent class="text-muted-foreground h-4 w-4 shrink-0" />
							<div class="flex-1">
								<span class="text-muted-foreground mr-2 text-xs">Probability</span>
								<EditableField
									value={String(formData.probability || '')}
									type="number"
									min="0"
									max="100"
									placeholder="0-100"
									emptyText="Add %"
									displayValue={formData.probability ? `${formData.probability}%` : ''}
									validate={(v) => {
										const num = parseInt(v);
										if (v && (num < 0 || num > 100)) return 'Must be 0-100';
										return null;
									}}
									onchange={(v) => updateField('probability', v)}
									class="inline"
								/>
							</div>
						</div>
						<div class="bg-muted/30 flex items-center gap-3 rounded-lg px-3 py-2">
							<Calendar class="text-muted-foreground h-4 w-4 shrink-0" />
							<div class="flex-1">
								<span class="text-muted-foreground mr-2 text-xs">Close Date</span>
								<EditableField
									value={formData.closeDate}
									type="date"
									emptyText="Set date"
									onchange={(v) => updateField('closeDate', v)}
									class="inline"
								/>
							</div>
						</div>
					</div>
				</div>

				<!-- Activity Tracking Section -->
				<div class="mb-6">
					<p class="text-muted-foreground mb-3 text-xs font-medium tracking-wider uppercase">
						Activity Tracking
					</p>
					<div class="grid grid-cols-2 gap-2">
						<div class="bg-muted/30 rounded-lg px-3 py-2">
							<span class="text-muted-foreground text-xs">Last Contacted</span>
							<EditableField
								value={formData.lastContacted}
								type="date"
								emptyText="Set date"
								onchange={(v) => updateField('lastContacted', v)}
								class="mt-1"
							/>
						</div>
						<div class="bg-muted/30 rounded-lg px-3 py-2">
							<span class="text-muted-foreground text-xs">Next Follow-up</span>
							<EditableField
								value={formData.nextFollowUp}
								type="date"
								emptyText="Set date"
								onchange={(v) => updateField('nextFollowUp', v)}
								class="mt-1"
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
						placeholder="Add notes about this lead..."
						emptyText="Add notes..."
						onchange={(v) => updateField('description', v)}
					/>
				</div>

				{#if !isCreateMode}
					<Separator class="mb-6" />

					<!-- Read-only sections for existing leads -->

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
									{lead?.owner?.name || 'Unassigned'}
								</p>
							</div>
							<div>
								<div class="text-muted-foreground flex items-center gap-1.5 text-xs">
									<Calendar class="h-3.5 w-3.5" />
									<span>Created</span>
								</div>
								<p class="text-foreground mt-0.5 text-sm font-medium">
									{formatDate(lead?.createdAt || '')}
								</p>
							</div>
						</div>
					</div>

					<!-- Activity Timeline -->
					<div>
						<div class="mb-3 flex items-center gap-2">
							<Activity class="text-muted-foreground h-4 w-4" />
							<p class="text-muted-foreground text-xs font-medium tracking-wider uppercase">
								Activity
							</p>
						</div>
						{#if lead?.comments && lead.comments.length > 0}
							<div class="space-y-3">
								{#each lead.comments.slice(0, 5) as comment (comment.id)}
									<div class="flex gap-3">
										<div
											class="bg-muted flex h-8 w-8 shrink-0 items-center justify-center rounded-full"
										>
											<MessageSquare class="text-muted-foreground h-4 w-4" />
										</div>
										<div class="min-w-0 flex-1">
											<p class="text-foreground text-sm">
												<span class="font-medium">{comment.author?.name || 'Unknown'}</span>
												{' '}added a note
											</p>
											<p class="text-muted-foreground mt-0.5 text-xs">
												{formatRelativeTime(comment.createdAt)}
											</p>
											<p class="text-muted-foreground mt-1 line-clamp-2 text-sm">
												{comment.body}
											</p>
										</div>
									</div>
								{/each}
							</div>
						{:else}
							<div class="flex flex-col items-center justify-center py-6 text-center">
								<MessageSquare class="text-muted-foreground/50 mb-2 h-8 w-8" />
								<p class="text-muted-foreground text-sm">No activity yet</p>
							</div>
						{/if}
					</div>
				{/if}
			</div>
		{/if}
	{/snippet}

	{#snippet footer()}
		<div class="flex w-full items-center justify-between">
			<div class="flex gap-2">
				{#if !isCreateMode && onDelete}
					<Button
						variant="ghost"
						class="text-destructive hover:text-destructive"
						onclick={onDelete}
						disabled={isSubmitting}
					>
						Delete
					</Button>
				{/if}
				{#if !isCreateMode && !isConverted && onConvert}
					<Button variant="outline" onclick={onConvert} disabled={isSubmitting}>
						<ArrowRightCircle class="mr-2 h-4 w-4" />
						Convert
					</Button>
				{/if}
			</div>
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
							{isCreateMode ? 'Create Lead' : 'Save Changes'}
						{/if}
					</Button>
				{/if}
			</div>
		</div>
	{/snippet}
</SideDrawer>
