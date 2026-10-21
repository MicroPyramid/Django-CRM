import { describe, it, expect } from 'vitest';
import { mentionPeople, mentionAt, insertMention, matchPeople, mentionTokens } from './mentions.js';

const liz = { username: 'liz.rao', name: 'Liz Rao' };
const sam = { username: 'sam', name: 'Sam Okafor' };

describe('mentionPeople', () => {
  it('names each person by their email local part, lower-cased, as the backend resolves them', () => {
    expect(mentionPeople([{ id: '1', name: 'Liz Rao', email: 'Liz.Rao@acme.com' }])).toEqual([liz]);
  });

  it('keeps one entry when two people share a local part', () => {
    const people = [
      { id: '1', name: 'Sam Okafor', email: 'sam@acme.com' },
      { id: '2', name: 'Sam Lee', email: 'sam@other.com' }
    ];
    expect(mentionPeople(people)).toEqual([sam]);
  });

  it('skips a person with no email', () => {
    expect(mentionPeople([{ id: '1', name: 'Nobody', email: '' }])).toEqual([]);
  });
});

describe('mentionAt', () => {
  it('finds the handle being typed after @', () => {
    expect(mentionAt('Hi @li', 6)).toEqual({ start: 3, query: 'li' });
  });

  it('opens on a bare @', () => {
    expect(mentionAt('@', 1)).toEqual({ start: 0, query: '' });
  });

  it('ignores an email address', () => {
    expect(mentionAt('mail liz@acme', 13)).toBeNull();
  });

  it('reads only up to the caret', () => {
    expect(mentionAt('Hi @liz there', 5)).toEqual({ start: 3, query: 'l' });
  });

  it('closes once a space follows the handle', () => {
    expect(mentionAt('Hi @liz ', 8)).toBeNull();
  });

  it('treats a missing caret as the end of the text', () => {
    expect(mentionAt('@li', null)).toEqual({ start: 0, query: 'li' });
  });
});

describe('insertMention', () => {
  it('replaces the typed handle and adds a space', () => {
    expect(insertMention('Hi @li', 3, 6, 'liz.rao')).toEqual({ text: 'Hi @liz.rao ', caret: 12 });
  });

  it('keeps the text after the caret', () => {
    expect(insertMention('Hi @li there', 3, 6, 'liz.rao')).toEqual({
      text: 'Hi @liz.rao there',
      caret: 11
    });
  });
});

describe('matchPeople', () => {
  it('matches the start of the handle or of a name, ignoring case', () => {
    expect(matchPeople([liz, sam], 'LI')).toEqual([liz]);
    expect(matchPeople([liz, sam], 'oka')).toEqual([sam]);
  });

  it('offers everyone, up to the cap, before anything is typed', () => {
    const many = Array.from({ length: 9 }, (_, i) => ({ username: `u${i}`, name: `U ${i}` }));
    expect(matchPeople(many, '')).toHaveLength(6);
  });
});

describe('mentionTokens', () => {
  it('marks a handle that names a member', () => {
    expect(mentionTokens('Thanks @liz.rao, done', [liz, sam])).toEqual([
      { type: 'text', value: 'Thanks ' },
      { type: 'mention', value: '@liz.rao', person: liz },
      { type: 'text', value: ', done' }
    ]);
  });

  it('matches a handle whatever its case', () => {
    expect(mentionTokens('@LIZ.RAO', [liz])).toEqual([
      { type: 'mention', value: '@LIZ.RAO', person: liz }
    ]);
  });

  it('leaves an unknown handle as text', () => {
    expect(mentionTokens('cc @bob', [liz])).toEqual([
      { type: 'text', value: 'cc ' },
      { type: 'text', value: '@bob' }
    ]);
  });

  it('leaves an email address alone', () => {
    expect(mentionTokens('mail liz.rao@acme.com', [liz])).toEqual([
      { type: 'text', value: 'mail liz.rao@acme.com' }
    ]);
  });

  it('reads a trailing full stop as part of the handle, as the backend does', () => {
    // `cases/notifications.py` captures "liz.rao." and resolves nobody, so no
    // notification went out and no chip may claim one did.
    expect(mentionTokens('Thanks @liz.rao.', [liz])).toEqual([
      { type: 'text', value: 'Thanks ' },
      { type: 'text', value: '@liz.rao.' }
    ]);
  });
});
