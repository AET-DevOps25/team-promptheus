package de.promptheus.contributions.service;

import de.promptheus.contributions.entity.GitRepository;
import de.promptheus.contributions.entity.Contribution;
import de.promptheus.contributions.repository.PersonalAccessTokenRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.kohsuke.github.*;
import org.springframework.stereotype.Service;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.io.IOException;
import java.time.Instant;
import java.util.*;
import java.util.regex.Pattern;
import java.util.regex.Matcher;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@Slf4j
public class GitHubApiService {

    private final PersonalAccessTokenRepository patRepository;
    private final ObjectMapper objectMapper;

    private static final Pattern REPO_URL_PATTERN = Pattern.compile("https://github\\.com/([^/]+)/([^/]+)");

    /**
     * Exception thrown when GitHub API rate limit is exceeded
     */
    public static class RateLimitExceededException extends RuntimeException {
        private final int remainingRequests;
        private final long resetTimeEpoch;

        public RateLimitExceededException(String message, int remainingRequests, long resetTimeEpoch) {
            super(message);
            this.remainingRequests = remainingRequests;
            this.resetTimeEpoch = resetTimeEpoch;
        }

        public int getRemainingRequests() { return remainingRequests; }
        public long getResetTimeEpoch() { return resetTimeEpoch; }
    }

    /**
     * Fetch all contributions for a repository (for manual trigger)
     */
    public List<Contribution> fetchAllContributions(String repositoryUrl) {
        log.info("Starting to fetch all contributions for repository: {}", repositoryUrl);

        try {
            return fetchContributionsInternal(repositoryUrl, null);
        } catch (Exception e) {
            if (isRateLimitError(e)) {
                log.warn("Rate limit detected during contribution fetch: {}", e.getMessage());
                throw new RateLimitExceededException("Rate limit exceeded during fetch", 0, System.currentTimeMillis() / 1000 + 3600);
            }
            throw e;
        }
    }

    /**
     * Fetch contributions since a specific timestamp (for scheduled fetching)
     */
    public List<Contribution> fetchContributionsSince(GitRepository repository, Instant since) {
        log.info("Starting GitHub API fetch for repository: {}, since: {}",
                repository.getRepositoryLink(), since != null ? since : "beginning of time");

        List<Contribution> contributions = new ArrayList<>();

        try {
            // Extract owner and repo from URL
            log.info("Step 1: Extracting owner and repo from URL: {}", repository.getRepositoryLink());
            String[] ownerRepo = extractOwnerAndRepo(repository.getRepositoryLink());
            String owner = ownerRepo[0];
            String repo = ownerRepo[1];

            log.info("Step 2: Extracted owner: {}, repo: {} from URL: {}", owner, repo, repository.getRepositoryLink());

            // Get GitHub instance with PAT
            log.info("Step 3: Getting GitHub API instance...");
            GitHub github = getGitHubInstance(repository.getRepositoryLink());
            if (github == null) {
                log.warn("Step 3 FAILED: No PAT found for repository: {}", repository.getRepositoryLink());
                return contributions;
            }

            log.info("Step 4: Successfully created GitHub API client for repository: {}", repository.getRepositoryLink());

            log.info("Step 5: Connecting to GitHub repository {}/{}...", owner, repo);
            GHRepository ghRepository = github.getRepository(owner + "/" + repo);
            log.info("Step 6: Successfully connected to GitHub repository: {}", ghRepository.getFullName());

            // Convert since timestamp to Date for GitHub API
            Date sinceDate = since != null ? Date.from(since) : null;

            log.info("Step 7: Starting to fetch contributions since {} for repository {}/{}",
                    since != null ? since : "beginning of time", owner, repo);

            // Fetch different types of contributions since the timestamp
            log.info("Step 8: Fetching commits...");
            List<Contribution> commits = fetchCommitsSince(ghRepository, sinceDate);
            log.info("Step 8 COMPLETED: Fetched {} commits", commits.size());
            contributions.addAll(commits);

            log.info("Step 9: Fetching pull requests...");
            List<Contribution> pullRequests = fetchPullRequestsSince(ghRepository, sinceDate);
            log.info("Step 9 COMPLETED: Fetched {} pull requests", pullRequests.size());
            contributions.addAll(pullRequests);

            log.info("Step 10: Fetching issues...");
            List<Contribution> issues = fetchIssuesSince(ghRepository, sinceDate);
            log.info("Step 10 COMPLETED: Fetched {} issues", issues.size());
            contributions.addAll(issues);

            log.info("Step 11: Fetching releases...");
            List<Contribution> releases = fetchReleasesSince(ghRepository, sinceDate);
            log.info("Step 11 COMPLETED: Fetched {} releases", releases.size());
            contributions.addAll(releases);

            log.info("Step 12: GitHub API fetch completed for repository {}/{}: {} total contributions (commits: {}, PRs: {}, issues: {}, releases: {})",
                    owner, repo, contributions.size(), commits.size(), pullRequests.size(), issues.size(), releases.size());

        } catch (RateLimitExceededException e) {
            log.error("GitHub API rate limit exceeded for repository {}: {}", repository.getRepositoryLink(), e.getMessage());
            throw e;
        } catch (Exception e) {
            log.error("Failed to fetch contributions for repository: {}", repository.getRepositoryLink(), e);

            // Check if this is a rate limit related error
            if (isRateLimitError(e)) {
                throw new RateLimitExceededException(
                    "GitHub API rate limit exceeded. Please try again later.",
                    0, System.currentTimeMillis() / 1000 + 3600); // Default 1 hour reset
            }
        }

        return contributions;
    }

