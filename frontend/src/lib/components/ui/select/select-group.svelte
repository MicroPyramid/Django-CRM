<script>
	import { Select as SelectPrimitive } from "bits-ui";

	let { ref = $bindable(null), ...restProps } = $props();
</script>

<SelectPrimitive.Group data-slot="select-group" {...restProps} />