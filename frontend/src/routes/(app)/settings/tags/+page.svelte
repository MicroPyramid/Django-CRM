<script>
  import { enhance } from '$app/forms';
  import { invalidateAll } from '$app/navigation';
  import { toast } from 'svelte-sonner';
  import {
    Tag,
    Plus,
    Archive,
    RotateCcw,
    Pencil,
    Search,
    MoreHorizontal,
    Check,
    X
  } from '@lucide/svelte';
  import { PageHeader } from '$lib/components/layout';
  import { Button } from '$lib/components/ui/button/index.js';
  import * as Dialog from '$lib/components/ui/dialog/index.js';
  import * as DropdownMenu from '$lib/components/ui/dropdown-menu/index.js';
  import { Input } from '$lib/components/ui/input/index.js';
  import { Label } from '$lib/components/ui/label/index.js';
  import { TAG_COLORS } from '$lib/constants/colors.js';

  /** @type {{ data: any, form: any }} */
  let { data, form } = $props();

  const tags = $derived(data.tags || []);
  const activeTags = $derived(tags.filter((/** @type {any} */ t) => t.is_active));
  const archivedTags = $derived(tags.filter((/** @type {any} */ t) => !t.is_active));

  // Search and filter
  let searchQuery = $state('');
  let showArchived = $state(false);

  const filteredActiveTags = $derived(
    activeTags.filter((/** @type {any} */ tag) =>
      tag.name.toLowerCase().includes(searchQuery.toLowerCase())
    )
  );

  const filteredArchivedTags = $derived(
    archivedTags.filter((/** @type {any} */ tag) =>
      tag.name.toLowerCase().includes(searchQuery.toLowerCase())
    )
  );

  // Dialog state
  let createDialogOpen = $state(false);
  let editDialogOpen = $state(false);
  /** @type {any} */
  let editingTag = $state(null);
  let isLoading = $state(false);

  // Form state
  let formName = $state('');
  let formColor = $state('blue');
  let formDescription = $state('');

  function openCreate() {
    formName = '';
    formColor = 'blue';
    formDescription = '';
    createDialogOpen = true;
  }

  /**
   * @param {any} tag
   */
  function openEdit(tag) {
    editingTag = tag;
    formName = tag.name;
    formColor = tag.color || 'blue';
    formDescription = tag.description || '';
    editDialogOpen = true;
  }

  function closeDialogs() {
    createDialogOpen = false;
    editDialogOpen = false;
    editingTag = null;
  }

  // Handle form results
  $effect(() => {
    if (form?.success) {
      const messages = {
        create: 'Tag created successfully',
        update: 'Tag updated successfully',
        archive: 'Tag archived successfully',
        restore: 'Tag restored successfully'
      };
      toast.success(messages[form.action] || 'Operation successful');
      closeDialogs();
      invalidateAll();
    } else if (form?.error) {
      toast.error(form.error);
    }
  });

  // HubSpot-style color mapping - simple, clean colors
  /**
   * @param {string} color
   */
  function getHubspotBadgeClass(color) {
    const colorMap = {
      gray: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300',
      red: 'bg-red-50 text-red-700 dark:bg-red-950 dark:text-red-400',
      orange: 'bg-orange-50 text-orange-700 dark:bg-orange-950 dark:text-orange-400',
      amber: 'bg-amber-50 text-amber-700 dark:bg-amber-950 dark:text-amber-400',
      yellow: 'bg-yellow-50 text-yellow-700 dark:bg-yellow-950 dark:text-yellow-400',
      lime: 'bg-lime-50 text-lime-700 dark:bg-lime-950 dark:text-lime-400',
      green: 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-400',
      emerald: 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-400',
      teal: 'bg-teal-50 text-teal-700 dark:bg-teal-950 dark:text-teal-400',
      cyan: 'bg-cyan-50 text-cyan-700 dark:bg-cyan-950 dark:text-cyan-400',
      sky: 'bg-sky-50 text-sky-700 dark:bg-sky-950 dark:text-sky-400',
      blue: 'bg-blue-50 text-blue-700 dark:bg-blue-950 dark:text-blue-400',
      indigo: 'bg-indigo-50 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-400',
      violet: 'bg-violet-50 text-violet-700 dark:bg-violet-950 dark:text-violet-400',
      purple: 'bg-purple-50 text-purple-700 dark:bg-purple-950 dark:text-purple-400',
      fuchsia: 'bg-fuchsia-50 text-fuchsia-700 dark:bg-fuchsia-950 dark:text-fuchsia-400',
      pink: 'bg-pink-50 text-pink-700 dark:bg-pink-950 dark:text-pink-400',
      rose: 'bg-rose-50 text-rose-700 dark:bg-rose-950 dark:text-rose-400'
    };
    return colorMap[color] || colorMap.blue;
  }

  /**
   * @param {string} color
   */
  function getColorDotClass(color) {
    const colorMap = {
      gray: 'bg-slate-500',
      red: 'bg-red-500',
      orange: 'bg-orange-500',
      amber: 'bg-amber-500',
      yellow: 'bg-yellow-500',
      lime: 'bg-lime-500',
      green: 'bg-emerald-500',
      emerald: 'bg-emerald-500',
      teal: 'bg-teal-500',
      cyan: 'bg-cyan-500',
      sky: 'bg-sky-500',
      blue: 'bg-blue-500',
      indigo: 'bg-indigo-500',
      violet: 'bg-violet-500',
      purple: 'bg-purple-500',
      fuchsia: 'bg-fuchsia-500',
      pink: 'bg-pink-500',
      rose: 'bg-rose-500'
    };
    return colorMap[color] || colorMap.blue;
  }
