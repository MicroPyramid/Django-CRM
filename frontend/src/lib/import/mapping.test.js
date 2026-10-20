import { describe, expect, it } from 'vitest';
import {
  droppedLines,
  hasAnyMatch,
  mappingPayload,
  setColumnField,
  skippedRowsCsv,
  suggestLeads,
  summaryLine
} from './mapping.js';

/** @param {number} index @param {string | null} field */
const col = (index, field) => ({ index, header: `H${index}`, field, samples: [] });

const CONTACT = { singular: 'contact', plural: 'contacts' };

/**
 * A preview body as the server sends it, reduced to what summaryLine reads.
 * @param {number} valid
 * @param {import('./mapping.js').Skipped[]} skipped
 */
function preview(valid, skipped = []) {
  return {
    valid: Array.from({ length: valid }, (_, i) => ({ row: i + 1 })),
    skipped,
    summary: { total: valid + skipped.length, valid, skipped: skipped.length }
  };
}

/**
 * A skipped row as the server sends it. `kind` is `duplicate` (already in the
 * org or earlier in the file) or `row` (cannot become a record).
 * @param {number} row @param {string} field @param {'duplicate' | 'row'} kind @param {string} [message]
 * @returns {import('./mapping.js').Skipped}
 */
const skip = (row, field, kind, message = 'Skipped') => ({ row, field, message, cells: [], kind });

describe('setColumnField', () => {
  it('sets the field on the chosen column and returns a new array', () => {
    const columns = [col(0, null), col(1, 'phone')];
    const next = setColumnField(columns, 0, 'email');
    expect(next).not.toBe(columns);
    expect(next.map((c) => c.field)).toEqual(['email', 'phone']);
    expect(columns.map((c) => c.field)).toEqual([null, 'phone']);
  });

  it('moves a field off the column that held it', () => {
    const columns = [col(0, 'email'), col(1, null), col(2, 'phone')];
    expect(setColumnField(columns, 1, 'email').map((c) => c.field)).toEqual([
      null,
      'email',
      'phone'
    ]);
  });

  it("sets a column to Don't import without touching the others", () => {
    const columns = [col(0, 'email'), col(1, 'phone')];
    expect(setColumnField(columns, 0, null).map((c) => c.field)).toEqual([null, 'phone']);
  });
});

describe('mappingPayload', () => {
  it('is a JSON object of column index to field or null', () => {
    expect(
      mappingPayload([
        { index: 0, field: 'email' },
        { index: 1, field: null }
      ])
    ).toBe('{"0":"email","1":null}');
  });
});

describe('hasAnyMatch', () => {
  it('is false when every column is set to null', () => {
    expect(hasAnyMatch([col(0, null), col(1, null)])).toBe(false);
  });

  it('is true when any column has a field', () => {
    expect(hasAnyMatch([col(0, null), col(1, 'email')])).toBe(true);
  });
});

describe('droppedLines', () => {
  const fields = [
    { name: 'phone', label: 'Phone', required: false },
    { name: 'linkedin_url', label: 'LinkedIn URL', required: false }
  ];

  it("gives one line per entry, each with the count and the field's label", () => {
    const lines = droppedLines(
      [
        { field: 'linkedin_url', count: 1 },
        { field: 'phone', count: 12 }
      ],
      fields
    );
    expect(lines).toHaveLength(2);
    expect(lines[0]).toContain('1');
    expect(lines[0]).toContain('LinkedIn URL');
    expect(lines[1]).toContain('12');
    expect(lines[1]).toContain('Phone');
  });

  it('agrees in number with the count', () => {
    const [one, many] = droppedLines(
      [
        { field: 'phone', count: 1 },
        { field: 'phone', count: 3 }
      ],
      fields
    );
    expect(one).toBe("Phone: 1 value we couldn't use was left blank.");
    expect(many).toBe("Phone: 3 values we couldn't use were left blank.");
  });

  it('falls back to the field name when the label is unknown', () => {
    expect(droppedLines([{ field: 'country', count: 2 }], fields)[0]).toContain('country');
  });

  it('is empty for nothing dropped', () => {
    expect(droppedLines([], fields)).toEqual([]);
  });
});

