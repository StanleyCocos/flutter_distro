import 'dart:async';

import 'package:fbuild_frontend/api_client.dart';
import 'package:fbuild_frontend/models.dart';
import 'package:flutter/material.dart';

class DashboardPage extends StatefulWidget {
  const DashboardPage({super.key, ApiClient? apiClient})
    : _apiClient = apiClient;

  final ApiClient? _apiClient;

  @override
  State<DashboardPage> createState() => _DashboardPageState();
}

class _DashboardPageState extends State<DashboardPage> {
  late final ApiClient _apiClient;
  final TextEditingController _repoController = TextEditingController();

  Timer? _pollingTimer;
  bool _initialLoading = true;
  bool _submitting = false;
  String? _errorMessage;
  List<Project> _projects = const <Project>[];
  List<BuildJob> _queuedJobs = const <BuildJob>[];
  BuildJob? _currentBuild;
  DateTime? _lastUpdatedAt;
  final Map<int, List<ProjectBranch>> _projectBranches =
      <int, List<ProjectBranch>>{};
  final Set<int> _syncingProjectIds = <int>{};
  final Set<int> _loadingBranchProjectIds = <int>{};
  final Map<int, String> _branchErrors = <int, String>{};
  final Set<String> _submittingBuildKeys = <String>{};

  @override
  void initState() {
    super.initState();
    _apiClient = widget._apiClient ?? ApiClient();
    unawaited(_loadDashboard());
    _pollingTimer = Timer.periodic(
      const Duration(seconds: 5),
      (_) => unawaited(_loadDashboard(showLoading: false)),
    );
  }

  @override
  void dispose() {
    _pollingTimer?.cancel();
    _repoController.dispose();
    super.dispose();
  }

  Future<void> _loadDashboard({bool showLoading = true}) async {
    if (showLoading) {
      setState(() {
        _initialLoading = true;
        _errorMessage = null;
      });
    }

    try {
      final results = await Future.wait([
        _apiClient.listProjects(),
        _apiClient.getCurrentBuild(),
        _apiClient.listQueuedBuilds(),
      ]);

      if (!mounted) {
        return;
      }

      setState(() {
        _projects = results[0] as List<Project>;
        _currentBuild = results[1] as BuildJob?;
        _queuedJobs = results[2] as List<BuildJob>;
        _lastUpdatedAt = DateTime.now();
        _errorMessage = null;
      });
    } catch (error) {
      if (!mounted) {
        return;
      }
      setState(() {
        _errorMessage = error.toString();
      });
    } finally {
      if (mounted) {
        setState(() {
          _initialLoading = false;
        });
      }
    }
  }