    /**
     * Internal method to fetch contributions (with optional since timestamp)
     */
    private List<Contribution> fetchContributionsInternal(String repositoryUrl, Instant since) {
        List<Contribution> contributions = new ArrayList<>();

        try {
            // Extract owner and repo from URL
            String[] ownerRepo = extractOwnerAndRepo(repositoryUrl);
            String owner = ownerRepo[0];
            String repo = ownerRepo[1];

            // Get GitHub instance with PAT
            GitHub github = getGitHubInstance(repositoryUrl);
            if (github == null) {
                log.warn("No PAT found for repository: {}", repositoryUrl);
                return contributions;
            }

            GHRepository repository = github.getRepository(owner + "/" + repo);

            // Convert since timestamp to Date for GitHub API
            Date sinceDate = since != null ? Date.from(since) : null;

            log.info("Fetching contributions for repository {}/{} since {}",
                    owner, repo, since != null ? since : "beginning of time");

            // Fetch different types of contributions
            contributions.addAll(fetchCommitsSince(repository, sinceDate));
            contributions.addAll(fetchPullRequestsSince(repository, sinceDate));
            contributions.addAll(fetchIssuesSince(repository, sinceDate));
            contributions.addAll(fetchReleasesSince(repository, sinceDate));

            log.info("Fetched {} contributions for repository {}/{}", contributions.size(), owner, repo);

        } catch (RateLimitExceededException e) {
            log.error("GitHub API rate limit exceeded: {}", e.getMessage());
            throw e;
        } catch (Exception e) {
            log.error("Failed to fetch contributions for repository: {}", repositoryUrl, e);

            // Check if this is a rate limit related error
            if (isRateLimitError(e)) {
                throw new RateLimitExceededException(
                    "GitHub API rate limit exceeded. Please try again later.",
                    0, System.currentTimeMillis() / 1000 + 3600); // Default 1 hour reset
            }
        }

        return contributions;
    }

