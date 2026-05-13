import { error, fail, redirect } from '@sveltejs/kit';
import { apiRequest } from '$lib/api-helpers.js';

/** @type {import('./$types').PageServerLoad} */
export async function load({ params, locals, cookies, url }) {
  const org = locals.org;
  if (!org) throw error(401, 'Organization context required');

  try {
    // Cheap probe: if this ticket is a merged duplicate, the backend returns
    // `{redirect_to: <primary_id>, ...}` rather than the full payload —
    // redirect server-side so we don't waste time fetching form options.
    // Pass `?show_merged=true` through to allow the audit escape hatch.
    const showMerged = url.searchParams.get('show_merged') === 'true';
    const detailPath = showMerged
      ? `/cases/${params.id}/?show_merged=true`
      : `/cases/${params.id}/`;
    const detail = await apiRequest(detailPath, {}, { cookies, org });

    if (detail && detail.redirect_to && !showMerged) {
      throw redirect(
        303,
        `/tickets/${detail.redirect_to}?from=${encodeURIComponent(detail.source_case_id || '')}`
      );
    }

    const [
      accountsRes,
      usersRes,
      contactsRes,
      teamsRes,
      tagsRes,
      solutionsRes,
      watchersRes,
      approvalsRes
    ] = await Promise.all([
      apiRequest('/accounts/', {}, { cookies, org }).catch(() => ({})),
      apiRequest('/users/', {}, { cookies, org }).catch(() => ({})),
      apiRequest('/contacts/', {}, { cookies, org }).catch(() => ({})),
      apiRequest('/teams/', {}, { cookies, org }).catch(() => ({})),
      apiRequest('/tags/', {}, { cookies, org }).catch(() => ({})),
      apiRequest(
        '/cases/solutions/?is_published=true&limit=200',
        {},
        { cookies, org }
      ).catch((e) => {
        console.warn('Solutions picker fetch failed:', e?.message);
        return {};
      }),
      apiRequest(`/cases/${params.id}/watchers/`, {}, { cookies, org }).catch(() => ({})),
      apiRequest(
        `/cases/approvals/?case=${params.id}&state=all`,
        {},
        { cookies, org }
      ).catch(() => ({}))
    ]);

    if (!detail || !detail.cases_obj) throw error(404, 'Ticket not found');

    const c = detail.cases_obj;
    const routedActivity = (detail.activities || []).find(
      (/** @type {any} */ a) => a.action === 'ROUTED' && !a.metadata?.reason
    );
    const mergedFromTickets = (detail.merged_from_cases || []).map(
      (/** @type {any} */ m) => ({
        id: m.id,
        name: m.name,
        mergedAt: m.merged_at
      })
    );
    const transformed = {
      id: c.id,
      subject: c.name,
      description: c.description,
      status: c.status,
      priority: c.priority,
      ticketType: c.case_type,
      closedOn: c.closed_on,
      createdAt: c.created_at,
      updatedAt: c.updated_at,
      escalationCount: c.escalation_count || 0,
      lastEscalationFiredAt: c.last_escalation_fired_at,
      routedByRuleName: routedActivity?.metadata?.rule_name || null,
      mergedInto: c.merged_into || null,
      mergedAt: c.merged_at || null,
      mergedFromTickets,
      account: c.account ? { id: c.account.id, name: c.account.name } : null,
      assignedTo: (c.assigned_to || []).map((p) => ({
        id: p.id,
        name:
          p.user_details?.first_name && p.user_details?.last_name
            ? `${p.user_details.first_name} ${p.user_details.last_name}`
            : p.user_details?.email || p.email
      })),
      contacts: (c.contacts || detail.contacts || []).map((ct) => ({
        id: ct.id,
        name:
          ct.first_name && ct.last_name ? `${ct.first_name} ${ct.last_name}` : ct.email,
        email: ct.email
      })),
      teams: (c.teams || []).map((t) => ({ id: t.id, name: t.name })),
      tags: (c.tags || []).map((t) => ({ id: t.id, name: t.name })),
      sla: {
        firstResponseDeadline: c.first_response_sla_deadline,
        resolutionDeadline: c.resolution_sla_deadline,
        firstResponseAt: c.first_response_at,
        resolvedAt: c.resolved_at,
        firstResponseBreached: c.is_sla_first_response_breached,
        resolutionBreached: c.is_sla_resolution_breached,
        pausedAt: c.sla_paused_at,
        firstResponseHours: c.sla_first_response_hours,
        resolutionHours: c.sla_resolution_hours
      },
      isProblem: !!c.is_problem,
      parentSummary: c.parent_summary
        ? {
            id: c.parent_summary.id,
            name: c.parent_summary.name,
            status: c.parent_summary.status
          }
        : null,
      childCount: c.child_count || 0,
      timeSummary: c.time_summary || {
        total_minutes: 0,
        billable_minutes: 0,
        last_entry_at: null,
        by_profile: []
      }
    };

    return {
      ticketItem: transformed,
      customFieldDefinitions: detail.custom_field_definitions || [],
      customFieldValues: c.custom_fields || {},
      comments: detail.comments || [],
      internalNotes: detail.internal_notes || [],
      activities: detail.activities || [],
      attachments: detail.attachments || [],
      inboundEmails: detail.email_messages || [],
      linkedSolutions: detail.solutions || [],
      availableSolutions: solutionsRes.results || solutionsRes.solutions || [],
      watchers: watchersRes.watchers || [],
      approvals: approvalsRes.approvals || [],
      currentUserId: locals.user?.id || null,
      currentProfileId: /** @type {any} */ (locals).profile?.id || null,
      isAdmin: /** @type {any} */ (locals).profile?.role === 'ADMIN',
      mentionCandidates: (usersRes.active_users?.active_users || [])
        .map((u) => {
          const email = u.user_details?.email || u.email || '';
          const local = email.split('@')[0];
          if (!local) return null;
          return { username: local, id: u.id, email };
        })
        .filter(Boolean),
      formOptions: {
        accounts: (
          accountsRes.active_accounts?.open_accounts ||
          accountsRes.results ||
          []
        ).map((a) => ({ id: a.id, name: a.name })),
        users: (usersRes.active_users?.active_users || []).map((u) => ({
          id: u.id,
          name:
            u.user_details?.first_name && u.user_details?.last_name
              ? `${u.user_details.first_name} ${u.user_details.last_name}`
              : u.user_details?.email || u.email
        })),
        contacts: (contactsRes.contact_obj_list || contactsRes.results || []).map(
          (ct) => ({
            id: ct.id,
            name:
              ct.first_name && ct.last_name
                ? `${ct.first_name} ${ct.last_name}`
                : ct.email,
            email: ct.email
          })
        ),
        teams: (teamsRes.teams || teamsRes.results || []).map((t) => ({
          id: t.id,
          name: t.name
        })),
        tags: (tagsRes.tags || tagsRes.results || []).map((t) => ({
          id: t.id,
          name: t.name,
          color: t.color || 'blue'
        }))
      }
    };
  } catch (err) {
    if (err.status) throw err;
    console.error('Error loading ticket detail:', err);
    throw error(500, `Failed to load ticket: ${err.message}`);
  }
}

