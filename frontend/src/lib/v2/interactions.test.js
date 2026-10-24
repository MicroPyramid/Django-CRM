import { describe, it, expect } from 'vitest';
import {
  durationText,
  interactionTitle,
  responseTimeText,
  secondsSince,
  spanText,
  whatsappHref
} from '#lib/v2/interactions.js';

describe('spanText', () => {
  it('reads as a person would say it', () => {
    expect(spanText(0)).toBe('under a minute');
    expect(spanText(59)).toBe('under a minute');
    expect(spanText(60)).toBe('1 min');
    expect(spanText(14 * 60 + 59)).toBe('14 min');
    expect(spanText(2 * 3600 + 14 * 60)).toBe('2 h 14 min');
    expect(spanText(3 * 3600)).toBe('3 h');
    expect(spanText(3 * 86400 + 4 * 3600 + 30 * 60)).toBe('3 d 4 h');
    expect(spanText(2 * 86400)).toBe('2 d');
  });

  it('is empty for no value and zero for a clock that ran backwards', () => {
    expect(spanText(null)).toBe('');
    expect(spanText(undefined)).toBe('');
    expect(spanText(Number.NaN)).toBe('');
    expect(spanText(-30)).toBe('under a minute');
  });
});

describe('secondsSince', () => {
  it('counts from an ISO instant to now', () => {
    const now = new Date('2026-10-24T12:00:00Z');
    expect(secondsSince('2026-10-24T09:46:00Z', now)).toBe(2 * 3600 + 14 * 60);
    expect(secondsSince(null, now)).toBeNull();
    expect(secondsSince('nonsense', now)).toBeNull();
  });
});

describe('durationText', () => {
  it('marks an estimate', () => {
    expect(durationText(240)).toBe('4 min');
    expect(durationText(240, true)).toBe('about 4 min');
    expect(durationText(null, true)).toBe('');
  });
});

describe('responseTimeText', () => {
  it('is the first response minus creation, empty before one', () => {
    expect(
      responseTimeText({
        created_at: '2026-10-24T09:00:00Z',
        first_response_at: '2026-10-24T09:12:00Z'
      })
    ).toBe('12 min');
    expect(responseTimeText({ created_at: '2026-10-24T09:00:00Z', first_response_at: null })).toBe(
      ''
    );
  });
});

describe('interactionTitle', () => {
  it('names the kind and the direction', () => {
    expect(interactionTitle({ kind: 'call', direction: 'outbound' })).toBe('Outgoing call');
    expect(interactionTitle({ kind: 'call', direction: 'inbound' })).toBe('Incoming call');
    expect(interactionTitle({ kind: 'meeting', direction: 'inbound' })).toBe('Meeting');
    expect(interactionTitle({ kind: 'sms', direction: 'outbound' })).toBe('Text sent');
    expect(interactionTitle({ kind: 'whatsapp', direction: 'inbound' })).toBe('WhatsApp received');
  });

  it('says where an enquiry came from', () => {
    expect(interactionTitle({ kind: 'enquiry', origin: 'webform' })).toBe('Enquiry via web form');
    expect(interactionTitle({ kind: 'enquiry', origin: 'intake' })).toBe(
      'Enquiry via lead webhook'
    );
    expect(interactionTitle({ kind: 'enquiry', origin: 'meta_ads' })).toBe('Enquiry via meta_ads');
    expect(interactionTitle({ kind: 'enquiry', origin: '' })).toBe('Enquiry');
  });
});

describe('whatsappHref', () => {
  it('links the E.164 digits', () => {
    expect(whatsappHref('+919876543210')).toBe('https://wa.me/919876543210');
  });

  it('refuses anything that is not E.164', () => {
    expect(whatsappHref('')).toBeNull();
    expect(whatsappHref(null)).toBeNull();
    expect(whatsappHref('98765 43210')).toBeNull();
    expect(whatsappHref('+0123456789')).toBeNull();
    expect(whatsappHref('+1234')).toBeNull();
    expect(whatsappHref('+1 555 0100')).toBeNull();
  });
});
