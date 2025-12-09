<script>
  import { Dialog as DialogPrimitive } from 'bits-ui';

  let { open = $bindable(false), ...restProps } = $props();
</script>

<DialogPrimitive.Root bind:open {...restProps} />
