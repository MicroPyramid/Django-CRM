<script>
  import { Avatar as AvatarPrimitive } from 'bits-ui';
  import { cn } from '$lib/utils.js';
  import { gradientFor, WORKSPACE_GRADIENT } from './avatar-gradients.js';

  /**
   * @type {{
   *   ref?: HTMLElement | null,
   *   class?: string,
   *   gradientSeed?: string | number,
   *   workspace?: boolean,
   *   style?: string,
   *   children?: import('svelte').Snippet,
   *   [key: string]: any
   * }}
   */
  let {
    ref = $bindable(null),
    class: className,
    gradientSeed = undefined,
    workspace = false,
    style: callerStyle = '',
    ...restProps
  } = $props();

  const bg = $derived(workspace ? WORKSPACE_GRADIENT : gradientFor(gradientSeed));
  const styleValue = $derived(`background-image: ${bg};${callerStyle ? ' ' + callerStyle : ''}`);
</script>

<AvatarPrimitive.Fallback
  bind:ref
  data-slot="avatar-fallback"
  class={cn(
    'flex size-full items-center justify-center rounded-full',
    'text-white font-semibold leading-none',
    className
  )}
  style={styleValue}
  {...restProps}
/>
