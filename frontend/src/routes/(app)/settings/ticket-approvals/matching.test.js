import { describe, it, expect } from 'vitest';
import {
  ROLES_THAT_EXIST,
  roleClears,
  approverSentence,
  clearableByNobody,
  ruleMatchSentence,
  ruleSpecificity,
  ruleSignature,
  shadowedRuleIds,
  shadowedBy
} from './matching.js';

const ADA = { id: 'p1', email: 'ada@acme.com' };
const BOB = { id: 'p2', email: 'bob@acme.com' };
const SUPPORT = { id: 't1', name: 'Support' };

/** @param {any} over */
function rule(over = {}) {
  return {
    id: 'r1',
    name: 'Close review',
    is_active: true,
    approver_role: 'ADMIN',
    approvers: [],
    match_priority: null,
    match_case_type: null,
    match_team: null,
    created_at: '2026-01-01T00:00:00Z',
    pending_count: 0,
    ...over
  };
}

describe('roleClears', () => {
  it('is true for admin, the one role a profile can hold', () => {
    expect(roleClears(rule())).toBe(true);
    expect(ROLES_THAT_EXIST).toEqual(['ADMIN']);
  });

  it('is false for manager, which matches no profile', () => {
    expect(roleClears(rule({ approver_role: 'MANAGER' }))).toBe(false);
  });
});

describe('approverSentence', () => {
  it('names the role when nobody is named', () => {
    expect(approverSentence(rule())).toBe('any admin');
  });

  it('adds named approvers to the role rather than replacing it', () => {
    // The finding. `can_be_acted_on_by` returns True for a named approver OR
    // anyone holding the role, and the row used to list only the names, so an
    // admin read a rule as tighter than it is.
    expect(approverSentence(rule({ approvers: [ADA, BOB] }))).toBe(
      'any admin, or ada@acme.com or bob@acme.com'
    );
  });

  it('is the names alone when the role matches nobody', () => {
    expect(approverSentence(rule({ approver_role: 'MANAGER', approvers: [ADA] }))).toBe(
      'ada@acme.com'
    );
  });

  it('says nobody when the role matches nobody and no one is named', () => {
    expect(approverSentence(rule({ approver_role: 'MANAGER' }))).toBe('nobody');
  });

  it('ignores an approver row with no email rather than printing a blank', () => {
    expect(approverSentence(rule({ approvers: [{ id: 'p9' }] }))).toBe('any admin');
  });
});

describe('clearableByNobody', () => {
  it('is a manager rule with no named approvers', () => {
    expect(clearableByNobody(rule({ approver_role: 'MANAGER' }))).toBe(true);
  });

  it('is not one with a named approver', () => {
    expect(clearableByNobody(rule({ approver_role: 'MANAGER', approvers: [ADA] }))).toBe(false);
  });

  it('is not an admin rule', () => {
    expect(clearableByNobody(rule())).toBe(false);
  });

  it('is not an inactive rule, which gates nothing to strand', () => {
    expect(clearableByNobody(rule({ approver_role: 'MANAGER', is_active: false }))).toBe(false);
  });
});

describe('ruleMatchSentence', () => {
  it('says every ticket when nothing narrows it', () => {
    expect(ruleMatchSentence(rule())).toBe('Every ticket');
  });

  it('joins the conditions that are set', () => {
    expect(
      ruleMatchSentence(
        rule({ match_priority: 'Urgent', match_case_type: 'Incident', match_team: SUPPORT })
      )
    ).toBe('Urgent priority · incident · Support team');
  });
});

describe('ruleSpecificity', () => {
  it('counts the filters, matching ApprovalRule.specificity', () => {
    expect(ruleSpecificity(rule())).toBe(0);
    expect(ruleSpecificity(rule({ match_priority: 'High' }))).toBe(1);
    expect(ruleSpecificity(rule({ match_priority: 'High', match_team: SUPPORT }))).toBe(2);
  });
});

