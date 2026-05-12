<script>
  import { cn } from '$lib/utils.js';

  /**
   * @typedef {Object} Props
   * @property {string} label
   * @property {string} [class]
   * @property {import('svelte').Snippet} children
   */

  /** @type {Props} */
  let { label, class: className, children } = $props();
</script>

<section class={cn('flex flex-col gap-2', className)}>
  <h4
    class="text-[10px] font-semibold uppercase tracking-[0.06em] text-[color:var(--text-subtle)]"
  >
    {label}
  </h4>
  <div class="flex flex-col gap-1.5 text-[13px] text-[color:var(--text)]">
    {@render children()}
  </div>
</section>
