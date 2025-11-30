<script>
	import { Loader2, X } from '@lucide/svelte';
	import SideDrawer from '$lib/components/layout/SideDrawer.svelte';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import { Textarea } from '$lib/components/ui/textarea/index.js';
	import { Separator } from '$lib/components/ui/separator/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { cn } from '$lib/utils.js';
	import {
		OPPORTUNITY_STAGES,
		OPPORTUNITY_TYPES,
		OPPORTUNITY_SOURCES,
		CURRENCY_CODES
	} from '$lib/constants/filters.js';

	/**
	 * @typedef {Object} OpportunityFormData
	 * @property {string} [id]
	 * @property {string} name
	 * @property {string} amount
	 * @property {string} stage
	 * @property {string} opportunity_type
	 * @property {string} currency
	 * @property {string} probability
	 * @property {string} lead_source
	 * @property {string} closed_on
	 * @property {string} account_id
	 * @property {string[]} contacts
	 * @property {string[]} tags
	 * @property {string} description
	 */

	/**
	 * @typedef {Object} FormOptions
	 * @property {Array<{ id: string, name: string }>} accounts
	 * @property {Array<{ id: string, name: string, email?: string }>} contacts
	 * @property {Array<{ id: string, name: string }>} tags
	 */

	/**
	 * @type {{
	 *   open?: boolean,
	 *   onOpenChange?: (open: boolean) => void,
	 *   mode?: 'create' | 'edit',
	 *   initialData?: Partial<OpportunityFormData> | null,
	 *   initialStage?: string,
	 *   options?: FormOptions,
	 *   loading?: boolean,
	 *   onSubmit?: (data: OpportunityFormData) => Promise<void>,
	 *   onCancel?: () => void,
	 * }}
	 */
	let {
		open = $bindable(false),
		onOpenChange,
		mode = 'create',
		initialData = null,
		initialStage = 'PROSPECTING',
		options = { accounts: [], contacts: [], tags: [] },
		loading = false,
		onSubmit,
		onCancel
	} = $props();

	// Stage options (without ALL filter)
	const stages = OPPORTUNITY_STAGES.filter((s) => s.value !== 'ALL');
	const opportunityTypes = OPPORTUNITY_TYPES;
	const leadSources = OPPORTUNITY_SOURCES;
	const currencies = CURRENCY_CODES;

	/** @type {OpportunityFormData} */
	let formData = $state({
		name: '',
		amount: '',
		stage: 'PROSPECTING',
		opportunity_type: '',
		currency: 'USD',
		probability: '50',
		lead_source: '',
		closed_on: '',
		account_id: '',
		contacts: [],
		tags: [],
		description: ''
	});

	/** @type {Record<string, string>} */
	let errors = $state({});
	let isSubmitting = $state(false);
	let tagInput = $state('');

	// Reset form when drawer opens with new data
	$effect(() => {
		if (open) {
			if (initialData) {
				formData = {
					name: initialData.name || '',
					amount: initialData.amount || '',
					stage: initialData.stage || 'PROSPECTING',
					opportunity_type: initialData.opportunity_type || '',
					currency: initialData.currency || 'USD',
					probability: initialData.probability || '50',
					lead_source: initialData.lead_source || '',
					closed_on: initialData.closed_on || '',
					account_id: initialData.account_id || '',
					contacts: initialData.contacts || [],
					tags: initialData.tags || [],
					description: initialData.description || ''
				};
			} else {
				formData = {
					name: '',
					amount: '',
					stage: initialStage || 'PROSPECTING',
					opportunity_type: '',
					currency: 'USD',
					probability: '50',
					lead_source: '',
					closed_on: '',
					account_id: '',
					contacts: [],
					tags: [],
					description: ''
				};
			}
			errors = {};
			tagInput = '';
		}
	});

	/**
	 * Validate form
	 */
	function validateForm() {
		errors = {};
		let isValid = true;

		if (!formData.name?.trim()) {
			errors.name = 'Opportunity name is required';
			isValid = false;
		}

		if (formData.amount) {
			const amt = Number(formData.amount);
			if (isNaN(amt) || amt < 0) {
				errors.amount = 'Please enter a valid amount';
				isValid = false;
			}
		}

		if (formData.probability) {
			const prob = Number(formData.probability);
			if (isNaN(prob) || prob < 0 || prob > 100) {
				errors.probability = 'Probability must be between 0 and 100';
				isValid = false;
			}
		}

		if (formData.closed_on) {
			const date = new Date(formData.closed_on);
			if (isNaN(date.getTime())) {
				errors.closed_on = 'Please enter a valid date';
				isValid = false;
			}
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

	/**
	 * Add tag
	 */
	function addTag() {
		const tag = tagInput.trim();
		if (tag && !formData.tags.includes(tag)) {
			formData.tags = [...formData.tags, tag];
		}
		tagInput = '';
	}

	/**
	 * Remove tag
	 * @param {string} tag
	 */
	function removeTag(tag) {
		formData.tags = formData.tags.filter((t) => t !== tag);
	}

	/**
	 * Handle tag input keydown
	 * @param {KeyboardEvent} e
	 */
	function handleTagKeydown(e) {
		if (e.key === 'Enter' || e.key === ',') {
			e.preventDefault();
			addTag();
		}
	}

	/**
	 * Toggle contact selection
	 * @param {string} contactId
	 */
	function toggleContact(contactId) {
		if (formData.contacts.includes(contactId)) {
			formData.contacts = formData.contacts.filter((id) => id !== contactId);
		} else {
			formData.contacts = [...formData.contacts, contactId];
		}
	}

	const title = $derived(mode === 'create' ? 'New Opportunity' : 'Edit Opportunity');
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
							<Label for="name" class="text-sm">Opportunity Name *</Label>
							<Input
								id="name"
								type="text"
								bind:value={formData.name}
								placeholder="e.g., Enterprise Software License"
								class={cn('mt-1.5', errors.name && 'border-destructive')}
							/>
							{#if errors.name}
								<p class="text-destructive mt-1 text-xs">{errors.name}</p>
							{/if}
						</div>

						<div>
							<Label for="opportunity_type" class="text-sm">Opportunity Type</Label>
							<select
								id="opportunity_type"
								bind:value={formData.opportunity_type}
								class="border-input bg-background ring-offset-background focus:ring-ring mt-1.5 w-full rounded-md border px-3 py-2 text-sm focus:ring-2 focus:ring-offset-2 focus:outline-none"
							>
								{#each opportunityTypes as type}
									<option value={type.value}>{type.label}</option>
								{/each}
							</select>
						</div>

						<div>
							<Label for="stage" class="text-sm">Stage</Label>
							<select
								id="stage"
								bind:value={formData.stage}
								class="border-input bg-background ring-offset-background focus:ring-ring mt-1.5 w-full rounded-md border px-3 py-2 text-sm focus:ring-2 focus:ring-offset-2 focus:outline-none"
							>
								{#each stages as stage}
									<option value={stage.value}>{stage.label}</option>
								{/each}
							</select>
						</div>
					</div>
				</div>

				<Separator class="mb-6" />

				<!-- Financial Information -->
				<div class="mb-6">
					<p class="text-muted-foreground mb-3 text-xs font-medium tracking-wider uppercase">
						Financial Information
					</p>
					<div class="space-y-4">
						<div class="grid grid-cols-2 gap-3">
							<div>
								<Label for="currency" class="text-sm">Currency</Label>
								<select
									id="currency"
									bind:value={formData.currency}
									class="border-input bg-background ring-offset-background focus:ring-ring mt-1.5 w-full rounded-md border px-3 py-2 text-sm focus:ring-2 focus:ring-offset-2 focus:outline-none"
								>
									{#each currencies as currency}
										<option value={currency.value}>{currency.label}</option>
									{/each}
								</select>
							</div>
							<div>
								<Label for="amount" class="text-sm">Amount</Label>
								<Input
									id="amount"
									type="number"
									min="0"
									step="0.01"
									bind:value={formData.amount}
									placeholder="10000"
									class={cn('mt-1.5', errors.amount && 'border-destructive')}
								/>
								{#if errors.amount}
									<p class="text-destructive mt-1 text-xs">{errors.amount}</p>
								{/if}
							</div>
						</div>

						<div class="grid grid-cols-2 gap-3">
							<div>
								<Label for="probability" class="text-sm">Probability (%)</Label>
								<Input
									id="probability"
									type="number"
									min="0"
									max="100"
									bind:value={formData.probability}
									placeholder="50"
									class={cn('mt-1.5', errors.probability && 'border-destructive')}
								/>
								{#if errors.probability}
									<p class="text-destructive mt-1 text-xs">{errors.probability}</p>
								{/if}
							</div>
							<div>
								<Label for="closed_on" class="text-sm">Expected Close Date</Label>
								<Input
									id="closed_on"
									type="date"
									bind:value={formData.closed_on}
									class={cn('mt-1.5', errors.closed_on && 'border-destructive')}
								/>
								{#if errors.closed_on}
									<p class="text-destructive mt-1 text-xs">{errors.closed_on}</p>
								{/if}
							</div>
						</div>
					</div>
				</div>

				<Separator class="mb-6" />

				<!-- Related Information -->
				<div class="mb-6">
					<p class="text-muted-foreground mb-3 text-xs font-medium tracking-wider uppercase">
						Related Information
					</p>
					<div class="space-y-4">
						<div>
							<Label for="account_id" class="text-sm">Account</Label>
							<select
								id="account_id"
								bind:value={formData.account_id}
								class="border-input bg-background ring-offset-background focus:ring-ring mt-1.5 w-full rounded-md border px-3 py-2 text-sm focus:ring-2 focus:ring-offset-2 focus:outline-none"
							>
								<option value="">Select account</option>
								{#if options.accounts.length > 0}
									{#each options.accounts as account}
										<option value={account.id}>{account.name}</option>
									{/each}
								{/if}
							</select>
						</div>

						<div>
							<Label for="lead_source" class="text-sm">Lead Source</Label>
							<select
								id="lead_source"
								bind:value={formData.lead_source}
								class="border-input bg-background ring-offset-background focus:ring-ring mt-1.5 w-full rounded-md border px-3 py-2 text-sm focus:ring-2 focus:ring-offset-2 focus:outline-none"
							>
								{#each leadSources as source}
									<option value={source.value}>{source.label}</option>
								{/each}
							</select>
						</div>

						<!-- Contacts Multi-Select -->
						{#if options.contacts && options.contacts.length > 0}
							<div>
								<Label class="text-sm">Contacts</Label>
								<div
									class="border-input mt-1.5 max-h-32 space-y-1 overflow-y-auto rounded-md border p-2"
								>
									{#each options.contacts as contact}
										<label class="hover:bg-muted flex cursor-pointer items-center gap-2 rounded p-1">
											<input
												type="checkbox"
												checked={formData.contacts.includes(contact.id)}
												onchange={() => toggleContact(contact.id)}
												class="rounded"
											/>
											<span class="text-sm">{contact.name}</span>
											{#if contact.email}
												<span class="text-muted-foreground text-xs">({contact.email})</span>
											{/if}
										</label>
									{/each}
								</div>
								{#if formData.contacts.length > 0}
									<p class="text-muted-foreground mt-1 text-xs">
										{formData.contacts.length} contact(s) selected
									</p>
								{/if}
							</div>
						{/if}
					</div>
				</div>

				<Separator class="mb-6" />

				<!-- Tags -->
				<div class="mb-6">
					<p class="text-muted-foreground mb-3 text-xs font-medium tracking-wider uppercase">
						Tags
					</p>
					<div>
						<Label for="tags" class="text-sm">Add Tags</Label>
						<div class="mt-1.5 flex gap-2">
							<Input
								id="tags"
								type="text"
								bind:value={tagInput}
								placeholder="Type and press Enter"
								onkeydown={handleTagKeydown}
								class="flex-1"
							/>
							<Button type="button" variant="outline" onclick={addTag} disabled={!tagInput.trim()}>
								Add
							</Button>
						</div>
						{#if formData.tags.length > 0}
							<div class="mt-2 flex flex-wrap gap-1">
								{#each formData.tags as tag}
									<Badge variant="secondary" class="gap-1 pr-1">
										{tag}
										<button
											type="button"
											class="hover:bg-muted ml-1 rounded-full p-0.5"
											onclick={() => removeTag(tag)}
										>
											<X class="h-3 w-3" />
										</button>
									</Badge>
								{/each}
							</div>
						{/if}
					</div>
				</div>

				<Separator class="mb-6" />

				<!-- Additional Details -->
				<div class="mb-6">
					<p class="text-muted-foreground mb-3 text-xs font-medium tracking-wider uppercase">
						Additional Details
					</p>
					<div>
						<Label for="description" class="text-sm">Description</Label>
						<Textarea
							id="description"
							bind:value={formData.description}
							placeholder="Additional notes about this opportunity..."
							rows={4}
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
					{mode === 'create' ? 'Create Opportunity' : 'Save Changes'}
				{/if}
			</Button>
		</div>
	{/snippet}
</SideDrawer>
