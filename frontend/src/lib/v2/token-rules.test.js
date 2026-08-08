import { describe, it, expect } from 'vitest';
import {
  lastActivityAt,
  staleness,
  tokenStatus,
  scopeSummary,
  expiryFromChoice,
  scopesFromChoice,
  EXPIRY_CHOICES
} from './token-rules.js';

const NOW = new Date('2026-08-08T12:00:00Z');

/** Days before NOW, as the ISO string the API sends. */
function ago(days) {
  return new Date(NOW.getTime() - days * 86400000).toISOString();
}

/** A live token as `/api/org/tokens/` returns one. */
function token(over = {}) {
  return {
    id: 't1',
    name: 'Nightly export',
    token_prefix: 'bcrm_pat_abc',
    scopes: [],
    expires_at: null,
    last_used_at: null,
    created_at: ago(1),
    revoked_at: null,
    is_live: true,
    owner: { id: 'p1', name: 'Ada Lovelace', role: 'ADMIN', is_active: true },
    ...over
  };
}

describe('lastActivityAt', () => {
  it('prefers the last use', () => {
    expect(lastActivityAt(token({ last_used_at: ago(3) }))).toBe(ago(3));
  });

  it('falls back to when the token was issued', () => {
    expect(lastActivityAt(token({ created_at: ago(5) }))).toBe(ago(5));
  });

  it('is null when the row carries neither', () => {
    expect(lastActivityAt({ last_used_at: null, created_at: null })).toBeNull();
  });
});

describe('staleness', () => {
  it('says nothing about a token issued today and not yet used', () => {
    // The finding: null last_used_at is not "long ago". A token created a
    // minute ago has to read as new on the row AND in the count.
    expect(staleness(token(), NOW)).toBeNull();
  });

  it('flags a never-used token once it is old enough, and dates it', () => {
    const note = staleness(token({ created_at: ago(120) }), NOW);
    expect(note).toBe('never used, issued 120 days ago');
  });

  it('flags a token last used more than 90 days ago', () => {
    expect(staleness(token({ last_used_at: ago(120) }), NOW)).toBe('unused for 120 days');
  });

  it('says nothing at exactly 90 days, matching the backend > 90', () => {
    expect(staleness(token({ last_used_at: ago(90) }), NOW)).toBeNull();
    expect(staleness(token({ last_used_at: ago(91) }), NOW)).toBe('unused for 91 days');
  });

  it('says nothing about a token that is no longer live', () => {
    // Revoked or expired is already not a credential. Calling it neglected too
    // would bury the rows worth acting on.
    expect(staleness(token({ is_live: false, created_at: ago(400) }), NOW)).toBeNull();
  });
});

describe('tokenStatus', () => {
  it('names revoked and expired apart, tones them the same', () => {
    expect(tokenStatus(token({ revoked_at: ago(1), is_live: false }))).toEqual({
      label: 'Revoked',
      tone: 'slate'
    });
    expect(tokenStatus(token({ is_live: false }))).toEqual({ label: 'Expired', tone: 'slate' });
  });

  it('a revoked token reads as revoked even if is_live is stale', () => {
    expect(tokenStatus(token({ revoked_at: ago(1) })).label).toBe('Revoked');
  });

  it('is Live otherwise', () => {
    expect(tokenStatus(token())).toEqual({ label: 'Live', tone: 'moss' });
  });
});

describe('scopeSummary', () => {
  it('says an empty list is unrestricted, in the owner name', () => {
    // Empty means unrestricted server-side, which is what every token issued
    // before enforcement carries. Drawing those as limited would be a lie.
    expect(scopeSummary(token())).toBe('Everything Ada can');
  });

  it('falls back to a name-free phrasing when the owner block is missing', () => {
    expect(scopeSummary(token({ owner: undefined }))).toBe('Everything its owner can');
  });

  it('calls an all-read list read only', () => {
    expect(scopeSummary(token({ scopes: ['*:read'] }))).toBe('Read only');
    expect(scopeSummary(token({ scopes: ['leads:read', 'cases:read'] }))).toBe('Read only');
  });

  it('lists anything narrower verbatim', () => {
    expect(scopeSummary(token({ scopes: ['leads:read', 'cases:write'] }))).toBe(
      'leads:read, cases:write'
    );
  });
});

describe('expiryFromChoice', () => {
  it('turns each offered choice into a future instant', () => {
    for (const choice of EXPIRY_CHOICES.filter((c) => c.days)) {
      const iso = expiryFromChoice(choice.value, NOW);
      expect(new Date(iso).getTime()).toBeGreaterThan(NOW.getTime());
    }
  });

  it('counts the days the label promises', () => {
    const iso = expiryFromChoice('30', NOW);
    expect(Math.round((new Date(iso).getTime() - NOW.getTime()) / 86400000)).toBe(30);
  });

  it('is null for never, and for anything it does not recognise', () => {
    expect(expiryFromChoice('never', NOW)).toBeNull();
    expect(expiryFromChoice('tuesday', NOW)).toBeNull();
    expect(expiryFromChoice(undefined, NOW)).toBeNull();
  });

  it('offers 90 days first, so the default is an expiry rather than never', () => {
    expect(EXPIRY_CHOICES[0].value).toBe('90');
  });
});

describe('scopesFromChoice', () => {
  it('read means a read-only wildcard', () => {
    expect(scopesFromChoice('read')).toEqual(['*:read']);
  });

  it('anything else means unrestricted, which is the empty list', () => {
    expect(scopesFromChoice('full')).toEqual([]);
    expect(scopesFromChoice(undefined)).toEqual([]);
  });
});
