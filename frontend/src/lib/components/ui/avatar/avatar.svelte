<script>
  import { Avatar as AvatarPrimitive } from 'bits-ui';
  import { cn } from '$lib/utils.js';

  /**
   * @typedef {'loading' | 'loaded' | 'error'} LoadingStatus
   */

  /**
   * @type {{
   *   ref?: HTMLElement | null,
   *   loadingStatus?: LoadingStatus,
   *   class?: string,
   *   children?: import('svelte').Snippet,
   *   [key: string]: any
   * }}
   */
  let {
    ref = $bindable(null),
    loadingStatus = $bindable(/** @type {LoadingStatus} */ ('loading')),
    class: className,
    ...restProps
  } = $props();
</script>

<AvatarPrimitive.Root
  bind:ref
  bind:loadingStatus
  data-slot="avatar"
  class={cn('relative flex size-8 shrink-0 overflow-hidden rounded-full', className)}
  {...restProps}
/>
