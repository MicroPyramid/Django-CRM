<script>
	import {
		Building2,
		Globe,
		Users,
		User,
		Shield,
		Edit,
		Plus,
		Check,
		X,
		Trash2,
		AlertCircle
	} from '@lucide/svelte';
	import PageHeader from '$lib/components/layout/PageHeader.svelte';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { Separator } from '$lib/components/ui/separator/index.js';
	import * as Card from '$lib/components/ui/card/index.js';
	import * as Table from '$lib/components/ui/table/index.js';
	import * as Avatar from '$lib/components/ui/avatar/index.js';
	import * as AlertDialog from '$lib/components/ui/alert-dialog/index.js';
	import { getInitials, formatDate } from '$lib/utils/formatting.js';

	/** @type {{ data: import('./$types').PageData }} */
	let { data } = $props();

	let org = $derived(data.organization);
	let editing = $state(false);
	// Form state - populated by startEdit() when editing begins
	let formOrg = $state({
		name: '',
		domain: '',
		description: ''
	});

	// Get logged-in user id from data
	let loggedInUserId = $derived(data.user?.id);

	// Transform users data
	let users = $derived(
		Array.isArray(data.users)
			? data.users.map((u) => ({
					id: u.user.id,
					name: u.user.name || u.user.email,
					email: u.user.email,
					role: u.role,
					joined: u.profile?.created_at
						? typeof u.profile.created_at === 'string'
							? u.profile.created_at.slice(0, 10)
							: new Date(u.profile.created_at).toISOString().slice(0, 10)
						: '',
					avatar: u.profile?.profile_photo || '',
					isSelf: loggedInUserId === u.user.id,
					isActive: u.isActive
				}))
			: []
	);

	// State for editing roles
	/** @type {string | null} */
	let editingRoleId = $state(null);
	/** @type {string | null} */
	let userToRemove = $state(null);

	function startEdit() {
		formOrg = {
			name: org?.name || '',
			domain: org?.domain || '',
			description: org?.description || ''
		};
		editing = true;
	}

	function cancelEdit() {
		editing = false;
	}
</script>

<svelte:head>
	<title>Organization Settings - BottleCRM</title>
</svelte:head>

<PageHeader title="Organization Settings" subtitle="Manage your organization and team members" />

