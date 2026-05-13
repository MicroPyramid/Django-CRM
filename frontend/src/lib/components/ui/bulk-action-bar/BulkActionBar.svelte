<script>
  import { X } from '@lucide/svelte';
  import { Button } from '$lib/components/ui/button/index.js';

  /** @typedef {{ label: string, onClick: () => void, variant?: 'default'|'outline'|'destructive' }} BulkAction */

  /** @type {{ count: number, actions?: BulkAction[], onClear: () => void }} */
  let { count, actions = [], onClear } = $props();
</script>

{#if count > 0}
  <div
    role="region"
    aria-label="Bulk actions"
    class="fixed inset-x-0 bottom-4 z-40 mx-auto flex w-fit items-center gap-2 rounded-full border border-[var(--border-default)] bg-[var(--surface-default)] px-4 py-2 shadow-lg"
  >
    <span class="text-sm font-medium">{count} selected</span>
    <span class="h-4 w-px bg-[var(--border-default)]"></span>
    {#each actions as a (a.label)}
      <Button size="sm" variant={a.variant || 'outline'} onclick={a.onClick}>{a.label}</Button>
    {/each}
    <button
      type="button"
      onclick={onClear}
      class="ml-1 rounded-full p-1 hover:bg-[var(--surface-sunken)]"
      aria-label="Clear selection"
    >
      <X class="h-4 w-4" />
    </button>
  </div>
{/if}
