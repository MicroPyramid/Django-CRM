<script>
  import { enhance } from '$app/forms';
  import { invalidateAll } from '$app/navigation';
  import { toast } from 'svelte-sonner';
  import { Tag, Plus, Archive, RotateCcw, Pencil } from '@lucide/svelte';
  import { PageHeader } from '$lib/components/layout';
  import { Button } from '$lib/components/ui/button/index.js';
  import * as Card from '$lib/components/ui/card/index.js';
  import * as Dialog from '$lib/components/ui/dialog/index.js';
  import { Input } from '$lib/components/ui/input/index.js';
  import { Label } from '$lib/components/ui/label/index.js';
  import { Badge } from '$lib/components/ui/badge/index.js';
  import { TAG_COLORS, getTagColorClass } from '$lib/constants/colors.js';

  /** @type {{ data: any, form: any }} */
  let { data, form } = $props();

  const tags = $derived(data.tags || []);
  const activeTags = $derived(tags.filter((/** @type {any} */ t) => t.is_active));
  const archivedTags = $derived(tags.filter((/** @type {any} */ t) => !t.is_active));

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
</script>

<svelte:head>
  <title>Tag Management - BottleCRM</title>
</svelte:head>

<PageHeader title="Tag Management" subtitle="Create and manage tags for your CRM entities">
  {#snippet actions()}
    <Button onclick={openCreate}>
      <Plus class="mr-2 h-4 w-4" />
      New Tag
    </Button>
  {/snippet}
</PageHeader>

<div class="flex-1 space-y-6 p-4 md:p-6">
  <!-- Active Tags -->
  <Card.Root>
    <Card.Header>
      <Card.Title class="flex items-center gap-2">
        <Tag class="h-5 w-5" />
        Active Tags ({activeTags.length})
      </Card.Title>
      <Card.Description>Tags available for use across all entities</Card.Description>
    </Card.Header>
    <Card.Content>
      {#if activeTags.length === 0}
        <p class="text-muted-foreground text-sm">
          No tags created yet. Click "New Tag" to create your first tag.
        </p>
      {:else}
        <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {#each activeTags as tag (tag.id)}
            <div class="flex items-center justify-between rounded-lg border p-3">
              <div class="flex flex-col gap-1">
                <Badge class={getTagColorClass(tag.color)}>{tag.name}</Badge>
                {#if tag.description}
                  <span class="text-muted-foreground max-w-[200px] truncate text-xs">
                    {tag.description}
                  </span>
                {/if}
              </div>
              <div class="flex gap-1">
                <Button variant="ghost" size="icon" onclick={() => openEdit(tag)} title="Edit tag">
                  <Pencil class="h-4 w-4" />
                </Button>
                <form method="POST" action="?/archive" use:enhance>
                  <input type="hidden" name="tagId" value={tag.id} />
                  <Button variant="ghost" size="icon" type="submit" title="Archive tag">
                    <Archive class="h-4 w-4" />
                  </Button>
                </form>
              </div>
            </div>
          {/each}
        </div>
      {/if}
    </Card.Content>
  </Card.Root>

  <!-- Archived Tags -->
  {#if archivedTags.length > 0}
    <Card.Root>
      <Card.Header>
        <Card.Title class="text-muted-foreground flex items-center gap-2">
          <Archive class="h-5 w-5" />
          Archived Tags ({archivedTags.length})
        </Card.Title>
        <Card.Description
          >Hidden from selection but preserved in existing associations</Card.Description
        >
      </Card.Header>
      <Card.Content>
        <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {#each archivedTags as tag (tag.id)}
            <div
              class="flex items-center justify-between rounded-lg border border-dashed p-3 opacity-60"
            >
              <Badge class={getTagColorClass(tag.color)}>{tag.name}</Badge>
              <form method="POST" action="?/restore" use:enhance>
                <input type="hidden" name="tagId" value={tag.id} />
                <Button variant="ghost" size="sm" type="submit">
                  <RotateCcw class="mr-1.5 h-3.5 w-3.5" />
                  Restore
                </Button>
              </form>
            </div>
          {/each}
        </div>
      </Card.Content>
    </Card.Root>
  {/if}
</div>

<!-- Create Dialog -->
<Dialog.Root bind:open={createDialogOpen}>
  <Dialog.Content class="sm:max-w-md">
    <Dialog.Header>
      <Dialog.Title>Create New Tag</Dialog.Title>
      <Dialog.Description>Add a new tag to organize your CRM entities</Dialog.Description>
    </Dialog.Header>
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
      <div class="grid gap-4 py-4">
        <div class="grid gap-2">
          <Label for="name">Name</Label>
          <Input
            id="name"
            name="name"
            bind:value={formName}
            placeholder="e.g., VIP, Hot Lead, Priority"
          />
        </div>
        <div class="grid gap-2">
          <Label>Color</Label>
          <div class="flex flex-wrap gap-2">
            {#each TAG_COLORS as color}
              <button
                type="button"
                onclick={() => (formColor = color.value)}
                class="flex h-8 w-8 items-center justify-center rounded-full border-2 transition-all {color.class} {formColor ===
                color.value
                  ? 'ring-primary ring-2 ring-offset-2'
                  : 'hover:scale-110'}"
                title={color.label}
              >
                {#if formColor === color.value}
                  <span class="text-xs font-bold">✓</span>
                {/if}
              </button>
            {/each}
          </div>
          <input type="hidden" name="color" value={formColor} />
        </div>
        <div class="grid gap-2">
          <Label for="description">Description (optional)</Label>
          <Input
            id="description"
            name="description"
            bind:value={formDescription}
            placeholder="What is this tag used for?"
          />
        </div>
      </div>
      <Dialog.Footer>
        <Button variant="outline" type="button" onclick={() => (createDialogOpen = false)}
          >Cancel</Button
        >
        <Button type="submit" disabled={!formName.trim() || isLoading}>
          {isLoading ? 'Creating...' : 'Create Tag'}
        </Button>
      </Dialog.Footer>
    </form>
  </Dialog.Content>
</Dialog.Root>

<!-- Edit Dialog -->
<Dialog.Root bind:open={editDialogOpen}>
  <Dialog.Content class="sm:max-w-md">
    <Dialog.Header>
      <Dialog.Title>Edit Tag</Dialog.Title>
      <Dialog.Description>Update tag details</Dialog.Description>
    </Dialog.Header>
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
      <div class="grid gap-4 py-4">
        <div class="grid gap-2">
          <Label for="edit-name">Name</Label>
          <Input id="edit-name" name="name" bind:value={formName} />
        </div>
        <div class="grid gap-2">
          <Label>Color</Label>
          <div class="flex flex-wrap gap-2">
            {#each TAG_COLORS as color}
              <button
                type="button"
                onclick={() => (formColor = color.value)}
                class="flex h-8 w-8 items-center justify-center rounded-full border-2 transition-all {color.class} {formColor ===
                color.value
                  ? 'ring-primary ring-2 ring-offset-2'
                  : 'hover:scale-110'}"
                title={color.label}
              >
                {#if formColor === color.value}
                  <span class="text-xs font-bold">✓</span>
                {/if}
              </button>
            {/each}
          </div>
          <input type="hidden" name="color" value={formColor} />
        </div>
        <div class="grid gap-2">
          <Label for="edit-description">Description</Label>
          <Input id="edit-description" name="description" bind:value={formDescription} />
        </div>
      </div>
      <Dialog.Footer>
        <Button variant="outline" type="button" onclick={() => (editDialogOpen = false)}
          >Cancel</Button
        >
        <Button type="submit" disabled={!formName.trim() || isLoading}>
          {isLoading ? 'Saving...' : 'Save Changes'}
        </Button>
      </Dialog.Footer>
    </form>
  </Dialog.Content>
</Dialog.Root>
