<script>
	import { Dialog as SheetPrimitive } from 'bits-ui';

	let { ref = $bindable(null), ...restProps } = $props();
</script>

<SheetPrimitive.Close bind:ref data-slot="sheet-close" {...restProps} />
