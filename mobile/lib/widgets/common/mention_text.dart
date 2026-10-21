import 'package:flutter/material.dart';

import '../../core/theme/theme.dart';
import '../../data/models/lookup_models.dart';

/// MENTION_RE in cases/notifications.py. The backend resolves the handle
/// against the email local part of an active member, so a chip appears only
/// where a notification went out. The web mirrors this in `lib/v2/mentions.js`.
final _mention = RegExp(r'(?<![A-Za-z0-9])@([A-Za-z0-9._-]+)');

/// The handles a comment can name: each active member's email local part.
Set<String> mentionHandles(Iterable<UserLookup> users) => {
  for (final u in users)
    if (u.isActive && u.email.contains('@'))
      u.email.split('@').first.toLowerCase(),
};

List<({String text, bool isMention})> mentionTokens(
  String body,
  Set<String> handles,
) {
  final out = <({String text, bool isMention})>[];
  var last = 0;
  for (final match in _mention.allMatches(body)) {
    if (match.start > last) {
      out.add((text: body.substring(last, match.start), isMention: false));
    }
    out.add((
      text: match.group(0)!,
      isMention: handles.contains(match.group(1)!.toLowerCase()),
    ));
    last = match.end;
  }
  if (last < body.length) {
    out.add((text: body.substring(last), isMention: false));
  }
  return out;
}

/// A comment body with each `@handle` that names a member drawn as a chip.
class MentionText extends StatelessWidget {
  final String text;
  final Set<String> handles;
  final TextStyle? style;

  const MentionText(this.text, {super.key, required this.handles, this.style});

  @override
  Widget build(BuildContext context) {
    return Text.rich(
      TextSpan(
        style: style,
        children: [
          for (final token in mentionTokens(text, handles))
            TextSpan(
              text: token.text,
              style: token.isMention
                  ? const TextStyle(
                      fontWeight: FontWeight.w600,
                      backgroundColor: AppColors.gray200,
                    )
                  : null,
            ),
        ],
      ),
    );
  }
}