/** @type {import('./$types').Actions} */
export const actions = {
  update: async ({ request, params, locals, cookies }) => {
    try {
      const form = await request.formData();
      /** @type {Record<string, unknown>} */
      const body = {};
      for (const k of ['name', 'description', 'priority', 'status', 'case_type', 'closed_on']) {
        if (form.has(k)) body[k] = form.get(k)?.toString() || null;
      }
      for (const k of ['assigned_to', 'contacts', 'teams', 'tags']) {
        const json = form.get(k)?.toString();
        if (json) body[k] = JSON.parse(json);
      }
      await apiRequest(
        `/cases/${params.id}/`,
        { method: 'PATCH', body },
        { cookies, org: locals.org }
      );
      return { success: true };
    } catch (err) {
      console.error('Update ticket error:', err);
      return fail(500, { error: 'Failed to update ticket' });
    }
  },

  linkSolution: async ({ request, params, locals, cookies }) => {
    const form = await request.formData();
    const solutionId = form.get('solutionId')?.toString();
    if (!solutionId) return fail(400, { error: 'solutionId required' });
    try {
      await apiRequest(
        `/cases/${params.id}/solutions/`,
        { method: 'POST', body: { solution_id: solutionId } },
        { cookies, org: locals.org }
      );
      return { success: true };
    } catch (err) {
      console.error('Link solution error:', err);
      return fail(500, { error: 'Failed to link solution' });
    }
  },

  unlinkSolution: async ({ request, params, locals, cookies }) => {
    const form = await request.formData();
    const solutionId = form.get('solutionId')?.toString();
    if (!solutionId) return fail(400, { error: 'solutionId required' });
    try {
      await apiRequest(
        `/cases/${params.id}/solutions/${solutionId}/`,
        { method: 'DELETE' },
        { cookies, org: locals.org }
      );
      return { success: true };
    } catch (err) {
      console.error('Unlink solution error:', err);
      return fail(500, { error: 'Failed to unlink solution' });
    }
  },

  updateCustomFields: async ({ request, params, locals, cookies }) => {
    const form = await request.formData();
    const raw = form.get('custom_fields')?.toString() || '{}';
    let parsed;
    try {
      parsed = JSON.parse(raw);
    } catch {
      return fail(400, { error: 'Malformed custom_fields payload' });
    }
    try {
      await apiRequest(
        `/cases/${params.id}/`,
        { method: 'PATCH', body: { custom_fields: parsed } },
        { cookies, org: locals.org }
      );
      return { success: true };
    } catch (err) {
      console.error('Update custom fields error:', err);
      return fail(400, { error: err?.message || 'Failed to save custom fields' });
    }
  },

  merge: async ({ request, params, locals, cookies }) => {
    const form = await request.formData();
    const intoId = form.get('into_id')?.toString();
    if (!intoId) return fail(400, { error: 'Target ticket is required' });
    if (intoId === params.id) {
      return fail(400, { error: 'Cannot merge a ticket into itself' });
    }
    try {
      const result = await apiRequest(
        `/cases/${params.id}/merge/${intoId}/`,
        { method: 'POST', body: {} },
        { cookies, org: locals.org }
      );
      return {
        success: true,
        merged: true,
        targetId: intoId,
        sourceId: params.id,
        alreadyMerged: !!result?.already_merged
      };
    } catch (err) {
      const msg = err?.message || 'Failed to merge tickets';
      console.error('Merge ticket error:', err);
      return fail(err?.status || 500, { error: msg });
    }
  },

  unmerge: async ({ request, params, locals, cookies }) => {
    const form = await request.formData();
    // The "Unmerge" button shows up in two places:
    //   - On the source page (the duplicate, accessed with ?show_merged=true).
    //     The form has no `source_id` because params.id IS the source.
    //   - On the target page, in the "Merged from" list (one button per row).
    //     Each row submits its own `source_id` so we know which source to
    //     unmerge from this target.
    const sourceId = form.get('source_id')?.toString() || params.id;
    try {
      await apiRequest(
        `/cases/${sourceId}/unmerge/`,
        { method: 'POST', body: {} },
        { cookies, org: locals.org }
      );
      return { success: true, unmerged: true, sourceId };
    } catch (err) {
      const msg = err?.message || 'Failed to unmerge ticket';
      console.error('Unmerge ticket error:', err);
      return fail(err?.status || 500, { error: msg });
    }
  },

  comment: async ({ request, params, locals, cookies }) => {
    const form = await request.formData();
    const body = form.get('body')?.toString().trim();
    if (!body) return fail(400, { error: 'Comment body required' });
    const isInternal = form.get('is_internal')?.toString() === 'true';
    try {
      await apiRequest(
        `/cases/${params.id}/`,
        {
          method: 'POST',
          body: { comment: body, is_internal: isInternal }
        },
        { cookies, org: locals.org }
      );
      return { success: true, isInternal };
    } catch (err) {
      console.error('Add comment error:', err);
      return fail(500, { error: 'Failed to add comment' });
    }
  }
};
