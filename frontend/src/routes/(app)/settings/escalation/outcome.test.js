import { describe, it, expect } from 'vitest';
import {
  actionNotifies,
  teamPhrase,
  halfFires,
  escalationOutcome,
  teamIgnoredNote,
  deadPolicyCount,
  breachesGoingNowhere,
  unconfiguredPriorities,
  joinWithAnd
} from './outcome.js';

const ALICE = { id: 'p1', name: 'Alice' };
const SUPPORT = { id: 't1', name: 'Support' };
const SUPPORT_TEAM = { id: 't2', name: 'Support Team' };

/** @param {any} over */
function policy(over = {}) {
  return {
    id: 'e1',
    priority: 'Urgent',
    is_active: true,
    first_response_action: 'notify',
    resolution_action: 'notify',
    first_response_target: ALICE,
    resolution_target: ALICE,
    notify_team: null,
    breaches_last_30d: { first_response: 0, resolution: 0 },
    ...over
  };
}

describe('actionNotifies', () => {
  it('is true for the two actions that build a recipient list', () => {
    expect(actionNotifies('notify')).toBe(true);
    expect(actionNotifies('notify_and_reassign')).toBe(true);
  });

  it('is false for reassign, which sends no mail at all', () => {
    expect(actionNotifies('reassign')).toBe(false);
  });
});

describe('halfFires', () => {
  it('is false for every half of an inactive policy', () => {
    const p = policy({ is_active: false });
    expect(halfFires(p, 'first_response')).toBe(false);
    expect(halfFires(p, 'resolution')).toBe(false);
  });

  // The three cases the inline version got wrong, one test each.
  it('is false for notify with a team but no target', () => {
    const p = policy({ first_response_target: null, notify_team: SUPPORT });
    expect(halfFires(p, 'first_response')).toBe(false);
  });

  it('is false for notify_and_reassign with no target and no team', () => {
    const p = policy({ first_response_action: 'notify_and_reassign', first_response_target: null });
    expect(halfFires(p, 'first_response')).toBe(false);
  });

  it('is false for notify_and_reassign with a team but no target', () => {
    const p = policy({
      first_response_action: 'notify_and_reassign',
      first_response_target: null,
      notify_team: SUPPORT
    });
    expect(halfFires(p, 'first_response')).toBe(false);
  });

  it('is false for reassign with no target', () => {
    const p = policy({ first_response_action: 'reassign', first_response_target: null });
    expect(halfFires(p, 'first_response')).toBe(false);
  });

  it('is true whenever an active policy has a target on that half', () => {
    for (const action of ['notify', 'reassign', 'notify_and_reassign']) {
      expect(halfFires(policy({ first_response_action: action }), 'first_response')).toBe(true);
    }
  });

  it('reads the half it was asked about, not the other one', () => {
    const p = policy({ first_response_target: null });
    expect(halfFires(p, 'first_response')).toBe(false);
    expect(halfFires(p, 'resolution')).toBe(true);
  });
});

describe('escalationOutcome', () => {
  it('names the policy being off before anything else', () => {
    const p = policy({ is_active: false, notify_team: SUPPORT });
    expect(escalationOutcome(p, 'first_response')).toEqual({
      text: 'Nothing. The policy is turned off',
      dead: true
    });
  });

  it('says nothing happens when no target is set', () => {
    const p = policy({ first_response_target: null });
    expect(escalationOutcome(p, 'first_response')).toEqual({
      text: 'Nothing. No target is set',
      dead: true
    });
  });

  it('names the team when one is set with no target, which is the trap', () => {
    const p = policy({ first_response_target: null, notify_team: SUPPORT });
    expect(escalationOutcome(p, 'first_response').text).toBe(
      'Nothing. No target is set, and the Support team is not notified on its own'
    );
  });

  it('appends the team on a notifying half', () => {
    const p = policy({ notify_team: SUPPORT });
    expect(escalationOutcome(p, 'first_response')).toEqual({
      text: 'Notify Alice and the Support team',
      dead: false
    });
  });

  it('does not say "team" twice for a team named Support Team', () => {
    const p = policy({ notify_team: SUPPORT_TEAM });
    expect(escalationOutcome(p, 'first_response').text).toBe('Notify Alice and the Support Team');
  });

  it('leaves the team out of a reassign half, which never emails', () => {
    const p = policy({ first_response_action: 'reassign', notify_team: SUPPORT });
    expect(escalationOutcome(p, 'first_response')).toEqual({
      text: 'Reassign to Alice',
      dead: false
    });
  });

  it('never renders a label with nothing after it', () => {
    for (const action of ['notify', 'reassign', 'notify_and_reassign']) {
      for (const team of [null, SUPPORT]) {
        const p = policy({
          first_response_action: action,
          first_response_target: null,
          notify_team: team
        });
        expect(escalationOutcome(p, 'first_response').text).not.toMatch(/ $/);
      }
    }
  });
});

