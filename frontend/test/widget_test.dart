import 'package:fbuild_frontend/api_client.dart';
import 'package:fbuild_frontend/app.dart';
import 'package:fbuild_frontend/models.dart';
import 'package:fbuild_frontend/dashboard_page.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

class FakeApiClient extends ApiClient {
  @override
  Future<Project> createProject(String repoUrl) async {
    return Project(
      id: 1,
      name: 'mobile-app',
      repoUrl: repoUrl,
      slug: 'mobile-app',
      workspacePath: '/tmp/mobile-app',
      isActive: true,
      defaultBranch: 'main',
      lastSyncAt: null,
      createdAt: DateTime.now().toIso8601String(),
      updatedAt: DateTime.now().toIso8601String(),
    );
  }

  @override
  Future<BuildJob?> getCurrentBuild() async => null;

  @override
  Future<BuildJob> createBuildJob({
    required int projectId,
    required String branch,
    required String platform,
  }) async {
    return BuildJob(
      id: 12,
      projectId: projectId,
      branch: branch,
      platform: platform,
      status: 'queued',
      requestedAt: '2026-03-26T00:00:00Z',
      startedAt: null,
      finishedAt: null,
      commitSha: null,
      artifactPath: null,
      pgyerUrl: null,
      errorMessage: null,
      queuePosition: 1,
    );
  }

  @override
  Future<List<Project>> listProjects() async {
    return const [
      Project(
        id: 1,
        name: 'mobile-app',
        repoUrl: 'https://github.com/acme/mobile-app.git',
        slug: 'mobile-app',
        workspacePath: '/tmp/mobile-app',
        isActive: true,
        defaultBranch: 'main',
        lastSyncAt: null,
        createdAt: '2026-03-26T00:00:00Z',
        updatedAt: '2026-03-26T00:00:00Z',
      ),
    ];
  }

  @override
  Future<List<ProjectBranch>> listProjectBranches(int projectId) async {
    return const [
      ProjectBranch(
        name: 'main',
        commitSha: 'abc1234',
        commitDate: '2026-03-26T00:00:00Z',
        commitSubject: 'bootstrap project',
      ),
    ];
  }

  @override
  Future<List<BuildJob>> listQueuedBuilds() async => const [];
}

void main() {
  testWidgets('renders dashboard title and project card', (tester) async {
    await tester.pumpWidget(
      MaterialApp(home: DashboardPage(apiClient: FakeApiClient())),
    );
    await tester.pumpAndSettle();

    expect(find.text('F-Build'), findsOneWidget);
    expect(find.text('mobile-app'), findsWidgets);
  });

  testWidgets('loads branches and shows build actions', (tester) async {
    await tester.pumpWidget(
      MaterialApp(home: DashboardPage(apiClient: FakeApiClient())),
    );
    await tester.pumpAndSettle();

    await tester.ensureVisible(find.text('查看分支'));
    await tester.tap(find.text('查看分支'));
    await tester.pumpAndSettle();

    expect(find.text('main'), findsOneWidget);
    expect(find.text('发起 Android'), findsOneWidget);
    expect(find.text('发起 iOS'), findsOneWidget);
  });

  testWidgets('app boots without debug banner', (tester) async {
    await tester.pumpWidget(FBuildApp(apiClient: FakeApiClient()));
    expect(find.byType(Banner), findsNothing);
  });
}
