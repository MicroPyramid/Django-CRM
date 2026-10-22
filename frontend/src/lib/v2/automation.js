/**
 * Editor logic for the automation builder. Browser-safe: pages and components
 * render from these helpers, and the catalogue is the only source of labels.
 */
import { runTime } from '#lib/v2/format.js';

/** @typedef {{ key: string, label: string, type: string, choices: any[], settable: boolean }} Field */

/**
 * @param {any} catalogue
 * @param {string} key
 * @returns {any | null}
 */
export function objectOf(catalogue, key) {
  return (catalogue?.objects ?? []).find((/** @type {any} */ o) => o.key === key) ?? null;
}

/**
 * @param {any} object
 * @param {string} key
 * @returns {Field | null}
 */
export function fieldOf(object, key) {
  return (object?.fields ?? []).find((/** @type {Field} */ f) => f.key === key) ?? null;
}

/** @param {any} object */
export function triggerFields(object) {
  return (object?.fields ?? []).filter((/** @type {Field} */ f) => f.type !== 'people');
}

/**
 * @param {any} catalogue
 * @param {Field | null} field
 * @param {string} event
 * @returns {string[]}
 */
export function operatorsFor(catalogue, field, event) {
  if (!field) return [];
  const base = catalogue?.operators?.[field.type] ?? [];
  if (event === 'updated' && field.type !== 'people') {
    return [...base, ...(catalogue?.update_only_operators ?? [])];
  }
  return [...base];
}

/** @type {Record<string, string>} */
const OPERATOR_LABELS = {
  eq: 'is',
  neq: 'is not',
  contains: 'contains',
  not_contains: 'does not contain',
  gt: 'is more than',
  lt: 'is less than',
  in: 'is any of',
  not_in: 'is none of',
  true: 'is true',
  false: 'is false',
  includes: 'includes',
  excludes: 'does not include',
  empty: 'is empty',
  not_empty: 'is not empty',
  was: 'was',
  was_not: 'was not'
};

/**
 * @param {string} op
 * @param {string} [fieldType]
 */
export function operatorLabel(op, fieldType) {
  if (fieldType === 'date' && op === 'gt') return 'is after';
  if (fieldType === 'date' && op === 'lt') return 'is before';
  if (fieldType === 'people' && op === 'eq') return 'is exactly';
  return OPERATOR_LABELS[op] ?? op;
}

/**
 * @param {{ type: string }} field
 * @param {string} op
 * @returns {'none' | 'text' | 'number' | 'date' | 'choice' | 'choices' | 'boolean' | 'person' | 'people'}
 */
export function valueKind(field, op) {
  if (['empty', 'not_empty', 'true', 'false'].includes(op)) return 'none';
  if (op === 'in' || op === 'not_in') return 'choices';
  if (field.type === 'people') return op === 'eq' ? 'people' : 'person';
  if ((op === 'was' || op === 'was_not') && field.type === 'boolean') return 'boolean';
  return /** @type {any} */ (field.type);
}

export function blankCondition() {
  return { field: '', op: '', value: null };
}

/** @param {string} type */
export function blankAction(type) {
  switch (type) {
    case 'create_task':
      return {
        type,
        title: '',
        due_in_days: 2,
        priority: 'Medium',
        assign_to: 'record',
        person: null
      };
    case 'notify':
      return { type, to: [], people: [], message: '' };
    case 'set_field':
      return { type, target: 'record', field: '', value: null };
    case 'assign':
      return { type, mode: 'replace', people: [] };
    case 'webhook':
      return { type, endpoint: '' };
    default:
      return { type };
  }
}

/**
 * @param {any} catalogue
 * @param {any} object
 * @returns {string[]}
 */
export function actionTypes(catalogue, object) {
  const assignees = fieldOf(object, 'assigned_to');
  const canAssign = assignees?.type === 'people' && assignees.settable;
  const canHook =
    !String(object?.key ?? '').startsWith('obj:') && (catalogue?.endpoints ?? []).length > 0;
  return (catalogue?.actions ?? []).filter(
    (/** @type {string} */ a) => (a !== 'assign' || canAssign) && (a !== 'webhook' || canHook)
  );
}

/**
 * Where `set_field` can write: the record, its parent, then each link.
 * @param {any} catalogue
 * @param {any} object
 * @returns {{ value: string, label: string, object: any }[]}
 */