  Future<void> _submitProject() async {
    final repoUrl = _repoController.text.trim();
    if (repoUrl.isEmpty) {
      setState(() {
        _errorMessage = '请先输入 Git 仓库地址。';
      });
      return;
    }

    setState(() {
      _submitting = true;
      _errorMessage = null;
    });

    try {
      await _apiClient.createProject(repoUrl);
      _repoController.clear();
      await _loadDashboard(showLoading: false);

      if (!mounted) {
        return;
      }
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('项目已加入构建系统。')));
    } catch (error) {
      if (!mounted) {
        return;
      }
      setState(() {
        _errorMessage = error.toString();
      });
    } finally {
      if (mounted) {
        setState(() {
          _submitting = false;
        });
      }
    }
  }

  Future<void> _syncAndLoadBranches(Project project) async {
    setState(() {
      _syncingProjectIds.add(project.id);
      _branchErrors.remove(project.id);
    });

    try {
      final syncedProject = await _apiClient.syncProject(project.id);
      final branches = await _apiClient.listProjectBranches(project.id);

      if (!mounted) {
        return;
      }

      setState(() {
        _projects = _projects
            .map((item) => item.id == syncedProject.id ? syncedProject : item)
            .toList(growable: false);
        _projectBranches[project.id] = branches;
      });
    } catch (error) {
      if (!mounted) {
        return;
      }

      setState(() {
        _branchErrors[project.id] = error.toString();
      });
    } finally {
      if (mounted) {
        setState(() {
          _syncingProjectIds.remove(project.id);
        });
      }
    }
  }

  Future<void> _loadBranches(Project project) async {
    setState(() {
      _loadingBranchProjectIds.add(project.id);
      _branchErrors.remove(project.id);
    });

    try {
      final branches = await _apiClient.listProjectBranches(project.id);

      if (!mounted) {
        return;
      }

      setState(() {
        _projectBranches[project.id] = branches;
      });
    } catch (error) {
      if (!mounted) {
        return;
      }

      setState(() {
        _branchErrors[project.id] = error.toString();
      });
    } finally {
      if (mounted) {
        setState(() {
          _loadingBranchProjectIds.remove(project.id);
        });
      }
    }
  }

  Future<void> _submitBuild(
    Project project,
    ProjectBranch branch,
    String platform,
  ) async {
    final actionKey = '${project.id}:${branch.name}:$platform';

    setState(() {
      _submittingBuildKeys.add(actionKey);
    });

    try {
      final job = await _apiClient.createBuildJob(
        projectId: project.id,
        branch: branch.name,
        platform: platform,
      );
      await _loadDashboard(showLoading: false);

      if (!mounted) {
        return;
      }

      final platformLabel = platform == 'ios' ? 'iOS' : 'Android';
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('$platformLabel 构建任务已创建，队列任务 #${job.id}')),
      );
    } catch (error) {
      if (!mounted) {
        return;
      }

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          backgroundColor: const Color(0xFF9F2A2A),
          content: Text('创建构建任务失败：$error'),
        ),
      );
    } finally {
      if (mounted) {
        setState(() {
          _submittingBuildKeys.remove(actionKey);
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: RefreshIndicator(
          onRefresh: _loadDashboard,
          child: SingleChildScrollView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.fromLTRB(20, 20, 20, 32),
            child: Center(
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 1240),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    _HeroBanner(
                      projectCount: _projects.length,
                      queueCount: _queuedJobs.length,
                      hasRunningBuild: _currentBuild != null,
                      lastUpdatedAt: _lastUpdatedAt,
                      onRefresh: () => _loadDashboard(showLoading: false),
                    ),
                    const SizedBox(height: 20),
                    if (_initialLoading)
                      const Padding(
                        padding: EdgeInsets.symmetric(vertical: 48),
                        child: Center(child: CircularProgressIndicator()),
                      )
                    else
                      LayoutBuilder(
                        builder: (context, constraints) {
                          if (constraints.maxWidth >= 980) {
                            return Row(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                SizedBox(
                                  width: 340,
                                  child: _DashboardRail(
                                    currentBuild: _currentBuild,
                                    queuedJobs: _queuedJobs,
                                    repoController: _repoController,
                                    errorMessage: _errorMessage,
                                    submitting: _submitting,
                                    onSubmitProject: _submitProject,
                                  ),
                                ),
                                const SizedBox(width: 20),
                                Expanded(
                                  child: _DashboardContent(
                                    projects: _projects,
                                    queuedJobs: _queuedJobs,
                                    projectBranches: _projectBranches,
                                    syncingProjectIds: _syncingProjectIds,
                                    loadingBranchProjectIds:
                                        _loadingBranchProjectIds,
                                    branchErrors: _branchErrors,
                                    onSyncProject: _syncAndLoadBranches,
                                    onLoadBranches: _loadBranches,
                                    submittingBuildKeys: _submittingBuildKeys,
                                    onSubmitBuild: _submitBuild,
                                  ),
                                ),
                              ],
                            );
                          }

                          return Column(
                            children: [
                              _DashboardRail(
                                currentBuild: _currentBuild,
                                queuedJobs: _queuedJobs,
                                repoController: _repoController,
                                errorMessage: _errorMessage,
                                submitting: _submitting,
                                onSubmitProject: _submitProject,
                              ),
                              const SizedBox(height: 20),
                              _DashboardContent(
                                projects: _projects,
                                queuedJobs: _queuedJobs,
                                projectBranches: _projectBranches,
                                syncingProjectIds: _syncingProjectIds,
                                loadingBranchProjectIds:
                                    _loadingBranchProjectIds,
                                branchErrors: _branchErrors,
                                onSyncProject: _syncAndLoadBranches,
                                onLoadBranches: _loadBranches,
                                submittingBuildKeys: _submittingBuildKeys,
                                onSubmitBuild: _submitBuild,
                              ),
                            ],
                          );
                        },
                      ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _HeroBanner extends StatelessWidget {
  const _HeroBanner({
    required this.projectCount,
    required this.queueCount,
    required this.hasRunningBuild,
    required this.lastUpdatedAt,
    required this.onRefresh,
  });

  final int projectCount;
  final int queueCount;
  final bool hasRunningBuild;
  final DateTime? lastUpdatedAt;
  final VoidCallback onRefresh;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final stats = <({String label, String value})>[
      (label: '已接入项目', value: '$projectCount'),
      (label: '排队任务', value: '$queueCount'),
      (label: '构建状态', value: hasRunningBuild ? 'Busy' : 'Idle'),
    ];

    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFF14213D),
        borderRadius: BorderRadius.circular(28),
        boxShadow: const [
          BoxShadow(
            color: Color(0x26000000),
            blurRadius: 36,
            offset: Offset(0, 18),
          ),
        ],
      ),
      padding: const EdgeInsets.all(28),
      child: LayoutBuilder(
        builder: (context, constraints) {
          final isWide = constraints.maxWidth >= 860;
          final headline = Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 14,
                  vertical: 8,
                ),
                decoration: BoxDecoration(
                  color: const Color(0xFFE76F51),
                  borderRadius: BorderRadius.circular(999),
                ),
                child: const Text(
                  'iMac Build Station',
                  style: TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
              const SizedBox(height: 20),
              Text(
                'F-Build',
                style: theme.textTheme.displayMedium?.copyWith(
                  color: Colors.white,
                ),
              ),
              const SizedBox(height: 10),
              Text(
                '给 QA / PM 一个能直接下发构建任务的 Flutter Web 控制台。',
                style: theme.textTheme.bodyLarge?.copyWith(
                  color: const Color(0xFFD8E3F0),
                ),
              ),
              const SizedBox(height: 20),
              OutlinedButton.icon(
                onPressed: onRefresh,
                icon: const Icon(Icons.refresh),
                label: Text(
                  lastUpdatedAt == null
                      ? '立即刷新'
                      : '最后更新 ${_formatTime(lastUpdatedAt!)}',
                ),
                style: OutlinedButton.styleFrom(
                  foregroundColor: Colors.white,
                  side: const BorderSide(color: Color(0xFF476082)),
                  padding: const EdgeInsets.symmetric(
                    horizontal: 18,
                    vertical: 16,
                  ),
                ),
              ),
            ],
          );

          final statCards = Wrap(
            spacing: 14,
            runSpacing: 14,
            children: stats
                .map(
                  (item) => Container(
                    width: 150,
                    padding: const EdgeInsets.all(18),
                    decoration: BoxDecoration(
                      color: const Color(0xFF1F3157),
                      borderRadius: BorderRadius.circular(22),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          item.label,
                          style: theme.textTheme.bodyMedium?.copyWith(
                            color: const Color(0xFFA6BBD3),
                          ),
                        ),
                        const SizedBox(height: 10),
                        Text(
                          item.value,
                          style: theme.textTheme.headlineMedium?.copyWith(
                            color: Colors.white,
                          ),
                        ),
                      ],
                    ),
                  ),
                )
                .toList(growable: false),
          );

          if (isWide) {
            return Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(child: headline),
                const SizedBox(width: 24),
                SizedBox(width: 328, child: statCards),
              ],
            );
          }

          return Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [headline, const SizedBox(height: 20), statCards],
          );
        },
      ),
    );
  }
}

