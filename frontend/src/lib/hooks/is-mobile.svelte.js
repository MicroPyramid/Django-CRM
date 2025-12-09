import { MediaQuery } from 'svelte/reactivity';

const MOBILE_BREAKPOINT = 768;

/**
 * A reactive class that tracks whether the viewport is mobile-sized.
 * Uses Svelte 5's MediaQuery to reactively check the viewport width.
 */
export class IsMobile extends MediaQuery {
  constructor() {
    super(`(max-width: ${MOBILE_BREAKPOINT - 1}px)`);
  }
}