export function targetsFor(catalogue, object) {
  if (!object) return [];
  const out = [{ value: 'record', label: `This ${object.label.toLowerCase()}`, object }];
  if (object.parent) {
    out.push({
      value: 'parent',
      label: `Its ${object.parent.label.toLowerCase()}`,
      object: objectOf(catalogue, object.parent.key) ?? {
        key: object.parent.key,
        label: object.parent.label,
        fields: [],
        parent: null,
        links: []
      }
    });
  }
  for (const link of object.links ?? []) {
    out.push({
      value: link.id,
      label: link.label,
      object: objectOf(catalogue, link.object_key) ?? {
        key: link.object_key,
        label: link.label,
        fields: [],
        parent: null,
        links: []
      }
    });
  }
  return out;
}

/**
 * @param {any} object
 * @returns {{ value: string, label: string }[]}
 */
export function recipientsFor(object) {
  const out = [
    { value: 'record_assignees', label: 'Its assignees' },
    { value: 'record_creator', label: 'Who created it' }
  ];
  const parent = parentAssignees(object);
  if (parent) out.push({ value: 'parent_assignees', label: parent });
  out.push({ value: 'admins', label: 'All admins' });
  for (const link of object?.links ?? []) {
    out.push({ value: `linked:${link.id}`, label: `Assignees of ${link.label}` });
  }
  return out;
}

/**
 * Whether the object has a parent a task or notification can reach.
 * @param {any} object
 */
export function offersParent(object) {
  if (object?.key === 'task') return true;
  return (object?.key === 'deal' || object?.key === 'ticket') && Boolean(object.parent);
}

/**
 * How the parent's assignees read in a list, or null where there is no parent.
 * @param {any} object
 * @returns {string | null}
 */
export function parentAssignees(object) {
  if (!offersParent(object)) return null;
  return object.key === 'task'
    ? "Its parent's assignees"
    : `The ${object.parent.label.toLowerCase()}'s assignees`;
}

/**
 * Who a created task can be for.
 * @param {any} object
 * @returns {{ value: string, label: string }[]}
 */
export function taskAudience(object) {
  const out = [{ value: 'record', label: 'Its assignees' }];
  const parent = parentAssignees(object);
  if (parent) out.push({ value: 'parent', label: parent });
  out.push(
    { value: 'owner', label: "The rule's owner" },
    { value: 'person', label: 'A chosen person' }
  );
  return out;
}

/** @type {Record<string, string>} */
const ACTION_LABELS = {
  set_field: 'Set a field',
  assign: 'Assign',
  create_task: 'Create a task',
  notify: 'Notify',
  webhook: 'Send to an endpoint'
};

/** @param {string} type */
export function actionLabel(type) {
  return ACTION_LABELS[type] ?? type;
}

/** How a recipient or task audience the object no longer offers reads. @param {string} value */
export function recipientLabel(value) {
  if (value.startsWith('linked:')) return 'Assignees of a removed link';
  /** @type {Record<string, string>} */
  const usual = {
    record_assignees: 'Its assignees',
    record_creator: 'Who created it',
    parent_assignees: "Its parent's assignees (no longer available)",
    parent: "Its parent's assignees (no longer available)",
    admins: 'All admins',
    record: 'Its assignees',
    owner: "The rule's owner",
    person: 'A chosen person'
  };
  return usual[value] ?? `${value} (no longer available)`;
}

/**
 * The action types to offer, plus the stored one the catalogue lost.
 * @param {any} catalogue
 * @param {any} object
 * @param {string} stored
 */
export function actionOptions(catalogue, object, stored) {
  const offered = actionTypes(catalogue, object).map((t) => ({ value: t, label: actionLabel(t) }));
  return withStored(offered, stored, {
    label: (type) => `${actionLabel(type)} (no longer available)`
  });
}

/**
 * Ticking "Clear it instead" sets null; unticking brings back what the action
 * held before, or leaves the value unchosen.
 * @param {any} action
 * @param {boolean} on
 * @param {any} previous
 */
export function applyClear(action, on, previous) {
  action.value = on ? null : (previous ?? undefined);
}

/** Null is a deliberate clear. @param {any} action */
export function isClearing(action) {
  return action.value === null;
}

