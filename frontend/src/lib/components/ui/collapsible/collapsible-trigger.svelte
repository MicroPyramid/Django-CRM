<script>
	import { Collapsible as CollapsiblePrimitive } from 'bits-ui';

	let { ref = $bindable(null), ...restProps } = $props();
</script>

<CollapsiblePrimitive.Trigger bind:ref data-slot="collapsible-trigger" {...restProps} />