class _DashboardRail extends StatelessWidget {
  const _DashboardRail({
    required this.currentBuild,
    required this.queuedJobs,
    required this.repoController,
    required this.errorMessage,
    required this.submitting,
    required this.onSubmitProject,
  });

  final BuildJob? currentBuild;
  final List<BuildJob> queuedJobs;
  final TextEditingController repoController;
  final String? errorMessage;
  final bool submitting;
  final Future<void> Function() onSubmitProject;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        _PanelCard(
          title: '添加项目',
          subtitle: '先录入 Git 地址，后面就能接上分支同步和打包。',
          accentColor: const Color(0xFFE76F51),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              TextField(
                controller: repoController,
                decoration: const InputDecoration(
                  labelText: 'Git 仓库地址',
                  hintText: 'https://github.com/acme/mobile-app.git',
                ),
                minLines: 1,
                maxLines: 2,
              ),
              const SizedBox(height: 14),
              SizedBox(
                width: double.infinity,
                child: FilledButton.icon(
                  onPressed: submitting ? null : onSubmitProject,
                  icon: submitting
                      ? const SizedBox(
                          height: 16,
                          width: 16,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.add_link_rounded),
                  label: Text(submitting ? '提交中...' : '加入构建系统'),
                ),
              ),
              if (errorMessage != null) ...[
                const SizedBox(height: 12),
                Text(
                  errorMessage!,
                  style: const TextStyle(
                    color: Color(0xFF9F2A2A),
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ],
          ),
        ),
        const SizedBox(height: 20),
        _PanelCard(
          title: '当前执行',
          subtitle: currentBuild == null ? '当前没有任务占用构建机。' : '构建机已进入工作状态。',
          accentColor: const Color(0xFF2A9D8F),
          child: currentBuild == null
              ? const _EmptyState(title: 'Idle', subtitle: '队列为空时，这里会显示空闲状态。')
              : _BuildJobSummary(job: currentBuild!, emphasizeStatus: true),
        ),
        const SizedBox(height: 20),
        _PanelCard(
          title: '队列概览',
          subtitle: '第一版先用轮询，不走 WebSocket。',
          accentColor: const Color(0xFF264653),
          child: queuedJobs.isEmpty
              ? const _EmptyState(title: 'Queue Clear', subtitle: '暂时没有排队中的任务。')
              : Column(
                  children: queuedJobs
                      .take(3)
                      .map(
                        (job) => Padding(
                          padding: const EdgeInsets.only(bottom: 12),
                          child: _BuildJobSummary(job: job),
                        ),
                      )
                      .toList(growable: false),
                ),
        ),
      ],
    );
  }
}

