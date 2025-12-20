import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'core/theme/theme.dart';
import 'providers/settings_provider.dart';
import 'routes/app_router.dart';
import 'services/auth_service.dart';
import 'services/settings_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Initialize services
  await AuthService().initialize();
  await SettingsService().initialize();

  // Set system UI overlay style
  SystemChrome.setSystemUIOverlayStyle(
    const SystemUiOverlayStyle(
      statusBarColor: Colors.transparent,
      statusBarIconBrightness: Brightness.dark,
      systemNavigationBarColor: AppColors.surface,
      systemNavigationBarIconBrightness: Brightness.dark,
    ),
  );

  // Lock to portrait mode for optimal CRM experience
  SystemChrome.setPreferredOrientations([
    DeviceOrientation.portraitUp,
    DeviceOrientation.portraitDown,
  ]);

  runApp(
    const ProviderScope(
      child: BottleCRMApp(),
    ),
  );
}

/// BottleCRM - Main Application Widget
class BottleCRMApp extends ConsumerStatefulWidget {
  const BottleCRMApp({super.key});

  @override
  ConsumerState<BottleCRMApp> createState() => _BottleCRMAppState();
}

class _BottleCRMAppState extends ConsumerState<BottleCRMApp> {
  @override
  void initState() {
    super.initState();
    // Initialize settings provider from persisted values
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(settingsProvider.notifier).initialize();
    });
  }

  @override
  Widget build(BuildContext context) {
    final router = ref.watch(appRouterProvider);
    final fontScale = ref.watch(fontScaleProvider);

    return MediaQuery(
      data: MediaQuery.of(context).copyWith(
        textScaler: TextScaler.linear(fontScale),
      ),
      child: MaterialApp.router(
        title: 'BottleCRM',
        debugShowCheckedModeBanner: false,

        // Theme
        theme: AppTheme.light,
        darkTheme: AppTheme.dark,
        themeMode: ThemeMode.light,

        // Router
        routerConfig: router,

        // Scroll behavior for smooth scrolling
        scrollBehavior: const MaterialScrollBehavior().copyWith(
          physics: const BouncingScrollPhysics(),
        ),
      ),
    );
  }
}
