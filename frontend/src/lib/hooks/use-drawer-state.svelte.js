import { goto } from '$app/navigation';

/**
 * @typedef {Object} DrawerStateOptions
 * @property {import('@sveltejs/kit').Page} [page] - SvelteKit page store for URL sync
 * @property {boolean} [syncUrl=false] - Whether to sync drawer state with URL
 */

/**
 * Creates reactive drawer state management for list pages
 * @param {DrawerStateOptions} [options={}]
 */
export function useDrawerState(options = {}) {
  const { page, syncUrl = false } = options;

  // Core state
  let detailOpen = $state(false);
  let formOpen = $state(false);
  /** @type {any} */
  let selected = $state(null);
  let mode = $state(/** @type {'create' | 'edit'} */ ('create'));
  let loading = $state(false);

  /**
   * Update URL without triggering navigation
   * @param {string | null} viewId
   * @param {string | null} action
   */
  function updateUrl(viewId, action) {
    if (!syncUrl || !page) return;

    const url = new URL(page.url);
    if (viewId) {
      url.searchParams.set('view', viewId);
      url.searchParams.delete('action');
    } else if (action) {
      url.searchParams.set('action', action);
      url.searchParams.delete('view');
    } else {
      url.searchParams.delete('view');
      url.searchParams.delete('action');
    }
    goto(url.toString(), { replaceState: true, noScroll: true });
  }

  /**
   * Open detail drawer with item
   * @param {any} item
   */
  function openDetail(item) {
    selected = item;
    mode = 'edit'; // Set to edit mode (view with inline editing)
    detailOpen = true;
    updateUrl(item?.id, null);
  }

  /**
   * Open create form
   */
  function openCreate() {
    selected = null;
    mode = 'create';
    detailOpen = true;
    formOpen = true;
    updateUrl(null, 'create');
  }

  /**
   * Open edit form (switches from detail to form)
   */
  function openEdit() {
    mode = 'edit';
    detailOpen = false;
    formOpen = true;
  }

  /**
   * Close detail drawer
   */
  function closeDetail() {
    detailOpen = false;
    updateUrl(null, null);
  }

  /**
   * Close form drawer
   */
  function closeForm() {
    formOpen = false;
    updateUrl(null, null);
  }

  /**
   * Close all drawers
   */
  function closeAll() {
    detailOpen = false;
    formOpen = false;
    updateUrl(null, null);
  }

  /**
   * Handle detail drawer open state change
   * @param {boolean} open
   */
  function handleDetailChange(open) {
    detailOpen = open;
    if (!open) updateUrl(null, null);
  }

  /**
   * Handle form drawer open state change
   * @param {boolean} open
   */
  function handleFormChange(open) {
    formOpen = open;
    if (!open) updateUrl(null, null);
  }

  /**
   * Initialize URL sync - call this with an effect and provide items list
   * @param {any[]} items - List of items to search for viewId
   */
  function initUrlSync(items) {
    if (!syncUrl || !page) return;

    const viewId = page.url.searchParams.get('view');
    const action = page.url.searchParams.get('action');

    if (action === 'create') {
      selected = null;
      mode = 'create';
      detailOpen = true;
      formOpen = true;
    } else if (viewId) {
      const item = items.find((i) => i.id === viewId);
      if (item) {
        selected = item;
        detailOpen = true;
      }
    }
  }

  return {
    // State getters/setters
    get detailOpen() {
      return detailOpen;
    },
    set detailOpen(v) {
      detailOpen = v;
    },
    get formOpen() {
      return formOpen;
    },
    set formOpen(v) {
      formOpen = v;
    },
    get selected() {
      return selected;
    },
    set selected(v) {
      selected = v;
    },
    get mode() {
      return mode;
    },
    set mode(v) {
      mode = v;
    },
    get loading() {
      return loading;
    },
    set loading(v) {
      loading = v;
    },

    // Actions
    openDetail,
    openCreate,
    openEdit,
    closeDetail,
    closeForm,
    closeAll,
    handleDetailChange,
    handleFormChange,
    initUrlSync
  };
}
