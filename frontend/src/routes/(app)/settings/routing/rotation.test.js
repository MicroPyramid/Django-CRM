import { describe, it, expect } from 'vitest';
import { nextInRotation, rotationPool } from './rotation.js';

/**
 * The routing page names who the next round-robin ticket goes to. It named the
 * wrong person in two independent ways, and both are pinned here.
 *
 * The same rule lives in `mobile/lib/data/models/routing_rule.dart`, tested in
 * `mobile/test/unit/routing_rules_test.dart`.
 */
const person = (id, name, is_active = true) => ({ id, name, is_active });

const rule = (overrides = {}) => ({
  strategy: 'round_robin',
  target_assignees: [],
  state: null,
  ...overrides
});

describe('nextInRotation', () => {
  it('names the agent at the stored index, not the one after', () => {
    // `_round_robin` reads `pool[state.last_assigned_index % len(pool)]` and
    // only THEN stores `idx + 1`, so the stored value is already the next one.
    const r = rule({
      target_assignees: [person('a', 'Ada'), person('b', 'Brin'), person('c', 'Cai')],
      state: { last_assigned_index: 1 }
    });
    expect(nextInRotation(r).name).toBe('Brin');
  });

  it('starts at the first agent when the rotation has never run', () => {
    // The engine's own dry run is `state.last_assigned_index if state else 0`,
    // so a rule with no state row yet is answerable rather than unknown.
    const r = rule({ target_assignees: [person('a', 'Ada'), person('b', 'Brin')] });
    expect(nextInRotation(r).name).toBe('Ada');
  });

  it('wraps rather than running off the end', () => {
    const r = rule({
      target_assignees: [person('a', 'Ada'), person('b', 'Brin')],
      state: { last_assigned_index: 7 }
    });
    expect(nextInRotation(r).name).toBe('Brin');
  });

  it('never names a deactivated agent', () => {
    // `_active_pool` filters them out, so the engine will never pick them.
    // Indexing the serializer's list names one, which is the one answer that
    // is certainly wrong.
    const r = rule({
      target_assignees: [person('a', 'Ada', false), person('b', 'Brin'), person('c', 'Cai')],
      state: { last_assigned_index: 0 }
    });
    expect(nextInRotation(r).name).toBe('Brin');
  });

  it('indexes the pool in id order, not the order it arrived in', () => {
    // `_active_pool` is `.order_by("id")`.
    const r = rule({
      target_assignees: [person('c', 'Cai'), person('a', 'Ada')],
      state: { last_assigned_index: 0 }
    });
    expect(nextInRotation(r).name).toBe('Ada');
  });

  it('says nothing for the strategies that have no cursor', () => {
    for (const strategy of ['direct', 'least_busy', 'by_team']) {
      const r = rule({
        strategy,
        target_assignees: [person('a', 'Ada')],
        state: { last_assigned_index: 0 }
      });
      expect(nextInRotation(r), strategy).toBeNull();
    }
  });

  it('says nothing when every assignee is deactivated', () => {
    const r = rule({ target_assignees: [person('a', 'Ada', false)] });
    expect(nextInRotation(r)).toBeNull();
  });

  it('does not mutate the rule it was handed', () => {
    // The pool is sorted, and sorting `r.target_assignees` in place would
    // reorder what the card renders beside this.
    const assignees = [person('c', 'Cai'), person('a', 'Ada')];
    const r = rule({ target_assignees: assignees });
    rotationPool(r);
    expect(assignees.map((p) => p.name)).toEqual(['Cai', 'Ada']);
  });
});