</script>

<svelte:head>
  <title>Tags - BottleCRM</title>
</svelte:head>

<!-- HubSpot-style header -->
<div class="border-border bg-card border-b">
  <div class="px-6 py-5">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-foreground text-2xl font-semibold tracking-tight">Tags</h1>
        <p class="text-muted-foreground mt-1 text-sm">
          Create and manage tags to organize contacts, companies, deals, and tickets.
        </p>
      </div>
      <Button
        onclick={openCreate}
        class="border-0 bg-[var(--color-primary-default)] text-white hover:bg-[var(--color-primary-dark)]"
      >
        <Plus class="mr-2 h-4 w-4" />
        Create tag
      </Button>
    </div>
  </div>
</div>

<div class="bg-background flex-1">
  <!-- Search and filter bar -->
  <div class="border-border bg-card border-b px-6 py-3">
    <div class="flex items-center gap-4">
      <div class="relative max-w-sm flex-1">
        <Search class="text-muted-foreground absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2" />
        <Input
          type="text"
          placeholder="Search tags..."
          bind:value={searchQuery}
          class="bg-background h-9 pl-9"
        />
      </div>
      <div class="flex items-center gap-2">
        <button
          onclick={() => (showArchived = false)}
          class="rounded-md px-3 py-1.5 text-sm font-medium transition-colors {!showArchived
            ? 'bg-secondary text-foreground'
            : 'text-muted-foreground hover:text-foreground hover:bg-secondary/50'}"
        >
          Active ({activeTags.length})
        </button>
        <button
          onclick={() => (showArchived = true)}
          class="rounded-md px-3 py-1.5 text-sm font-medium transition-colors {showArchived
            ? 'bg-secondary text-foreground'
            : 'text-muted-foreground hover:text-foreground hover:bg-secondary/50'}"
        >
          Archived ({archivedTags.length})
        </button>
      </div>
    </div>
  </div>

  <!-- Tags table -->
  <div class="px-6 py-4">
    {#if !showArchived}
      {#if filteredActiveTags.length === 0}
        <div class="flex flex-col items-center justify-center py-16 text-center">
          <div class="bg-muted mb-4 flex h-14 w-14 items-center justify-center rounded-full">
            <Tag class="text-muted-foreground h-7 w-7" />
          </div>
          {#if searchQuery}
            <h3 class="text-foreground text-lg font-medium">No tags found</h3>
            <p class="text-muted-foreground mt-1 text-sm">
              No tags match "{searchQuery}". Try a different search term.
            </p>
          {:else}
            <h3 class="text-foreground text-lg font-medium">No tags yet</h3>
            <p class="text-muted-foreground mt-1 max-w-sm text-sm">
              Tags help you organize and filter your CRM records. Create your first tag to get
              started.
            </p>
            <Button
              onclick={openCreate}
              class="mt-4 border-0 bg-[var(--color-primary-default)] text-white hover:bg-[var(--color-primary-dark)]"
            >
              <Plus class="mr-2 h-4 w-4" />
              Create tag
            </Button>
          {/if}
        </div>
      {:else}
        <div class="border-border overflow-hidden rounded-lg border">
          <table class="w-full">
            <thead>
              <tr class="border-border bg-muted/50 border-b">
                <th
                  class="text-muted-foreground px-4 py-3 text-left text-xs font-semibold tracking-wider uppercase"
                >
                  Tag name
                </th>
                <th
                  class="text-muted-foreground px-4 py-3 text-left text-xs font-semibold tracking-wider uppercase"
                >
                  Description
                </th>
                <th
                  class="text-muted-foreground px-4 py-3 text-right text-xs font-semibold tracking-wider uppercase"
                >
                  Actions
                </th>
              </tr>
            </thead>
            <tbody class="divide-border divide-y">
              {#each filteredActiveTags as tag (tag.id)}
                <tr class="group bg-card hover:bg-muted/30 transition-colors">
                  <td class="px-4 py-3">
                    <div class="flex items-center gap-3">
                      <span
                        class="inline-flex items-center gap-1.5 rounded-md px-2.5 py-1 text-sm font-medium {getHubspotBadgeClass(
                          tag.color
                        )}"
                      >
                        <span class="h-2 w-2 rounded-full {getColorDotClass(tag.color)}"></span>
                        {tag.name}
                      </span>
                    </div>
                  </td>
                  <td class="px-4 py-3">
                    <span class="text-muted-foreground text-sm">
                      {tag.description || '—'}
                    </span>
                  </td>
                  <td class="px-4 py-3 text-right">
                    <div
                      class="flex items-center justify-end gap-1 opacity-0 transition-opacity group-hover:opacity-100"
                    >
                      <Button
                        variant="ghost"
                        size="sm"
                        onclick={() => openEdit(tag)}
                        class="text-muted-foreground hover:text-foreground h-8 px-2"
                      >
                        <Pencil class="h-4 w-4" />
                        <span class="ml-1.5">Edit</span>
                      </Button>
                      <DropdownMenu.Root>
                        <DropdownMenu.Trigger>
                          <Button
                            variant="ghost"
                            size="icon"
                            class="text-muted-foreground hover:text-foreground h-8 w-8"
                          >
                            <MoreHorizontal class="h-4 w-4" />
                          </Button>
                        </DropdownMenu.Trigger>
                        <DropdownMenu.Content align="end">
                          <form method="POST" action="?/archive" use:enhance>
                            <input type="hidden" name="tagId" value={tag.id} />
                            <DropdownMenu.Item class="text-destructive focus:text-destructive">
                              <button type="submit" class="flex w-full items-center gap-2">
                                <Archive class="h-4 w-4" />
                                Archive tag
                              </button>
                            </DropdownMenu.Item>
                          </form>
                        </DropdownMenu.Content>
                      </DropdownMenu.Root>
                    </div>
                  </td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
        <p class="text-muted-foreground mt-3 text-xs">
          Showing {filteredActiveTags.length} of {activeTags.length} active tags
        </p>
      {/if}
    {:else if filteredArchivedTags.length === 0}
      <div class="flex flex-col items-center justify-center py-16 text-center">
        <div class="bg-muted mb-4 flex h-14 w-14 items-center justify-center rounded-full">
          <Archive class="text-muted-foreground h-7 w-7" />
        </div>
        {#if searchQuery}
          <h3 class="text-foreground text-lg font-medium">No archived tags found</h3>
          <p class="text-muted-foreground mt-1 text-sm">
            No archived tags match "{searchQuery}".
          </p>
        {:else}
          <h3 class="text-foreground text-lg font-medium">No archived tags</h3>
          <p class="text-muted-foreground mt-1 text-sm">Archived tags will appear here.</p>
        {/if}
      </div>
    {:else}
      <div class="border-border overflow-hidden rounded-lg border">
        <table class="w-full">
          <thead>
            <tr class="border-border bg-muted/50 border-b">
              <th
                class="text-muted-foreground px-4 py-3 text-left text-xs font-semibold tracking-wider uppercase"
              >
                Tag name
              </th>
              <th
                class="text-muted-foreground px-4 py-3 text-left text-xs font-semibold tracking-wider uppercase"
              >
                Description
              </th>
              <th
                class="text-muted-foreground px-4 py-3 text-right text-xs font-semibold tracking-wider uppercase"
              >
                Actions
              </th>
            </tr>
          </thead>
          <tbody class="divide-border divide-y">
            {#each filteredArchivedTags as tag (tag.id)}
              <tr class="group bg-card opacity-60 transition-all hover:opacity-100">
                <td class="px-4 py-3">
                  <div class="flex items-center gap-3">
                    <span
                      class="inline-flex items-center gap-1.5 rounded-md px-2.5 py-1 text-sm font-medium {getHubspotBadgeClass(
                        tag.color
                      )}"
                    >
                      <span class="h-2 w-2 rounded-full {getColorDotClass(tag.color)}"></span>
                      {tag.name}
                    </span>
                  </div>
                </td>
                <td class="px-4 py-3">
                  <span class="text-muted-foreground text-sm">
                    {tag.description || '—'}
                  </span>
                </td>
                <td class="px-4 py-3 text-right">
                  <form method="POST" action="?/restore" use:enhance class="inline">
                    <input type="hidden" name="tagId" value={tag.id} />
                    <Button
                      variant="ghost"
                      size="sm"
                      type="submit"
                      class="text-muted-foreground hover:text-foreground h-8 gap-1.5 opacity-0 group-hover:opacity-100"
                    >
                      <RotateCcw class="h-4 w-4" />
                      Restore
                    </Button>
                  </form>
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
      <p class="text-muted-foreground mt-3 text-xs">
        Showing {filteredArchivedTags.length} of {archivedTags.length} archived tags
      </p>
    {/if}
  </div>
</div>

<!-- Create Dialog - HubSpot style -->
<Dialog.Root bind:open={createDialogOpen}>
  <Dialog.Content class="gap-0 overflow-hidden p-0 sm:max-w-md">
    <div class="border-border border-b px-6 py-4">
      <Dialog.Title class="text-lg font-semibold">Create a tag</Dialog.Title>
      <Dialog.Description class="text-muted-foreground mt-1 text-sm">
        Tags help you organize and segment your records.
      </Dialog.Description>
    </div>
    <form
      method="POST"
      action="?/create"
      use:enhance={() => {
        isLoading = true;
        return async ({ update }) => {
          await update();
          isLoading = false;
        };
      }}
    >
      <div class="space-y-5 px-6 py-5">
        <div class="space-y-2">
          <Label for="name" class="text-sm font-medium">
            Tag name <span class="text-destructive">*</span>
          </Label>
          <Input
            id="name"
            name="name"
            bind:value={formName}
            placeholder="e.g., VIP Customer, Hot Lead"
            class="h-10"
          />
        </div>

        <div class="space-y-2">
          <Label class="text-sm font-medium">Color</Label>
          <div class="flex flex-wrap gap-2">
            {#each TAG_COLORS as color}
              <button
                type="button"
                onclick={() => (formColor = color.value)}
                class="group relative flex h-7 w-7 items-center justify-center rounded-full transition-all {getColorDotClass(
                  color.value
                )} {formColor === color.value
                  ? 'ring-offset-background ring-foreground scale-110 ring-2 ring-offset-2'
                  : 'hover:scale-110'}"
                title={color.label}
              >
                {#if formColor === color.value}
                  <Check class="h-3.5 w-3.5 text-white" />
                {/if}
              </button>
            {/each}
          </div>
          <input type="hidden" name="color" value={formColor} />
        </div>

        <div class="space-y-2">
          <Label for="description" class="text-sm font-medium">
            Description <span class="text-muted-foreground font-normal">(optional)</span>
          </Label>
          <Input
            id="description"
            name="description"
            bind:value={formDescription}
            placeholder="Describe what this tag is for..."
            class="h-10"
          />
        </div>

        <!-- Preview -->
        <div class="pt-2">
          <Label class="text-muted-foreground text-sm font-medium">Preview</Label>
          <div class="mt-2 flex items-center">
            <span
              class="inline-flex items-center gap-1.5 rounded-md px-2.5 py-1 text-sm font-medium {getHubspotBadgeClass(
                formColor
              )}"
            >
              <span class="h-2 w-2 rounded-full {getColorDotClass(formColor)}"></span>
              {formName || 'Tag name'}
            </span>
          </div>
        </div>
      </div>

      <div class="border-border bg-muted/30 flex justify-end gap-2 border-t px-6 py-4">
        <Button variant="outline" type="button" onclick={() => (createDialogOpen = false)}>
          Cancel
        </Button>
        <Button
          type="submit"
          disabled={!formName.trim() || isLoading}
          class="border-0 bg-[var(--color-primary-default)] text-white hover:bg-[var(--color-primary-dark)]"
        >
          {isLoading ? 'Creating...' : 'Create tag'}
        </Button>
      </div>
    </form>
  </Dialog.Content>
