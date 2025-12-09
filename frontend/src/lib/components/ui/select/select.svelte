<script>
  import { Select as SelectPrimitive } from 'bits-ui';

  let {
    open = $bindable(false),
    value = $bindable(),
    type = /** @type {"single" | "multiple"} */ ('single'),
    ...restProps
  } = $props();
</script>

<SelectPrimitive.Root bind:open bind:value {type} {...restProps} />
