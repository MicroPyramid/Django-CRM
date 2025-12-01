<script>
	import {
		Globe,
		Phone,
		Mail,
		MapPin,
		Calendar,
		Users,
		Target,
		DollarSign,
		Briefcase,
		Building2,
		User,
		AlertTriangle,
		Lock,
		Unlock,
		Loader2,
		Trash2
	} from '@lucide/svelte';
	import SideDrawer from '$lib/components/layout/SideDrawer.svelte';
	import { EditableField } from '$lib/components/ui/editable-field/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Separator } from '$lib/components/ui/separator/index.js';
	import { Skeleton } from '$lib/components/ui/skeleton/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { cn } from '$lib/utils.js';
	import { COUNTRIES, getCountryName } from '$lib/constants/countries.js';

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
	 * @typedef {Object} Account
	 * @property {string} [id]
	 * @property {string} name
	 * @property {string} [industry]
	 * @property {string} [website]
	 * @property {string} [phone]
	 * @property {string} [email]
	 * @property {string} [description]
	 * @property {string} [addressLine]
	 * @property {string} [city]
	 * @property {string} [state]
	 * @property {string} [postcode]
	 * @property {string} [country]
	 * @property {number|string} [annualRevenue]
	 * @property {number|string} [numberOfEmployees]
	 * @property {boolean} [isActive]
	 * @property {string} [closedAt]
	 * @property {string} [closureReason]
	 * @property {string} [createdAt]
	 * @property {string} [updatedAt]
	 * @property {{name: string, email?: string}} [owner]
	 * @property {number} [contactCount]
	 * @property {number} [opportunityCount]
	 * @property {number} [caseCount]
	 */

	/**
	 * @type {{
	 *   open?: boolean,
	 *   onOpenChange?: (open: boolean) => void,
	 *   account?: Account | null,
	 *   mode?: 'view' | 'create',
	 *   loading?: boolean,
	 *   onSave?: (data: any) => Promise<void>,
	 *   onDelete?: () => void,
	 *   onClose?: () => void,
	 *   onReopen?: () => void,
	 *   onAddContact?: () => void,
	 *   onAddOpportunity?: () => void,
	 *   onCancel?: () => void,
	 * }}
	 */
	let {
		open = $bindable(false),
		onOpenChange,
		account = null,
		mode = 'view',
		loading = false,
		onSave,
		onDelete,
		onClose,
		onReopen,
		onAddContact,
		onAddOpportunity,
		onCancel
	} = $props();

	// Empty account template for create mode
	const emptyAccount = {
		name: '',
		industry: '',
		website: '',
		phone: '',
		email: '',
		description: '',
		addressLine: '',
		city: '',
		state: '',
		postcode: '',
		country: '',
		annualRevenue: '',
		numberOfEmployees: ''
	};

	// Form data state - editable copy of account
	let formData = $state(/** @type {Account} */ ({ ...emptyAccount }));
	let originalData = $state(/** @type {Account} */ ({ ...emptyAccount }));
	let isSubmitting = $state(false);

	// Reset form data when account changes or drawer opens
	$effect(() => {
		if (open) {
			if (mode === 'create') {
				formData = { ...emptyAccount };
				originalData = { ...emptyAccount };
			} else if (account) {
				formData = { ...account };
				originalData = { ...account };
			}
		}
	});

	// Check if form has changes
	const isDirty = $derived.by(() => {
		return JSON.stringify(formData) !== JSON.stringify(originalData);
	});

	// Check if it's create mode
	const isCreateMode = $derived(mode === 'create');

	// Check if account is closed (inactive)
	const isClosed = $derived(account?.isActive === false);

	// Validation
	const errors = $derived.by(() => {
		/** @type {Record<string, string>} */
		const errs = {};
		if (!formData.name?.trim()) {
			errs.name = 'Account name is required';
		}
		if (formData.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
			errs.email = 'Invalid email address';
		}
		if (
			formData.website &&
			!/^(https?:\/\/)?[\w.-]+\.[a-z]{2,}(\/\S*)?$/i.test(formData.website)
		) {
			errs.website = 'Invalid website URL';
		}
		return errs;
	});

	const isValid = $derived(Object.keys(errors).length === 0);

	/**
	 * Update a field in form data
	 * @param {keyof Account} field
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
				name: formData.name,
				industry: formData.industry || '',
				website: formData.website || '',
				phone: formData.phone || '',
				email: formData.email || '',
				description: formData.description || '',
				address_line: formData.addressLine || '',
				city: formData.city || '',
				state: formData.state || '',
				postcode: formData.postcode || '',
				country: formData.country || '',
				annual_revenue: formData.annualRevenue || '',
				number_of_employees: formData.numberOfEmployees || ''
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
	 * Get initials for avatar
	 */
	function getInitials() {
		return (formData.name?.[0] || 'A').toUpperCase();
	}

	/**
	 * Format date
	 * @param {string | null | undefined} date
	 */
	function formatDate(date) {
		if (!date) return '-';
		return new Date(date).toLocaleDateString('en-US', {
			month: 'short',
			day: 'numeric',
			year: 'numeric'
		});
	}

	/**
	 * Format currency
	 * @param {number | string | null | undefined} value
	 */
	function formatCurrency(value) {
		if (!value) return '';
		const num = typeof value === 'string' ? parseFloat(value) : value;
		if (isNaN(num)) return '';
		return new Intl.NumberFormat('en-US', {
			style: 'currency',
			currency: 'USD',
			minimumFractionDigits: 0,
			maximumFractionDigits: 0
		}).format(num);
	}

	/**
	 * Format number
	 * @param {number | string | null | undefined} value
	 */
	function formatNumber(value) {
		if (!value) return '';
		const num = typeof value === 'string' ? parseFloat(value) : value;
		if (isNaN(num)) return '';
		return new Intl.NumberFormat('en-US').format(num);
	}

	/**
	 * Get industry label from value
	 * @param {string | undefined} value
	 */
	function getIndustryLabel(value) {
		if (!value) return '';
		const industry = INDUSTRIES.find((i) => i.value === value);
		return industry?.label || value;
	}

	const title = $derived(isCreateMode ? 'New Account' : 'Account');

	// Options for select fields
	const industryOptions = INDUSTRIES.map((i) => ({ value: i.value, label: i.label }));
	const countryOptions = COUNTRIES.map((c) => ({ value: c.code, label: c.name }));