    private List<Contribution> fetchCommitsSince(GHRepository repository, Date since) {
        log.info("COMMITS Step 1: Starting to fetch commits from repository: {}, since: {}", repository.getFullName(), since);
        List<Contribution> commits = new ArrayList<>();

        try {
            log.info("COMMITS Step 2: Creating commit query for repository: {}", repository.getFullName());
            PagedIterable<GHCommit> commitIterable;
            if (since != null) {
                log.info("COMMITS Step 3: Querying commits since: {}", since);
                commitIterable = repository.queryCommits().since(since).list();
                log.info("COMMITS Step 4: Query created successfully, starting iteration...");
            } else {
                log.info("COMMITS Step 3: Querying all commits (no since date)");
                commitIterable = repository.queryCommits().list();
                log.info("COMMITS Step 4: Query created successfully, starting iteration...");
            }

            int processedCount = 0;
            log.info("COMMITS Step 5: Starting to iterate through commits...");
            for (GHCommit commit : commitIterable) {
                processedCount++;
                log.debug("COMMITS Step 6.{}: Processing commit SHA={}, author={}, message={}",
                         processedCount, commit.getSHA1(),
                         commit.getAuthor() != null ? commit.getAuthor().getLogin() : "unknown",
                         commit.getCommitShortInfo().getMessage().substring(0, Math.min(50, commit.getCommitShortInfo().getMessage().length())));

                Contribution contribution = createContributionFromCommit(commit);
                if (contribution != null) {
                    commits.add(contribution);
                    log.debug("COMMITS Step 7.{}: Created contribution from commit: type={}, id={}, username={}",
                             processedCount, contribution.getType(), contribution.getId(), contribution.getUsername());
                } else {
                    log.warn("COMMITS Step 7.{}: Failed to create contribution from commit: {}", processedCount, commit.getSHA1());
                }

                // Log every 10 commits to track progress
                if (processedCount % 10 == 0) {
                    log.info("COMMITS Progress: Processed {} commits so far", processedCount);
                }
            }

            log.info("COMMITS Step 8: Completed fetching commits: processed {} commits, created {} contributions",
                    processedCount, commits.size());

        } catch (Exception e) {
            log.error("COMMITS ERROR: Failed to fetch commits since {} for repository {}: {}",
                    since, repository.getFullName(), e.getMessage(), e);
        }

        return commits;
    }

    private List<Contribution> fetchPullRequestsSince(GHRepository repository, Date since) {
        List<Contribution> pullRequests = new ArrayList<>();

        try {
            List<GHPullRequest> prs = repository.getPullRequests(GHIssueState.ALL);

            for (GHPullRequest pr : prs) {
                Date updatedAt = pr.getUpdatedAt();
                if (since == null || (updatedAt != null && updatedAt.after(since))) {
                    Contribution contribution = createContributionFromPullRequest(pr);
                    if (contribution != null) {
                        pullRequests.add(contribution);
                    }
                }
            }

        } catch (Exception e) {
            log.error("Failed to fetch pull requests since {} for repository {}",
                    since, repository.getFullName(), e);
        }

        return pullRequests;
    }

    private List<Contribution> fetchIssuesSince(GHRepository repository, Date since) {
        List<Contribution> issues = new ArrayList<>();

        try {
            List<GHIssue> issueList = repository.getIssues(GHIssueState.ALL);

            for (GHIssue issue : issueList) {
                if (!issue.isPullRequest()) {
                    Date updatedAt = issue.getUpdatedAt();
                    if (since == null || (updatedAt != null && updatedAt.after(since))) {
                        Contribution contribution = createContributionFromIssue(issue);
                        if (contribution != null) {
                            issues.add(contribution);
                        }
                    }
                }
            }

        } catch (Exception e) {
            log.error("Failed to fetch issues since {} for repository {}",
                    since, repository.getFullName(), e);
        }

        return issues;
    }

    private List<Contribution> fetchReleasesSince(GHRepository repository, Date since) {
        List<Contribution> releases = new ArrayList<>();

        try {
            PagedIterable<GHRelease> releaseIterable = repository.listReleases();

            for (GHRelease release : releaseIterable) {
                Date publishedAt = release.getPublished_at();
                if (since == null || (publishedAt != null && publishedAt.after(since))) {
                    Contribution contribution = createContributionFromRelease(release);
                    if (contribution != null) {
                        releases.add(contribution);
                    }
                }
            }

        } catch (Exception e) {
            log.error("Failed to fetch releases since {} for repository {}",
                    since, repository.getFullName(), e);
        }

        return releases;
    }

