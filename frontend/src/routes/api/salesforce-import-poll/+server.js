import { apiRequest } from '$lib/api-helpers.js';
import { json } from '@sveltejs/kit';

/** @type {import('./$types').RequestHandler} */
export async function GET({ url, cookies }) {
  const jobId = url.searchParams.get('job');

  try {
    const [jobResult, historyResult] = await Promise.all([
      jobId
        ? apiRequest(`/salesforce/import/${jobId}/`, {}, { cookies })
        : Promise.resolve(null),
      apiRequest('/salesforce/import/history/', {}, { cookies })
    ]);

    return json({
      job: jobResult?.job || jobResult || null,
      jobs: historyResult?.jobs || []
    });
  } catch {
    return json({ job: null, jobs: [] }, { status: 500 });
  }
}