class _DashboardContent extends StatelessWidget {
  const _DashboardContent({
    required this.projects,
    required this.queuedJobs,
    required this.projectBranches,
    required this.syncingProjectIds,
    required this.loadingBranchProjectIds,
    required this.branchErrors,
    required this.onSyncProject,
    required this.onLoadBranches,
    required this.submittingBuildKeys,
    required this.onSubmitBuild,
  });

  final List<Project> projects;
  final List<BuildJob> queuedJobs;
  final Map<int, List<ProjectBranch>> projectBranches;
  final Set<int> syncingProjectIds;
  final Set<int> loadingBranchProjectIds;
  final Map<int, String> branchErrors;
  final Future<void> Function(Project project) onSyncProject;
  final Future<void> Function(Project project) onLoadBranches;
  final Set<String> submittingBuildKeys;
  final Future<void> Function(
    Project project,
    ProjectBranch branch,
    String platform,
  )
  onSubmitBuild;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        _PanelCard(
          title: '项目总览',
          subtitle: '这里先展示已接入项目，下一步再接分支同步与构建按钮。',
          accentColor: const Color(0xFFD4A373),
          child: projects.isEmpty
              ? const _EmptyState(
                  title: 'No Projects Yet',
                  subtitle: '先在左侧录入一个 Git 地址，系统会开始管理它。',
                )
              : Column(
                  children: projects
                      .map(
                        (project) => Padding(
                          padding: const EdgeInsets.only(bottom: 14),
                          child: _ProjectCard(
                            project: project,
                            branches:
                                projectBranches[project.id] ??
                                const <ProjectBranch>[],
                            branchError: branchErrors[project.id],
                            syncing: syncingProjectIds.contains(project.id),
                            loadingBranches: loadingBranchProjectIds.contains(
                              project.id,
                            ),
                            onSyncProject: () => onSyncProject(project),
                            onLoadBranches: () => onLoadBranches(project),
                            submittingBuildKeys: submittingBuildKeys,
                            onSubmitBuild: (branch, platform) =>
                                onSubmitBuild(project, branch, platform),
                          ),
                        ),
                      )
                      .toList(growable: false),
                ),
        ),
        const SizedBox(height: 20),
        _PanelCard(
          title: '即将到来的任务',
          subtitle: '现在已经能看到排队顺序，后续再接任务详情和日志页。',
          accentColor: const Color(0xFF8D6E63),
          child: queuedJobs.isEmpty
              ? const _EmptyState(
                  title: 'Nothing Waiting',
                  subtitle: '一旦有人提交构建任务，这里就会按队列顺序出现。',
                )
              : Column(
                  children: queuedJobs
                      .map(
                        (job) => Padding(
                          padding: const EdgeInsets.only(bottom: 12),
                          child: _BuildJobSummary(job: job),
                        ),
                      )
                      .toList(growable: false),
                ),
        ),
      ],
    );
  }
}