</Dialog.Root>

<!-- Edit Dialog - HubSpot style -->
<Dialog.Root bind:open={editDialogOpen}>
  <Dialog.Content class="gap-0 overflow-hidden p-0 sm:max-w-md">
    <div class="border-border border-b px-6 py-4">
      <Dialog.Title class="text-lg font-semibold">Edit tag</Dialog.Title>
      <Dialog.Description class="text-muted-foreground mt-1 text-sm">
        Update the tag name, color, or description.
      </Dialog.Description>
    </div>
    <form
      method="POST"
      action="?/update"
      use:enhance={() => {
        isLoading = true;
        return async ({ update }) => {
          await update();
          isLoading = false;
        };
      }}
    >
      <input type="hidden" name="tagId" value={editingTag?.id} />
      <div class="space-y-5 px-6 py-5">
        <div class="space-y-2">
          <Label for="edit-name" class="text-sm font-medium">
            Tag name <span class="text-destructive">*</span>
          </Label>
          <Input id="edit-name" name="name" bind:value={formName} class="h-10" />
        </div>

        <div class="space-y-2">
          <Label class="text-sm font-medium">Color</Label>
          <div class="flex flex-wrap gap-2">
            {#each TAG_COLORS as color}
              <button
                type="button"
                onclick={() => (formColor = color.value)}
                class="group relative flex h-7 w-7 items-center justify-center rounded-full transition-all {getColorDotClass(
                  color.value
                )} {formColor === color.value
                  ? 'ring-offset-background ring-foreground scale-110 ring-2 ring-offset-2'
                  : 'hover:scale-110'}"
                title={color.label}
              >
                {#if formColor === color.value}
                  <Check class="h-3.5 w-3.5 text-white" />
                {/if}
              </button>
            {/each}
          </div>
          <input type="hidden" name="color" value={formColor} />
        </div>

        <div class="space-y-2">
          <Label for="edit-description" class="text-sm font-medium">
            Description <span class="text-muted-foreground font-normal">(optional)</span>
          </Label>
          <Input
            id="edit-description"
            name="description"
            bind:value={formDescription}
            class="h-10"
          />
        </div>

        <!-- Preview -->
        <div class="pt-2">
          <Label class="text-muted-foreground text-sm font-medium">Preview</Label>
          <div class="mt-2 flex items-center">
            <span
              class="inline-flex items-center gap-1.5 rounded-md px-2.5 py-1 text-sm font-medium {getHubspotBadgeClass(
                formColor
              )}"
            >
              <span class="h-2 w-2 rounded-full {getColorDotClass(formColor)}"></span>
              {formName || 'Tag name'}
            </span>
          </div>
        </div>
      </div>

      <div class="border-border bg-muted/30 flex justify-end gap-2 border-t px-6 py-4">
        <Button variant="outline" type="button" onclick={() => (editDialogOpen = false)}>
          Cancel
        </Button>
        <Button
          type="submit"
          disabled={!formName.trim() || isLoading}
          class="border-0 bg-[var(--color-primary-default)] text-white hover:bg-[var(--color-primary-dark)]"
        >
          {isLoading ? 'Saving...' : 'Save'}
        </Button>
      </div>
    </form>
  </Dialog.Content>
</Dialog.Root>