/**
 * A value from the input. Null from a select or number input means nothing is
 * chosen, never a clear.
 * @param {any} action
 * @param {any} value
 */
export function setActionValue(action, value) {
  action.value = value === null ? undefined : value;
}

/**
 * What the value input shows: a placeholder while nothing is chosen.
 * @param {any} action
 */
export function shownValue(action) {
  return action.value === undefined ? null : action.value;
}

/**
 * Changing assign's mode empties its people, which differ in count.
 * @param {any} action
 * @param {string} mode
 */
export function applyMode(action, mode) {
  action.mode = mode;
  action.people = [];
}

/**
 * A `set_field` row pointed at another target starts over, in place.
 * @param {any} action
 * @param {string} target
 */
export function applyTarget(action, target) {
  action.target = target;
  action.field = '';
  action.value = undefined;
}

/**
 * A chosen field has no value yet; an absent value is refused, a null one clears.
 * @param {any} action
 * @param {string} field
 */
export function applyField(action, field) {
  action.field = field;
  action.value = undefined;
}

/**
 * Who a task is for; only a chosen person keeps a person.
 * @param {any} action
 * @param {string} who
 */
export function applyAssignTo(action, who) {
  action.assign_to = who;
  if (who !== 'person') action.person = null;
}

/**
 * Options plus any stored value they no longer carry, so editing a rule never
 * silently drops what it holds.
 *
 * @param {{ value: string, label: string, group?: string, settable?: boolean, gone?: boolean }[]} options
 * @param {any} stored One value, a list of them, or empty.
 * @param {{ person?: boolean, label?: (value: any) => string | undefined }} [opts]
 *   `person`: stored values are member ids. `label`: how a lost value reads.
 * @returns {{ value: string, label: string, group?: string, settable?: boolean, gone?: boolean }[]}
 */
export function withStored(options, stored, { person = false, label = undefined } = {}) {
  const out = [...options];
  const seen = new Set(options.map((o) => o.value));
  const values = Array.isArray(stored) ? stored : [stored];
  for (const value of values) {
    if (value === null || value === undefined || value === '' || seen.has(value)) continue;
    seen.add(value);
    out.push({
      value,
      label:
        label?.(value) ?? (person ? 'Someone no longer active' : `${value} (no longer available)`),
      group: '',
      settable: false,
      gone: true
    });
  }
  return out;
}

/**
 * The person a replace assign shows as chosen. A stored rule can hold several
 * though the API takes exactly one, so none is preselected then and the admin
 * chooses who stays.
 * @param {{ people?: string[] }} action
 * @returns {{ id: string, several: boolean }}
 */
export function replacePerson(action) {
  const people = Array.isArray(action?.people) ? action.people : [];
  return { id: people.length === 1 ? people[0] : '', several: people.length > 1 };
}

/**
 * @param {{ object_key?: string, trigger?: any }} rule
 * @param {any} catalogue
 */
export function triggerSentence(rule, catalogue) {
  const trigger = rule?.trigger ?? {};
  if (trigger.event === 'created') return 'Created';
  if (!trigger.field) return 'Updated';
  const field = fieldOf(objectOf(catalogue, rule.object_key ?? ''), trigger.field);
  if (!field) return 'A field that is no longer available changes';
  const base = `${field.label} changes`;
  if (trigger.to === undefined || trigger.to === null) return base;
  if (field.type === 'boolean')
    return `${base} to ${trigger.to === true || trigger.to === 'true' ? 'Yes' : 'No'}`;
  if (field.type === 'choice') {
    const option = field.choices.find((/** @type {any} */ c) => c.value === String(trigger.to));
    return `${base} to ${option ? option.label : trigger.to}`;
  }
  return `${base} to ${trigger.to}`;
}

/** @param {{ runs_7d?: number, failures_7d?: number }} row */
export function runsLabel(row) {
  const runs = row?.runs_7d ?? 0;
  if (!runs) return 'No runs';
  const text = `${runs} ${runs === 1 ? 'run' : 'runs'}`;
  return row.failures_7d ? `${text}, ${row.failures_7d} failed` : text;
}

export const STATUS = {
  on: { label: 'On', tone: 'moss' },
  off: { label: 'Off', tone: 'slate' },
  paused: { label: 'Paused', tone: 'clay' },
  over_limit: { label: 'Not running', tone: 'clay' },
  needs_attention: { label: 'Needs attention', tone: 'rust' }
};