class _PanelCard extends StatelessWidget {
  const _PanelCard({
    required this.title,
    required this.subtitle,
    required this.accentColor,
    required this.child,
  });

  final String title;
  final String subtitle;
  final Color accentColor;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(22),
      decoration: BoxDecoration(
        color: const Color(0xFFFFFBF4),
        borderRadius: BorderRadius.circular(26),
        border: Border.all(color: const Color(0xFFE2D9CC)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 12,
                height: 12,
                decoration: BoxDecoration(
                  color: accentColor,
                  borderRadius: BorderRadius.circular(999),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(child: Text(title, style: theme.textTheme.titleLarge)),
            ],
          ),
          const SizedBox(height: 10),
          Text(
            subtitle,
            style: theme.textTheme.bodyMedium?.copyWith(
              color: const Color(0xFF6B625B),
            ),
          ),
          const SizedBox(height: 18),
          child,
        ],
      ),
    );
  }
}

class _ProjectCard extends StatelessWidget {
  const _ProjectCard({
    required this.project,
    required this.branches,
    required this.branchError,
    required this.syncing,
    required this.loadingBranches,
    required this.onSyncProject,
    required this.onLoadBranches,
    required this.submittingBuildKeys,
    required this.onSubmitBuild,
  });

  final Project project;
  final List<ProjectBranch> branches;
  final String? branchError;
  final bool syncing;
  final bool loadingBranches;
  final VoidCallback onSyncProject;
  final VoidCallback onLoadBranches;
  final Set<String> submittingBuildKeys;
  final Future<void> Function(ProjectBranch branch, String platform)
  onSubmitBuild;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: const Color(0xFFF4ECE0),
        borderRadius: BorderRadius.circular(22),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  project.name,
                  style: theme.textTheme.titleLarge?.copyWith(
                    fontWeight: FontWeight.w800,
                  ),
                ),
              ),
              _StatusPill(
                text: project.isActive ? 'active' : 'paused',
                color: project.isActive
                    ? const Color(0xFF2A9D8F)
                    : const Color(0xFF8D6E63),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Text(
            project.repoUrl,
            style: theme.textTheme.bodyMedium?.copyWith(
              color: const Color(0xFF4B5D67),
            ),
          ),
          const SizedBox(height: 12),
          Wrap(
            spacing: 10,
            runSpacing: 10,
            children: [
              _MetaChip(icon: Icons.tag_rounded, label: project.slug),
              _MetaChip(
                icon: Icons.folder_open_rounded,
                label: project.workspacePath,
              ),
              _MetaChip(
                icon: Icons.account_tree_rounded,
                label: '默认分支 ${project.defaultBranch ?? '未识别'}',
              ),
              _MetaChip(
                icon: Icons.sync_alt_rounded,
                label: project.lastSyncAt == null ? '待同步分支' : '已同步分支',
              ),
            ],
          ),
          const SizedBox(height: 14),
          Wrap(
            spacing: 10,
            runSpacing: 10,
            children: [
              FilledButton.icon(
                onPressed: syncing ? null : onSyncProject,
                icon: syncing
                    ? const SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.sync_rounded),
                label: Text(syncing ? '同步中...' : '同步项目'),
              ),
              OutlinedButton.icon(
                onPressed: loadingBranches ? null : onLoadBranches,
                icon: loadingBranches
                    ? const SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.alt_route_rounded),
                label: Text(loadingBranches ? '读取中...' : '查看分支'),
              ),
            ],
          ),
          if (branchError != null) ...[
            const SizedBox(height: 12),
            Text(
              branchError!,
              style: theme.textTheme.bodyMedium?.copyWith(
                color: const Color(0xFF9F2A2A),
                fontWeight: FontWeight.w700,
              ),
            ),
          ],
          if (branches.isNotEmpty) ...[
            const SizedBox(height: 16),
            ...branches.map(
              (branch) => Padding(
                padding: const EdgeInsets.only(bottom: 10),
                child: _BranchRow(
                  projectId: project.id,
                  branch: branch,
                  submittingBuildKeys: submittingBuildKeys,
                  onSubmitBuild: onSubmitBuild,
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _BranchRow extends StatelessWidget {
  const _BranchRow({
    required this.projectId,
    required this.branch,
    required this.submittingBuildKeys,
    required this.onSubmitBuild,
  });

  final int projectId;
  final ProjectBranch branch;
  final Set<String> submittingBuildKeys;
  final Future<void> Function(ProjectBranch branch, String platform)
  onSubmitBuild;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final androidActionKey = '$projectId:${branch.name}:android';
    final iosActionKey = '$projectId:${branch.name}:ios';
    final androidSubmitting = submittingBuildKeys.contains(androidActionKey);
    final iosSubmitting = submittingBuildKeys.contains(iosActionKey);

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: const Color(0xFFE2D9CC)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  branch.name,
                  style: theme.textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w800,
                  ),
                ),
              ),
              Text(
                branch.commitSha,
                style: theme.textTheme.bodyMedium?.copyWith(
                  color: const Color(0xFF4B5D67),
                  fontWeight: FontWeight.w700,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            branch.commitSubject,
            style: theme.textTheme.bodyMedium?.copyWith(
              color: const Color(0xFF231F20),
            ),
          ),
          const SizedBox(height: 6),
          Text(
            branch.commitDate,
            style: theme.textTheme.bodySmall?.copyWith(
              color: const Color(0xFF6B625B),
            ),
          ),
          const SizedBox(height: 12),
          Wrap(
            spacing: 10,
            runSpacing: 10,
            children: [
              FilledButton.icon(
                onPressed: androidSubmitting
                    ? null
                    : () => onSubmitBuild(branch, 'android'),
                icon: androidSubmitting
                    ? const SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.android_rounded),
                label: Text(androidSubmitting ? '提交中...' : '发起 Android'),
              ),
              OutlinedButton.icon(
                onPressed: iosSubmitting
                    ? null
                    : () => onSubmitBuild(branch, 'ios'),
                icon: iosSubmitting
                    ? const SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.phone_iphone_rounded),
                label: Text(iosSubmitting ? '提交中...' : '发起 iOS'),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _BuildJobSummary extends StatelessWidget {
  const _BuildJobSummary({required this.job, this.emphasizeStatus = false});

  final BuildJob job;
  final bool emphasizeStatus;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: emphasizeStatus
            ? const Color(0xFFE7F4F1)
            : const Color(0xFFF4ECE0),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _StatusPill(
            text: job.status,
            color: job.status == 'queued'
                ? const Color(0xFF8D6E63)
                : const Color(0xFF2A9D8F),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '${job.platform.toUpperCase()} · ${job.branch}',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w800,
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  'Project #${job.projectId} · Job #${job.id}',
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: const Color(0xFF6B625B),
                  ),
                ),
              ],
            ),
          ),
          if (job.queuePosition != null)
            Text(
              '#${job.queuePosition}',
              style: Theme.of(
                context,
              ).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w900),
            ),
        ],
      ),
    );
  }
}

