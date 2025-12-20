import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Font size options for the app
enum FontSizeOption {
  small('Small', 1.0),
  defaultSize('Default', 1.25),
  large('Large', 1.5);

  const FontSizeOption(this.label, this.scale);
  final String label;
  final double scale;

  /// Get FontSizeOption from stored string value
  static FontSizeOption fromString(String? value) {
    switch (value) {
      case 'small':
        return FontSizeOption.small;
      case 'large':
        return FontSizeOption.large;
      default:
        return FontSizeOption.defaultSize;
    }
  }

  /// Get string value for storage
  String toStorageString() {
    switch (this) {
      case FontSizeOption.small:
        return 'small';
      case FontSizeOption.large:
        return 'large';
      case FontSizeOption.defaultSize:
        return 'default';
    }
  }
}

/// Settings service for persisting app preferences
class SettingsService {
  static final SettingsService _instance = SettingsService._internal();
  factory SettingsService() => _instance;
  SettingsService._internal();

  // Storage keys
  static const String _fontSizeKey = 'font_size_preference';

  // State
  FontSizeOption _fontSize = FontSizeOption.defaultSize;

  // Getters
  FontSizeOption get fontSize => _fontSize;
  double get fontScale => _fontSize.scale;

  /// Initialize the settings service - call on app startup
  Future<void> initialize() async {
    debugPrint('SettingsService: Initializing...');
    await _loadFromStorage();
    debugPrint('SettingsService: Initialized with font size: ${_fontSize.label}');
  }

  /// Set font size preference
  Future<void> setFontSize(FontSizeOption size) async {
    _fontSize = size;
    await _saveToStorage();
    debugPrint('SettingsService: Font size set to ${size.label}');
  }

  /// Load settings from SharedPreferences
  Future<void> _loadFromStorage() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final fontSizeValue = prefs.getString(_fontSizeKey);
      _fontSize = FontSizeOption.fromString(fontSizeValue);
    } catch (e) {
      debugPrint('SettingsService: Error loading settings: $e');
      _fontSize = FontSizeOption.defaultSize;
    }
  }

  /// Save settings to SharedPreferences
  Future<void> _saveToStorage() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(_fontSizeKey, _fontSize.toStorageString());
    } catch (e) {
      debugPrint('SettingsService: Error saving settings: $e');
    }
  }
}