/**
 * The line under a list row's pill, or null. A paused rule's sentence is shown
 * once, in its paused note above the list.
 * @param {{ status?: string, status_text?: string } | null | undefined} rule
 * @returns {string | null}
 */
export function statusNote(rule) {
  if (!rule?.status_text || rule.status === 'paused') return null;
  const label = /** @type {Record<string, {label: string}>} */ (STATUS)[rule.status ?? '']?.label;
  return rule.status_text === (label ?? rule.status) ? null : rule.status_text;
}

/**
 * What a run's card head says beside its time and record.
 * @param {any} run
 * @returns {{ reason: string | null, by: string | null }}
 */
export function runNotes(run) {
  const reason = typeof run?.reason === 'string' && run.reason ? run.reason : null;
  const rule = run?.triggered_by?.rule_name;
  return { reason, by: typeof rule === 'string' && rule ? `Set off by "${rule}"` : null };
}

export { recordHref as recordRoute } from '#lib/v2/custom-objects.js';

/** @type {Record<string, string[]>} */
const ACTION_KEYS = {
  set_field: ['target', 'field', 'value'],
  assign: ['mode', 'people'],
  create_task: ['title', 'due_in_days', 'priority', 'assign_to', 'person'],
  notify: ['to', 'people', 'message'],
  webhook: ['endpoint']
};

/**
 * The rule's body keys in a fixed order, copied, so two drafts compare by what
 * would be saved.
 * @param {any} rule
 * @param {string} objectKey
 */
function normalise(rule, objectKey) {
  const trigger = rule?.trigger ?? { event: 'created' };
  /** @type {Record<string, any>} */
  const t = { event: trigger.event };
  if (Object.hasOwn(trigger, 'field')) t.field = trigger.field;
  if (Object.hasOwn(trigger, 'to')) t.to = trigger.to;
  return JSON.parse(
    JSON.stringify({
      name: rule?.name ?? '',
      object_key: rule?.object_key ?? objectKey,
      match: rule?.match ?? 'all',
      trigger: t,
      conditions: (rule?.conditions ?? []).map((/** @type {any} */ c) => ({
        field: c.field,
        op: c.op,
        value: c.value ?? null
      })),
      actions: (rule?.actions ?? []).map((/** @type {any} */ a) => {
        /** @type {Record<string, any>} */
        const out = { type: a.type };
        for (const key of ACTION_KEYS[a.type] ?? []) {
          if (Object.hasOwn(a, key)) out[key] = a[key];
        }
        return out;
      })
    })
  );
}

/**
 * @param {any | null} rule
 * @param {string} objectKey Used for a new rule.
 */
export function editorState(rule, objectKey) {
  return normalise(rule, objectKey);
}

/**
 * @param {any} draft
 * @param {any} saved
 */
export function isDirty(draft, saved) {
  return JSON.stringify(normalise(draft, '')) !== JSON.stringify(normalise(saved, ''));
}

/**
 * Why Try is unavailable: the hint to show, `''` when blocked with nothing to
 * say (sending, or no record chosen), or null when it may run.
 * @param {{ dirty: boolean, busy: boolean, chosen: unknown[] }} state
 * @returns {string | null}
 */
export function tryBlocked({ dirty, busy, chosen }) {
  if (dirty) return 'Save first: Try uses the saved rule.';
  return busy || chosen.length === 0 ? '' : null;
}

/**
 * @template T
 * @param {T[]} list
 * @param {number} index
 * @param {number} direction -1 up, 1 down
 * @returns {T[]}
 */
export function moveItem(list, index, direction) {
  const next = [...list];
  const to = index + direction;
  if (index < 0 || index >= next.length || to < 0 || to >= next.length) return next;
  [next[index], next[to]] = [next[to], next[index]];
  return next;
}

/**
 * A condition's value once its operator changes. It survives only while the
 * new operator reads the same kind of value, so a stale one is never sent.
 * @param {Field | null} field
 * @param {string} fromOp
 * @param {string} toOp
 * @param {any} value
 */
export function keptValue(field, fromOp, toOp, value) {
  if (!field) return null;
  const kind = valueKind(field, toOp);
  return kind === 'none' || kind !== valueKind(field, fromOp) ? null : (value ?? null);
}

