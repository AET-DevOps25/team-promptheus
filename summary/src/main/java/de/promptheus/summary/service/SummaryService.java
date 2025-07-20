package de.promptheus.summary.service;

import de.promptheus.summary.client.ContributionClient;
import de.promptheus.summary.client.GenAiClient;
import de.promptheus.summary.contribution.model.ContributionDto;
import de.promptheus.summary.dto.SummaryDto;
import de.promptheus.summary.genai.model.ContributionMetadata;
import de.promptheus.summary.genai.model.ContributionType;
import de.promptheus.summary.genai.model.ContributionsIngestRequest;
import de.promptheus.summary.persistence.Summary;
import de.promptheus.summary.persistence.SummaryRepository;
import de.promptheus.summary.persistence.GitRepository;
import de.promptheus.summary.persistence.GitRepositoryRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.beans.factory.annotation.Value;
import jakarta.annotation.PostConstruct;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import reactor.core.publisher.Mono;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.temporal.IsoFields;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.Semaphore;
import java.util.concurrent.TimeUnit;
import java.util.function.Function;
import java.util.stream.Collectors;
import java.util.stream.Stream;

@Service
@RequiredArgsConstructor
@Slf4j
public class SummaryService {

    private final GenAiClient genAiClient;
    private final ContributionClient contributionClient;
    private final SummaryRepository summaryRepository;
    private final GitRepositoryRepository gitRepositoryRepository;

    @Value("${app.githubPat:}")
    private String githubPat;

    @Value("${app.backfill.maxConcurrentSummaries:5}")
    private int maxConcurrentSummaries;

    @Value("${app.backfill.delayBetweenRequests:2000}")
    private long delayBetweenRequestsMs;

    @Value("${app.backfill.delayBetweenUsers:5000}")
    private long delayBetweenUsersMs;

    // Semaphore to control concurrent summary generation during backfill
    private Semaphore backfillSemaphore;

    // Initialize semaphore after properties are injected
    @PostConstruct
    private void initializeSemaphore() {
        this.backfillSemaphore = new Semaphore(maxConcurrentSummaries, true);
    }

    /**
     * Get summaries with filters and pagination
     */
    public Page<Summary> getSummariesPaginated(
            Optional<String> week,
            Optional<String> username,
            Optional<String> repositoryName,
            Pageable pageable) {

        String weekFilter = week.orElse(null);
        String usernameFilter = username.orElse(null);
        String repositoryFilter = repositoryName.orElse(null);

        // Convert repository name to repository link format if provided
        String repositoryLinkFilter = null;
        if (repositoryFilter != null) {
            // Support both full URLs and owner/repo format
            if (repositoryFilter.startsWith("http")) {
                repositoryLinkFilter = repositoryFilter;
            } else if (repositoryFilter.contains("/")) {
                // Convert owner/repo to GitHub URL
                repositoryLinkFilter = "https://github.com/" + repositoryFilter;
            } else {
                // Treat as partial repository name for LIKE search
                repositoryLinkFilter = repositoryFilter;
            }
        }

        return summaryRepository.findSummariesWithFilters(
                weekFilter, usernameFilter, repositoryLinkFilter, pageable);
    }

    /**
     * Get summaries with filters and pagination, returning DTOs with repository information
     */
    public Page<SummaryDto> getSummariesPaginatedWithRepoInfo(
            Optional<String> week,
            Optional<String> username,
            Optional<String> repositoryName,
            Pageable pageable) {

        Page<Summary> summaries = getSummariesPaginated(week, username, repositoryName, pageable);

        // Get all unique repository IDs from the summaries
        List<Long> repositoryIds = summaries.getContent().stream()
                .map(Summary::getGitRepositoryId)
                .filter(id -> id != null)
                .distinct()
                .collect(Collectors.toList());

        // Fetch all repositories in one query
        Map<Long, GitRepository> repositoryMap = gitRepositoryRepository.findAllById(repositoryIds)
                .stream()
                .collect(Collectors.toMap(GitRepository::getId, Function.identity()));

        // Convert summaries to DTOs with repository information
        return summaries.map(summary -> {
            GitRepository repository = repositoryMap.get(summary.getGitRepositoryId());
            return SummaryDto.fromEntity(summary, repository);
        });
    }