    private Contribution createContributionFromCommit(GHCommit commit) {
        try {
            String commitSha = commit.getSHA1();
            String author = "";

            // Get author login, fallback to commit author name
            GHUser ghUser = commit.getAuthor();
            if (ghUser != null) {
                author = ghUser.getLogin();
            } else {
                GHCommit.ShortInfo shortInfo = commit.getCommitShortInfo();
                if (shortInfo != null && shortInfo.getAuthor() != null) {
                    author = shortInfo.getAuthor().getName();
                }
            }

            // Convert to JSON for details storage
            Map<String, Object> details = convertToMap(commit);

            return Contribution.builder()
                    .id(commitSha)
                    .type("commit")
                    .username(author)
                    .summary(commit.getCommitShortInfo().getMessage())
                    .createdAt(commit.getCommitDate().toInstant())
                    .details(objectMapper.valueToTree(details))
                    .isSelected(true)
                    .build();
        } catch (Exception e) {
            log.warn("Failed to create contribution from commit", e);
            return null;
        }
    }

    private Contribution createContributionFromPullRequest(GHPullRequest pr) {
        try {
            String prId = String.valueOf(pr.getNumber());
            String author = pr.getUser().getLogin();

            // Convert to JSON for details storage
            Map<String, Object> details = convertToMap(pr);

            return Contribution.builder()
                    .id(prId)
                    .type("pull_request")
                    .username(author)
                    .summary(pr.getTitle())
                    .createdAt(pr.getCreatedAt().toInstant())
                    .details(objectMapper.valueToTree(details))
                    .isSelected(true)
                    .build();
        } catch (Exception e) {
            log.warn("Failed to create contribution from pull request", e);
            return null;
        }
    }

    private Contribution createContributionFromIssue(GHIssue issue) {
        try {
            String issueId = String.valueOf(issue.getNumber());
            String author = issue.getUser().getLogin();

            // Convert to JSON for details storage
            Map<String, Object> details = convertToMap(issue);

            return Contribution.builder()
                    .id(issueId)
                    .type("issue")
                    .username(author)
                    .summary(issue.getTitle())
                    .createdAt(issue.getCreatedAt().toInstant())
                    .details(objectMapper.valueToTree(details))
                    .isSelected(true)
                    .build();
        } catch (Exception e) {
            log.warn("Failed to create contribution from issue", e);
            return null;
        }
    }

    private Contribution createContributionFromRelease(GHRelease release) {
        try {
            String releaseId = String.valueOf(release.getId());
            String author = ""; // Releases don't have a direct author field in GitHub API

            // Convert to JSON for details storage
            Map<String, Object> details = convertToMap(release);

            return Contribution.builder()
                    .id(releaseId)
                    .type("release")
                    .username(author)
                    .summary(release.getName())
                    .createdAt(release.getPublished_at().toInstant())
                    .details(objectMapper.valueToTree(details))
                    .isSelected(true)
                    .build();
        } catch (Exception e) {
            log.warn("Failed to create contribution from release", e);
            return null;
        }
    }

    private GitHub getGitHubInstance(String repositoryUrl) {
        try {
            // Get repository ID from URL (this requires a lookup in the database)
            // For now, we'll get the first available PAT
            String token = getPersonalAccessToken(repositoryUrl);
            if (token == null) {
                return null;
            }

            return new GitHubBuilder()
                    .withOAuthToken(token)
                    .build();

        } catch (Exception e) {
            log.error("Failed to create GitHub instance for repository: {}", repositoryUrl, e);
            return null;
        }
    }

    private String getPersonalAccessToken(String repositoryUrl) {
        // This is a simplified implementation - in reality, you'd look up by repository ID
        // For now, we'll just get any available PAT
        try {
            List<String> tokens = patRepository.findAll().stream()
                    .map(pat -> pat.getPat())
                    .collect(Collectors.toList());

            return tokens.isEmpty() ? null : tokens.get(0);
        } catch (Exception e) {
            log.error("Failed to get PAT for repository: {}", repositoryUrl, e);
            return null;
        }
    }