describe('ruleSignature', () => {
  it('is equal for two rules matching the same tickets', () => {
    expect(ruleSignature(rule({ id: 'a', match_priority: 'High' }))).toBe(
      ruleSignature(rule({ id: 'b', match_priority: 'High' }))
    );
  });

  it('separates a null condition from a set one', () => {
    expect(ruleSignature(rule())).not.toBe(ruleSignature(rule({ match_priority: 'High' })));
  });

  it('separates two teams', () => {
    expect(ruleSignature(rule({ match_team: SUPPORT }))).not.toBe(
      ruleSignature(rule({ match_team: { id: 't2', name: 'Billing' } }))
    );
  });
});

describe('shadowedRuleIds', () => {
  it('flags the older of two rules with identical conditions', () => {
    // Both always match together, and the stable sort over -created_at hands
    // every case to the newer one, so the older never runs.
    const rules = [
      rule({ id: 'old', created_at: '2026-01-01T00:00:00Z' }),
      rule({ id: 'new', created_at: '2026-02-01T00:00:00Z' })
    ];
    expect([...shadowedRuleIds(rules)]).toEqual(['old']);
  });

  it('leaves rules with different conditions alone', () => {
    // A broad rule is a fallback for the tickets the narrow one misses, not a
    // dead rule.
    const rules = [
      rule({ id: 'broad', created_at: '2026-01-01T00:00:00Z' }),
      rule({ id: 'narrow', match_priority: 'Urgent', created_at: '2026-02-01T00:00:00Z' })
    ];
    expect([...shadowedRuleIds(rules)]).toEqual([]);
  });

  it('ignores an inactive rule in both directions', () => {
    const rules = [
      rule({ id: 'old', created_at: '2026-01-01T00:00:00Z' }),
      rule({ id: 'newer-but-off', created_at: '2026-02-01T00:00:00Z', is_active: false })
    ];
    expect([...shadowedRuleIds(rules)]).toEqual([]);

    const inverse = [
      rule({ id: 'old-and-off', created_at: '2026-01-01T00:00:00Z', is_active: false }),
      rule({ id: 'new', created_at: '2026-02-01T00:00:00Z' })
    ];
    expect([...shadowedRuleIds(inverse)]).toEqual([]);
  });

  it('flags every loser when three share conditions', () => {
    const rules = [
      rule({ id: 'a', created_at: '2026-01-01T00:00:00Z' }),
      rule({ id: 'b', created_at: '2026-02-01T00:00:00Z' }),
      rule({ id: 'c', created_at: '2026-03-01T00:00:00Z' })
    ];
    expect([...shadowedRuleIds(rules)].sort()).toEqual(['a', 'b']);
  });

  it('flags nothing when a timestamp is missing, rather than guessing', () => {
    // A blank must not read as "created first", which would declare a live
    // rule dead on the strength of an absent field.
    const rules = [rule({ id: 'a', created_at: null }), rule({ id: 'b' })];
    expect([...shadowedRuleIds(rules)]).toEqual([]);
  });

  it('is empty for no rules', () => {
    expect([...shadowedRuleIds([])]).toEqual([]);
    expect([...shadowedRuleIds(undefined)]).toEqual([]);
  });
});

describe('shadowedBy', () => {
  it('names the newest rule that takes the cases', () => {
    const rules = [
      rule({ id: 'a', name: 'Oldest', created_at: '2026-01-01T00:00:00Z' }),
      rule({ id: 'b', name: 'Middle', created_at: '2026-02-01T00:00:00Z' }),
      rule({ id: 'c', name: 'Newest', created_at: '2026-03-01T00:00:00Z' })
    ];
    expect(shadowedBy(rules[0], rules).name).toBe('Newest');
  });

  it('is null for a rule nothing shadows', () => {
    const rules = [rule({ id: 'a' })];
    expect(shadowedBy(rules[0], rules)).toBeNull();
  });
});