</script>

<SideDrawer bind:open {onOpenChange} {title}>
	{#snippet children()}
		{#if loading}
			<!-- Loading skeleton -->
			<div class="space-y-6 p-6">
				<div class="flex items-start gap-4">
					<Skeleton class="h-14 w-14 rounded-lg" />
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
						class="flex h-14 w-14 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-blue-600 text-lg font-semibold text-white"
					>
						{getInitials()}
					</div>
					<div class="min-w-0 flex-1 space-y-1">
						<!-- Editable Name -->
						<div class="flex items-center gap-2">
							<EditableField
								value={formData.name}
								placeholder="Account name"
								required
								emptyText="Account name"
								disabled={isClosed && !isCreateMode}
								onchange={(v) => updateField('name', v)}
								class="flex-1 text-lg font-semibold"
							/>
							{#if !isCreateMode}
								{#if account?.isActive !== false}
									<Badge variant="default" class="shrink-0 bg-green-500 hover:bg-green-600">
										Active
									</Badge>
								{:else}
									<Badge variant="secondary" class="shrink-0 bg-gray-500">Closed</Badge>
								{/if}
							{/if}
						</div>
						<!-- Editable Industry -->
						<div class="bg-muted/30 flex items-center gap-2 rounded-lg px-3 py-1.5">
							<Briefcase class="text-muted-foreground h-4 w-4 shrink-0" />
							<EditableField
								value={formData.industry}
								type="select"
								options={industryOptions}
								placeholder="Select industry"
								emptyText="Add industry"
								displayValue={getIndustryLabel(formData.industry)}
								disabled={isClosed && !isCreateMode}
								onchange={(v) => updateField('industry', v)}
								class="flex-1 text-sm"
							/>
						</div>
					</div>
				</div>

				<!-- Closure Warning -->
				{#if isClosed && !isCreateMode}
					<div class="border-destructive/50 bg-destructive/10 mb-6 rounded-lg border p-4">
						<div class="flex gap-3">
							<AlertTriangle class="text-destructive h-5 w-5 shrink-0" />
							<div>
								<p class="text-destructive font-medium">
									This account is closed
								</p>
								<p class="text-muted-foreground mt-1 text-sm">
									Reopen the account to make changes
								</p>
							</div>
						</div>
					</div>
				{/if}

				<!-- Contact Information Section (Notion-style property rows) -->
				<div class="mb-6">
					<p class="text-gray-500 mb-3 text-xs font-medium tracking-wider uppercase">
						Contact Information
					</p>
					<div class="space-y-0">
						<!-- Website property -->
						<div class="flex items-center min-h-[36px] px-2 -mx-2 rounded hover:bg-gray-50/60 transition-colors duration-75 group">
							<div class="w-28 shrink-0 flex items-center gap-2 text-[13px] text-gray-500">
								<Globe class="h-4 w-4 text-gray-400" />
								Website
							</div>
							<div class="flex-1 min-w-0">
								<EditableField
									value={formData.website}
									type="url"
									placeholder="https://example.com"
									emptyText="Add website"
									disabled={isClosed && !isCreateMode}
									validate={(v) => {
										if (v && !/^(https?:\/\/)?[\w.-]+\.[a-z]{2,}(\/\S*)?$/i.test(v)) {
											return 'Invalid website URL';
										}
										return null;
									}}
									onchange={(v) => updateField('website', v)}
									class="flex-1"
								/>
							</div>
						</div>
						<!-- Phone property -->
						<div class="flex items-center min-h-[36px] px-2 -mx-2 rounded hover:bg-gray-50/60 transition-colors duration-75 group">
							<div class="w-28 shrink-0 flex items-center gap-2 text-[13px] text-gray-500">
								<Phone class="h-4 w-4 text-gray-400" />
								Phone
							</div>
							<div class="flex-1 min-w-0">
								<EditableField
									value={formData.phone}
									type="phone"
									placeholder="+1 (555) 000-0000"
									emptyText="Add phone"
									disabled={isClosed && !isCreateMode}
									onchange={(v) => updateField('phone', v)}
									class="flex-1"
								/>
							</div>
						</div>
						<!-- Email property -->
						<div class="flex items-center min-h-[36px] px-2 -mx-2 rounded hover:bg-gray-50/60 transition-colors duration-75 group">
							<div class="w-28 shrink-0 flex items-center gap-2 text-[13px] text-gray-500">
								<Mail class="h-4 w-4 text-gray-400" />
								Email
							</div>
							<div class="flex-1 min-w-0">
								<EditableField
									value={formData.email}
									type="email"
									placeholder="contact@company.com"
									emptyText="Add email"
									disabled={isClosed && !isCreateMode}
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
						</div>
					</div>
				</div>

				<!-- Related Entities Stats (view mode only) -->
				{#if !isCreateMode && account}
					<div class="mb-6 grid grid-cols-3 gap-3">
						<div class="bg-muted/50 rounded-lg p-3 text-center">
							<div class="text-muted-foreground flex items-center justify-center gap-1.5">
								<Users class="h-4 w-4" />
							</div>
							<p class="text-foreground mt-1 text-xl font-semibold">
								{account.contactCount || 0}
							</p>
							<p class="text-muted-foreground text-xs">Contacts</p>
						</div>
						<div class="bg-muted/50 rounded-lg p-3 text-center">
							<div class="text-muted-foreground flex items-center justify-center gap-1.5">
								<Target class="h-4 w-4" />
							</div>
							<p class="text-foreground mt-1 text-xl font-semibold">
								{account.opportunityCount || 0}
							</p>
							<p class="text-muted-foreground text-xs">Opportunities</p>
						</div>
						<div class="bg-muted/50 rounded-lg p-3 text-center">
							<div class="text-muted-foreground flex items-center justify-center gap-1.5">
								<AlertTriangle class="h-4 w-4" />
							</div>
							<p class="text-foreground mt-1 text-xl font-semibold">
								{account.caseCount || 0}
							</p>
							<p class="text-muted-foreground text-xs">Cases</p>
						</div>
					</div>
				{/if}

				<!-- Business Details Section (Notion-style property rows) -->
				<div class="mb-6">
					<p class="text-gray-500 mb-3 text-xs font-medium tracking-wider uppercase">
						Business Details
					</p>
					<div class="space-y-0">
						<!-- Annual Revenue property -->
						<div class="flex items-center min-h-[36px] px-2 -mx-2 rounded hover:bg-gray-50/60 transition-colors duration-75 group">
							<div class="w-28 shrink-0 flex items-center gap-2 text-[13px] text-gray-500">
								<DollarSign class="h-4 w-4 text-gray-400" />
								Revenue
							</div>
							<div class="flex-1 min-w-0">
								<EditableField
									value={formData.annualRevenue?.toString() || ''}
									type="number"
									placeholder="1000000"
									emptyText="Add annual revenue"
									displayValue={formatCurrency(formData.annualRevenue)}
									disabled={isClosed && !isCreateMode}
									onchange={(v) => updateField('annualRevenue', v)}
									class="flex-1"
								/>
							</div>
						</div>
						<!-- Employees property -->
						<div class="flex items-center min-h-[36px] px-2 -mx-2 rounded hover:bg-gray-50/60 transition-colors duration-75 group">
							<div class="w-28 shrink-0 flex items-center gap-2 text-[13px] text-gray-500">
								<Users class="h-4 w-4 text-gray-400" />
								Employees
							</div>
							<div class="flex-1 min-w-0">
								<EditableField
									value={formData.numberOfEmployees?.toString() || ''}
									type="number"
									placeholder="100"
									emptyText="Add employee count"
									displayValue={formatNumber(formData.numberOfEmployees)}
									disabled={isClosed && !isCreateMode}
									onchange={(v) => updateField('numberOfEmployees', v)}
									class="flex-1"
								/>
							</div>
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
							disabled={isClosed && !isCreateMode}
							onchange={(v) => updateField('addressLine', v)}
						/>
						<div class="grid grid-cols-2 gap-2">
							<EditableField
								value={formData.city}
								placeholder="City"
								emptyText="City"
								disabled={isClosed && !isCreateMode}
								onchange={(v) => updateField('city', v)}
							/>
							<EditableField
								value={formData.state}
								placeholder="State/Province"
								emptyText="State"
								disabled={isClosed && !isCreateMode}
								onchange={(v) => updateField('state', v)}
							/>
						</div>
						<div class="grid grid-cols-2 gap-2">
							<EditableField
								value={formData.postcode}
								placeholder="Postal code"
								emptyText="Postal code"
								disabled={isClosed && !isCreateMode}
								onchange={(v) => updateField('postcode', v)}
							/>
							<EditableField
								value={formData.country}
								type="select"
								options={countryOptions}
								placeholder="Select country"
								emptyText="Country"
								displayValue={formData.country ? getCountryName(formData.country) : ''}
								disabled={isClosed && !isCreateMode}
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
						placeholder="Add notes about this account..."
						emptyText="Add notes..."
						disabled={isClosed && !isCreateMode}
						onchange={(v) => updateField('description', v)}
					/>
				</div>

				{#if !isCreateMode && account}
					<Separator class="mb-6" />

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
									{account.owner?.name || 'Unassigned'}
								</p>
							</div>
							<div>
								<div class="text-muted-foreground flex items-center gap-1.5 text-xs">
									<Calendar class="h-3.5 w-3.5" />
									<span>Created</span>
								</div>
								<p class="text-foreground mt-0.5 text-sm font-medium">
									{formatDate(account.createdAt)}
								</p>
							</div>
							{#if account.updatedAt}
								<div>
									<div class="text-muted-foreground flex items-center gap-1.5 text-xs">
										<Calendar class="h-3.5 w-3.5" />
										<span>Updated</span>
									</div>
									<p class="text-foreground mt-0.5 text-sm font-medium">
										{formatDate(account.updatedAt)}
									</p>
								</div>
							{/if}
						</div>
					</div>

					<!-- Quick Actions (for active accounts only) -->
					{#if !isClosed && (onAddContact || onAddOpportunity)}
						<div class="mb-6">
							<p class="text-muted-foreground mb-2 text-xs font-medium tracking-wider uppercase">
								Quick Actions
							</p>
							<div class="flex gap-2">
								{#if onAddContact}
									<Button
										variant="outline"
										size="sm"
										onclick={onAddContact}
										class="flex-1"
										disabled={false}
									>
										<Users class="mr-1.5 h-4 w-4" />
										Add Contact
									</Button>
								{/if}
								{#if onAddOpportunity}
									<Button
										variant="outline"
										size="sm"
										onclick={onAddOpportunity}
										class="flex-1"
										disabled={false}
									>
										<Target class="mr-1.5 h-4 w-4" />
										Add Opportunity
									</Button>
								{/if}
							</div>
						</div>
					{/if}
				{/if}
			</div>
		{/if}
	{/snippet}

	{#snippet footer()}
		<div class="flex w-full items-center justify-between">
			<!-- Left side: Delete and Close/Reopen buttons -->
			{#if !isCreateMode && account}
				<div class="flex gap-2">
					{#if onDelete}
						<Button
							variant="ghost"
							class="text-destructive hover:bg-destructive/10 hover:text-destructive"
							onclick={onDelete}
							disabled={isSubmitting}
						>
							<Trash2 class="mr-2 h-4 w-4" />
							Delete
						</Button>
					{/if}
					{#if isClosed}
						{#if onReopen}
							<Button
								variant="outline"
								class="text-green-600 hover:text-green-700"
								onclick={onReopen}
								disabled={isSubmitting}
							>
								<Unlock class="mr-2 h-4 w-4" />
								Reopen Account
							</Button>
						{/if}
					{:else if onClose}
						<Button
							variant="ghost"
							class="text-destructive hover:text-destructive"
							onclick={onClose}
							disabled={isSubmitting}
						>
							<Lock class="mr-2 h-4 w-4" />
							Close Account
						</Button>
					{/if}
				</div>
			{:else}
				<div></div>
			{/if}

			<!-- Right side: Cancel and Save buttons -->
			<div class="flex gap-2">
				<Button variant="outline" onclick={handleCancel} disabled={isSubmitting}>
					Cancel
				</Button>
				{#if (isDirty || isCreateMode) && !isClosed}
					<Button onclick={handleSave} disabled={isSubmitting || !isValid}>
						{#if isSubmitting}
							<Loader2 class="mr-2 h-4 w-4 animate-spin" />
							{isCreateMode ? 'Creating...' : 'Saving...'}
						{:else}
							{isCreateMode ? 'Create Account' : 'Save Changes'}
						{/if}
					</Button>
				{/if}
			</div>
		</div>
	{/snippet}
</SideDrawer>
