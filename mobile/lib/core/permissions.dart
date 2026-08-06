/// Client-side mirrors of the server's authorization rules.
///
/// These decide which affordances to *offer*. They are not a security
/// boundary: the DRF views re-check every one of them, and a caller with curl
/// never runs this file. The point is to stop offering actions the server will
/// answer with a 403, which is how a member came to see "Delete" on ten
/// records they could not delete.
///
/// Keep each rule beside the view that enforces it, named in the doc comment,
/// so the two can be checked against each other.
library;

/// Whether the signed-in user is an org admin or the record's owner.
///
/// This one rule appears three times on the server under different names:
/// `LeadDetailView.delete` and `OpportunityDetailView.delete` allow admins and
/// the creator (assignment grants read and edit there, never delete), and
/// `cases.kb_access.has_solution_write_access` allows admins and the author for
/// both editing and deleting an article.
///
/// [currentUserKey] and [ownerKey] must be the same kind of identifier as each
/// other: two emails, or two user ids. Which one depends on what the endpoint
/// serialises, so the caller picks and the comparison stays honest.
///
/// Returns `false` when the owner is unknown, so an unparsed payload hides the
/// action rather than offering one that may fail. [isAdmin] short-circuits
/// first, so an admin is never blocked by a missing owner.
bool isAdminOrOwner({
  required bool isAdmin,
  required String? currentUserKey,
  required String? ownerKey,
}) {
  if (isAdmin) return true;
  final me = currentUserKey?.trim().toLowerCase();
  final owner = ownerKey?.trim().toLowerCase();
  if (me == null || me.isEmpty || owner == null || owner.isEmpty) return false;
  return me == owner;
}
