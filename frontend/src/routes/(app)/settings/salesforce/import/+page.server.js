import { apiRequest } from '$lib/api-helpers.js';
import { redirect, fail } from '@sveltejs/kit';

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

/** @type {import('./$types').PageServerLoad} */
export async function load({ cookies, url }) {
  let status;
  try {
    status = await apiRequest('/salesforce/status/', {}, { cookies });
  } catch {
    throw redirect(302, '/settings/salesforce');
  }

  if (!status?.connected) {
    throw redirect(302, '/settings/salesforce');
  }

  let history = { jobs: [] };
  try {
    history = await apiRequest('/salesforce/import/history/', {}, { cookies });
  } catch {
    /* ignore history fetch failure */
  }

  const jobs = history.jobs || [];

  // Determine active job: explicit ?job= param, or auto-detect from history
  const jobIdParam = url.searchParams.get('job');
  let activeJob = null;

  if (jobIdParam && UUID_RE.test(jobIdParam)) {
    try {
      const result = await apiRequest(`/salesforce/import/${jobIdParam}/`, {}, { cookies });
      activeJob = result.job || result;
    } catch {
      /* job may have been deleted or is inaccessible */
    }
  }

  // Auto-detect: if no explicit job param, find any running job from history
  // Skip jobs that have been running for over 60 minutes (likely crashed workers)
  if (!activeJob) {
    const STALE_MS = 60 * 60 * 1000;
    const now = Date.now();
    const runningJob = jobs.find((/** @type {any} */ j) => {
      if (j.status !== 'PENDING' && j.status !== 'IN_PROGRESS') return false;
      const startedAt = j.started_at || j.created_at;
      if (startedAt) {
        const startMs = new Date(startedAt).getTime();
        if (isNaN(startMs) || now - startMs > STALE_MS) return false;
      }
      return true;
    });
    if (runningJob) {
      activeJob = runningJob;
    }
  }

  return {
    sfStatus: status,
    importHistory: jobs,
    activeJob
  };
}

/** @type {import('./$types').Actions} */
export const actions = {
  startImport: async ({ request, cookies }) => {
    const formData = await request.formData();
    const objectTypesRaw = formData.get('object_types')?.toString();

    if (!objectTypesRaw) {
      return fail(400, { importError: 'Please select at least one object type.' });
    }

    const objectTypes = objectTypesRaw.split(',').filter(Boolean);
    if (objectTypes.length === 0) {
      return fail(400, { importError: 'Please select at least one object type.' });
    }

    try {
      const result = await apiRequest(
        '/salesforce/import/',
        { method: 'POST', body: { object_types: objectTypes } },
        { cookies }
      );
      const jobId = result.job?.id || result.id;
      return { importStarted: true, jobId };
    } catch (err) {
      return fail(400, { importError: err?.message || 'Failed to start import.' });
    }
  },
  cancelImport: async ({ request, cookies }) => {
    const formData = await request.formData();
    const jobId = formData.get('job_id')?.toString();

    if (!jobId) {
      return fail(400, { importError: 'No job ID provided.' });
    }

    if (!UUID_RE.test(jobId)) {
      return fail(400, { importError: 'Invalid job ID.' });
    }

    try {
      await apiRequest(
        `/salesforce/import/${jobId}/cancel/`,
        { method: 'POST' },
        { cookies }
      );
      return { importCancelled: true };
    } catch (err) {
      return fail(400, { importError: err?.message || 'Failed to cancel import.' });
    }
  }
};