    /**
     * Generate summaries for all weeks from oldest contribution to current week for all repo/user combinations
     */
    public void generateBackfillSummaries() {
        log.info("Starting backfill summary generation for all repositories and users");

        // Get all repositories from the database
        List<GitRepository> repositories = gitRepositoryRepository.findAll();
        log.info("Found {} repositories to process for backfill", repositories.size());

        for (GitRepository repository : repositories) {
            // Get PAT for this repository
            String token = gitRepositoryRepository.findTokenByRepositoryId(repository.getId());
            if (token == null) {
                log.warn("No PAT found for repository: {} (ID: {}), skipping backfill", repository.getRepositoryLink(), repository.getId());
                continue;
            }

            // Get all users who have contributions in this repository
            List<String> users = gitRepositoryRepository.findDistinctUsersByRepositoryId(repository.getId());
            log.info("Found {} users with contributions in repository: {} (ID: {}) for backfill", users.size(), repository.getRepositoryLink(), repository.getId());

            // Generate summaries for each user in this repository with rate limiting
            for (int i = 0; i < users.size(); i++) {
                String username = users.get(i);

                try {
                    generateBackfillSummariesForUser(username, repository, token);

                    // Add delay between users to prevent overwhelming the system
                    if (i < users.size() - 1) { // Don't delay after the last user
                        Thread.sleep(delayBetweenUsersMs);
                    }
                } catch (InterruptedException e) {
                    log.warn("Backfill process interrupted for user: {} in repository: {}", username, repository.getRepositoryLink());
                    Thread.currentThread().interrupt();
                    break;
                } catch (Exception e) {
                    log.error("Error during backfill for user: {} in repository: {}", username, repository.getRepositoryLink(), e);
                    // Continue with next user
                }
            }
        }

        log.info("Completed backfill summary generation for all repositories and users");
    }

    /**
     * Generate summaries for all weeks from oldest contribution to current week for a specific user and repository
     */
    public void generateBackfillSummariesForUser(String username, GitRepository repository, String token) {
        log.info("Starting backfill summary generation for user: {}, repository: {} (ID: {})", username, repository.getRepositoryLink(), repository.getId());

        // Get the oldest contribution date for this user and repository
        contributionClient.getOldestContributionDate(username, repository.getId())
                .subscribe(
                    oldestDate -> {
                        if (oldestDate == null) {
                            log.warn("No contributions found for user: {} in repository: {} (ID: {})", username, repository.getRepositoryLink(), repository.getId());
                            return;
                        }

                        log.info("Oldest contribution date for user: {} in repository: {} (ID: {}): {}", username, repository.getRepositoryLink(), repository.getId(), oldestDate);

                        // Get all weeks from oldest contribution to current week
                        List<String> weeks = generateWeeksFromDateToCurrent(oldestDate);
                        log.info("Generated {} weeks for backfill from {} to current week for user: {} in repository: {}",
                                weeks.size(), oldestDate, username, repository.getRepositoryLink());

                        // Generate summaries for each week with rate limiting
                        for (int i = 0; i < weeks.size(); i++) {
                            String week = weeks.get(i);

                            try {
                                log.info("Generating backfill summary for user: {}, week: {}, repository: {} ({}/{})",
                                        username, week, repository.getRepositoryLink(), i + 1, weeks.size());
                                generateSummaryForWeekWithRateLimit(username, week, repository, token, true);

                                // Add delay between requests to prevent overwhelming GenAI service
                                if (i < weeks.size() - 1) { // Don't delay after the last week
                                    Thread.sleep(delayBetweenRequestsMs);
                                }
                            } catch (InterruptedException e) {
                                log.warn("Backfill process interrupted for user: {} in repository: {}", username, repository.getRepositoryLink());
                                Thread.currentThread().interrupt();
                                break;
                            } catch (Exception e) {
                                log.error("Error generating backfill summary for user: {}, week: {}, repository: {}",
                                        username, week, repository.getRepositoryLink(), e);
                                // Continue with next week
                            }
                        }

                        log.info("Completed backfill summary generation for user: {} in repository: {}", username, repository.getRepositoryLink());
                    },
                    error -> log.error("Failed to get oldest contribution date for user: {} in repository: {}", username, repository.getRepositoryLink(), error)
                );
    }

