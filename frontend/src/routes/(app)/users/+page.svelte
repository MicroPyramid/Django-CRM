<script>
	import { enhance } from '$app/forms';
	import { invalidateAll } from '$app/navigation';
	import { toast } from 'svelte-sonner';
	import {
		Users,
		UsersRound,
		User,
		Shield,
		Edit,
		Plus,
		Check,
		X,
		Trash2,
		AlertCircle,
		UserCheck
	} from '@lucide/svelte';
	import PageHeader from '$lib/components/layout/PageHeader.svelte';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import * as Card from '$lib/components/ui/card/index.js';
	import * as Table from '$lib/components/ui/table/index.js';
	import * as Avatar from '$lib/components/ui/avatar/index.js';
	import * as AlertDialog from '$lib/components/ui/alert-dialog/index.js';
	import * as Tabs from '$lib/components/ui/tabs/index.js';
	import { getInitials, formatDate } from '$lib/utils/formatting.js';
	import { TeamCard, TeamFormDialog } from '$lib/components/users/index.js';

	/** @type {{ data: import('./$types').PageData, form: any }} */
	let { data, form } = $props();

	// Get logged-in user id from data
	let loggedInUserId = $derived(data.user?.id);

	// Transform users data for table display
	let users = $derived(
		Array.isArray(data.users)
			? data.users.map((u) => ({
					id: u.user.id,
					odId: u.profile?.id || u.odId,
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

	// Teams data
	let teams = $derived(data.teams || []);

	// Users list for team assignment (active users only, transformed for multi-select)
	let availableUsers = $derived(
		users
			.filter((u) => u.isActive)
			.map((u) => ({
				id: u.odId,
				name: u.name,
				email: u.email
			}))
	);

	// State for editing roles
	/** @type {string | null} */
	let editingRoleId = $state(null);

	// State for team dialog
	let teamDialogOpen = $state(false);
	/** @type {any} */
	let editingTeam = $state(null);
	let isTeamLoading = $state(false);

	// Handle form results
	$effect(() => {
		if (form?.success) {
			if (form.action === 'create_team') {
				toast.success('Team created successfully');
				teamDialogOpen = false;
				editingTeam = null;
			} else if (form.action === 'update_team') {
				toast.success('Team updated successfully');
				teamDialogOpen = false;
				editingTeam = null;
			} else if (form.action === 'delete_team') {
				toast.success('Team deleted successfully');
			} else if (form.action === 'remove_user') {
				toast.success('User deactivated');
			} else if (form.action === 'activate_user') {
				toast.success('User activated');
			}
			invalidateAll();
		} else if (form?.error) {
			toast.error(form.error);
		}
		isTeamLoading = false;
	});

	/**
	 * Open dialog to create a new team
	 */
	function openCreateTeamDialog() {
		editingTeam = null;
		teamDialogOpen = true;
	}

	/**
	 * Open dialog to edit a team
	 * @param {any} team
	 */
	function openEditTeamDialog(team) {
		editingTeam = team;
		teamDialogOpen = true;
	}

	/**
	 * Handle team form submission
	 * @param {{ name: string, description: string, users: string[], teamId?: string }} formData
	 */
	function handleTeamSubmit(formData) {
		isTeamLoading = true;

		// Create a hidden form and submit it
		const form = document.createElement('form');
		form.method = 'POST';
		form.action = formData.teamId ? '?/update_team' : '?/create_team';
		form.style.display = 'none';

		// Add form fields
		const addField = (/** @type {string} */ name, /** @type {string} */ value) => {
			const input = document.createElement('input');
			input.type = 'hidden';
			input.name = name;
			input.value = value;
			form.appendChild(input);
		};

		addField('name', formData.name);
		addField('description', formData.description);
		if (formData.teamId) {
			addField('team_id', formData.teamId);
		}
		formData.users.forEach((userId) => {
			addField('users', userId);
		});

		document.body.appendChild(form);
		form.submit();
	}

	/**
	 * Handle team deletion
	 * @param {string} teamId
	 */
	function handleTeamDelete(teamId) {
		const form = document.createElement('form');
		form.method = 'POST';
		form.action = '?/delete_team';
		form.style.display = 'none';

		const input = document.createElement('input');
		input.type = 'hidden';
		input.name = 'team_id';
		input.value = teamId;
		form.appendChild(input);

		document.body.appendChild(form);
		form.submit();
	}

	/**
	 * Handle user removal from organization
	 * @param {string} userId
	 */
	function handleRemoveUser(userId) {
		const form = document.createElement('form');
		form.method = 'POST';
		form.action = '?/remove_user';
		form.style.display = 'none';

		const input = document.createElement('input');
		input.type = 'hidden';
		input.name = 'user_id';
		input.value = userId;
		form.appendChild(input);

		document.body.appendChild(form);
		form.submit();
	}

	/**
	 * Handle user activation (restore inactive user)
	 * @param {string} userId
	 */
	function handleActivateUser(userId) {
		const form = document.createElement('form');
		form.method = 'POST';
		form.action = '?/activate_user';
		form.style.display = 'none';

		const input = document.createElement('input');
		input.type = 'hidden';
		input.name = 'user_id';
		input.value = userId;
		form.appendChild(input);

		document.body.appendChild(form);
		form.submit();
	}
</script>

<svelte:head>
	<title>Users & Teams - BottleCRM</title>
</svelte:head>

<PageHeader title="Users & Teams" subtitle="Manage users and teams in your organization" />

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
		<div class="mx-auto max-w-5xl">
			<Tabs.Root value="users" class="w-full">
				<Tabs.List class="mb-6 grid w-full grid-cols-2 lg:w-[400px]">
					<Tabs.Trigger value="users" class="gap-2">
						<Users class="h-4 w-4" />
						Users
					</Tabs.Trigger>
					<Tabs.Trigger value="teams" class="gap-2">
						<UsersRound class="h-4 w-4" />
						Teams
					</Tabs.Trigger>
				</Tabs.List>

				<!-- Users Tab -->
				<Tabs.Content value="users" class="space-y-6">
					<!-- Add User Form -->
					<Card.Root>
						<Card.Header class="pb-4">
							<div class="flex items-center gap-3">
								<div
									class="flex h-10 w-10 items-center justify-center rounded-lg bg-green-100 dark:bg-green-900/30"
								>
									<Plus class="h-5 w-5 text-green-600 dark:text-green-400" />
								</div>
								<div>
									<Card.Title class="">Add New Member</Card.Title>
									<Card.Description class="">Invite a user to join your organization</Card.Description>
								</div>
							</div>
						</Card.Header>
						<Card.Content>
							<form
								method="POST"
								action="?/add_user"
								class="flex flex-col gap-4 sm:flex-row sm:items-end"
							>
								<div class="flex-1">
									<Label class="" for="add-user-email">Email Address *</Label>
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
									<Label class="" for="add-user-role">Role</Label>
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
						</Card.Content>
					</Card.Root>

					<!-- Users Table -->
					<Card.Root>
						<Card.Header class="pb-4">
							<div class="flex items-center gap-3">
								<div
									class="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-100 dark:bg-blue-900/30"
								>
									<Users class="h-5 w-5 text-blue-600 dark:text-blue-400" />
								</div>
								<div>
									<Card.Title class="">Team Members</Card.Title>
									<Card.Description class=""
										>{users.length} member{users.length !== 1 ? 's' : ''} in your organization</Card.Description
									>
								</div>
							</div>
						</Card.Header>
						<Card.Content>
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
																<Avatar.Image class="" src={user.avatar} alt={user.name} />
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
													<span class="text-muted-foreground text-sm"
														>{formatDate(user.joined)}</span
													>
												</Table.Cell>
												<Table.Cell>
													{#if user.isSelf}
														<span class="text-muted-foreground">-</span>
													{:else if !user.isActive}
														<!-- Inactive user: show Activate button -->
														<Button
															variant="ghost"
															size="icon"
															class="text-green-600 hover:bg-green-100 h-8 w-8"
															onclick={() => handleActivateUser(user.id)}
															title="Activate user"
														>
															<UserCheck class="h-4 w-4" />
														</Button>
													{:else}
														<!-- Active user: show Deactivate button -->
														<AlertDialog.Root>
															<AlertDialog.Trigger>
																<Button
																	variant="ghost"
																	size="icon"
																	class="text-destructive hover:bg-destructive/10 h-8 w-8"
																	title="Deactivate user"
																>
																	<Trash2 class="h-4 w-4" />
																</Button>
															</AlertDialog.Trigger>
															<AlertDialog.Content>
																<AlertDialog.Header>
																	<AlertDialog.Title>Deactivate Team Member</AlertDialog.Title>
																	<AlertDialog.Description>
																		Are you sure you want to deactivate <strong>{user.name}</strong>?
																		They will no longer be able to access the organization.
																	</AlertDialog.Description>
																</AlertDialog.Header>
																<AlertDialog.Footer>
																	<AlertDialog.Cancel>Cancel</AlertDialog.Cancel>
																	<Button
																		variant="destructive"
																		onclick={() => handleRemoveUser(user.id)}
																	>
																		Deactivate
																	</Button>
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
				</Tabs.Content>

				<!-- Teams Tab -->
				<Tabs.Content value="teams" class="space-y-6">
					<!-- Header with Create Button -->
					<div class="flex items-center justify-between">
						<div>
							<h2 class="text-lg font-semibold">Teams</h2>
							<p class="text-muted-foreground text-sm">
								Create teams to group users for assignments and access control.
							</p>
						</div>
						<Button onclick={openCreateTeamDialog}>
							<Plus class="mr-2 h-4 w-4" />
							Create Team
						</Button>
					</div>

					<!-- Teams Grid -->
					{#if teams.length > 0}
						<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
							{#each teams as team (team.id)}
								<TeamCard {team} onEdit={openEditTeamDialog} onDelete={handleTeamDelete} />
							{/each}
						</div>
					{:else}
						<!-- Empty State -->
						<Card.Root class="py-12">
							<Card.Content class="text-center">
								<div
									class="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-purple-100 dark:bg-purple-900/30"
								>
									<UsersRound class="h-8 w-8 text-purple-600 dark:text-purple-400" />
								</div>
								<h3 class="mb-2 text-lg font-semibold">No teams yet</h3>
								<p class="text-muted-foreground mx-auto mb-6 max-w-sm text-sm">
									Teams help you organize users and manage access to records. Create your first
									team to get started.
								</p>
								<Button onclick={openCreateTeamDialog}>
									<Plus class="mr-2 h-4 w-4" />
									Create Your First Team
								</Button>
							</Card.Content>
						</Card.Root>
					{/if}
				</Tabs.Content>
			</Tabs.Root>
		</div>
	{/if}
</div>

<!-- Team Form Dialog -->
<TeamFormDialog
	bind:open={teamDialogOpen}
	team={editingTeam}
	users={availableUsers}
	onClose={() => {
		teamDialogOpen = false;
		editingTeam = null;
	}}
	onSubmit={handleTeamSubmit}
	isLoading={isTeamLoading}
/>
