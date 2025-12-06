<script>
	import { Dialog as DialogPrimitive } from "bits-ui";

	let { ...restProps } = $props();
</script>

<DialogPrimitive.Portal {...restProps} />