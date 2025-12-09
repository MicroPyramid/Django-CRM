<script>
  import { Filter } from '@lucide/svelte';
  import { Button } from '$lib/components/ui/button/index.js';
  import { Badge } from '$lib/components/ui/badge/index.js';
  import * as Popover from '$lib/components/ui/popover/index.js';

  /**
   * @type {{
   *   activeCount?: number,
   *   onClear?: () => void,
   *   children?: import('svelte').Snippet
   * }}
   */
  let { activeCount = 0, onClear, children } = $props();

  let open = $state(false);
</script>

<Popover.Root bind:open>
  <Popover.Trigger asChild class="">
    {#snippet child({ props })}
      <Button variant="outline" {...props}>
        <Filter class="mr-2 h-4 w-4" />
        Filters
        {#if activeCount > 0}
          <Badge variant="secondary" class="ml-2">{activeCount}</Badge>
        {/if}
      </Button>
    {/snippet}
  </Popover.Trigger>
  <Popover.Content align="end" class="w-72">
    <div class="space-y-4">
      <h4 class="text-sm font-medium">Filters</h4>
      {@render children?.()}
      {#if onClear}
        <Button variant="ghost" onclick={onClear} class="w-full">Clear Filters</Button>
      {/if}
    </div>
  </Popover.Content>
</Popover.Root>
