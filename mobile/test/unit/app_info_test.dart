import 'dart:io';

import 'package:bottle_crm/core/app_info.dart';
import 'package:flutter_test/flutter_test.dart';

/// The header carries `appVersion`, and the store build carries the pubspec's
/// version. The server tells this build from older ones by the header, so the
/// two must not drift apart.
void main() {
  test('appVersion is the pubspec version without its build number', () {
    final line = File(
      'pubspec.yaml',
    ).readAsLinesSync().firstWhere((l) => l.startsWith('version:'));
    final version = line.substring('version:'.length).trim().split('+').first;
    expect(appVersion, version);
  });
}
