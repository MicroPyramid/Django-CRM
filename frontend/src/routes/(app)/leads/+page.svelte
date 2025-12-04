<script>
	import { enhance } from '$app/forms';
	import { invalidateAll } from '$app/navigation';
	import { tick, onMount } from 'svelte';
	import { toast } from 'svelte-sonner';
	import {
		Plus,
		Phone,
		Mail,
		Building2,
		User,
		Calendar,
		Eye,
		Star,
		Globe,
		Briefcase,
		Linkedin,
		Target,
		DollarSign,
		Percent,
		MapPin,
		FileText,
		Users,
		UserPlus,
		Tag,
		MessageSquare,
		Loader2,
		ArrowRightCircle
	} from '@lucide/svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { Button } from '$lib/components/ui/button/index.js';
	import { INDUSTRIES, COUNTRIES } from '$lib/constants/lead-choices.js';
	import * as DropdownMenu from '$lib/components/ui/dropdown-menu/index.js';
	import { formatRelativeDate, formatDate, getNameInitials } from '$lib/utils/formatting.js';
	import { useListFilters } from '$lib/hooks';
	import {
		leadStatusOptions,
		leadRatingOptions,
		getOptionStyle,
		getOptionLabel,
		getOptionBgColor
	} from '$lib/utils/table-helpers.js';
	import CrmTable from '$lib/components/ui/crm-table/CrmTable.svelte';
	import CrmDrawer from '$lib/components/ui/crm-drawer/CrmDrawer.svelte';

	// Column visibility configuration
	const STORAGE_KEY = 'leads-column-config';

	/**
	 * @typedef {'text' | 'email' | 'number' | 'date' | 'select' | 'checkbox' | 'relation'} ColumnType
	 * @typedef {{ key: string, label: string, type?: ColumnType, width?: string, editable?: boolean, canHide?: boolean, getValue?: (row: any) => any, emptyText?: string, relationIcon?: string, options?: any[] }} ColumnDef
	 */

	/** @type {ColumnDef[]} */
	const columns = [
		{
			key: 'title',
			label: 'Title',
			type: 'text',
			width: 'w-48',
			canHide: false,
			emptyText: 'Untitled'
		},
		{
			key: 'name',
			label: 'Name',
			type: 'text',
			width: 'w-[200px]',
			editable: false,
			canHide: false,
			getValue: (row) => `${row.firstName || ''} ${row.lastName || ''}`.trim(),
			emptyText: ''
		},
		{
			key: 'company',
			label: 'Company',
			type: 'relation',
			width: 'w-40',
			relationIcon: 'building',
			getValue: (row) => (typeof row.company === 'object' ? row.company?.name : row.company),
			emptyText: ''
		},
		{
			key: 'email',
			label: 'Email',
			type: 'email',
			width: 'w-52',
			emptyText: ''
		},
		{
			key: 'phone',
			label: 'Phone',
			type: 'text',
			width: 'w-36',
			emptyText: ''
		},
		{
			key: 'rating',
			label: 'Rating',
			type: 'select',
			width: 'w-28',
			options: leadRatingOptions
		},
		{
			key: 'status',
			label: 'Status',
			type: 'select',
			width: 'w-28',
			options: leadStatusOptions
		},
		{
			key: 'createdAt',
			label: 'Created',
			type: 'date',
			width: 'w-36',
			editable: false
		},
		{
			key: 'jobTitle',
			label: 'Job Title',
			type: 'text',
			width: 'w-36',
			canHide: true,
			emptyText: ''
		},
		{
			key: 'leadSource',
			label: 'Source',
			type: 'select',
			width: 'w-28',
			canHide: true
		},
		{
			key: 'industry',
			label: 'Industry',
			type: 'select',
			width: 'w-32',
			canHide: true,
			options: INDUSTRIES.map((i) => ({ ...i, color: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300' }))
		},
		{
			key: 'owner',
			label: 'Assigned',
			type: 'relation',
			width: 'w-36',
			canHide: true,
			relationIcon: 'user',
			getValue: (row) => row.owner?.name || '',
			emptyText: ''
		}
	];

	// Visible columns state - default to hiding new columns
	let visibleColumns = $state(columns.filter((c) => !['jobTitle', 'leadSource', 'industry', 'owner'].includes(c.key)).map((c) => c.key));

	// Source options for leads
	const sourceOptions = [
		{ value: 'call', label: 'Call', color: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400' },
		{ value: 'email', label: 'Email', color: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400' },
		{ value: 'existing customer', label: 'Existing Customer', color: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' },
		{ value: 'partner', label: 'Partner', color: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400' },
		{ value: 'public relations', label: 'Public Relations', color: 'bg-pink-100 text-pink-700 dark:bg-pink-900/30 dark:text-pink-400' },
		{ value: 'campaign', label: 'Campaign', color: 'bg-cyan-100 text-cyan-700 dark:bg-cyan-900/30 dark:text-cyan-400' },
		{ value: 'other', label: 'Other', color: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300' }
	];

	// Salutation options
	const salutationOptions = [
		{ value: 'Mr', label: 'Mr', color: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300' },
		{ value: 'Mrs', label: 'Mrs', color: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300' },
		{ value: 'Ms', label: 'Ms', color: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300' },
		{ value: 'Dr', label: 'Dr', color: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300' },
		{ value: 'Prof', label: 'Prof', color: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300' }
	];

	// Full drawer columns for NotionDrawer (all lead fields)
	const drawerColumns = [
		// Contact Information
		{
			key: 'salutation',
			label: 'Salutation',
			type: 'select',
			icon: User,
			options: salutationOptions
		},
		{
			key: 'firstName',
			label: 'First Name',
			type: 'text',
			icon: User,
			placeholder: 'First name'
		},
		{
			key: 'lastName',
			label: 'Last Name',
			type: 'text',
			icon: User,
			placeholder: 'Last name'
		},
		{
			key: 'email',
			label: 'Email',
			type: 'email',
			icon: Mail,
			placeholder: 'Add email'
		},
		{
			key: 'phone',
			label: 'Phone',
			type: 'text',
			icon: Phone,
			placeholder: 'Add phone'
		},
		{
			key: 'jobTitle',
			label: 'Job Title',
			type: 'text',
			icon: Briefcase,
			placeholder: 'Add job title'
		},
		{
			key: 'company',
			label: 'Company',
			type: 'text',
			icon: Building2,
			getValue: (/** @type {any} */ row) =>
				typeof row.company === 'object' ? row.company?.name : row.company,
			placeholder: 'Add company'
		},
		{
			key: 'website',
			label: 'Website',
			type: 'text',
			icon: Globe,
			placeholder: 'Add website'
		},
		{
			key: 'linkedinUrl',
			label: 'LinkedIn',
			type: 'text',
			icon: Linkedin,
			placeholder: 'Add LinkedIn URL'
		},
		// Lead Details
		{
			key: 'status',
			label: 'Status',
			type: 'select',
			icon: Briefcase,
			options: leadStatusOptions
		},
		{
			key: 'rating',
			label: 'Rating',
			type: 'select',
			icon: Star,
			options: leadRatingOptions
		},
		// Metadata
		{
			key: 'createdAt',
			label: 'Created',
			type: 'date',
			icon: Calendar,
			editable: false
		},
		{
			key: 'leadSource',
			label: 'Source',
			type: 'select',
			icon: Target,
			options: sourceOptions
		},
		{
			key: 'industry',
			label: 'Industry',
			type: 'select',
			icon: Building2,
			options: INDUSTRIES.map((i) => ({ ...i, color: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300' }))
		},
		// Deal Information
		{
			key: 'opportunityAmount',
			label: 'Deal Value',
			type: 'number',
			icon: DollarSign,
			prefix: '$',
			placeholder: '0'
		},
		{
			key: 'probability',
			label: 'Probability',
			type: 'number',
			icon: Percent,
			placeholder: '0-100'
		},
		{
			key: 'closeDate',
			label: 'Close Date',
			type: 'date',
			icon: Calendar,
			placeholder: 'Set date'
		},
		// Activity
		{
			key: 'lastContacted',
			label: 'Last Contact',
			type: 'date',
			icon: Calendar,
			placeholder: 'Set date'
		},
		{
			key: 'nextFollowUp',
			label: 'Follow-up',
			type: 'date',
			icon: Calendar,
			placeholder: 'Set date'
		},
		// Address
		{
			key: 'addressLine',
			label: 'Address',
			type: 'text',
			icon: MapPin,
			placeholder: 'Street address'
		},
		{
			key: 'city',
			label: 'City',
			type: 'text',
			icon: MapPin,
			placeholder: 'City'
		},
		{
			key: 'state',
			label: 'State',
			type: 'text',
			icon: MapPin,
			placeholder: 'State/Province'
		},
		{
			key: 'postcode',
			label: 'Postal Code',
			type: 'text',
			icon: MapPin,
			placeholder: 'Postal code'
		},
		{
			key: 'country',
			label: 'Country',
			type: 'select',
			icon: Globe,
			options: COUNTRIES.map((c) => ({ ...c, color: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300' }))
		},
		// Notes
		{
			key: 'description',
			label: 'Notes',
			type: 'textarea',
			icon: FileText,
			placeholder: 'Add notes...'
		},
		// Assignment (multi-select fields - options populated dynamically)
		{
			key: 'assignedTo',
			label: 'Assigned To',
			type: 'multiselect',
			icon: Users,
			options: []
		},
		{
			key: 'teams',
			label: 'Teams',
			type: 'multiselect',
			icon: Users,
			options: []
		},
		{
			key: 'contacts',
			label: 'Contacts',
			type: 'multiselect',
			icon: UserPlus,
			options: []
		},
		{
			key: 'tags',
			label: 'Tags',
			type: 'multiselect',
			icon: Tag,
			options: []
		}
	];


	/**
	 * Load column visibility from localStorage
	 */
	function loadColumnVisibility() {
		if (typeof window === 'undefined') return;
		try {
			const saved = localStorage.getItem(STORAGE_KEY);
			if (saved) {
				const parsed = JSON.parse(saved);
				// Filter to only include valid column keys
				visibleColumns = parsed.filter((key) => columns.some((c) => c.key === key));
			}
		} catch (e) {
			console.error('Failed to load column visibility:', e);
		}
	}

	onMount(() => {
		loadColumnVisibility();
	});

	// Save to localStorage when column visibility changes
	$effect(() => {
		if (typeof window !== 'undefined') {
			localStorage.setItem(STORAGE_KEY, JSON.stringify(visibleColumns));
		}
	});

	/**
	 * Toggle column visibility
	 * @param {string} key
	 */
	function toggleColumn(key) {
		const col = columns.find((c) => c.key === key);
		if (col?.canHide === false) return;

		if (visibleColumns.includes(key)) {
			visibleColumns = visibleColumns.filter((k) => k !== key);
		} else {
			visibleColumns = [...visibleColumns, key];
		}
	}

	/** @type {{ data: any }} */
	let { data } = $props();

	// Computed values
	const leads = $derived(data.leads || []);
	const formOptions = $derived(data.formOptions || {});

	// Drawer state (NotionDrawer for view/create)
	let drawerOpen = $state(false);
	/** @type {'view' | 'create'} */
	let drawerMode = $state(/** @type {'view' | 'create'} */ ('view'));
	/** @type {any} */
	let drawerData = $state(null);
	let drawerLoading = $state(false);
	let isSaving = $state(false);

	// For create mode - temporary form data
	let createFormData = $state(/** @type {Record<string, any>} */ ({
		title: '',
		salutation: '',
		firstName: '',
		lastName: '',
		email: '',
		phone: '',
		jobTitle: '',
		company: '',
		website: '',
		linkedinUrl: '',
		status: 'ASSIGNED',
		rating: '',
		leadSource: '',
		industry: '',
		opportunityAmount: '',
		probability: '',
		closeDate: '',
		lastContacted: '',
		nextFollowUp: '',
		addressLine: '',
		city: '',
		state: '',
		postcode: '',
		country: '',
		description: '',
		assignedTo: [],
		teams: [],
		contacts: [],
		tags: []
	}));

	// Current drawer data (either selected lead or create form data)
	const currentDrawerData = $derived(drawerMode === 'create' ? createFormData : drawerData);

	// Drawer columns with dynamic options for multi-selects
	const drawerColumnsWithOptions = $derived(
		drawerColumns.map((col) => {
			if (col.key === 'assignedTo') return { ...col, options: formOptions.users || [] };
			if (col.key === 'teams') return { ...col, options: formOptions.teamsList || [] };
			if (col.key === 'contacts') return { ...col, options: formOptions.contactsList || [] };
			if (col.key === 'tags') return { ...col, options: formOptions.tagsList || [] };
			return col;
		})
	);

	// URL sync
	$effect(() => {
		const viewId = $page.url.searchParams.get('view');
		const action = $page.url.searchParams.get('action');

		if (action === 'create') {
			drawerData = null;
			drawerMode = 'create';
			drawerOpen = true;
		} else if (viewId && leads.length > 0) {
			const lead = leads.find((l) => l.id === viewId);
			if (lead) {
				drawerData = lead;
				drawerMode = 'view';
				drawerOpen = true;
			}
		}
	});

	/**
	 * Update URL
	 * @param {string | null} viewId
	 * @param {string | null} action
	 */
	function updateUrl(viewId, action) {
		const url = new URL($page.url);
		if (viewId) {
			url.searchParams.set('view', viewId);
			url.searchParams.delete('action');
		} else if (action) {
			url.searchParams.set('action', action);
			url.searchParams.delete('view');
		} else {
			url.searchParams.delete('view');
			url.searchParams.delete('action');
		}
		goto(url.toString(), { replaceState: true, noScroll: true });
	}

	/**
	 * Open drawer for viewing/editing a lead
	 * @param {any} lead
	 */
	function openLead(lead) {
		drawerData = lead;
		drawerMode = 'view';
		drawerOpen = true;
		updateUrl(lead.id, null);
	}

	/**
	 * Open drawer for creating a new lead
	 */
	function openCreate() {
		// Reset create form data
		createFormData = {
			title: '',
			salutation: '',
			firstName: '',
			lastName: '',
			email: '',
			phone: '',
			jobTitle: '',
			company: '',
			website: '',
			linkedinUrl: '',
			status: 'ASSIGNED',
			rating: '',
			leadSource: '',
			industry: '',
			opportunityAmount: '',
			probability: '',
			closeDate: '',
			lastContacted: '',
			nextFollowUp: '',
			addressLine: '',
			city: '',
			state: '',
			postcode: '',
			country: '',
			description: '',
			assignedTo: [],
			teams: [],
			contacts: [],
			tags: []
		};
		drawerData = null;
		drawerMode = 'create';
		drawerOpen = true;
		updateUrl(null, 'create');
	}

	/**
	 * Close drawer
	 */
	function closeDrawer() {
		drawerOpen = false;
		drawerData = null;
		updateUrl(null, null);
	}

	/**
	 * Handle drawer open change
	 * @param {boolean} open
	 */
	function handleDrawerChange(open) {
		drawerOpen = open;
		if (!open) {
			drawerData = null;
			updateUrl(null, null);
		}
	}

	/**
	 * Handle row change from NotionTable (inline editing)
	 * @param {any} row
	 * @param {string} field
	 * @param {any} value
	 */
	async function handleRowChange(row, field, value) {
		await handleQuickEdit(row, field, value);
	}

	/**
	 * Handle field change from CrmDrawer - just updates local state
	 * @param {string} field
	 * @param {any} value
	 */
	function handleDrawerFieldChange(field, value) {
		if (drawerMode === 'create') {
			// For create mode, just update the form data
			createFormData = { ...createFormData, [field]: value };
		} else if (drawerData) {
			// For edit mode, just update local data - no auto-save
			drawerData = { ...drawerData, [field]: value };
		}
	}

	/**
	 * Handle save for view/edit mode
	 */
	async function handleDrawerUpdate() {
		if (drawerMode !== 'view' || !drawerData) return;

		isSaving = true;
		// Populate form state with current drawer data
		const currentState = leadToFormState(drawerData);
		Object.assign(formState, currentState);

		await tick();
		updateForm.requestSubmit();
	}

	/**
	 * Handle title change from NotionDrawer
	 * @param {string} value
	 */
	async function handleTitleChange(value) {
		if (drawerMode === 'create') {
			// Parse the name into firstName and lastName
			const parts = value.trim().split(' ');
			createFormData = {
				...createFormData,
				title: value,
				firstName: parts[0] || '',
				lastName: parts.slice(1).join(' ') || ''
			};
		} else if (drawerData) {
			// For existing leads, update title
			await handleQuickEdit(drawerData, 'title', value);
		}
	}

	/**
	 * Handle delete from NotionDrawer
	 */
	async function handleDrawerDelete() {
		if (!drawerData) return;
		const lead = drawerData;
		closeDrawer();
		await handleRowDelete(lead);
	}

	/**
	 * Handle convert from NotionDrawer
	 */
	async function handleDrawerConvert() {
		if (!drawerData) return;
		formState.leadId = drawerData.id;
		await tick();
		convertForm.requestSubmit();
	}

	/**
	 * Handle create new lead
	 */
	async function handleCreateLead() {
		if (!createFormData.title?.trim()) {
			toast.error('Lead title is required');
			return;
		}

		isSaving = true;
		try {
			// Populate form state
			formState.salutation = createFormData.salutation || '';
			formState.title = createFormData.title || '';
			formState.firstName = createFormData.firstName || '';
			formState.lastName = createFormData.lastName || '';
			formState.email = createFormData.email || '';
			formState.phone = createFormData.phone || '';
			formState.jobTitle = createFormData.jobTitle || '';
			formState.company = createFormData.company || '';
			formState.website = createFormData.website || '';
			formState.linkedinUrl = createFormData.linkedinUrl || '';
			formState.status = createFormData.status || 'ASSIGNED';
			formState.source = createFormData.leadSource || '';
			formState.rating = createFormData.rating || '';
			formState.industry = createFormData.industry || '';
			formState.opportunityAmount = createFormData.opportunityAmount || '';
			formState.probability = createFormData.probability || '';
			formState.closeDate = createFormData.closeDate || '';
			formState.lastContacted = createFormData.lastContacted || '';
			formState.nextFollowUp = createFormData.nextFollowUp || '';
			formState.addressLine = createFormData.addressLine || '';
			formState.city = createFormData.city || '';
			formState.state = createFormData.state || '';
			formState.postcode = createFormData.postcode || '';
			formState.country = createFormData.country || '';
			formState.description = createFormData.description || '';
			formState.assignedTo = createFormData.assignedTo || [];
			formState.teams = createFormData.teams || [];
			formState.contacts = createFormData.contacts || [];
			formState.tags = createFormData.tags || [];

			await tick();
			createForm.requestSubmit();
		} finally {
			isSaving = false;
		}
	}

	// Filter/search/sort state
	const list = useListFilters({
		searchFields: ['firstName', 'lastName', 'company', 'email'],
		filters: [
			{
				key: 'statusFilter',
				defaultValue: 'ALL',
				match: (item, value) => value === 'ALL' || item.status === value
			},
			{
				key: 'sourceFilter',
				defaultValue: 'ALL',
				match: (item, value) => value === 'ALL' || item.leadSource === value
			},
			{
				key: 'ratingFilter',
				defaultValue: 'ALL',
				match: (item, value) => value === 'ALL' || item.rating === value
			}
		],
		defaultSortColumn: 'createdAt',
		defaultSortDirection: 'desc'
	});

	// Filtered and sorted leads
	const filteredLeads = $derived(list.filterAndSort(leads));

	// Form references for server actions
	/** @type {HTMLFormElement} */
	let createForm;
	/** @type {HTMLFormElement} */
	let updateForm;
	/** @type {HTMLFormElement} */
	let deleteForm;
	/** @type {HTMLFormElement} */
	let convertForm;
	// Form data state
	let formState = $state({
		leadId: '',
		// Core Information
		salutation: '',
		firstName: '',
		lastName: '',
		email: '',
		phone: '',
		company: '',
		title: '',
		jobTitle: '',
		website: '',
		linkedinUrl: '',
		// Sales Pipeline
		status: '',
		source: '',
		industry: '',
		rating: '',
		opportunityAmount: '',
		probability: '',
		closeDate: '',
		// Address
		addressLine: '',
		city: '',
		state: '',
		postcode: '',
		country: '',
		// Activity
		lastContacted: '',
		nextFollowUp: '',
		description: '',
		// Assignment
		ownerId: '',
		assignedTo: /** @type {string[]} */ ([]),
		teams: /** @type {string[]} */ ([]),
		contacts: /** @type {string[]} */ ([]),
		tags: /** @type {string[]} */ ([])
	});

	/**
	 * Get full name
	 * @param {any} lead
	 */
	function getFullName(lead) {
		return `${lead.firstName} ${lead.lastName}`.trim();
	}

	/**
	 * Get initials for lead
	 * @param {any} lead
	 */
	function getLeadInitials(lead) {
		return getNameInitials(lead.firstName, lead.lastName);
	}

	/**
	 * Handle form submit from drawer
	 * @param {any} formData
	 */
	async function handleFormSubmit(formData) {
		// Populate form state
		// Core Information
		formState.firstName = formData.first_name || '';
		formState.lastName = formData.last_name || '';
		formState.email = formData.email || '';
		formState.phone = formData.phone || '';
		formState.company = formData.company_name || '';
		formState.title = formData.title || '';
		formState.jobTitle = formData.job_title || '';
		formState.website = formData.website || '';
		formState.linkedinUrl = formData.linkedin_url || '';
		// Sales Pipeline
		formState.status = formData.status || '';
		formState.source = formData.source || '';
		formState.industry = formData.industry || '';
		formState.rating = formData.rating || '';
		formState.opportunityAmount = formData.opportunity_amount || '';
		formState.probability = formData.probability || '';
		formState.closeDate = formData.close_date || '';
		// Address
		formState.addressLine = formData.address_line || '';
		formState.city = formData.city || '';
		formState.state = formData.state || '';
		formState.postcode = formData.postcode || '';
		formState.country = formData.country || '';
		// Activity
		formState.lastContacted = formData.last_contacted || '';
		formState.nextFollowUp = formData.next_follow_up || '';
		formState.description = formData.description || '';

		await tick();

		if (drawerMode === 'view' && drawerData) {
			// Edit mode
			formState.leadId = drawerData.id;
			// Use existing owner when editing (form doesn't have owner selection)
			formState.ownerId = drawerData.owner?.id || '';
			await tick();
			updateForm.requestSubmit();
		} else {
			// Create mode
			formState.ownerId = '';
			createForm.requestSubmit();
		}
	}

	/**
	 * Handle lead delete
	 */
	async function handleDelete() {
		if (!drawerData) return;
		if (!confirm(`Are you sure you want to delete ${getFullName(drawerData)}?`)) return;

		formState.leadId = drawerData.id;
		await tick();
		deleteForm.requestSubmit();
	}

	/**
	 * Handle lead convert
	 */
	async function handleConvert() {
		if (!drawerData) return;

		formState.leadId = drawerData.id;
		await tick();
		convertForm.requestSubmit();
	}

	/**
	 * Handle lead delete from row action
	 * @param {any} lead
	 */
	async function handleRowDelete(lead) {
		if (!confirm(`Are you sure you want to delete ${getFullName(lead)}?`)) return;

		formState.leadId = lead.id;
		await tick();
		deleteForm.requestSubmit();
	}

	/**
	 * Convert lead to form state for quick edit
	 * @param {any} lead
	 */
	function leadToFormState(lead) {
		return {
			leadId: lead.id,
			salutation: lead.salutation || '',
			firstName: lead.firstName || '',
			lastName: lead.lastName || '',
			email: lead.email || '',
			phone: lead.phone || '',
			company: typeof lead.company === 'object' ? lead.company?.name || '' : lead.company || '',
			title: lead.title || '',
			jobTitle: lead.jobTitle || '',
			website: lead.website || '',
			linkedinUrl: lead.linkedinUrl || '',
			status: lead.status || '',
			source: lead.leadSource || '',
			industry: lead.industry || '',
			rating: lead.rating || '',
			opportunityAmount: lead.opportunityAmount || '',
			probability: lead.probability || '',
			closeDate: lead.closeDate || '',
			addressLine: lead.addressLine || '',
			city: lead.city || '',
			state: lead.state || '',
			postcode: lead.postcode || '',
			country: lead.country || '',
			lastContacted: lead.lastContacted || '',
			nextFollowUp: lead.nextFollowUp || '',
			description: lead.description || '',
			ownerId: lead.owner?.id || '',
			assignedTo: lead.assignedTo || [],
			teams: lead.teams || [],
			contacts: lead.contacts || [],
			tags: lead.tags || []
		};
	}

	/**
	 * Handle quick edit from cell
	 * @param {any} lead
	 * @param {string} field
	 * @param {string} value
	 */
	async function handleQuickEdit(lead, field, value) {
		// Populate form state with current lead data
		const currentState = leadToFormState(lead);

		// Update the specific field
		currentState[field] = value;

		// Copy to form state
		Object.assign(formState, currentState);

		await tick();
		updateForm.requestSubmit();
	}

	/**
	 * Create enhance handler for form actions
	 * @param {string} successMessage
	 * @param {boolean} shouldCloseDrawer
	 */
	function createEnhanceHandler(successMessage, shouldCloseDrawer = true) {
		return () => {
			return async ({ result }) => {
				isSaving = false;
				if (result.type === 'success') {
					toast.success(successMessage);
					if (shouldCloseDrawer) {
						closeDrawer();
					}
					await invalidateAll();
				} else if (result.type === 'failure') {
					toast.error(result.data?.error || 'Operation failed');
				} else if (result.type === 'error') {
					toast.error('An unexpected error occurred');
				}
			};
		};
	}
</script>

<svelte:head>
	<title>Leads - BottleCRM</title>
</svelte:head>

<div class="min-h-screen bg-white dark:bg-gray-950">
	<!-- Notion-style Header -->
	<div class="border-b border-gray-200 dark:border-gray-800 px-6 py-4">
		<div class="flex items-center justify-between">
			<div>
				<h1 class="text-2xl font-semibold text-gray-900 dark:text-gray-100">Leads</h1>
				<p class="mt-1 text-sm text-gray-500 dark:text-gray-400">{filteredLeads.length} leads</p>
			</div>
			<div class="flex items-center gap-2">
				<!-- Column Visibility (Notion-style) -->
				<DropdownMenu.Root>
					<DropdownMenu.Trigger asChild>
						{#snippet child({ props })}
							<Button {...props} variant="outline" size="sm" class="gap-2">
								<Eye class="h-4 w-4" />
								Columns
								{#if visibleColumns.length < columns.length}
									<span
										class="rounded-full bg-blue-100 px-1.5 py-0.5 text-xs font-medium text-blue-700 dark:bg-blue-900/30 dark:text-blue-400"
									>
										{visibleColumns.length}/{columns.length}
									</span>
								{/if}
							</Button>
						{/snippet}
					</DropdownMenu.Trigger>
					<DropdownMenu.Content align="end" class="w-48">
						<DropdownMenu.Label>Toggle columns</DropdownMenu.Label>
						<DropdownMenu.Separator />
						{#each columns as column (column.key)}
							<DropdownMenu.CheckboxItem
								class=""
								checked={visibleColumns.includes(column.key)}
								disabled={column.canHide === false}
								onCheckedChange={() => toggleColumn(column.key)}
							>
								{column.label}
							</DropdownMenu.CheckboxItem>
						{/each}
					</DropdownMenu.Content>
				</DropdownMenu.Root>

				<Button size="sm" class="gap-2" onclick={openCreate}>
					<Plus class="h-4 w-4" />
					New
				</Button>
			</div>
		</div>
	</div>

	<!-- Table -->
	{#if filteredLeads.length === 0}
		<div class="flex flex-col items-center justify-center py-16 text-center">
			<User class="mb-4 h-12 w-12 text-gray-300 dark:text-gray-600" />
			<h3 class="text-lg font-medium text-gray-900 dark:text-gray-100">No leads found</h3>
			<p class="mt-1 text-sm text-gray-500 dark:text-gray-400">Create your first lead to get started.</p>
			<Button onclick={openCreate} class="mt-4" size="sm">
				<Plus class="mr-2 h-4 w-4" />
				New Lead
			</Button>
		</div>
	{:else}
		<!-- Desktop Table using CrmTable -->
		<div class="hidden md:block">
			<CrmTable
				data={filteredLeads}
				{columns}
				bind:visibleColumns
				onRowChange={handleRowChange}
				onRowClick={(row) => openLead(row)}
			>
				{#snippet emptyState()}
					<div class="flex flex-col items-center justify-center py-16 text-center">
						<User class="mb-4 h-12 w-12 text-gray-300 dark:text-gray-600" />
						<h3 class="text-lg font-medium text-gray-900 dark:text-gray-100">No leads found</h3>
						<p class="mt-1 text-sm text-gray-500 dark:text-gray-400">Create your first lead to get started.</p>
						<Button onclick={openCreate} class="mt-4" size="sm">
							<Plus class="mr-2 h-4 w-4" />
							New Lead
						</Button>
					</div>
				{/snippet}
			</CrmTable>

			<!-- New row button -->
			<div class="border-t border-gray-100/60 dark:border-gray-800 px-4 py-2">
				<button
					type="button"
					onclick={openCreate}
					class="flex items-center gap-2 rounded px-2 py-1.5 text-sm text-gray-500 transition-colors hover:bg-gray-50 hover:text-gray-700 dark:hover:bg-gray-800 dark:hover:text-gray-300"
				>
					<Plus class="h-4 w-4" />
					New
				</button>
			</div>
		</div>

		<!-- Mobile Card View -->
		<div class="divide-y dark:divide-gray-800 md:hidden">
			{#each filteredLeads as lead (lead.id)}
				<button
					type="button"
					class="flex w-full items-start gap-3 px-4 py-3 text-left transition-colors hover:bg-gray-50/30 dark:hover:bg-gray-800/30"
					onclick={() => openLead(lead)}
				>
					<div class="min-w-0 flex-1">
						<div class="flex items-start justify-between gap-2">
							<div>
								<p class="text-sm font-medium text-gray-900 dark:text-gray-100">{getFullName(lead)}</p>
								{#if lead.company}
									<p class="text-sm text-gray-500 dark:text-gray-400">
										{typeof lead.company === 'object' ? lead.company.name : lead.company}
									</p>
								{/if}
							</div>
							<span
								class="shrink-0 rounded-full px-2 py-0.5 text-xs font-medium {getOptionStyle(
									lead.status,
									leadStatusOptions
								)}"
							>
								{getOptionLabel(lead.status, leadStatusOptions)}
							</span>
						</div>
						<div class="mt-2 flex flex-wrap items-center gap-3 text-xs text-gray-500 dark:text-gray-400">
							{#if lead.rating}
								<span
									class="rounded-full px-2 py-0.5 {getOptionStyle(lead.rating, leadRatingOptions)}"
								>
									{getOptionLabel(lead.rating, leadRatingOptions)}
								</span>
							{/if}
							<span>{formatRelativeDate(lead.createdAt)}</span>
						</div>
					</div>
				</button>
			{/each}

			<!-- Mobile new row button -->
			<button
				type="button"
				onclick={openCreate}
				class="flex w-full items-center gap-2 px-4 py-3 text-sm text-gray-500 transition-colors hover:bg-gray-50 hover:text-gray-700 dark:hover:bg-gray-800 dark:hover:text-gray-300"
			>
				<Plus class="h-4 w-4" />
				New
			</button>
		</div>
	{/if}
</div>

<!-- Lead Drawer -->
<CrmDrawer
	bind:open={drawerOpen}
	onOpenChange={handleDrawerChange}
	data={currentDrawerData}
	columns={drawerColumnsWithOptions}
	titleKey="title"
	titlePlaceholder={drawerMode === 'create' ? 'Lead Title' : 'Untitled Lead'}
	headerLabel={drawerMode === 'create' ? 'New Lead' : 'Lead'}
	mode={drawerMode}
	loading={drawerLoading}
	onFieldChange={handleDrawerFieldChange}
	onDelete={drawerMode !== 'create' ? handleDrawerDelete : undefined}
	onClose={closeDrawer}
>
	{#snippet activitySection()}
		{#if drawerMode !== 'create' && drawerData?.comments?.length > 0}
			<div class="space-y-3">
				<div class="flex items-center gap-2 text-sm font-medium text-gray-500 dark:text-gray-400">
					<MessageSquare class="h-4 w-4" />
					Activity
				</div>
				{#each drawerData.comments.slice(0, 3) as comment (comment.id)}
					<div class="flex gap-3">
						<div class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gray-100 dark:bg-gray-800">
							<MessageSquare class="h-4 w-4 text-gray-400 dark:text-gray-500" />
						</div>
						<div class="min-w-0 flex-1">
							<p class="text-sm text-gray-900 dark:text-gray-100">
								<span class="font-medium">{comment.author?.name || 'Unknown'}</span>
								{' '}added a note
							</p>
							<p class="mt-0.5 text-xs text-gray-500 dark:text-gray-400">
								{formatRelativeDate(comment.createdAt)}
							</p>
							<p class="mt-1 line-clamp-2 text-sm text-gray-600 dark:text-gray-400">
								{comment.body}
							</p>
						</div>
					</div>
				{/each}
			</div>
		{/if}
	{/snippet}

	{#snippet footerActions()}
		{#if drawerMode === 'create'}
			<Button variant="outline" onclick={closeDrawer}>
				Cancel
			</Button>
			<Button onclick={handleCreateLead} disabled={isSaving}>
				{#if isSaving}
					<Loader2 class="mr-2 h-4 w-4 animate-spin" />
					Creating...
				{:else}
					Create Lead
				{/if}
			</Button>
		{:else}
			<Button variant="outline" onclick={closeDrawer} disabled={isSaving}>
				Cancel
			</Button>
			{#if drawerData?.status !== 'converted'}
				<Button variant="outline" onclick={handleDrawerConvert} disabled={isSaving}>
					<ArrowRightCircle class="mr-2 h-4 w-4" />
					Convert
				</Button>
			{/if}
			<Button onclick={handleDrawerUpdate} disabled={isSaving}>
				{#if isSaving}
					<Loader2 class="mr-2 h-4 w-4 animate-spin" />
					Saving...
				{:else}
					Save
				{/if}
			</Button>
		{/if}
	{/snippet}
</CrmDrawer>

<!-- Hidden forms for server actions -->
<form
	method="POST"
	action="?/create"
	bind:this={createForm}
	use:enhance={createEnhanceHandler('Lead created successfully')}
	class="hidden"
>
	<!-- Core Information -->
	<input type="hidden" name="salutation" value={formState.salutation} />
	<input type="hidden" name="firstName" value={formState.firstName} />
	<input type="hidden" name="lastName" value={formState.lastName} />
	<input type="hidden" name="email" value={formState.email} />
	<input type="hidden" name="phone" value={formState.phone} />
	<input type="hidden" name="company" value={formState.company} />
	<input type="hidden" name="title" value={formState.title} />
	<input type="hidden" name="jobTitle" value={formState.jobTitle} />
	<input type="hidden" name="website" value={formState.website} />
	<input type="hidden" name="linkedinUrl" value={formState.linkedinUrl} />
	<!-- Sales Pipeline -->
	<input type="hidden" name="status" value={formState.status} />
	<input type="hidden" name="source" value={formState.source} />
	<input type="hidden" name="industry" value={formState.industry} />
	<input type="hidden" name="rating" value={formState.rating} />
	<input type="hidden" name="opportunityAmount" value={formState.opportunityAmount} />
	<input type="hidden" name="probability" value={formState.probability} />
	<input type="hidden" name="closeDate" value={formState.closeDate} />
	<!-- Address -->
	<input type="hidden" name="addressLine" value={formState.addressLine} />
	<input type="hidden" name="city" value={formState.city} />
	<input type="hidden" name="state" value={formState.state} />
	<input type="hidden" name="postcode" value={formState.postcode} />
	<input type="hidden" name="country" value={formState.country} />
	<!-- Activity -->
	<input type="hidden" name="lastContacted" value={formState.lastContacted} />
	<input type="hidden" name="nextFollowUp" value={formState.nextFollowUp} />
	<input type="hidden" name="description" value={formState.description} />
	<!-- Assignment -->
	<input type="hidden" name="ownerId" value={formState.ownerId} />
	<input type="hidden" name="assignedTo" value={JSON.stringify(formState.assignedTo)} />
	<input type="hidden" name="teams" value={JSON.stringify(formState.teams)} />
	<input type="hidden" name="contacts" value={JSON.stringify(formState.contacts)} />
	<input type="hidden" name="tags" value={JSON.stringify(formState.tags)} />
</form>

<form
	method="POST"
	action="?/update"
	bind:this={updateForm}
	use:enhance={createEnhanceHandler('Lead updated successfully')}
	class="hidden"
>
	<input type="hidden" name="leadId" value={formState.leadId} />
	<!-- Core Information -->
	<input type="hidden" name="salutation" value={formState.salutation} />
	<input type="hidden" name="firstName" value={formState.firstName} />
	<input type="hidden" name="lastName" value={formState.lastName} />
	<input type="hidden" name="email" value={formState.email} />
	<input type="hidden" name="phone" value={formState.phone} />
	<input type="hidden" name="company" value={formState.company} />
	<input type="hidden" name="title" value={formState.title} />
	<input type="hidden" name="jobTitle" value={formState.jobTitle} />
	<input type="hidden" name="website" value={formState.website} />
	<input type="hidden" name="linkedinUrl" value={formState.linkedinUrl} />
	<!-- Sales Pipeline -->
	<input type="hidden" name="status" value={formState.status} />
	<input type="hidden" name="source" value={formState.source} />
	<input type="hidden" name="industry" value={formState.industry} />
	<input type="hidden" name="rating" value={formState.rating} />
	<input type="hidden" name="opportunityAmount" value={formState.opportunityAmount} />
	<input type="hidden" name="probability" value={formState.probability} />
	<input type="hidden" name="closeDate" value={formState.closeDate} />
	<!-- Address -->
	<input type="hidden" name="addressLine" value={formState.addressLine} />
	<input type="hidden" name="city" value={formState.city} />
	<input type="hidden" name="state" value={formState.state} />
	<input type="hidden" name="postcode" value={formState.postcode} />
	<input type="hidden" name="country" value={formState.country} />
	<!-- Activity -->
	<input type="hidden" name="lastContacted" value={formState.lastContacted} />
	<input type="hidden" name="nextFollowUp" value={formState.nextFollowUp} />
	<input type="hidden" name="description" value={formState.description} />
	<!-- Assignment -->
	<input type="hidden" name="ownerId" value={formState.ownerId} />
	<input type="hidden" name="assignedTo" value={JSON.stringify(formState.assignedTo)} />
	<input type="hidden" name="teams" value={JSON.stringify(formState.teams)} />
	<input type="hidden" name="contacts" value={JSON.stringify(formState.contacts)} />
	<input type="hidden" name="tags" value={JSON.stringify(formState.tags)} />
</form>

<form
	method="POST"
	action="?/delete"
	bind:this={deleteForm}
	use:enhance={createEnhanceHandler('Lead deleted successfully')}
	class="hidden"
>
	<input type="hidden" name="leadId" value={formState.leadId} />
</form>

<form
	method="POST"
	action="?/convert"
	bind:this={convertForm}
	use:enhance={createEnhanceHandler('Lead converted successfully')}
	class="hidden"
>
	<input type="hidden" name="leadId" value={formState.leadId} />
</form>

