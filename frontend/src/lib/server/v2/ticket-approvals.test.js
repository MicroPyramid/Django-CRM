import { describe, it, expect, vi, beforeEach } from 'vitest';

const apiRequest = vi.fn();
vi.mock('$lib/api-helpers.js', () => ({ apiRequest: (...a) => apiRequest(...a) }));

const { createApprovalRule, updateApprovalRule, deleteApprovalRule } =
  await import('./ticket-approvals.js');

const cookies = /** @type {any} */ ({ get: () => 'token' });
const event = /** @type {any} */ ({ cookies });

const base = {
  name: 'Urgent close needs a manager',
  match_priority: 'Urgent',
  match_case_type: 'Incident',
  match_team_id: 't1',
  approver_role: 'ADMIN',
  approver_ids: ['p1', 'p2'],
  is_active: true
};

describe('createApprovalRule', () => {
  beforeEach(() => {
    apiRequest.mockReset();
  });

  it('sends only allow-listed keys on create and drops a hostile org', async () => {
    apiRequest.mockResolvedValue({});
    await createApprovalRule(event, {
      ...base,
      org: 'ATTACKER-ORG',
      created_by: 'ATTACKER'
    });
    const [url, opts] = apiRequest.mock.calls[0];
    expect(url).toBe('/cases/approval-rules/');
    expect(opts.method).toBe('POST');
    expect(Object.keys(opts.body).sort()).toEqual([
      'approver_ids',
      'approver_role',
      'is_active',
      'match_case_type',
      'match_priority',
      'match_team_id',
      'name',
      'trigger_event'
    ]);
    expect(opts.body.org).toBeUndefined();
    expect(opts.body.created_by).toBeUndefined();
  });

  it('always sends trigger_event as pre_close, ignoring any caller-supplied value', async () => {
    apiRequest.mockResolvedValue({});
    await createApprovalRule(event, { ...base, trigger_event: 'post_close' });
    const { body } = apiRequest.mock.calls[0][1];
    expect(body.trigger_event).toBe('pre_close');
  });

  it('sends null, not an empty string, for an unselected match_priority', async () => {
    apiRequest.mockResolvedValue({});
    await createApprovalRule(event, { ...base, match_priority: '' });
    const { body } = apiRequest.mock.calls[0][1];
    expect(body.match_priority).toBeNull();
  });

  it('sends null, not an empty string, for an unselected match_case_type', async () => {
    apiRequest.mockResolvedValue({});
    await createApprovalRule(event, { ...base, match_case_type: '' });
    const { body } = apiRequest.mock.calls[0][1];
    expect(body.match_case_type).toBeNull();
  });

  it('sends null, not an empty string, for an unselected match_team_id', async () => {
    apiRequest.mockResolvedValue({});
    await createApprovalRule(event, { ...base, match_team_id: '' });
    const { body } = apiRequest.mock.calls[0][1];
    expect(body.match_team_id).toBeNull();
  });

  it('filters blank entries out of approver_ids', async () => {
    apiRequest.mockResolvedValue({});
    await createApprovalRule(event, {
      ...base,
      approver_ids: ['p1', '', null, 'p2']
    });
    const { body } = apiRequest.mock.calls[0][1];
    expect(body.approver_ids).toEqual(['p1', 'p2']);
  });

  it('coerces is_active to a boolean', async () => {
    apiRequest.mockResolvedValue({});
    await createApprovalRule(event, { ...base, is_active: 'true' });
    const { body } = apiRequest.mock.calls[0][1];
    expect(body.is_active).toBe(true);
    expect(typeof body.is_active).toBe('boolean');
  });

  it('refuses a rule with no name before making a request', async () => {
    await expect(createApprovalRule(event, { ...base, name: '' })).rejects.toThrow(/needs a name/i);
    expect(apiRequest).not.toHaveBeenCalled();
  });
});

describe('updateApprovalRule', () => {
  beforeEach(() => {
    apiRequest.mockReset();
  });

  it('PUTs to the detail endpoint', async () => {
    apiRequest.mockResolvedValue({});
    await updateApprovalRule(event, 'r1', base);
    const [url, opts] = apiRequest.mock.calls[0];
    expect(url).toBe('/cases/approval-rules/r1/');
    expect(opts.method).toBe('PUT');
  });

  it('sends only what it is given, with no trigger_event and no org/created_by', async () => {
    apiRequest.mockResolvedValue({});
    await updateApprovalRule(event, 'r1', {
      ...base,
      org: 'ATTACKER-ORG',
      created_by: 'ATTACKER'
    });
    const { body } = apiRequest.mock.calls[0][1];
    expect(Object.keys(body).sort()).toEqual([
      'approver_ids',
      'approver_role',
      'is_active',
      'match_case_type',
      'match_priority',
      'match_team_id',
      'name'
    ]);
    expect(body.trigger_event).toBeUndefined();
    expect(body.org).toBeUndefined();
    expect(body.created_by).toBeUndefined();
  });

  it('sends exactly one key for a minimal { is_active: true } body (the turn-on path)', async () => {
    apiRequest.mockResolvedValue({});
    await updateApprovalRule(event, 'r1', { is_active: true });
    const { body } = apiRequest.mock.calls[0][1];
    expect(body).toEqual({ is_active: true });
  });

  it('sends exactly one key for a minimal { is_active: false } body (the turn-off path)', async () => {
    apiRequest.mockResolvedValue({});
    await updateApprovalRule(event, 'r1', { is_active: false });
    const { body } = apiRequest.mock.calls[0][1];
    expect(body).toEqual({ is_active: false });
  });

  it('throws when the id is missing', async () => {
    await expect(updateApprovalRule(event, '', base)).rejects.toThrow(/which rule/i);
    expect(apiRequest).not.toHaveBeenCalled();
  });
});

describe('deleteApprovalRule', () => {
  beforeEach(() => {
    apiRequest.mockReset();
  });

  it('DELETEs the detail endpoint', async () => {
    apiRequest.mockResolvedValue(null);
    await deleteApprovalRule(event, 'r1');
    const [url, opts] = apiRequest.mock.calls[0];
    expect(url).toBe('/cases/approval-rules/r1/');
    expect(opts.method).toBe('DELETE');
  });

  it('reports a real delete when the response carries no body', async () => {
    // `ApprovalRuleDetailView.delete` answers 204 on the hard-delete branch,
    // and `apiRequest` turns a 204 into `null`.
    apiRequest.mockResolvedValue(null);
    await expect(deleteApprovalRule(event, 'r1')).resolves.toEqual({ turned_off: false });
  });

  it('reports a soft disable when the response says is_active is false', async () => {
    // The other branch: `rule.requests.exists()` is true, so the view sets
    // `is_active = False` and answers 200 with `{ id, is_active: false }`.
    // Nothing about the status code distinguishes the two for a caller that
    // only checks "did it throw", which is how the page came to promise a
    // permanence the backend never delivered.
    apiRequest.mockResolvedValue({ id: 'r1', is_active: false });
    await expect(deleteApprovalRule(event, 'r1')).resolves.toEqual({ turned_off: true });
  });

  it('does not read a soft disable out of an unrelated 200 body', async () => {
    apiRequest.mockResolvedValue({ id: 'r1' });
    await expect(deleteApprovalRule(event, 'r1')).resolves.toEqual({ turned_off: false });
  });

  it('throws when the id is missing', async () => {
    await expect(deleteApprovalRule(event, '')).rejects.toThrow(/which rule/i);
    expect(apiRequest).not.toHaveBeenCalled();
  });
});
