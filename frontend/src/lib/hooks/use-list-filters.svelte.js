/**
 * @typedef {Object} FilterDef
 * @property {string} key - The filter key name
 * @property {any} defaultValue - Default value for this filter
 * @property {(item: any, value: any) => boolean} [match] - Custom match function
 */

/**
 * @typedef {Object} ListFiltersOptions
 * @property {string[]} [searchFields=[]] - Fields to search in
 * @property {FilterDef[]} [filters=[]] - Filter definitions
 * @property {string} [defaultSortColumn='createdAt'] - Default sort column
 * @property {'asc' | 'desc'} [defaultSortDirection='desc'] - Default sort direction
 */

/**
 * Helper function to get nested values like "owner.name"
 * @param {any} obj
 * @param {string} path
 * @returns {any}
 */
function getNestedValue(obj, path) {
  return path.split('.').reduce((current, key) => current?.[key], obj);
}

/**
 * Creates reactive filter, search, and sort state for list pages
 * @param {ListFiltersOptions} [options={}]
 */
export function useListFilters(options = {}) {
  const {
    searchFields = [],
    filters = [],
    defaultSortColumn = 'createdAt',
    defaultSortDirection = 'desc'
  } = options;

  // Search state
  let searchQuery = $state('');
  let showFilters = $state(false);

  // Sort state
  let sortColumn = $state(defaultSortColumn);
  let sortDirection = $state(/** @type {'asc' | 'desc'} */ (defaultSortDirection));

  // Build initial filter state from definitions
  /** @type {Record<string, any>} */
  const initialFilterState = {};
  /** @type {Record<string, any>} */
  const filterDefaults = {};
  for (const filter of filters) {
    initialFilterState[filter.key] = filter.defaultValue;
    filterDefaults[filter.key] = filter.defaultValue;
  }

  // Filter state as a reactive object
  let filterState = $state(initialFilterState);

  /**
   * Toggle sort column/direction
   * @param {string} column
   */
  function toggleSort(column) {
    if (sortColumn === column) {
      sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
    } else {
      sortColumn = column;
      sortDirection = 'desc';
    }
  }

  /**
   * Clear all filters
   */
  function clearFilters() {
    searchQuery = '';
    for (const filter of filters) {
      filterState[filter.key] = filter.defaultValue;
    }
  }

  /**
   * Get count of active filters
   * @returns {number}
   */
  function getActiveFilterCount() {
    let count = 0;
    for (const filter of filters) {
      if (filterState[filter.key] !== filter.defaultValue) {
        count++;
      }
    }
    return count;
  }

  /**
   * Apply search filter to item
   * @param {any} item
   * @returns {boolean}
   */
  function matchesSearch(item) {
    if (searchQuery === '') return true;

    const query = searchQuery.toLowerCase();
    return searchFields.some((field) => {
      const value = getNestedValue(item, field);
      return value && String(value).toLowerCase().includes(query);
    });
  }

  /**
   * Apply custom filters to item
   * @param {any} item
   * @returns {boolean}
   */
  function matchesFilters(item) {
    for (const filter of filters) {
      const filterValue = filterState[filter.key];

      // Skip if filter is at default value
      if (filterValue === filter.defaultValue) continue;

      // Use custom match function if provided
      if (filter.match) {
        if (!filter.match(item, filterValue)) return false;
      } else {
        // Default: direct field comparison
        if (getNestedValue(item, filter.key) !== filterValue) return false;
      }
    }
    return true;
  }

  /**
   * Apply filters to items array
   * @param {any[]} items
   * @returns {any[]}
   */
  function applyFilters(items) {
    return items.filter((item) => matchesSearch(item) && matchesFilters(item));
  }

  /**
   * Apply sorting to items array
   * @param {any[]} items
   * @returns {any[]}
   */
  function applySort(items) {
    return [...items].sort((a, b) => {
      const aValue = getNestedValue(a, sortColumn);
      const bValue = getNestedValue(b, sortColumn);

      if (aValue == null && bValue == null) return 0;
      if (aValue == null) return 1;
      if (bValue == null) return -1;

      const comparison = aValue > bValue ? 1 : aValue < bValue ? -1 : 0;
      return sortDirection === 'asc' ? comparison : -comparison;
    });
  }

  /**
   * Apply both filtering and sorting
   * @param {any[]} items
   * @returns {any[]}
   */
  function filterAndSort(items) {
    return applySort(applyFilters(items));
  }

  return {
    // Search state
    get searchQuery() {
      return searchQuery;
    },
    set searchQuery(v) {
      searchQuery = v;
    },
    get showFilters() {
      return showFilters;
    },
    set showFilters(v) {
      showFilters = v;
    },

    // Sort state
    get sortColumn() {
      return sortColumn;
    },
    set sortColumn(v) {
      sortColumn = v;
    },
    get sortDirection() {
      return sortDirection;
    },
    set sortDirection(v) {
      sortDirection = v;
    },

    // Filter state (reactive object)
    get filters() {
      return filterState;
    },

    // Actions
    toggleSort,
    clearFilters,

    // Computed helpers
    getActiveFilterCount,
    applyFilters,
    applySort,
    filterAndSort
  };
}