/**
 * The draft moved to another object: conditions go, and so does any action the
 * object cannot take; a task for a missing parent falls back to the record.
 * @param {any} draft
 * @param {any} catalogue
 * @param {string} key
 */
export function switchObject(draft, catalogue, key) {
  const copy = JSON.parse(JSON.stringify(draft));
  const next = objectOf(catalogue, key);
  const offered = new Set(recipientsFor(next).map((r) => r.value));
  const offeredTypes = actionTypes(catalogue, next);
  const parent = offersParent(next);
  return {
    ...copy,
    object_key: key,
    trigger: { event: copy.trigger?.event ?? 'created' },
    conditions: [],
    actions: (copy.actions ?? [])
      .filter((/** @type {any} */ a) => offeredTypes.includes(a.type))
      .map((/** @type {any} */ a) => {
        if (a.type === 'create_task' && a.assign_to === 'parent' && !parent) {
          return { ...a, assign_to: 'record' };
        }
        if (a.type === 'set_field') return blankAction('set_field');
        if (a.type === 'notify') {
          return { ...a, to: (a.to ?? []).filter((/** @type {string} */ v) => offered.has(v)) };
        }
        return a;
      })
  };
}

/**
 * The note under a "changes to" value, or null until there is one.
 * @param {Field | null} field
 * @param {any} to
 */
export function changeHint(field, to) {
  if (!field || to === undefined || to === null || to === '') return null;
  let value = String(to);
  if (field.type === 'boolean') value = to === true || to === 'true' ? 'Yes' : 'No';
  if (field.type === 'choice') {
    value = field.choices.find((/** @type {any} */ c) => c.value === value)?.label ?? value;
  }
  return `Runs once, when the ${field.label.toLowerCase()} moves into ${value}; later edits do not run it again.`;
}

/**
 * A save's errors split between the rows the page shows and one general line
 * for the rest, so no refusal goes unseen.
 * @param {{ general?: string | null, rows?: Record<string, string> } | null | undefined} save
 * @param {(key: string) => boolean} shown
 * @returns {{ general: string | null, rows: Record<string, string> }}
 */
export function placeErrors(save, shown) {
  /** @type {Record<string, string>} */
  const rows = {};
  const rest = save?.general ? [save.general] : [];
  for (const [key, message] of Object.entries(save?.rows ?? {})) {
    const row = /^(conditions|actions)\.(\d+)$/.exec(key);
    if (shown(key)) rows[key] = message;
    else if (row) {
      rest.push(
        `${row[1] === 'conditions' ? 'Condition' : 'Action'} ${Number(row[2]) + 1}: ${message}`
      );
    } else rest.push(message);
  }
  return { general: rest.length ? rest.join(' ') : null, rows };
}

/** Keys the editor shows under their own section or field. */
const SECTION_KEYS = ['name', 'match', 'trigger', 'conditions', 'actions'];

/** @typedef {{ conditions: any[], actions: any[], copies: { conditions: string[], actions: string[] } }} SentRows */

/**
 * The rows a save sends: the row objects themselves, and a copy of each as it
 * was, so `editorErrors` can tell a row edited since.
 * @param {{ conditions?: any[], actions?: any[] }} draft
 * @returns {SentRows}
 */
export function sentRows(draft) {
  const conditions = [...(draft?.conditions ?? [])];
  const actions = [...(draft?.actions ?? [])];
  const copy = (/** @type {any} */ row) => JSON.stringify(row);
  return {
    conditions,
    actions,
    copies: { conditions: conditions.map(copy), actions: actions.map(copy) }
  };
}

/**
 * A save's errors as the editor shows them. A row's message goes to the row
 * object it was sent as, so it stays with that row when another is removed,
 * and leaves once that row is edited; anything with no place on the page
 * joins the general line.
 * @param {{ general?: string | null, rows?: Record<string, string> } | null | undefined} save
 * @param {SentRows} sent From `sentRows` when the save was sent.
 * @param {{ conditions: any[], actions?: any[] }} current The rows on the page now.
 * @returns {{ general: string | null, rows: Record<string, string>, conditions: (string | null)[], actions: (string | null)[] }}
 */
