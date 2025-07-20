package de.promptheus.summary.dto;

import de.promptheus.summary.persistence.Summary;
import de.promptheus.summary.persistence.GitRepository;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import lombok.Builder;

import java.time.LocalDateTime;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class SummaryDto {

    private Long id;
    private Long gitRepositoryId;
    private String repositoryName;
    private String repositoryUrl;
    private String username;
    private String week;
    private String overview;
    private String commitsSummary;
    private String pullRequestsSummary;
    private String issuesSummary;
    private String releasesSummary;
    private String analysis;
    private String[] keyAchievements;
    private String[] areasForImprovement;
    private Integer totalContributions;
    private Integer commitsCount;
    private Integer pullRequestsCount;
    private Integer issuesCount;
    private Integer releasesCount;
    private LocalDateTime createdAt;

    // Helper method to create DTO from entity
    public static SummaryDto fromEntity(Summary summary, GitRepository repository) {
        String repositoryName = null;
        if (repository != null && repository.getRepositoryLink() != null) {
            // Extract owner/repo from URL
            String url = repository.getRepositoryLink();
            if (url.contains("github.com/")) {
                String[] parts = url.split("/");
                if (parts.length >= 2) {
                    repositoryName = parts[parts.length - 2] + "/" + parts[parts.length - 1];
                }
            }
        }

        return SummaryDto.builder()
                .id(summary.getId())
                .gitRepositoryId(summary.getGitRepositoryId())
                .repositoryName(repositoryName)
                .repositoryUrl(repository != null ? repository.getRepositoryLink() : null)
                .username(summary.getUsername())
                .week(summary.getWeek())
                .overview(summary.getOverview())
                .commitsSummary(summary.getCommitsSummary())
                .pullRequestsSummary(summary.getPullRequestsSummary())
                .issuesSummary(summary.getIssuesSummary())
                .releasesSummary(summary.getReleasesSummary())
                .analysis(summary.getAnalysis())
                .keyAchievements(summary.getKeyAchievements())
                .areasForImprovement(summary.getAreasForImprovement())
                .totalContributions(summary.getTotalContributions())
                .commitsCount(summary.getCommitsCount())
                .pullRequestsCount(summary.getPullRequestsCount())
                .issuesCount(summary.getIssuesCount())
                .releasesCount(summary.getReleasesCount())
                .createdAt(summary.getCreatedAt())
                .build();
    }

    // Overloaded method for when repository is null
    public static SummaryDto fromEntity(Summary summary) {
        return fromEntity(summary, null);
    }
}
