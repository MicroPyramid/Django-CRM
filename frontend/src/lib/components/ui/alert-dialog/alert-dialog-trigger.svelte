<script>
	import { AlertDialog as AlertDialogPrimitive } from 'bits-ui';

	let { ref = $bindable(null), ...restProps } = $props();
</script>

<AlertDialogPrimitive.Trigger bind:ref data-slot="alert-dialog-trigger" {...restProps} />
