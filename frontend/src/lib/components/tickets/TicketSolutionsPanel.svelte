<script>
  import { enhance } from '$app/forms';
  import { invalidateAll } from '$app/navigation';
  import { toast } from 'svelte-sonner';
  import { Plus, X, BookOpen } from '@lucide/svelte';
  import { Button } from '$lib/components/ui/button/index.js';

  /** @type {{ ticketId: string, linked: any[], available: any[] }} */
  let { ticketId, linked, available } = $props();

  let pickerOpen = $state(false);
  let search = $state('');

  const linkedIds = $derived(new Set(linked.map((s) => s.id)));
  const filteredAvailable = $derived(
    available.filter(
      (s) =>
        !linkedIds.has(s.id) &&
        (search === '' || s.title.toLowerCase().includes(search.toLowerCase()))
    )
  );
</script>

<section class="rounded-lg border border-[var(--border-default)] bg-[var(--surface-default)] p-4">
  <div class="mb-3 flex items-center justify-between">
    <h3 class="text-sm font-medium text-[var(--text-secondary)]">
      Knowledge Base ({linked.length})
    </h3>
    <Button size="sm" variant="ghost" onclick={() => (pickerOpen = !pickerOpen)}>
      <Plus class="mr-1 h-3 w-3" />
      Link solution
    </Button>
  </div>

  {#if pickerOpen}
    <div class="mb-3 rounded-md border border-[var(--border-default)] p-2">
      <input
        type="text"
        bind:value={search}
        placeholder="Search published solutions..."
        class="mb-2 w-full rounded-md border border-[var(--border-default)] px-2 py-1 text-sm"
      />
      {#if available.length === 0}
        <div class="px-1 py-2 text-xs text-[var(--text-secondary)]">
          No published solutions yet.
          <a href="/solutions" class="text-[var(--text-primary)] underline">
            Visit Knowledge Base
          </a>
          to publish one — only Live articles appear here.
        </div>
      {:else if filteredAvailable.length === 0}
        <p class="px-1 py-2 text-xs text-[var(--text-secondary)]">
          {linkedIds.size > 0 && search === ''
            ? 'All published solutions are already linked.'
            : 'No matching solutions.'}
        </p>
      {:else}
        <ul class="max-h-48 overflow-y-auto">
          {#each filteredAvailable as sol (sol.id)}
            <li class="flex items-center justify-between gap-2 rounded px-2 py-1 hover:bg-[var(--surface-sunken)]">
              <span class="truncate text-sm">{sol.title}</span>
              <form
                method="POST"
                action="?/linkSolution"
                use:enhance={() =>
                  async ({ result }) => {
                    if (result.type === 'success') {
                      toast.success('Solution linked');
                      pickerOpen = false;
                      search = '';
                      await invalidateAll();
                    } else {
                      toast.error('Failed to link');
                    }
                  }}
              >
                <input type="hidden" name="solutionId" value={sol.id} />
                <Button type="submit" size="sm" variant="outline">Link</Button>
              </form>
            </li>
          {/each}
        </ul>
      {/if}
    </div>
  {/if}

  {#if linked.length === 0}
    <div class="flex flex-col items-center gap-1 py-4 text-center">
      <BookOpen class="h-6 w-6 text-[var(--text-tertiary)]" />
      <p class="text-xs text-[var(--text-secondary)]">No KB articles linked yet.</p>
    </div>
  {:else}
    <ul class="space-y-2">
      {#each linked as sol (sol.id)}
        <li class="flex items-start justify-between gap-2 rounded-md bg-[var(--surface-sunken)] p-2">
          <div class="min-w-0">
            <p class="truncate text-sm font-medium">{sol.title}</p>
            {#if sol.description}
              <p class="truncate text-xs text-[var(--text-secondary)]">
                {sol.description.slice(0, 100)}
              </p>
            {/if}
          </div>
          <form
            method="POST"
            action="?/unlinkSolution"
            use:enhance={() =>
              async ({ result }) => {
                if (result.type === 'success') {
                  toast.success('Solution unlinked');
                  await invalidateAll();
                }
              }}
          >
            <input type="hidden" name="solutionId" value={sol.id} />
            <Button type="submit" size="sm" variant="ghost" aria-label="Unlink">
              <X class="h-3 w-3" />
            </Button>
          </form>
        </li>
      {/each}
    </ul>
  {/if}
</section>