class _EmptyState extends StatelessWidget {
  const _EmptyState({required this.title, required this.subtitle});

  final String title;
  final String subtitle;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: const Color(0xFFF4ECE0),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: theme.textTheme.titleLarge?.copyWith(
              fontWeight: FontWeight.w800,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            subtitle,
            style: theme.textTheme.bodyMedium?.copyWith(
              color: const Color(0xFF6B625B),
            ),
          ),
        ],
      ),
    );
  }
}

class _StatusPill extends StatelessWidget {
  const _StatusPill({required this.text, required this.color});

  final String text;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: color,
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(
        text,
        style: const TextStyle(
          color: Colors.white,
          fontWeight: FontWeight.w700,
        ),
      ),
    );
  }
}

class _MetaChip extends StatelessWidget {
  const _MetaChip({required this.icon, required this.label});

  final IconData icon;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: const Color(0xFFE2D9CC)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 16, color: const Color(0xFF4B5D67)),
          const SizedBox(width: 8),
          Text(label),
        ],
      ),
    );
  }
}

String _formatTime(DateTime dateTime) {
  final hour = dateTime.hour.toString().padLeft(2, '0');
  final minute = dateTime.minute.toString().padLeft(2, '0');
  final second = dateTime.second.toString().padLeft(2, '0');
  return '$hour:$minute:$second';
}
