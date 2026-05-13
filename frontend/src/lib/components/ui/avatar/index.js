import Root from './avatar.svelte';
import Image from './avatar-image.svelte';
import Fallback from './avatar-fallback.svelte';

export {
  Root,
  Image,
  Fallback,
  //
  Root as Avatar,
  Image as AvatarImage,
  Fallback as AvatarFallback
};
export { gradientFor, AVATAR_GRADIENTS, WORKSPACE_GRADIENT } from './avatar-gradients.js';
