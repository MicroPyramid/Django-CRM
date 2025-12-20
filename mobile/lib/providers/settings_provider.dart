import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../services/settings_service.dart';

/// Re-export FontSizeOption for convenience
export '../services/settings_service.dart' show FontSizeOption;

/// Settings state for the app
class SettingsState {
  final FontSizeOption fontSize;

  const SettingsState({
    this.fontSize = FontSizeOption.defaultSize,
  });

  /// Initial state
  const SettingsState.initial() : fontSize = FontSizeOption.defaultSize;

  /// Get font scale factor
  double get fontScale => fontSize.scale;

  /// Create a copy with updated fields
  SettingsState copyWith({
    FontSizeOption? fontSize,
  }) {
    return SettingsState(
      fontSize: fontSize ?? this.fontSize,
    );
  }

  @override
  String toString() => 'SettingsState(fontSize: ${fontSize.label})';
}

/// Notifier for settings state changes
class SettingsNotifier extends StateNotifier<SettingsState> {
  SettingsNotifier() : super(const SettingsState.initial());

  final SettingsService _settingsService = SettingsService();

  /// Initialize settings from storage (call on app launch)
  Future<void> initialize() async {
    debugPrint('SettingsNotifier: Initializing...');

    // SettingsService.initialize() should have been called before this
    state = state.copyWith(
      fontSize: _settingsService.fontSize,
    );

    debugPrint('SettingsNotifier: Initialized with font size: ${state.fontSize.label}');
  }

  /// Set font size preference
  Future<void> setFontSize(FontSizeOption size) async {
    debugPrint('SettingsNotifier: Setting font size to ${size.label}...');

    // Update state immediately for live preview
    state = state.copyWith(fontSize: size);

    // Persist to storage
    await _settingsService.setFontSize(size);

    debugPrint('SettingsNotifier: Font size set to ${size.label}');
  }
}

/// Provider for settings state
final settingsProvider = StateNotifierProvider<SettingsNotifier, SettingsState>((ref) {
  return SettingsNotifier();
});

/// Convenience provider for font scale
final fontScaleProvider = Provider<double>((ref) {
  return ref.watch(settingsProvider).fontScale;
});

/// Convenience provider for current font size option
final fontSizeOptionProvider = Provider<FontSizeOption>((ref) {
  return ref.watch(settingsProvider).fontSize;
});
