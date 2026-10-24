/**
 * What an inbound address actually does with mail, as opposed to what its
 * on/off switch says.
 *
 * `is_active` is one of three gates a delivery has to clear, and the page used
 * to draw it as the only one: an address was either "Creating tickets" or
 * "Creating nothing". Two states were drawn as the first and behave as the
 * second, both silently, because inbound mail has no user watching it fail:
 *
 * 1. **An unimplemented provider.** `InboundMailbox.PROVIDER_CHOICES` offers
 *    four, and `InboundMailboxWebhookView.post` answers 501 for `imap`. An IMAP
 *    address marked active accepts mail and opens nothing, forever.
 * 2. **An unconnected address.** An SES address needs both a valid SNS
 *    signature and a `topic_arn` that matches this mailbox, because a signature
 *    alone only proves the message came from *some* topic in *some* AWS
 *    account. A mailbox gets its pin one of two ways: an admin enters the Topic
 *    ARN, or a signature-verified SubscriptionConfirmation arrives from a topic
 *    in an AWS account the server allows (`INBOUND_SNS_ACCOUNT_IDS`). A Postmark
 *    or Mailgun address needs a stored `webhook_secret` (`has_webhook_secret`,
 *    which only admins are sent); with none, every post is refused.
 *
 * A generated address (`is_generated`) has no pin of its own: the server's
 * catch-all webhook checks its one topic for every generated address.
 *
 * The states are ordered as the webhook itself checks them, so `deliveryState`
 * answers "which gate does a delivery fail first", and an address that clears
 * all three is the only one called live. Nothing here is a security control:
 * every gate is enforced in `cases/inbound_views.py`, and this only decides
 * what the page says about it.
 *
 * `mobile/lib/data/models/mailbox.dart` carries the same rules.
 */

/** The providers the webhook actually handles. `imap` 501s. */
export const SUPPORTED_PROVIDERS = ['ses', 'mailgun', 'postmark'];

/** Providers whose deliveries are proved by a stored `webhook_secret`. */
export const SECRET_PROVIDERS = ['mailgun', 'postmark'];

/**
 * The first gate mail to this address would fail, or `'live'`.
 *
 * @param {{ is_active?: boolean, provider?: string, has_topic_arn?: boolean, has_webhook_secret?: boolean, is_generated?: boolean }} mailbox
 * @returns {'off' | 'unsupported' | 'unconfirmed' | 'live'}
 */
export function deliveryState(mailbox) {
  if (!mailbox?.is_active) return 'off';
  if (!SUPPORTED_PROVIDERS.includes(mailbox.provider)) return 'unsupported';
  // Fails closed: a row that does not say (a member is not sent
  // `has_webhook_secret`) reads as not connected.
  if (SECRET_PROVIDERS.includes(mailbox.provider)) {
    return mailbox.has_webhook_secret === true ? 'live' : 'unconfirmed';
  }
  if (!mailbox.has_topic_arn && !mailbox.is_generated) return 'unconfirmed';
  return 'live';
}

const LABEL = {
  off: 'Creating nothing',
  unsupported: 'Provider not wired up',
  unconfirmed: 'Not connected yet',
  live: 'Creating tickets'
};

/**
 * @param {string} state
 * @param {string} [creates] the mailbox's `creates`: `tickets` or `leads`
 */
export function deliveryLabel(state, creates = 'tickets') {
  if (state === 'live' && creates === 'leads') return 'Creating leads';
  return LABEL[state] ?? LABEL.off;
}

const TONE = {
  off: 'clay',
  unsupported: 'rust',
  unconfirmed: 'clay',
  live: 'moss'
};

/** @param {string} state */
export function deliveryTone(state) {
  return TONE[state] ?? TONE.off;
}

/**
 * Why nothing is arriving, in the words the page uses, or null when it is.
 *
 * `providerLabel` is passed in rather than imported so this module stays free
 * of the enum map the page already holds.
 *
 * @param {string} state
 * @param {string} providerLabel
 * @param {string} [creates] the mailbox's `creates`: `tickets` or `leads`
 * @param {string} [provider] the mailbox's provider value
 */
export function deliveryExplanation(state, providerLabel, creates = 'tickets', provider = 'ses') {
  if (state === 'off') {
    return creates === 'leads'
      ? 'Mail still arrives here and no lead is made. Nothing bounces, so a portal or a person writing here gets no error and the enquiry is lost.'
      : 'Mail still arrives here and no ticket is opened. Nothing bounces, so whoever wrote gets silence rather than an error.';
  }
  if (state === 'unsupported') {
    return `${providerLabel} deliveries are not implemented. The webhook refuses them, so mail to this address becomes nothing whatever else is set here.`;
  }
  if (state === 'unconfirmed') {
    if (SECRET_PROVIDERS.includes(provider)) {
      return `Waiting for its ${provider === 'postmark' ? 'basic-auth password' : 'signing key'}. Every post is refused until an admin stores the webhook secret on this address.`;
    }
    return 'Waiting for its SNS topic. Every message is refused until this address has a Topic ARN: an admin can enter it here, or it is set when AWS confirms a subscription from an AWS account this server allows.';
  }
  return null;
}

/**
 * The addresses that would actually open a ticket right now.
 *
 * Derived from the rows rather than read off the server's `totals.active`,
 * which counts `is_active` and nothing else. `GET /cases/mailboxes/` returns
 * every mailbox in the org unfiltered and unpaginated, so this counts the same
 * set the total does, and answers the question the header asks.
 *
 * @param {any[]} mailboxes
 */
export function deliveringCount(mailboxes) {
  return (mailboxes ?? []).filter((m) => deliveryState(m) === 'live').length;
}

/**
 * The rows worth a banner: on, and creating nothing.
 *
 * An off address is left out on purpose. Somebody chose that, and it is the
 * one state of the three the row already reads correctly.
 *
 * @param {any[]} mailboxes
 */
export function silentMailboxes(mailboxes) {
  return (mailboxes ?? []).filter((m) => {
    const state = deliveryState(m);
    return state === 'unsupported' || state === 'unconfirmed';
  });
}

/**
 * The provider select's label for one choice.
 *
 * `imap` stays selectable: the column accepts it, and hiding it would silently
 * rewrite a mailbox already set to it. It says so instead.
 *
 * @param {string} value
 * @param {string} label
 */
export function providerChoiceLabel(value, label) {
  return SUPPORTED_PROVIDERS.includes(value) ? label : `${label} (not wired up yet)`;
}

/**
 * The URL to give the provider for one mailbox, built from the API host.
 *
 * Postmark carries the secret as the basic-auth password, so the URL shows a
 * `<secret>` placeholder, never the stored value (which the client never has).
 * Mailgun's route action wraps the URL in `forward()`. Null for SES and IMAP.
 *
 * @param {string} provider
 * @param {string} id the mailbox id
 * @param {string} apiBase the API origin, e.g. `https://api.example.com`
 * @returns {string | null}
 */
export function webhookSetupUrl(provider, id, apiBase) {
  if (!SECRET_PROVIDERS.includes(provider) || !id || !apiBase) return null;
  const base = apiBase.replace(/\/+$/, '');
  const path = `/api/cases/inbound/${id}/`;
  if (provider === 'postmark') {
    return base.replace(/^(https?:\/\/)/, '$1postmark:<secret>@') + path;
  }
  return `forward("${base}${path}")`;
}