describe('summaryLine', () => {
  it('says everything is already in BottleCRM when every skipped row is a duplicate', () => {
    const line = summaryLine(
      CONTACT,
      preview(0, [skip(1, 'email', 'duplicate'), skip(2, 'phone', 'duplicate')])
    );
    expect(line).toBe('Everything in this file is already in BottleCRM.');
  });

  it('says the same for a lead file imported twice', () => {
    const line = summaryLine(
      { singular: 'prospect', plural: 'prospects' },
      preview(0, [skip(1, 'email', 'duplicate')])
    );
    expect(line).toBe('Everything in this file is already in BottleCRM.');
  });

  it('reads the kind, not the message', () => {
    expect(
      summaryLine(CONTACT, preview(0, [skip(1, 'email', 'duplicate', 'Worded differently')]))
    ).toBe('Everything in this file is already in BottleCRM.');
    expect(
      summaryLine(CONTACT, preview(0, [skip(1, 'last_name', 'row', 'This already exists')]))
    ).toBe('Nothing in this file can be imported.');
  });

  it('does not claim the rows exist when any was skipped for another reason', () => {
    const line = summaryLine(
      CONTACT,
      preview(0, [skip(1, 'email', 'duplicate'), skip(2, 'last_name', 'row')])
    );
    expect(line).toBe('Nothing in this file can be imported.');
  });

  it("counts the records with the caller's own words", () => {
    expect(summaryLine({ singular: 'prospect', plural: 'prospects' }, preview(1))).toBe(
      '1 prospect will be imported.'
    );
    expect(summaryLine(CONTACT, preview(12))).toBe('12 contacts will be imported.');
  });

  it('counts the skipped rows beside the imported ones', () => {
    expect(summaryLine(CONTACT, preview(3, [skip(4, 'last_name', 'row')]))).toBe(
      '3 contacts will be imported, and 1 row will be skipped.'
    );
  });

  it('says when every skipped row is a duplicate', () => {
    expect(
      summaryLine(
        CONTACT,
        preview(2, [skip(3, 'email', 'duplicate'), skip(4, 'email', 'duplicate')])
      )
    ).toBe('2 contacts will be imported, and 2 duplicate rows will be skipped.');
  });

  it('says so when the file has no rows', () => {
    expect(summaryLine(CONTACT, preview(0))).toBe('This file has no rows to import.');
  });
});

describe('suggestLeads', () => {
  it('is true for contacts with a row skipped for its name', () => {
    expect(suggestLeads('contacts', [skip(2, 'last_name', 'row')])).toBe(true);
    expect(suggestLeads('contacts', [skip(2, 'first_name', 'row')])).toBe(true);
  });

  it('is false for leads, which accept one name', () => {
    expect(suggestLeads('leads', [skip(2, 'first_name', 'row')])).toBe(false);
  });

  it('is false for contacts skipped for anything but the name', () => {
    expect(suggestLeads('contacts', [skip(2, 'email', 'row')])).toBe(false);
    expect(suggestLeads('contacts', [])).toBe(false);
  });

  it('is false for a name that is skipped as a duplicate', () => {
    // A lead would duplicate the contact that already holds this name.
    expect(
      suggestLeads('contacts', [
        skip(2, 'first_name', 'duplicate'),
        skip(3, 'last_name', 'duplicate')
      ])
    ).toBe(false);
  });
});

describe('skippedRowsCsv', () => {
  it('keeps the original headers and cells in order and appends the reason', () => {
    const csv = skippedRowsCsv(
      ['Name', 'Mobile', 'Email ID'],
      [
        {
          row: 2,
          field: 'last_name',
          message: 'Last name is required',
          cells: ['Ada', '5550100', 'ada@x.test'],
          kind: 'row'
        }
      ]
    );
    expect(csv).toBe(
      'Name,Mobile,Email ID,Reason\n' + 'Ada,5550100,ada@x.test,Last name is required'
    );
  });

  it('neutralises a cell a spreadsheet would run as a formula', () => {
    const csv = skippedRowsCsv(
      ['Name', 'Notes'],
      [
        {
          row: 1,
          field: 'last_name',
          message: 'Last name is required',
          cells: ['Ada', '=HYPERLINK("x")'],
          kind: 'row'
        }
      ]
    );
    expect(csv.split('\n')[1]).toBe(`Ada,"'=HYPERLINK(""x"")",Last name is required`);
  });

  it('quotes a reason that holds a comma', () => {
    const csv = skippedRowsCsv(
      ['Name'],
      [
        {
          row: 1,
          field: 'first_name',
          message: 'Same name as row 1 in this file; add an email or phone, please',
          cells: ['Ada Lovelace'],
          kind: 'row'
        }
      ]
    );
    expect(csv.split('\n')[1]).toBe(
      'Ada Lovelace,"Same name as row 1 in this file; add an email or phone, please"'
    );
  });

  it('keeps the reason in its own column for short and long rows', () => {
    const csv = skippedRowsCsv(
      ['A', 'B'],
      [
        { row: 1, field: 'last_name', message: 'short', cells: ['a'], kind: 'row' },
        { row: 2, field: 'last_name', message: 'long', cells: ['a', 'b', 'c'], kind: 'row' }
      ]
    );
    expect(csv.split('\n')).toEqual(['A,B,,Reason', 'a,,,short', 'a,b,c,long']);
  });

  it('guards a + phone with exactly the apostrophe the importer takes off', () => {
    // The backend reader (`common/spreadsheet.py`, `_FORMULA_GUARD`) removes one
    // leading apostrophe from a cell that, after its apostrophes, starts with
    // = + - or @. Re-uploading this file must give back the original phone.
    const FORMULA_GUARD = /^'+[=+\-@]/;
    const phone = '+44 20 7946 0000';
    const csv = skippedRowsCsv(
      ['Name', 'Phone'],
      [
        {
          row: 1,
          field: 'last_name',
          message: 'Last name is required',
          cells: ['Ada', phone],
          kind: 'row'
        }
      ]
    );
    const guarded = csv.split('\n')[1].split(',')[1];
    expect(guarded[0]).toBe("'");
    expect(guarded).toBe(`'${phone}`);
    expect(FORMULA_GUARD.test(guarded)).toBe(true);
    expect(guarded.slice(1)).toBe(phone);
  });
});
