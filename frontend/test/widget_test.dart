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
  Future<BuildJob> getBuildJob(int jobId) async {
    return BuildJob(
      id: jobId,
      projectId: 1,
      branch: 'main',
      platform: 'android',
      status: 'success',
      requestedAt: '2026-03-26T00:00:00Z',
      startedAt: '2026-03-26T00:00:10Z',
      finishedAt: '2026-03-26T00:01:00Z',
      commitSha: 'abc1234',
      artifactPath: '/tmp/app-release.apk',
      pgyerUrl: 'https://www.pgyer.com/demo',
      errorMessage: null,
      queuePosition: null,
    );
  }

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
  Future<List<BuildLogEntry>> listBuildLogs({
    required int jobId,
    int afterSeq = 0,
  }) async {
    if (afterSeq > 0) {
      return const [];
    }
    return const [
      BuildLogEntry(
        id: 1,
        jobId: 12,
        seq: 1,
        stream: 'system',
        message: 'Build job queued.',
        createdAt: '2026-03-26T00:00:00Z',
      ),
    ];
  }

  @override
  Future<List<BuildJob>> listRecentBuilds({int limit = 20}) async {
    return const [
      BuildJob(
        id: 12,
        projectId: 1,
        branch: 'main',
        platform: 'android',
        status: 'success',
        requestedAt: '2026-03-26T00:00:00Z',
        startedAt: '2026-03-26T00:00:10Z',
        finishedAt: '2026-03-26T00:01:00Z',
        commitSha: 'abc1234',
        artifactPath: '/tmp/app-release.apk',
        pgyerUrl: 'https://www.pgyer.com/demo',
        errorMessage: null,
        queuePosition: null,
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

  testWidgets('opens recent build details and shows logs', (tester) async {
    await tester.pumpWidget(
      MaterialApp(home: DashboardPage(apiClient: FakeApiClient())),
    );
    await tester.pumpAndSettle();

    await tester.ensureVisible(find.text('Job #12 · Project #1'));
    await tester.tap(find.text('Job #12 · Project #1'));
    await tester.pumpAndSettle();

    expect(find.text('复制蒲公英链接'), findsOneWidget);
    expect(
      find.byWidgetPredicate(
        (widget) =>
            widget is RichText &&
            widget.text.toPlainText().contains('Build job queued.'),
      ),
      findsOneWidget,
    );
  });
}