describe('teamIgnoredNote', () => {
  it('warns when a team is set on a reassign half', () => {
    const p = policy({ first_response_action: 'reassign', notify_team: SUPPORT });
    expect(teamIgnoredNote(p, 'first_response')).toBe(
      'The Support team is not notified here: this half only reassigns.'
    );
  });

  it('is null when the half notifies', () => {
    const p = policy({ first_response_action: 'notify_and_reassign', notify_team: SUPPORT });
    expect(teamIgnoredNote(p, 'first_response')).toBeNull();
  });

  it('is null with no team', () => {
    expect(
      teamIgnoredNote(policy({ first_response_action: 'reassign' }), 'first_response')
    ).toBeNull();
  });

  it('is null on a half that does not fire, where the outcome line already says so', () => {
    const p = policy({
      first_response_action: 'reassign',
      first_response_target: null,
      notify_team: SUPPORT
    });
    expect(teamIgnoredNote(p, 'first_response')).toBeNull();
  });
});

describe('deadPolicyCount', () => {
  it('counts only policies dead on both halves', () => {
    const half = policy({ id: 'a', first_response_target: null });
    const both = policy({ id: 'b', first_response_target: null, resolution_target: null });
    const off = policy({ id: 'c', is_active: false });
    expect(deadPolicyCount([half, both, off])).toBe(2);
  });
});

describe('breachesGoingNowhere', () => {
  it('counts only the halves that cannot fire', () => {
    const p = policy({
      first_response_target: null,
      breaches_last_30d: { first_response: 11, resolution: 4 }
    });
    expect(breachesGoingNowhere([p])).toBe(11);
  });

  it('counts both halves of an off policy', () => {
    const p = policy({
      is_active: false,
      breaches_last_30d: { first_response: 11, resolution: 4 }
    });
    expect(breachesGoingNowhere([p])).toBe(15);
  });

  it('counts a team-but-no-target half, which the old rule reported as live', () => {
    const p = policy({
      first_response_target: null,
      notify_team: SUPPORT,
      breaches_last_30d: { first_response: 7, resolution: 0 }
    });
    expect(breachesGoingNowhere([p])).toBe(7);
  });

  it('is zero when every half fires', () => {
    expect(
      breachesGoingNowhere([policy({ breaches_last_30d: { first_response: 9, resolution: 9 } })])
    ).toBe(0);
  });
});

describe('unconfiguredPriorities', () => {
  it('returns the priorities with no policy, worst first', () => {
    expect(unconfiguredPriorities([policy({ priority: 'High' })])).toEqual([
      'Urgent',
      'Normal',
      'Low'
    ]);
  });

  it('is empty once all four are configured', () => {
    const all = ['Urgent', 'High', 'Normal', 'Low'].map((priority) => policy({ priority }));
    expect(unconfiguredPriorities(all)).toEqual([]);
  });
});

describe('teamPhrase', () => {
  it('adds the word so a bare name reads as a team', () => {
    expect(teamPhrase('Support')).toBe('the Support team');
  });

  it('does not repeat it when the name already says team', () => {
    expect(teamPhrase('Support Team')).toBe('the Support Team');
    expect(teamPhrase('support teams')).toBe('the support teams');
    expect(teamPhrase('Team')).toBe('the Team');
  });

  it('does not fire on a name that merely ends in those letters', () => {
    expect(teamPhrase('Downsteam')).toBe('the Downsteam team');
  });
});

describe('joinWithAnd', () => {
  it('joins one, two and three parts', () => {
    expect(joinWithAnd([])).toBe('');
    expect(joinWithAnd(['Urgent'])).toBe('Urgent');
    expect(joinWithAnd(['Urgent', 'High'])).toBe('Urgent and High');
    expect(joinWithAnd(['Urgent', 'High', 'Low'])).toBe('Urgent, High and Low');
  });
});