    private String[] extractOwnerAndRepo(String repositoryUrl) {
        Matcher matcher = REPO_URL_PATTERN.matcher(repositoryUrl);
        if (matcher.matches()) {
            return new String[]{matcher.group(1), matcher.group(2)};
        }
        throw new IllegalArgumentException("Invalid GitHub repository URL: " + repositoryUrl);
    }

    private Map<String, Object> convertToMap(GHCommit commit) {
        Map<String, Object> details = new HashMap<>();
        try {
            details.put("sha", commit.getSHA1());
            details.put("url", commit.getHtmlUrl().toString());
            details.put("message", commit.getCommitShortInfo().getMessage());
            details.put("date", commit.getCommitDate());

            if (commit.getAuthor() != null) {
                details.put("author_login", commit.getAuthor().getLogin());
                details.put("author_url", commit.getAuthor().getHtmlUrl().toString());
            }

            if (commit.getCommitShortInfo().getAuthor() != null) {
                details.put("author_name", commit.getCommitShortInfo().getAuthor().getName());
                details.put("author_email", commit.getCommitShortInfo().getAuthor().getEmail());
            }
        } catch (Exception e) {
            log.warn("Failed to convert commit to map", e);
        }
        return details;
    }

    private Map<String, Object> convertToMap(GHPullRequest pr) {
        Map<String, Object> details = new HashMap<>();
        try {
            details.put("number", pr.getNumber());
            details.put("title", pr.getTitle());
            details.put("body", pr.getBody());
            details.put("state", pr.getState().toString());
            details.put("url", pr.getHtmlUrl().toString());
            details.put("created_at", pr.getCreatedAt());
            details.put("updated_at", pr.getUpdatedAt());
            details.put("merged_at", pr.getMergedAt());
            details.put("user_login", pr.getUser().getLogin());
            details.put("user_url", pr.getUser().getHtmlUrl().toString());
            details.put("head_ref", pr.getHead().getRef());
            details.put("base_ref", pr.getBase().getRef());
        } catch (Exception e) {
            log.warn("Failed to convert pull request to map", e);
        }
        return details;
    }

    private Map<String, Object> convertToMap(GHIssue issue) {
        Map<String, Object> details = new HashMap<>();
        try {
            details.put("number", issue.getNumber());
            details.put("title", issue.getTitle());
            details.put("body", issue.getBody());
            details.put("state", issue.getState().toString());
            details.put("url", issue.getHtmlUrl().toString());
            details.put("created_at", issue.getCreatedAt());
            details.put("updated_at", issue.getUpdatedAt());
            details.put("closed_at", issue.getClosedAt());
            details.put("user_login", issue.getUser().getLogin());
            details.put("user_url", issue.getUser().getHtmlUrl().toString());

            // Add labels
            List<String> labels = issue.getLabels().stream()
                    .map(GHLabel::getName)
                    .collect(Collectors.toList());
            details.put("labels", labels);
        } catch (Exception e) {
            log.warn("Failed to convert issue to map", e);
        }
        return details;
    }

    private Map<String, Object> convertToMap(GHRelease release) {
        Map<String, Object> details = new HashMap<>();
        try {
            details.put("id", release.getId());
            details.put("tag_name", release.getTagName());
            details.put("name", release.getName());
            details.put("body", release.getBody());
            details.put("draft", release.isDraft());
            details.put("prerelease", release.isPrerelease());
            details.put("url", release.getHtmlUrl().toString());
            details.put("created_at", release.getCreatedAt());
            details.put("published_at", release.getPublished_at());

            // Note: GHRelease doesn't have a direct getAuthor() method
            // The author information is typically available through other means
        } catch (Exception e) {
            log.warn("Failed to convert release to map", e);
        }
        return details;
    }

    /**
     * Check if an exception is related to rate limiting
     */
    private boolean isRateLimitError(Exception e) {
        String message = e.getMessage();
        if (message == null) return false;

        return message.toLowerCase().contains("rate limit") ||
               message.toLowerCase().contains("api rate limit exceeded") ||
               message.contains("403") ||
               (e instanceof HttpException && ((HttpException) e).getResponseCode() == 403);
    }
}
