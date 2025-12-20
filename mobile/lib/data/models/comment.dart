/// Comment model for notes on leads, deals, etc.
class Comment {
  final String id;
  final String comment;
  final DateTime commentedOn;
  final String? commentedById;
  final String? commentedByName;
  final String? commentedByEmail;

  const Comment({
    required this.id,
    required this.comment,
    required this.commentedOn,
    this.commentedById,
    this.commentedByName,
    this.commentedByEmail,
  });

  /// Get display name for the commenter
  String get authorName {
    if (commentedByName != null && commentedByName!.isNotEmpty) {
      return commentedByName!;
    }
    if (commentedByEmail != null && commentedByEmail!.isNotEmpty) {
      return commentedByEmail!.split('@').first;
    }
    return 'Unknown';
  }

  /// Factory constructor to create Comment from JSON
  factory Comment.fromJson(Map<String, dynamic> json) {
    // Handle commented_by which can be a map or an ID
    String? commentedById;
    String? commentedByName;
    String? commentedByEmail;

    final commentedBy = json['commented_by'];
    if (commentedBy is Map<String, dynamic>) {
      commentedById = commentedBy['id']?.toString();
      commentedByEmail = commentedBy['user__email'] as String? ??
          commentedBy['email'] as String?;
      commentedByName = commentedBy['user__first_name'] as String? ??
          commentedBy['first_name'] as String?;
      if (commentedByName != null) {
        final lastName = commentedBy['user__last_name'] as String? ??
            commentedBy['last_name'] as String?;
        if (lastName != null && lastName.isNotEmpty) {
          commentedByName = '$commentedByName $lastName';
        }
      }
    } else if (commentedBy != null) {
      commentedById = commentedBy.toString();
    }

    return Comment(
      id: json['id']?.toString() ?? '',
      comment: json['comment'] as String? ?? '',
      commentedOn: json['commented_on'] != null
          ? DateTime.tryParse(json['commented_on'] as String) ?? DateTime.now()
          : DateTime.now(),
      commentedById: commentedById,
      commentedByName: commentedByName,
      commentedByEmail: commentedByEmail,
    );
  }

  /// Convert Comment to JSON
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'comment': comment,
      'commented_on': commentedOn.toIso8601String(),
      'commented_by': commentedById,
    };
  }

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is Comment && runtimeType == other.runtimeType && id == other.id;

  @override
  int get hashCode => id.hashCode;
}
