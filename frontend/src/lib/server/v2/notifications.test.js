import { describe, expect, it } from 'vitest';

import { resolvedLink, PRODUCED_VERBS } from './notifications.js';

/**
 * `Notification.link` is a value read out of the database, and it becomes an
 * href. These cases are the reason it is parsed rather than followed.
 */
describe('resolvedLink', () => {
  const id = '4d60686d-bd3d-4e33-b114-ab36f194a6cd';

  it('normalises both CRM ticket spellings to the v2 route', () => {
    expect(resolvedLink(`/tickets/${id}`)).toBe(`/tickets/${id}`);
    expect(resolvedLink(`/cases/${id}`)).toBe(`/tickets/${id}`);
  });

  it('normalises product support to /help, including rows written as /support', () => {
    expect(resolvedLink(`/help/${id}`)).toBe(`/help/${id}`);
    expect(resolvedLink(`/support/${id}`)).toBe(`/help/${id}`);
  });

  it('tolerates a trailing slash on either shape', () => {
    expect(resolvedLink(`/tickets/${id}/`)).toBe(`/tickets/${id}`);
    expect(resolvedLink(`/support/${id}/`)).toBe(`/help/${id}`);
  });

  it.each([
    ['https://evil.example/help/1', 'an absolute URL'],
    ['//evil.example/help/1', 'a protocol-relative URL'],
    ['javascript:alert(1)', 'a javascript: URL'],
    ['/help/1/../../admin', 'a traversal attempt'],
    ['/help/', 'a help path with no id'],
    ['/settings', 'an unrelated internal path'],
    ['', 'an empty string'],
    [null, 'null'],
    [{ toString: () => '/help/1' }, 'a non-string that stringifies']
  ])('refuses %s (%s)', (link, _description) => {
    expect(resolvedLink(/** @type {any} */ (link))).toBe('');
  });

  it('escapes an id so it cannot break out of the path', () => {
    expect(resolvedLink('/help/a b')).toBe('/help/a%20b');
  });
});

describe('automation notifications', () => {
  const id = '4d60686d-bd3d-4e33-b114-ab36f194a6cd';

  it('knows the four automation verbs', () => {
    for (const v of ['message', 'failed', 'paused', 'limit']) {
      expect(PRODUCED_VERBS).toContain(`automation.${v}`);
    }
  });

  it('resolves the record and settings links', () => {
    for (const base of ['leads', 'contacts', 'accounts', 'pipeline', 'tasks', 'tickets']) {
      expect(resolvedLink(`/${base}/${id}`)).toBe(`/${base}/${id}`);
    }
    expect(resolvedLink(`/objects/project_x/${id}`)).toBe(`/objects/project_x/${id}`);
    expect(resolvedLink('/settings/automation')).toBe('/settings/automation');
    expect(resolvedLink(`/settings/automation/${id}`)).toBe(`/settings/automation/${id}`);
  });

  it('resolves nothing for absolute, protocol-relative, javascript: and malformed links', () => {
    for (const link of [
      'https://evil.example/leads/1',
      '//evil.example',
      'javascript:alert(1)',
      '/leads/not-a-uuid',
      `/leads/${id}/x`,
      `/objects/BAD/${id}`,
      '/objects/ok_key/9',
      '/settings/automation/x',
      '/settings/automation/',
      `/LEADS/${id}`,
      `/leads/${id}/../../x`,
      `/leads/${id}?next=//evil`,
      '/%2F%2Fevil',
      `/leads/${id}/`,
      `\\leads\\${id}`,
      `/\\evil.example`,
      ` /leads/${id}`,
      `/leads/${id} `
    ]) {
      expect(resolvedLink(link)).toBe('');
    }
  });
});
