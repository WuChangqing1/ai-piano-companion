class HandIssue {
  final double timestamp;
  final int measure;
  final String issueType;
  final String description;

  HandIssue({
    required this.timestamp,
    required this.measure,
    required this.issueType,
    required this.description,
  });

  factory HandIssue.fromJson(Map<String, dynamic> j) => HandIssue(
        timestamp: (j['timestamp'] as num).toDouble(),
        measure: j['measure'] as int,
        issueType: j['issue_type'] as String,
        description: j['description'] as String,
      );
}

class AudioIssue {
  final double timestamp;
  final int measure;
  final String issueType;
  final String? expected;
  final String? actual;

  AudioIssue({
    required this.timestamp,
    required this.measure,
    required this.issueType,
    this.expected,
    this.actual,
  });

  factory AudioIssue.fromJson(Map<String, dynamic> j) => AudioIssue(
        timestamp: (j['timestamp'] as num).toDouble(),
        measure: j['measure'] as int,
        issueType: j['issue_type'] as String,
        expected: j['expected'] as String?,
        actual: j['actual'] as String?,
      );
}

class PracticeReport {
  final int overallScore;
  final int rhythmScore;
  final int accuracyScore;
  final int fluencyScore;
  final int handHealthScore;
  final int wrongNotes;
  final int missingNotes;
  final int handIssuesCount;
  final String teacherComment;
  final double durationSeconds;
  final List<HandIssue> handIssues;
  final List<AudioIssue> audioIssues;

  PracticeReport({
    required this.overallScore,
    required this.rhythmScore,
    required this.accuracyScore,
    required this.fluencyScore,
    required this.handHealthScore,
    required this.wrongNotes,
    required this.missingNotes,
    required this.handIssuesCount,
    required this.teacherComment,
    required this.durationSeconds,
    required this.handIssues,
    required this.audioIssues,
  });

  factory PracticeReport.fromJson(Map<String, dynamic> j) => PracticeReport(
        overallScore: j['overall_score'] as int,
        rhythmScore: j['rhythm_score'] as int,
        accuracyScore: j['accuracy_score'] as int,
        fluencyScore: j['fluency_score'] as int,
        handHealthScore: j['hand_health_score'] as int,
        wrongNotes: j['wrong_notes'] as int,
        missingNotes: j['missing_notes'] as int,
        handIssuesCount: j['hand_issues_count'] as int,
        teacherComment: j['teacher_comment'] as String,
        durationSeconds: (j['duration_seconds'] as num).toDouble(),
        handIssues: (j['hand_issues'] as List)
            .map((e) => HandIssue.fromJson(e as Map<String, dynamic>))
            .toList(),
        audioIssues: (j['audio_issues'] as List)
            .map((e) => AudioIssue.fromJson(e as Map<String, dynamic>))
            .toList(),
      );
}

class EvaluateResult {
  final String reportId;
  final PracticeReport report;
  final String audioUrl;

  EvaluateResult({
    required this.reportId,
    required this.report,
    required this.audioUrl,
  });

  factory EvaluateResult.fromJson(Map<String, dynamic> j) => EvaluateResult(
        reportId: j['report_id'] as String,
        report: PracticeReport.fromJson(j['report'] as Map<String, dynamic>),
        audioUrl: j['audio_url'] as String,
      );
}