    /**
     * Generate a summary for a specific week if it doesn't already exist
     */
    private void generateSummaryForWeek(String username, String week, GitRepository repository, String token) {
        generateSummaryForWeekWithRateLimit(username, week, repository, token, false);
    }

    /**
     * Generate a summary for a specific week with optional rate limiting for backfill operations
     */
    private void generateSummaryForWeekWithRateLimit(String username, String week, GitRepository repository, String token, boolean isBackfill) {
        // Check if summary already exists for this user, week, and repository
        List<Summary> existingSummaries = summaryRepository.findByUsernameAndWeek(username, week);
        boolean summaryExists = existingSummaries.stream()
                .anyMatch(s -> s.getGitRepositoryId() != null && s.getGitRepositoryId().equals(repository.getId()));

        if (summaryExists) {
            log.info("Summary already exists for user: {}, week: {}, repository: {} - skipping generation", username, week, repository.getRepositoryLink());
            return;
        }

        if (isBackfill) {
            // For backfill operations, use semaphore to limit concurrent requests
            try {
                boolean acquired = backfillSemaphore.tryAcquire(30, TimeUnit.SECONDS);
                if (!acquired) {
                    log.warn("Could not acquire permit for backfill summary generation within 30 seconds for user: {}, week: {}, repository: {}",
                            username, week, repository.getRepositoryLink());
                    return;
                }

                try {
                    generateSummary(username, week, repository, token, isBackfill);
                } finally {
                    backfillSemaphore.release();
                }
            } catch (InterruptedException e) {
                log.warn("Interrupted while waiting for backfill semaphore for user: {}, week: {}, repository: {}",
                        username, week, repository.getRepositoryLink());
                Thread.currentThread().interrupt();
            }
        } else {
            // For non-backfill operations, proceed without rate limiting
            generateSummary(username, week, repository, token, isBackfill);
        }
    }

    /**
     * Generate all weeks from a given date to the current week
     */
    private List<String> generateWeeksFromDateToCurrent(java.time.Instant startDate) {
        LocalDate startLocalDate = startDate.atZone(java.time.ZoneOffset.UTC).toLocalDate();
        LocalDate currentDate = LocalDate.now();

        return Stream.iterate(startLocalDate, date -> date.plusWeeks(1))
                .takeWhile(date -> !date.isAfter(currentDate))
                .map(this::dateToWeekString)
                .collect(Collectors.toList());
    }

    /**
     * Convert a LocalDate to week string format (YYYY-WXX)
     */
    private String dateToWeekString(LocalDate date) {
        return String.format("%d-W%02d",
                date.get(IsoFields.WEEK_BASED_YEAR),
                date.get(IsoFields.WEEK_OF_WEEK_BASED_YEAR));
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
        generateSummary(username, week, repository, token, false);
    }

