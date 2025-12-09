/**
 * API Helper Functions
 *
 * Shared utilities for making API requests to Django backend.
 * Used by SvelteKit server files during migration from Prisma to API.
 */

import { env } from '$env/dynamic/public';

const API_BASE_URL = `${env.PUBLIC_DJANGO_API_URL}/api`;

/**
 * @typedef {import('@sveltejs/kit').Cookies} Cookies
 */

/**
 * Make authenticated API request to Django backend
 *
 * This helper is designed for SvelteKit server-side use, where cookies
 * are managed by hooks and locals contains the user and org context.
 *
 * @param {string} endpoint - API endpoint (e.g., '/accounts/', '/leads/123/')
 * @param {{ method?: string, body?: Record<string, unknown>, headers?: Record<string, string> }} options - Fetch options
 * @param {{ cookies?: Cookies, org?: { id: string } } | Cookies} locals - SvelteKit locals object or cookies directly
 * @returns {Promise<any>} Response data
 * @throws {Error} If request fails
 */
export async function apiRequest(endpoint, options = {}, locals) {
  const { method = 'GET', body, headers = {} } = options;

  // Get access token from cookies (server-side)
  // In server load functions, cookies is passed directly
  /** @type {Cookies | undefined} */
  const cookies = /** @type {Cookies | undefined} */ (
    /** @type {{ cookies?: Cookies }} */ (locals).cookies || locals
  );
  // Support both naming conventions (jwt_access from login, access_token from legacy)
  const accessToken = cookies?.get?.('jwt_access') || cookies?.get?.('access_token');

  // Build request headers
  /** @type {Record<string, string>} */
  const requestHeaders = {
    'Content-Type': 'application/json',
    ...headers
  };

  // Add authentication
  // Note: Organization context is now embedded in JWT token, not sent as header
  if (accessToken) {
    requestHeaders['Authorization'] = `Bearer ${accessToken}`;
  }

  // Build request options
  /** @type {RequestInit} */
  const requestOptions = {
    method,
    headers: requestHeaders
  };

  // Add body for non-GET requests
  if (body && method !== 'GET') {
    requestOptions.body = JSON.stringify(body);
  }

  const url = `${API_BASE_URL}${endpoint}`;

  try {
    const response = await fetch(url, requestOptions);

    // Handle error responses
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));

      // Extract meaningful error message from various Django error formats
      let errorMessage = `HTTP ${response.status}: ${response.statusText}`;

      if (errorData.detail) {
        errorMessage = errorData.detail;
      } else if (errorData.error && typeof errorData.error === 'string') {
        errorMessage = errorData.error;
      } else if (errorData.errors && typeof errorData.errors === 'object') {
        // Handle field-level errors
        const fieldErrors = Object.entries(errorData.errors)
          .map(([field, msgs]) => `${field}: ${Array.isArray(msgs) ? msgs.join(', ') : msgs}`)
          .join('; ');
        errorMessage = fieldErrors || errorMessage;
      } else if (errorData.non_field_errors) {
        errorMessage = Array.isArray(errorData.non_field_errors)
          ? errorData.non_field_errors.join(', ')
          : errorData.non_field_errors;
      } else if (typeof errorData === 'object' && Object.keys(errorData).length > 0) {
        // Handle field-level validation errors from DRF serializers
        const fieldErrors = Object.entries(errorData)
          .filter(([key, value]) => key !== 'error' || typeof value === 'string')
          .map(([field, msgs]) => {
            if (Array.isArray(msgs)) {
              return `${field}: ${msgs.join(', ')}`;
            } else if (typeof msgs === 'string') {
              return `${field}: ${msgs}`;
            }
            return null;
          })
          .filter(Boolean)
          .join('; ');
        if (fieldErrors) {
          errorMessage = fieldErrors;
        }
      }

      console.error(`API Error Response:`, errorData);
      throw new Error(errorMessage);
    }

    // Handle 204 No Content
    if (response.status === 204) {
      return null;
    }

    // Return JSON response
    return await response.json();
  } catch (error) {
    console.error(`API request failed: ${method} ${endpoint}`, error);
    throw error;
  }
}

/**
 * Transform Django field names to camelCase for SvelteKit
 *
 * @param {any} obj - Django object with snake_case fields
 * @returns {any} Object with camelCase fields
 */
export function transformFromDjango(obj) {
  if (!obj) return obj;
  if (Array.isArray(obj)) return obj.map(transformFromDjango);
  if (typeof obj !== 'object') return obj;

  /** @type {Record<string, unknown>} */
  const transformed = {};
  for (const [key, value] of Object.entries(obj)) {
    const camelKey = key.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase());
    transformed[camelKey] = typeof value === 'object' ? transformFromDjango(value) : value;
  }
  return transformed;
}

/**
 * Transform camelCase field names to Django snake_case
 *
 * @param {any} obj - SvelteKit object with camelCase fields
 * @returns {any} Object with snake_case fields
 */
export function transformToDjango(obj) {
  if (!obj) return obj;
  if (Array.isArray(obj)) return obj.map(transformToDjango);
  if (typeof obj !== 'object') return obj;

  /** @type {Record<string, unknown>} */
  const transformed = {};
  for (const [key, value] of Object.entries(obj)) {
    const snakeKey = key.replace(/[A-Z]/g, (letter) => `_${letter.toLowerCase()}`);
    transformed[snakeKey] = typeof value === 'object' ? transformToDjango(value) : value;
  }
  return transformed;
}

/**
 * Build Django query parameters from filter object
 *
 * @param {Object} filters - Filter object
 * @param {number} [filters.page] - Page number (1-indexed)
 * @param {number} [filters.limit] - Items per page
 * @param {string} [filters.sort] - Sort field name
 * @param {string} [filters.order] - Sort order ('asc' or 'desc')
 * @returns {URLSearchParams} Query parameters for Django API
 */
export function buildQueryParams(filters = {}) {
  const { page = 1, limit = 10, sort, order = 'asc', ...otherFilters } = filters;

  const params = new URLSearchParams();

  // Pagination
  params.append('limit', limit.toString());
  params.append('offset', ((page - 1) * limit).toString());

  // Sorting (Django uses - prefix for descending)
  if (sort) {
    const ordering = order === 'desc' ? `-${sort}` : sort;
    params.append('ordering', ordering);
  }

  // Other filters
  for (const [key, value] of Object.entries(otherFilters)) {
    if (value !== null && value !== undefined && value !== '') {
      params.append(key, value.toString());
    }
  }

  return params;
}

/**
 * Extract pagination info from Django response
 *
 * @param {{ count?: number, next?: string | null, previous?: string | null, results?: unknown[] }} response - Django paginated response
 * @param {number} [limit=10] - Items per page
 * @returns {{ page: number, limit: number, total: number, totalPages: number, hasNext: boolean, hasPrevious: boolean }} Pagination info compatible with SvelteKit
 */
export function extractPagination(response, limit = 10) {
  const total = response.count || 0;
  const totalPages = Math.ceil(total / limit);

  // Determine current page from offset in next/previous URLs
  let currentPage = 1;
  if (response.next) {
    const url = new URL(response.next, 'http://localhost');
    const offset = parseInt(url.searchParams.get('offset') || '0');
    currentPage = Math.floor(offset / limit);
  } else if (response.previous) {
    const url = new URL(response.previous, 'http://localhost');
    const offset = parseInt(url.searchParams.get('offset') || '0');
    currentPage = Math.floor(offset / limit) + 2;
  }

  return {
    page: currentPage,
    limit,
    total,
    totalPages,
    hasNext: response.next !== null,
    hasPrevious: response.previous !== null
  };
}
