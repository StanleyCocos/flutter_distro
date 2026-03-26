class Project {
  const Project({
    required this.id,
    required this.name,
    required this.repoUrl,
    required this.slug,
    required this.workspacePath,
    required this.isActive,
    required this.defaultBranch,
    required this.lastSyncAt,
    required this.createdAt,
    required this.updatedAt,
  });

  factory Project.fromJson(Map<String, dynamic> json) {
    return Project(
      id: json['id'] as int,
      name: json['name'] as String,
      repoUrl: json['repo_url'] as String,
      slug: json['slug'] as String,
      workspacePath: json['workspace_path'] as String,
      isActive: json['is_active'] as bool,
      defaultBranch: json['default_branch'] as String?,
      lastSyncAt: json['last_sync_at'] as String?,
      createdAt: json['created_at'] as String,
      updatedAt: json['updated_at'] as String,
    );
  }

  final int id;
  final String name;
  final String repoUrl;
  final String slug;
  final String workspacePath;
  final bool isActive;
  final String? defaultBranch;
  final String? lastSyncAt;
  final String createdAt;
  final String updatedAt;
}

class BuildJob {
  const BuildJob({
    required this.id,
    required this.projectId,
    required this.branch,
    required this.platform,
    required this.status,
    required this.requestedAt,
    required this.startedAt,
    required this.finishedAt,
    required this.commitSha,
    required this.artifactPath,
    required this.pgyerUrl,
    required this.errorMessage,
    required this.queuePosition,
  });

  factory BuildJob.fromJson(Map<String, dynamic> json) {
    return BuildJob(
      id: json['id'] as int,
      projectId: json['project_id'] as int,
      branch: json['branch'] as String,
      platform: json['platform'] as String,
      status: json['status'] as String,
      requestedAt: json['requested_at'] as String,
      startedAt: json['started_at'] as String?,
      finishedAt: json['finished_at'] as String?,
      commitSha: json['commit_sha'] as String?,
      artifactPath: json['artifact_path'] as String?,
      pgyerUrl: json['pgyer_url'] as String?,
      errorMessage: json['error_message'] as String?,
      queuePosition: json['queue_position'] as int?,
    );
  }

  final int id;
  final int projectId;
  final String branch;
  final String platform;
  final String status;
  final String requestedAt;
  final String? startedAt;
  final String? finishedAt;
  final String? commitSha;
  final String? artifactPath;
  final String? pgyerUrl;
  final String? errorMessage;
  final int? queuePosition;
}

class ProjectBranch {
  const ProjectBranch({
    required this.name,
    required this.commitSha,
    required this.commitDate,
    required this.commitSubject,
  });

  factory ProjectBranch.fromJson(Map<String, dynamic> json) {
    return ProjectBranch(
      name: json['name'] as String,
      commitSha: json['commit_sha'] as String,
      commitDate: json['commit_date'] as String,
      commitSubject: json['commit_subject'] as String,
    );
  }

  final String name;
  final String commitSha;
  final String commitDate;
  final String commitSubject;
}

class BuildLogEntry {
  const BuildLogEntry({
    required this.id,
    required this.jobId,
    required this.seq,
    required this.stream,
    required this.message,
    required this.createdAt,
  });

  factory BuildLogEntry.fromJson(Map<String, dynamic> json) {
    return BuildLogEntry(
      id: json['id'] as int,
      jobId: json['job_id'] as int,
      seq: json['seq'] as int,
      stream: json['stream'] as String,
      message: json['message'] as String,
      createdAt: json['created_at'] as String,
    );
  }

  final int id;
  final int jobId;
  final int seq;
  final String stream;
  final String message;
  final String createdAt;
}
