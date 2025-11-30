import { AlertDialog as AlertDialogPrimitive } from 'bits-ui';
import Trigger from './alert-dialog-trigger.svelte';
import Overlay from './alert-dialog-overlay.svelte';
import Content from './alert-dialog-content.svelte';
import Header from './alert-dialog-header.svelte';
import Footer from './alert-dialog-footer.svelte';
import Title from './alert-dialog-title.svelte';
import Description from './alert-dialog-description.svelte';
import Action from './alert-dialog-action.svelte';
import Cancel from './alert-dialog-cancel.svelte';

const Root = AlertDialogPrimitive.Root;
const Portal = AlertDialogPrimitive.Portal;

export {
	Root,
	Trigger,
	Portal,
	Overlay,
	Content,
	Header,
	Footer,
	Title,
	Description,
	Action,
	Cancel,
	//
	Root as AlertDialog,
	Trigger as AlertDialogTrigger,
	Portal as AlertDialogPortal,
	Overlay as AlertDialogOverlay,
	Content as AlertDialogContent,
	Header as AlertDialogHeader,
	Footer as AlertDialogFooter,
	Title as AlertDialogTitle,
	Description as AlertDialogDescription,
	Action as AlertDialogAction,
	Cancel as AlertDialogCancel
};
