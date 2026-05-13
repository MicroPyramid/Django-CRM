import { writable } from 'svelte/store';

const STORAGE_KEY = 'bottlecrm:side-panel-hidden';

function readInitial() {
  if (typeof sessionStorage === 'undefined') return false;
  try {
    return sessionStorage.getItem(STORAGE_KEY) === '1';
  } catch {
    return false;
  }
}

export const sidePanelHidden = writable(readInitial());

if (typeof window !== 'undefined') {
  sidePanelHidden.subscribe((v) => {
    try {
      sessionStorage.setItem(STORAGE_KEY, v ? '1' : '0');
    } catch {
      /* private mode / storage disabled */
    }
  });
}

export { default as SidePanel } from './SidePanel.svelte';
export { default as SidePanelSection } from './SidePanelSection.svelte';
