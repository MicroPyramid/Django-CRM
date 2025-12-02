<script>
	import { Mail, Building2, Circle, Zap, DollarSign, Calendar, Star } from '@lucide/svelte';
	import { NotionTable } from '$lib/components/ui/notion-table';
	import { NotionDrawer } from '$lib/components/ui/notion-drawer';

	// Status and priority options with colors
	const statusOptions = [
		{ value: 'active', label: 'Active', color: 'bg-emerald-100 text-emerald-700' },
		{ value: 'inactive', label: 'Inactive', color: 'bg-gray-100 text-gray-600' },
		{ value: 'pending', label: 'Pending', color: 'bg-amber-100 text-amber-700' }
	];

	const priorityOptions = [
		{ value: 'high', label: 'High', color: 'bg-red-100 text-red-700' },
		{ value: 'medium', label: 'Medium', color: 'bg-yellow-100 text-yellow-700' },
		{ value: 'low', label: 'Low', color: 'bg-blue-100 text-blue-700' }
	];

	/**
	 * @typedef {'text' | 'email' | 'number' | 'date' | 'select' | 'checkbox' | 'relation'} ColumnType
	 */

	// Column definitions for table
	/** @type {{ key: string, label: string, type: ColumnType, width: string, options?: { value: string, label: string, color: string }[] }[]} */
	const columns = [
		{ key: 'name', label: 'Name', type: 'text', width: 'w-48' },
		{ key: 'email', label: 'Email', type: 'email', width: 'w-52' },
		{ key: 'company', label: 'Company', type: 'text', width: 'w-40' },
		{ key: 'status', label: 'Status', type: 'select', options: statusOptions, width: 'w-28' },
		{
			key: 'priority',
			label: 'Priority',
			type: 'select',
			options: priorityOptions,
			width: 'w-28'
		},
		{ key: 'dealValue', label: 'Deal Value', type: 'number', width: 'w-32' },
		{ key: 'lastContact', label: 'Last Contact', type: 'date', width: 'w-36' },
		{ key: 'isVIP', label: 'VIP', type: 'checkbox', width: 'w-16' }
	];

	// Column definitions for drawer (with icons)
	/** @type {any[]} */
	const drawerColumns = [
		{ key: 'name', label: 'Name', type: 'text' },
		{ key: 'email', label: 'Email', type: 'email', icon: Mail, placeholder: 'Add email' },
		{ key: 'company', label: 'Company', type: 'text', icon: Building2, placeholder: 'Add company' },
		{ key: 'status', label: 'Status', type: 'select', icon: Circle, options: statusOptions },
		{ key: 'priority', label: 'Priority', type: 'select', icon: Zap, options: priorityOptions },
		{
			key: 'dealValue',
			label: 'Deal Value',
			type: 'number',
			icon: DollarSign,
			prefix: '$',
			placeholder: '0'
		},
		{ key: 'lastContact', label: 'Last Contact', type: 'date', icon: Calendar },
		{ key: 'isVIP', label: 'VIP', type: 'checkbox', icon: Star }
	];

	// Mock data
	let data = $state([
		{
			id: '1',
			name: 'John Smith',
			email: 'john@acme.com',
			company: 'Acme Corp',
			status: 'active',
			priority: 'high',
			dealValue: 50000,
			lastContact: '2024-01-15',
			isVIP: true
		},
		{
			id: '2',
			name: 'Sarah Johnson',
			email: 'sarah@techflow.io',
			company: 'TechFlow',
			status: 'active',
			priority: 'medium',
			dealValue: 35000,
			lastContact: '2024-01-18',
			isVIP: false
		},
		{
			id: '3',
			name: 'Michael Chen',
			email: 'mchen@innovate.co',
			company: 'Innovate Co',
			status: 'pending',
			priority: 'high',
			dealValue: 75000,
			lastContact: '2024-01-10',
			isVIP: true
		},
		{
			id: '4',
			name: 'Emily Davis',
			email: 'emily@startup.xyz',
			company: 'StartupXYZ',
			status: 'inactive',
			priority: 'low',
			dealValue: 15000,
			lastContact: '2023-12-20',
			isVIP: false
		},
		{
			id: '5',
			name: 'Robert Wilson',
			email: 'rwilson@enterprise.com',
			company: 'Enterprise Inc',
			status: 'active',
			priority: 'high',
			dealValue: 120000,
			lastContact: '2024-01-22',
			isVIP: true
		},
		{
			id: '6',
			name: 'Lisa Anderson',
			email: 'lisa@cloudtech.io',
			company: 'CloudTech',
			status: 'pending',
			priority: 'medium',
			dealValue: 45000,
			lastContact: '2024-01-08',
			isVIP: false
		},
		{
			id: '7',
			name: 'David Martinez',
			email: 'david@global.net',
			company: 'Global Networks',
			status: 'active',
			priority: 'low',
			dealValue: 28000,
			lastContact: '2024-01-19',
			isVIP: false
		},
		{
			id: '8',
			name: 'Jennifer Brown',
			email: 'jbrown@fintech.co',
			company: 'FinTech Solutions',
			status: 'active',
			priority: 'high',
			dealValue: 95000,
			lastContact: '2024-01-21',
			isVIP: true
		},
		{
			id: '9',
			name: 'Chris Taylor',
			email: 'chris@datawise.com',
			company: 'DataWise',
			status: 'inactive',
			priority: 'medium',
			dealValue: 22000,
			lastContact: '2023-11-30',
			isVIP: false
		},
		{
			id: '10',
			name: 'Amanda White',
			email: 'awhite@growthco.io',
			company: 'GrowthCo',
			status: 'pending',
			priority: 'high',
			dealValue: 68000,
			lastContact: '2024-01-16',
			isVIP: true
		}
	]);

	// Drawer state
	let drawerOpen = $state(false);
	/** @type {string | null} */
	let selectedRowId = $state(null);

	// Get selected row data
	const selectedRow = $derived(data.find((r) => r.id === selectedRowId) || null);

	/**
	 * Handle row change from table
	 * @param {any} row
	 * @param {string} field
	 * @param {any} value
	 */
	function handleRowChange(row, field, value) {
		data = data.map((r) => {
			if (r.id === row.id) {
				return { ...r, [field]: value };
			}
			return r;
		});
	}

	/**
	 * Handle row click (open drawer)
	 * @param {any} row
	 */
	function handleRowClick(row) {
		selectedRowId = row.id;
		drawerOpen = true;
	}

	function handleAddRow() {
		const newId = (Math.max(...data.map((d) => parseInt(d.id))) + 1).toString();
		data = [
			...data,
			{
				id: newId,
				name: '',
				email: '',
				company: '',
				status: 'pending',
				priority: 'medium',
				dealValue: 0,
				lastContact: new Date().toISOString().split('T')[0],
				isVIP: false
			}
		];
	}

	/**
	 * Handle reorder
	 * @param {any[]} newData
	 */
	function handleReorder(newData) {
		data = newData;
	}

	function closeDrawer() {
		drawerOpen = false;
		selectedRowId = null;
	}

	/**
	 * Handle field change from drawer
	 * @param {string} key
	 * @param {any} value
	 */
	function handleDrawerFieldChange(key, value) {
		if (!selectedRowId) return;
		data = data.map((row) => {
			if (row.id === selectedRowId) {
				return { ...row, [key]: value };
			}
			return row;
		});
	}

	function deleteSelectedRow() {
		if (!selectedRowId) return;
		data = data.filter((row) => row.id !== selectedRowId);
		closeDrawer();
	}
</script>

<NotionTable
	{data}
	{columns}
	storageKey="notion-table-columns"
	title="Contacts Database"
	onRowChange={handleRowChange}
	onRowClick={handleRowClick}
	onAddRow={handleAddRow}
	onReorder={handleReorder}
/>

<!-- Row Detail Drawer -->
<NotionDrawer
	bind:open={drawerOpen}
	onOpenChange={(open) => !open && closeDrawer()}
	data={selectedRow}
	columns={drawerColumns}
	titleKey="name"
	titlePlaceholder="Untitled"
	headerLabel="Contact"
	onFieldChange={handleDrawerFieldChange}
	onDelete={deleteSelectedRow}
	onClose={closeDrawer}
/>