<div class="flex-1 space-y-6 p-4 md:p-6">
	<!-- Error Message -->
	{#if data.error}
		<Card.Root class="border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-900/20">
			<Card.Content class="flex items-center gap-3 p-4">
				<div
					class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-red-100 dark:bg-red-800"
				>
					<AlertCircle class="h-4 w-4 text-red-600 dark:text-red-300" />
				</div>
				<p class="text-sm font-medium text-red-800 dark:text-red-200">
					{data.error.name}
				</p>
			</Card.Content>
		</Card.Root>
	{:else}
		<div class="mx-auto max-w-4xl space-y-6">
			<!-- Organization Details Card -->
			<Card.Root>
				<Card.Header class="">
					<div class="flex items-start justify-between">
						<div class="flex items-center gap-3">
							<div
								class="flex h-12 w-12 items-center justify-center rounded-lg bg-blue-100 dark:bg-blue-900/30"
							>
								<Building2 class="h-6 w-6 text-blue-600 dark:text-blue-400" />
							</div>
							<div>
								<Card.Title class="text-xl">{org.name}</Card.Title>
								<div class="text-muted-foreground mt-1 flex flex-wrap items-center gap-4 text-sm">
									{#if org.domain}
										<span class="flex items-center gap-1">
											<Globe class="h-4 w-4" />
											{org.domain}
										</span>
									{/if}
									<span class="flex items-center gap-1">
										<Users class="h-4 w-4" />
										{users.length} member{users.length !== 1 ? 's' : ''}
									</span>
								</div>
							</div>
						</div>
						{#if !editing}
							<Button variant="ghost" size="icon" onclick={startEdit}>
								<Edit class="h-4 w-4" />
							</Button>
						{/if}
					</div>
				</Card.Header>

				{#if org.description && !editing}
					<Card.Content>
						<p class="text-muted-foreground">{org.description}</p>
					</Card.Content>
				{/if}

				{#if editing}
					<Card.Content>
						<form method="POST" action="?/update" class="space-y-6">
							<div class="grid grid-cols-1 gap-6 sm:grid-cols-2">
								<div>
									<Label for="org-name" class="">Organization Name *</Label>
									<div class="relative mt-1.5">
										<Building2
											class="text-muted-foreground absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2"
										/>
										<Input
											id="org-name"
											name="name"
											type="text"
											bind:value={formOrg.name}
											required
											class="pl-10"
											placeholder="Enter organization name"
										/>
									</div>
								</div>

								<div>
									<Label for="org-domain" class="">Domain</Label>
									<div class="relative mt-1.5">
										<Globe
											class="text-muted-foreground absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2"
										/>
										<Input
											id="org-domain"
											name="domain"
											type="text"
											bind:value={formOrg.domain}
											placeholder="yourcompany.com"
											class="pl-10"
										/>
									</div>
								</div>
							</div>

							<div>
								<Label for="org-description" class="">Description</Label>
								<textarea
									id="org-description"
									name="description"
									rows="3"
									bind:value={formOrg.description}
									class="border-input bg-background ring-offset-background placeholder:text-muted-foreground focus-visible:ring-ring mt-1.5 flex min-h-[80px] w-full rounded-md border px-3 py-2 text-sm focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-50"
									placeholder="Describe your organization..."
								></textarea>
							</div>

							<Separator />

							<div class="flex justify-end gap-3">
								<Button type="button" variant="outline" onclick={cancelEdit}>
									<X class="mr-2 h-4 w-4" />
									Cancel
								</Button>
								<Button type="submit">
									<Check class="mr-2 h-4 w-4" />
									Save Changes
								</Button>
							</div>
						</form>
					</Card.Content>
				{/if}
			</Card.Root>

			<!-- Team Members Card -->
			<Card.Root>
				<Card.Header class="">
					<div class="flex items-center gap-3">
						<div
							class="flex h-10 w-10 items-center justify-center rounded-lg bg-green-100 dark:bg-green-900/30"
						>
							<Users class="h-5 w-5 text-green-600 dark:text-green-400" />
						</div>
						<div>
							<Card.Title class="">Team Members</Card.Title>
							<Card.Description class="">Manage users in your organization</Card.Description>
						</div>
					</div>
				</Card.Header>
				<Card.Content class="space-y-6">
					<!-- Add User Form -->
					<div class="bg-muted/30 rounded-lg border p-4">
						<div class="mb-3 flex items-center gap-2 text-sm font-medium">
							<Plus class="h-4 w-4" />
							Add New Member
						</div>
						<form
							method="POST"
							action="?/add_user"
							class="flex flex-col gap-4 sm:flex-row sm:items-end"
						>
							<div class="flex-1">
								<Label for="add-user-email" class="">Email Address *</Label>
								<Input
									id="add-user-email"
									name="email"
									type="email"
									required
									placeholder="user@example.com"
									class="mt-1.5"
								/>
							</div>
							<div class="sm:w-40">
								<Label for="add-user-role" class="">Role</Label>
								<select
									id="add-user-role"
									name="role"
									class="border-input bg-background ring-offset-background focus-visible:ring-ring mt-1.5 flex h-10 w-full rounded-md border px-3 py-2 text-sm focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:outline-none"
								>
									<option value="USER">User</option>
									<option value="ADMIN">Admin</option>
								</select>
							</div>
							<Button type="submit">
								<Plus class="mr-2 h-4 w-4" />
								Add Member
							</Button>
						</form>
					</div>

					<!-- Users Table -->
					<div class="rounded-lg border">
						<Table.Root>
							<Table.Header>
								<Table.Row>
									<Table.Head class="w-[300px]">Member</Table.Head>
									<Table.Head>Role</Table.Head>
									<Table.Head>Joined</Table.Head>
									<Table.Head class="w-[80px]">Actions</Table.Head>
								</Table.Row>
							</Table.Header>
							<Table.Body>
								{#each users as user (user.id)}
									<Table.Row>
										<Table.Cell>
											<div class="flex items-center gap-3">
												<Avatar.Root class="h-9 w-9">
													{#if user.avatar}
														<Avatar.Image src={user.avatar} alt={user.name} class="" />
													{/if}
													<Avatar.Fallback
														class="bg-gradient-to-br from-blue-500 to-purple-600 text-sm text-white"
													>
														{getInitials(user.name)}
													</Avatar.Fallback>
												</Avatar.Root>
												<div>
													<div class="flex items-center gap-2">
														<span class="text-foreground font-medium">{user.name}</span>
														{#if user.isSelf}
															<Badge variant="secondary" class="text-xs">You</Badge>
														{/if}
														{#if !user.isActive}
															<Badge variant="outline" class="text-muted-foreground text-xs"
																>Inactive</Badge
															>
														{/if}
													</div>
													<span class="text-muted-foreground text-sm">{user.email}</span>
												</div>
											</div>
										</Table.Cell>
										<Table.Cell>
											{#if user.isSelf || editingRoleId !== user.id}
												<Badge
													variant={user.role === 'ADMIN' ? 'default' : 'secondary'}
													class="cursor-default"
												>
													{#if user.role === 'ADMIN'}
														<Shield class="mr-1 h-3 w-3" />
													{:else}
														<User class="mr-1 h-3 w-3" />
													{/if}
													{user.role}
												</Badge>
												{#if !user.isSelf}
													<Button
														variant="ghost"
														size="sm"
														class="ml-2 h-6 px-2 text-xs"
														onclick={() => (editingRoleId = user.id)}
													>
														<Edit class="h-3 w-3" />
													</Button>
												{/if}
											{:else}
												<form method="POST" action="?/edit_role" class="flex items-center gap-2">
													<input type="hidden" name="user_id" value={user.id} />
													<select
														name="role"
														class="border-input bg-background h-8 rounded-md border px-2 text-sm"
													>
														<option value="USER" selected={user.role === 'USER'}>User</option>
														<option value="ADMIN" selected={user.role === 'ADMIN'}>Admin</option>
													</select>
													<Button type="submit" size="icon" class="h-7 w-7" variant="default">
														<Check class="h-3.5 w-3.5" />
													</Button>
													<Button
														type="button"
														size="icon"
														class="h-7 w-7"
														variant="outline"
														onclick={() => (editingRoleId = null)}
													>
														<X class="h-3.5 w-3.5" />
													</Button>
												</form>
											{/if}
										</Table.Cell>
										<Table.Cell>
											<span class="text-muted-foreground text-sm">{formatDate(user.joined)}</span>
										</Table.Cell>
										<Table.Cell>
											{#if user.isSelf}
												<span class="text-muted-foreground">-</span>
											{:else}
												<AlertDialog.Root>
													<AlertDialog.Trigger>
														<Button
															variant="ghost"
															size="icon"
															class="text-destructive hover:bg-destructive/10 h-8 w-8"
														>
															<Trash2 class="h-4 w-4" />
														</Button>
													</AlertDialog.Trigger>
													<AlertDialog.Content>
														<AlertDialog.Header class="">
															<AlertDialog.Title class="">Remove Team Member</AlertDialog.Title>
															<AlertDialog.Description class="">
																Are you sure you want to remove <strong>{user.name}</strong> from the
																organization? This action cannot be undone.
															</AlertDialog.Description>
														</AlertDialog.Header>
														<AlertDialog.Footer class="">
															<AlertDialog.Cancel class="">Cancel</AlertDialog.Cancel>
															<form method="POST" action="?/remove_user" class="inline">
																<input type="hidden" name="user_id" value={user.id} />
																<Button type="submit" variant="destructive">Remove</Button>
															</form>
														</AlertDialog.Footer>
													</AlertDialog.Content>
												</AlertDialog.Root>
											{/if}
										</Table.Cell>
									</Table.Row>
								{/each}

								{#if users.length === 0}
									<Table.Row>
										<Table.Cell colspan={4} class="py-8 text-center">
											<Users class="text-muted-foreground/50 mx-auto h-8 w-8" />
											<p class="text-muted-foreground mt-2 text-sm">No team members found</p>
										</Table.Cell>
									</Table.Row>
								{/if}
							</Table.Body>
						</Table.Root>
					</div>
				</Card.Content>
			</Card.Root>
		</div>
	{/if}
</div>
