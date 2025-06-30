package de.promptheus.summary.service;

import de.promptheus.summary.client.ContributionClient;
import de.promptheus.summary.client.GenAiClient;
import de.promptheus.summary.contribution.model.ContributionDto;
import de.promptheus.summary.genai.model.ContributionMetadata;
import de.promptheus.summary.genai.model.ContributionType;
import de.promptheus.summary.persistence.Summary;
import de.promptheus.summary.persistence.SummaryRepository;
import de.promptheus.summary.persistence.GitRepository;
import de.promptheus.summary.persistence.GitRepositoryRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Mono;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.temporal.IsoFields;
import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@Slf4j
public class SummaryService {

    private final GenAiClient genAiClient;
    private final ContributionClient contributionClient;
    private final SummaryRepository summaryRepository;
    private final GitRepositoryRepository gitRepositoryRepository;

    public List<Summary> getSummaries(Optional<String> week) {
        if (week.isPresent()) {
            return summaryRepository.findByWeek(week.get());
        }
        return summaryRepository.findAll();
    }

    @Scheduled(cron = "0 0 0 * * MON")
    public void generateWeeklySummaries() {
        // Calculate the previous week (since this runs on Monday, we want last week's summary)
        LocalDate today = LocalDate.now();
        LocalDate previousWeek = today.minusWeeks(1);
        String week = String.format("%d-W%02d",
                previousWeek.get(IsoFields.WEEK_BASED_YEAR),
                previousWeek.get(IsoFields.WEEK_OF_WEEK_BASED_YEAR));

        log.info("Starting automatic weekly summary generation for week: {}", week);

        // Get all repositories from the database
        List<GitRepository> repositories = gitRepositoryRepository.findAll();
        log.info("Found {} repositories to process", repositories.size());

        for (GitRepository repository : repositories) {
            // Get PAT for this repository
            String token = gitRepositoryRepository.findTokenByRepositoryId(repository.getId());
            if (token == null) {
                log.warn("No PAT found for repository: {} (ID: {}), skipping", repository.getRepositoryLink(), repository.getId());
                continue;
            }

            // Get all users who have contributions in this repository
            List<String> users = gitRepositoryRepository.findDistinctUsersByRepositoryId(repository.getId());
            log.info("Found {} users with contributions in repository: {} (ID: {})", users.size(), repository.getRepositoryLink(), repository.getId());

            // Generate summary for each user in this repository
            for (String username : users) {
                generateSummary(username, week, repository, token);
            }
        }
    }

    public void generateSummary(String username, String week, GitRepository repository, String token) {
        log.info("Starting summary generation for user: {}, week: {}, repository: {} (ID: {})", username, week, repository.getRepositoryLink(), repository.getId());

        // Check if summary already exists for this user, week, and repository
        List<Summary> existingSummaries = summaryRepository.findByUsernameAndWeek(username, week);
        boolean summaryExists = existingSummaries.stream()
                .anyMatch(s -> s.getGitRepositoryId() != null && s.getGitRepositoryId().equals(repository.getId()));

        if (summaryExists) {
            log.info("Summary already exists for user: {}, week: {}, repository: {} - skipping generation", username, week, repository.getRepositoryLink());
            return;
        }

        // Step 1: Fetch contributions for the specific user and week
        contributionClient.getContributionsForUserAndWeek(username, week)
                .flatMap(contributions -> {
                    log.info("Found {} total contributions for user: {}, week: {}", contributions.size(), username, week);

                    // Step 2: Filter by isSelected = true
                    List<ContributionDto> selectedContributions = contributions.stream()
                            .filter(contrib -> contrib.getIsSelected() != null && contrib.getIsSelected())
                            .collect(Collectors.toList());

                    if (selectedContributions.isEmpty()) {
                        log.warn("No selected contributions found for user: {}, week: {} - skipping summary generation", username, week);
                        return Mono.empty();
                    }

                    log.info("Found {} selected contributions for user: {}, week: {}", selectedContributions.size(), username, week);

                    // Step 3: Convert selected contributions to metadata format for GenAI service
                    List<ContributionMetadata> metadata = selectedContributions.stream()
                            .map(contrib -> {
                                ContributionMetadata meta = new ContributionMetadata();
                                meta.setType(mapToContributionType(contrib.getType()));
                                meta.setId(contrib.getId());
                                meta.setSelected(true); // All passed contributions are selected
                                return meta;
                            })
                            .collect(Collectors.toList());

                    log.info("Sending {} selected contributions to GenAI service for user: {}, week: {}", metadata.size(), username, week);

                    // Step 4: Send to GenAI service and monitor task completion
                    // Extract repository information from the repository object
                    String repositoryLink = repository.getRepositoryLink();

                    // Convert repository URL to owner/repo format for GenAI service
                    // e.g., "https://github.com/owner/repo" -> "owner/repo"
                    String repositoryName = extractOwnerRepoFromUrl(repositoryLink);

                    log.info("Sending {} selected contributions to GenAI service for user: {}, week: {}, repository: {}",
                            metadata.size(), username, week, repositoryName);

                    return genAiClient.generateSummaryAsync(username, week, repositoryName, metadata);
                })
                .subscribe(
                    summaryMarkdown -> {
                        // Step 5: Save the summary to database
                        try {
                            Summary summary = new Summary();
                            summary.setUsername(username);
                            summary.setWeek(week);
                            summary.setGitRepositoryId(repository.getId());
                            summary.setSummary(summaryMarkdown);
                            summary.setCreatedAt(LocalDateTime.now());

                            Summary savedSummary = summaryRepository.save(summary);
                            log.info("Successfully generated and saved summary with ID {} for user: {}, week: {}, repository: {}",
                                    savedSummary.getId(), username, week, repository.getRepositoryLink());
                        } catch (Exception e) {
                            log.error("Failed to save summary for user: {}, week: {}, repository: {}", username, week, repository.getRepositoryLink(), e);
                        }
                    },
                    error -> {
                        log.error("Failed to generate summary for user: {}, week: {}, repository: {}", username, week, repository.getRepositoryLink(), error);
                    },
                    () -> {
                        log.debug("Summary generation completed for user: {}, week: {}, repository: {}", username, week, repository.getRepositoryLink());
                    }
                );
    }

    private ContributionType mapToContributionType(String type) {
        switch (type.toLowerCase()) {
            case "commit":
                return ContributionType.COMMIT;
            case "pull_request":
                return ContributionType.PULL_REQUEST;
            case "issue":
                return ContributionType.ISSUE;
            case "release":
                return ContributionType.RELEASE;
            default:
                log.warn("Unknown contribution type: {}, defaulting to COMMIT", type);
                return ContributionType.COMMIT;
        }
    }

    /**
     * Extract owner/repo format from GitHub URL.
     * e.g., "https://github.com/owner/repo" -> "owner/repo"
     */
    private String extractOwnerRepoFromUrl(String repositoryUrl) {
        if (repositoryUrl == null) {
            return null;
        }

        // Remove trailing slash if present
        String cleanUrl = repositoryUrl.endsWith("/") ? repositoryUrl.substring(0, repositoryUrl.length() - 1) : repositoryUrl;

        // Split by "/" and get the last two parts (owner and repo)
        String[] parts = cleanUrl.split("/");
        if (parts.length >= 2) {
            String owner = parts[parts.length - 2];
            String repo = parts[parts.length - 1];
            return owner + "/" + repo;
        }

        // Fallback: return the original URL if we can't parse it
        log.warn("Could not extract owner/repo from URL: {}", repositoryUrl);
        return repositoryUrl;
    }
}