export function editorErrors(save, sent, current) {
  const asSent = { conditions: sent?.conditions ?? [], actions: sent?.actions ?? [] };
  const placed = placeErrors(save, (key) => {
    if (SECTION_KEYS.includes(key)) return true;
    const at = /^(conditions|actions)\.(\d+)$/.exec(key);
    return (
      Boolean(at) &&
      Number(at?.[2]) < asSent[/** @type {'conditions' | 'actions'} */ (at?.[1])].length
    );
  });
  /** @param {'conditions' | 'actions'} kind */
  const onRows = (kind) =>
    (current?.[kind] ?? []).map((/** @type {any} */ row) => {
      const at = asSent[kind].indexOf(row);
      if (at === -1 || sent?.copies?.[kind]?.[at] !== JSON.stringify(row)) return null;
      return placed.rows[`${kind}.${at}`] ?? null;
    });
  // "Add at least one action." and its like are about the list as sent.
  const now = current?.actions ?? [];
  const same = now.length === asSent.actions.length && now.every((a, i) => a === asSent.actions[i]);
  const { actions: listError, ...rows } = placed.rows;
  return {
    general: placed.general,
    rows: same && listError ? { ...rows, actions: listError } : rows,
    conditions: onRows('conditions'),
    actions: onRows('actions')
  };
}

/**
 * A saved rule's status: its list row's, or else what the rule itself says.
 * Null for a rule not saved yet.
 * @param {any} rule
 * @param {any} row
 * @returns {string | null}
 */
export function ruleStatus(rule, row) {
  if (!rule) return null;
  if (row?.status) return row.status;
  return rule.is_active ? 'on' : rule.paused_reason ? 'paused' : 'off';
}

/**
 * The second save button for a status, or null when the rule is already on.
 * @param {string | null | undefined} status Null for a rule not saved yet.
 */
export function switchLabel(status) {
  if (status === 'paused') return 'Save and take over';
  if (status === 'off' || status === null || status === undefined) return 'Save and switch on';
  return null;
}

/**
 * The settings hub row's value and warning from `automationSummary`.
 * @param {{ active: number, failing: number, attention: boolean } | null | undefined} summary
 * @returns {{ value: string | null, warn: boolean }}
 */
export function hubValue(summary) {
  if (!summary) return { value: null, warn: false };
  const rules = summary.active
    ? `${summary.active} active ${summary.active === 1 ? 'rule' : 'rules'}`
    : 'No active rules';
  return {
    value: summary.failing > 0 ? `${rules}, ${summary.failing} failing` : rules,
    warn: Boolean(summary.attention)
  };
}

/**
 * The sentence an automation notification shows, composed from `data`. Null for
 * any other verb or data of the wrong type, so the row keeps its usual copy.
 *
 * @param {any} n
 * @param {string} timeZone
 * @returns {{ text: string, source: string | null } | null}
 */
export function notificationText(n, timeZone) {
  const d = n?.data;
  if (!d || typeof d !== 'object' || Array.isArray(d)) return null;
  const str = (/** @type {unknown} */ v) => typeof v === 'string';
  switch (n.verb) {
    case 'automation.message':
      if (!str(d.message) || !str(d.rule)) return null;
      return { text: d.message, source: `From the rule "${d.rule}"` };
    case 'automation.failed':
      if (!str(d.rule) || !str(d.reason)) return null;
      return { text: `The rule "${d.rule}" failed: ${d.reason}`, source: null };
    case 'automation.paused':
      if (!str(d.reason) || !Array.isArray(d.rules) || !d.rules.every(str)) return null;
      return { text: `${d.reason} Paused: ${d.rules.join(', ')}.`, source: null };
    case 'automation.limit': {
      if (!str(d.window_start)) return null;
      const from = runTime(d.window_start, timeZone).replace(/^(Today|Yesterday) /, (w) =>
        w.toLowerCase()
      );
      return {
        text: `Automation reached its limit of 1,000 runs in the hour from ${from}. The rest of that hour's runs were skipped.`,
        source: null
      };
    }
    default:
      return null;
  }
}

/**
 * Who a notification row credits. The API's actor carries `user_details.email`
 * and no `name`.
 *
 * @param {any} n
 * @returns {string}
 */
export function actorName(n) {
  return n?.actor?.name || n?.actor?.user_details?.email || 'Someone';
}

export const AUTOMATION_FALLBACK = 'An automation rule sent a notification.';
