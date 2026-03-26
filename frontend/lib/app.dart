import 'package:fbuild_frontend/dashboard_page.dart';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:fbuild_frontend/api_client.dart';

class FBuildApp extends StatelessWidget {
  const FBuildApp({super.key, this.apiClient});

  final ApiClient? apiClient;

  @override
  Widget build(BuildContext context) {
    final baseTextTheme = GoogleFonts.manropeTextTheme();

    return MaterialApp(
      title: 'F-Build',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        scaffoldBackgroundColor: const Color(0xFFF5EFE4),
        colorScheme: const ColorScheme.light(
          primary: Color(0xFF1F4C45),
          secondary: Color(0xFFE76F51),
          surface: Color(0xFFFFFBF4),
          onPrimary: Colors.white,
          onSecondary: Colors.white,
          onSurface: Color(0xFF231F20),
        ),
        textTheme: baseTextTheme.copyWith(
          displayLarge: baseTextTheme.displayLarge?.copyWith(
            fontWeight: FontWeight.w800,
            letterSpacing: -1.6,
          ),
          displayMedium: baseTextTheme.displayMedium?.copyWith(
            fontWeight: FontWeight.w800,
            letterSpacing: -1.2,
          ),
          headlineMedium: baseTextTheme.headlineMedium?.copyWith(
            fontWeight: FontWeight.w800,
            letterSpacing: -0.8,
          ),
          titleLarge: baseTextTheme.titleLarge?.copyWith(
            fontWeight: FontWeight.w700,
          ),
          bodyLarge: baseTextTheme.bodyLarge?.copyWith(height: 1.45),
        ),
      ),
      home: DashboardPage(apiClient: apiClient),
    );
  }
}
