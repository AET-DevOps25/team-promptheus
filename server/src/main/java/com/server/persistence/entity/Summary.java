package com.server.persistence.entity;

import jakarta.persistence.*;
import lombok.Data;

import java.time.LocalDateTime;

@Entity
@Table(name = "summaries")
@Data
public class Summary {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "git_repository_id")
    private Long gitRepositoryId;

    private String username;

    private String week;

    @Column(name = "overview")
    private String overview;

    @Column(name = "commits_summary")
    private String commitsSummary;

    @Column(name = "pull_requests_summary")
    private String pullRequestsSummary;

    @Column(name = "issues_summary")
    private String issuesSummary;

    @Column(name = "releases_summary")
    private String releasesSummary;

    private String analysis;

    @Column(name = "key_achievements", columnDefinition = "text[]")
    private String[] keyAchievements;

    @Column(name = "areas_for_improvement", columnDefinition = "text[]")
    private String[] areasForImprovement;

    @Column(name = "total_contributions")
    private Integer totalContributions;

    @Column(name = "commits_count")
    private Integer commitsCount;

    @Column(name = "pull_requests_count")
    private Integer pullRequestsCount;

    @Column(name = "issues_count")
    private Integer issuesCount;

    @Column(name = "releases_count")
    private Integer releasesCount;

    @Column(name = "created_at")
    private LocalDateTime createdAt;
}
