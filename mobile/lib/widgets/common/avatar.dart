import 'package:flutter/material.dart';
import '../../core/theme/theme.dart';

/// Avatar sizes
enum AvatarSize {
  xs(24),
  sm(32),
  md(40),
  lg(48),
  xl(64),
  xxl(80);

  final double size;
  const AvatarSize(this.size);

  double get fontSize {
    switch (this) {
      case AvatarSize.xs:
        return 10;
      case AvatarSize.sm:
        return 12;
      case AvatarSize.md:
        return 14;
      case AvatarSize.lg:
        return 16;
      case AvatarSize.xl:
        return 20;
      case AvatarSize.xxl:
        return 24;
    }
  }
}

/// User Avatar Widget
/// Displays user avatar image or initials fallback
class UserAvatar extends StatelessWidget {
  final String? imageUrl;
  final String name;
  final AvatarSize size;
  final Color? backgroundColor;
  final VoidCallback? onTap;
  final bool showBorder;

  const UserAvatar({
    super.key,
    this.imageUrl,
    required this.name,
    this.size = AvatarSize.md,
    this.backgroundColor,
    this.onTap,
    this.showBorder = false,
  });

  String get _initials {
    final parts = name.trim().split(' ');
    if (parts.length >= 2) {
      return '${parts[0][0]}${parts[1][0]}'.toUpperCase();
    } else if (parts.isNotEmpty && parts[0].isNotEmpty) {
      return parts[0][0].toUpperCase();
    }
    return '?';
  }

  Color get _backgroundColor {
    if (backgroundColor != null) return backgroundColor!;
    return AppColors.getAvatarColor(name);
  }

  @override
  Widget build(BuildContext context) {
    final avatar = Container(
      width: size.size,
      height: size.size,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        color: _backgroundColor,
        border: showBorder
            ? Border.all(color: Colors.white, width: 2)
            : null,
        boxShadow: showBorder ? AppLayout.shadowSm : null,
      ),
      child: imageUrl != null && imageUrl!.isNotEmpty
          ? ClipOval(
              child: Image.network(
                imageUrl!,
                fit: BoxFit.cover,
                errorBuilder: (context, error, stackTrace) => _InitialsAvatar(
                  initials: _initials,
                  fontSize: size.fontSize,
                ),
              ),
            )
          : _InitialsAvatar(
              initials: _initials,
              fontSize: size.fontSize,
            ),
    );

    if (onTap != null) {
      return GestureDetector(
        onTap: onTap,
        child: avatar,
      );
    }

    return avatar;
  }
}

class _InitialsAvatar extends StatelessWidget {
  final String initials;
  final double fontSize;

  const _InitialsAvatar({
    required this.initials,
    required this.fontSize,
  });

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Text(
        initials,
        style: TextStyle(
          color: Colors.white,
          fontSize: fontSize,
          fontWeight: FontWeight.w600,
          letterSpacing: -0.5,
        ),
      ),
    );
  }
}

/// Avatar Stack - Shows multiple overlapping avatars
class AvatarStack extends StatelessWidget {
  final List<String> names;
  final List<String?> imageUrls;
  final AvatarSize size;
  final int maxDisplay;
  final double overlapFactor;

  const AvatarStack({
    super.key,
    required this.names,
    this.imageUrls = const [],
    this.size = AvatarSize.sm,
    this.maxDisplay = 3,
    this.overlapFactor = 0.3,
  });

  @override
  Widget build(BuildContext context) {
    final displayCount = names.length > maxDisplay ? maxDisplay : names.length;
    final remaining = names.length - maxDisplay;

    return SizedBox(
      height: size.size,
      child: Stack(
        clipBehavior: Clip.none,
        children: [
          for (int i = 0; i < displayCount; i++)
            Positioned(
              left: i * size.size * (1 - overlapFactor),
              child: UserAvatar(
                name: names[i],
                imageUrl: i < imageUrls.length ? imageUrls[i] : null,
                size: size,
                showBorder: true,
              ),
            ),
          if (remaining > 0)
            Positioned(
              left: displayCount * size.size * (1 - overlapFactor),
              child: Container(
                width: size.size,
                height: size.size,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: AppColors.gray200,
                  border: Border.all(color: Colors.white, width: 2),
                ),
                child: Center(
                  child: Text(
                    '+$remaining',
                    style: TextStyle(
                      color: AppColors.gray600,
                      fontSize: size.fontSize - 2,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }
}