    private void generateSummary(String username, String week, GitRepository repository, String token, boolean isBackfill) {
        log.info("Starting summary generation for user: {}, week: {}, repository: {} (ID: {}) (backfill: {})",
                username, week, repository.getRepositoryLink(), repository.getId(), isBackfill);

        // For backfill, we don't want to regenerate existing summaries, so check and skip
        if (isBackfill) {
            Optional<Summary> existingSummary = summaryRepository.findByUsernameAndWeekAndGitRepositoryId(username, week, repository.getId());
            if (existingSummary.isPresent()) {
                log.info("Summary already exists for user: {}, week: {}, repository: {} - skipping backfill generation", username, week, repository.getRepositoryLink());
                return;
            }
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

                    ContributionsIngestRequest request = new ContributionsIngestRequest();
                    request.setUser(username);
                    request.setWeek(week);
                    request.setRepository(repositoryName);
                    request.setContributions(metadata);
                    request.setGithubPat(token); // Use the repository-specific token instead of the global one

                    return genAiClient.generateSummaryAsync(request, isBackfill);
                })
                .subscribe(
                    summaryResponse -> {
                        // Step 5: Upsert the summary to database
                        try {
                            // Check if summary already exists for this exact combination
                            Optional<Summary> existingSummaryOpt = summaryRepository.findByUsernameAndWeekAndGitRepositoryId(username, week, repository.getId());

                            Summary summary;
                            boolean isUpdate = false;

                            if (existingSummaryOpt.isPresent()) {
                                // Update existing summary
                                summary = existingSummaryOpt.get();
                                isUpdate = true;
                                log.info("Updating existing summary with ID {} for user: {}, week: {}, repository: {}",
                                        summary.getId(), username, week, repository.getRepositoryLink());
                            } else {
                                // Create new summary
                                summary = new Summary();
                                summary.setUsername(username);
                                summary.setWeek(week);
                                summary.setGitRepositoryId(repository.getId());
                                summary.setCreatedAt(LocalDateTime.now());
                                log.info("Creating new summary for user: {}, week: {}, repository: {}",
                                        username, week, repository.getRepositoryLink());
                            }

                            // Map from DTO to entity (same for both create and update)
                            summary.setOverview(summaryResponse.getOverview());
                            summary.setCommitsSummary(summaryResponse.getCommitsSummary());
                            summary.setPullRequestsSummary(summaryResponse.getPullRequestsSummary());
                            summary.setIssuesSummary(summaryResponse.getIssuesSummary());
                            summary.setReleasesSummary(summaryResponse.getReleasesSummary());
                            summary.setAnalysis(summaryResponse.getAnalysis());
                            if (summaryResponse.getKeyAchievements() != null) {
                                summary.setKeyAchievements(summaryResponse.getKeyAchievements().stream().toArray(String[]::new));
                            }
                            if (summaryResponse.getAreasForImprovement() != null) {
                                summary.setAreasForImprovement(summaryResponse.getAreasForImprovement().stream().toArray(String[]::new));
                            }

                            if (summaryResponse.getMetadata() != null) {
                                summary.setTotalContributions(summaryResponse.getMetadata().getTotalContributions());
                                summary.setCommitsCount(summaryResponse.getMetadata().getCommitsCount());
                                summary.setPullRequestsCount(summaryResponse.getMetadata().getPullRequestsCount());
                                summary.setIssuesCount(summaryResponse.getMetadata().getIssuesCount());
                                summary.setReleasesCount(summaryResponse.getMetadata().getReleasesCount());
                            }

                            Summary savedSummary = summaryRepository.save(summary);
                            log.info("Successfully {} summary with ID {} for user: {}, week: {}, repository: {}",
                                    isUpdate ? "updated" : "created", savedSummary.getId(), username, week, repository.getRepositoryLink());
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

    /**
     * Convert contribution type string to enum
     */
    private ContributionType mapToContributionType(String type) {
        return switch (type.toLowerCase()) {
            case "commit" -> ContributionType.COMMIT;
            case "pull_request", "pullrequest" -> ContributionType.PULL_REQUEST;
            case "issue" -> ContributionType.ISSUE;
            case "release" -> ContributionType.RELEASE;
            default -> {
                log.warn("Unknown contribution type: {}, defaulting to COMMIT", type);
                yield ContributionType.COMMIT;
            }
        };
    }

    /**
     * Extract owner/repo from GitHub URL
     */
    private String extractOwnerRepoFromUrl(String repositoryLink) {
        // Extract owner/repo from URL like "https://github.com/owner/repo"
        if (repositoryLink.startsWith("https://github.com/")) {
            String ownerRepo = repositoryLink.substring("https://github.com/".length());
            // Remove any trailing slash or .git extension
            ownerRepo = ownerRepo.replaceAll("(\\.git)?/?$", "");
            return ownerRepo;
        }

        // If it's already in owner/repo format, return as is
        if (repositoryLink.matches("^[^/]+/[^/]+$")) {
            return repositoryLink;
        }

        log.warn("Could not extract owner/repo from repository link: {}", repositoryLink);
        return repositoryLink; // Return as is if we can't parse it
    }
}
