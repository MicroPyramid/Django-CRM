<script>
  import { initials } from '$lib/v2/format.js';

  /** @type {{ name: string, size?: number }} */
  let { name, size = 26 } = $props();
</script>

<span
  class="v2-avatar"
  style="width:{size}px;height:{size}px;font-size:{(size * 0.38).toFixed(1)}px"
  title={name}
  aria-hidden="true">{initials(name)}</span
>
