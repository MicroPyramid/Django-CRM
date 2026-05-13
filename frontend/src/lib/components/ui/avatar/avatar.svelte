<script>
  import { Avatar as AvatarPrimitive } from 'bits-ui';
  import { cn } from '$lib/utils.js';

  /**
   * @typedef {'loading' | 'loaded' | 'error'} LoadingStatus
   * @typedef {'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl'} AvatarSize
   */

  /**
   * @type {{
   *   ref?: HTMLElement | null,
   *   loadingStatus?: LoadingStatus,
   *   size?: AvatarSize,
   *   class?: string,
   *   children?: import('svelte').Snippet,
   *   [key: string]: any
   * }}
   */
  let {
    ref = $bindable(null),
    loadingStatus = $bindable(/** @type {LoadingStatus} */ ('loading')),
    size = 'md',
    class: className,
    ...restProps
  } = $props();

  // Spec §6.5: 18 / 22 / 24 / 28 / 32 / 44.
  const sizeClass = $derived(
    {
      xs: 'size-[18px] text-[8px]',
      sm: 'size-[22px] text-[9px]',
      md: 'size-[24px] text-[10px]',
      lg: 'size-[28px] text-[11px]',
      xl: 'size-[32px] text-[12px]',
      '2xl': 'size-[44px] text-[14px]'
    }[size] || 'size-[24px] text-[10px]'
  );
</script>

<AvatarPrimitive.Root
  bind:ref
  bind:loadingStatus
  data-slot="avatar"
  data-size={size}
  class={cn('relative flex shrink-0 overflow-hidden rounded-full', sizeClass, className)}
  {...restProps}
/>
