package de.promptheus.contributions.service;

import de.promptheus.contributions.entity.GitRepository;
import de.promptheus.contributions.entity.Contribution;
import de.promptheus.contributions.repository.PersonalAccessTokenRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.time.Instant;
import java.util.List;
import java.util.ArrayList;
import java.util.regex.Pattern;
import java.util.regex.Matcher;

@Service
@RequiredArgsConstructor
@Slf4j
public class GitHubApiService {

    private final RestTemplate restTemplate;
    private final PersonalAccessTokenRepository patRepository;
    private final ObjectMapper objectMapper;

    private static final String GITHUB_API_BASE = "https://api.github.com";
    private static final Pattern REPO_URL_PATTERN = Pattern.compile("https://github\\.com/([^/]+)/([^/]+)");

    public List<Contribution> fetchContributionsSince(GitRepository repository, Instant since) {
        List<Contribution> contributions = new ArrayList<>();

        try {
            // Extract owner and repo from URL
            String[] ownerRepo = extractOwnerAndRepo(repository.getRepositoryLink());
            String owner = ownerRepo[0];
            String repo = ownerRepo[1];

            // Get PAT for this repository
            String token = getPersonalAccessToken(repository.getId());
            if (token == null) {
                log.warn("No PAT found for repository: {}", repository.getRepositoryLink());
                return contributions;
            }

            // Fetch different types of contributions
            contributions.addAll(fetchCommits(owner, repo, token, since));
            contributions.addAll(fetchPullRequests(owner, repo, token, since));
            contributions.addAll(fetchIssues(owner, repo, token, since));
            contributions.addAll(fetchReleases(owner, repo, token, since));

            log.info("Fetched {} contributions for repository {}/{}",
                    contributions.size(), owner, repo);

        } catch (Exception e) {
            log.error("Failed to fetch contributions for repository: {}",
                    repository.getRepositoryLink(), e);
        }

        return contributions;
    }

    private List<Contribution> fetchCommits(String owner, String repo, String token, Instant since) {
        List<Contribution> commits = new ArrayList<>();

        try {
            String url = String.format("%s/repos/%s/%s/commits", GITHUB_API_BASE, owner, repo);
            if (since != null) {
                url += "?since=" + since.toString();
            }

            JsonNode response = makeGitHubApiCall(url, token);
            if (response != null && response.isArray()) {
                for (JsonNode commitNode : response) {
                    Contribution contribution = createContributionFromCommit(commitNode);
                    if (contribution != null) {
                        commits.add(contribution);
                    }
                }
            }

        } catch (Exception e) {
            log.error("Failed to fetch commits for {}/{}", owner, repo, e);
        }

        return commits;
    }

    private List<Contribution> fetchPullRequests(String owner, String repo, String token, Instant since) {
        List<Contribution> pullRequests = new ArrayList<>();

        try {
            String url = String.format("%s/repos/%s/%s/pulls?state=all&sort=updated&direction=desc",
                    GITHUB_API_BASE, owner, repo);

            JsonNode response = makeGitHubApiCall(url, token);
            if (response != null && response.isArray()) {
                for (JsonNode prNode : response) {
                    if (isAfterSince(prNode.path("updated_at").asText(), since)) {
                        Contribution contribution = createContributionFromPullRequest(prNode);
                        if (contribution != null) {
                            pullRequests.add(contribution);
                        }
                    }
                }
            }

        } catch (Exception e) {
            log.error("Failed to fetch pull requests for {}/{}", owner, repo, e);
        }

        return pullRequests;
    }

    private List<Contribution> fetchIssues(String owner, String repo, String token, Instant since) {
        List<Contribution> issues = new ArrayList<>();

        try {
            String url = String.format("%s/repos/%s/%s/issues?state=all&sort=updated&direction=desc",
                    GITHUB_API_BASE, owner, repo);

            JsonNode response = makeGitHubApiCall(url, token);
            if (response != null && response.isArray()) {
                for (JsonNode issueNode : response) {
                    // Skip pull requests (they appear in issues endpoint too)
                    if (!issueNode.has("pull_request")) {
                        if (isAfterSince(issueNode.path("updated_at").asText(), since)) {
                            Contribution contribution = createContributionFromIssue(issueNode);
                            if (contribution != null) {
                                issues.add(contribution);
                            }
                        }
                    }
                }
            }

        } catch (Exception e) {
            log.error("Failed to fetch issues for {}/{}", owner, repo, e);
        }

        return issues;
    }

    private List<Contribution> fetchReleases(String owner, String repo, String token, Instant since) {
        List<Contribution> releases = new ArrayList<>();

        try {
            String url = String.format("%s/repos/%s/%s/releases", GITHUB_API_BASE, owner, repo);

            JsonNode response = makeGitHubApiCall(url, token);
            if (response != null && response.isArray()) {
                for (JsonNode releaseNode : response) {
                    if (isAfterSince(releaseNode.path("published_at").asText(), since)) {
                        Contribution contribution = createContributionFromRelease(releaseNode);
                        if (contribution != null) {
                            releases.add(contribution);
                        }
                    }
                }
            }

        } catch (Exception e) {
            log.error("Failed to fetch releases for {}/{}", owner, repo, e);
        }

        return releases;
    }

    private JsonNode makeGitHubApiCall(String url, String token) {
        try {
            HttpHeaders headers = new HttpHeaders();
            headers.set("Authorization", "Bearer " + token);
            headers.set("Accept", "application/vnd.github.v3+json");
            headers.set("User-Agent", "Contribution-Service/1.0");

            HttpEntity<String> entity = new HttpEntity<>(headers);
            ResponseEntity<String> response = restTemplate.exchange(url, HttpMethod.GET, entity, String.class);

            if (response.getStatusCode().is2xxSuccessful()) {
                return objectMapper.readTree(response.getBody());
            } else {
                log.warn("GitHub API call failed with status: {}", response.getStatusCode());
            }

        } catch (Exception e) {
            log.error("Failed to make GitHub API call to: {}", url, e);
        }

        return null;
    }

    private Contribution createContributionFromCommit(JsonNode commitNode) {
        try {
            String commitSha = commitNode.path("sha").asText();
            // Get author login, fallback to commit author name if not available
            String author = commitNode.path("author").path("login").asText();
            if (author.isEmpty()) {
                author = commitNode.path("commit").path("author").path("name").asText();
            }
            return Contribution.builder()
                    .id(commitSha)
                    .type("commit")
                    .username(author)
                    .summary(commitNode.path("commit").path("message").asText())
                    .createdAt(Instant.parse(commitNode.path("commit").path("author").path("date").asText()))
                    .details(commitNode)
                    .isSelected(true)
                    .build();
        } catch (Exception e) {
            log.warn("Failed to create contribution from commit", e);
            return null;
        }
    }

    private Contribution createContributionFromPullRequest(JsonNode prNode) {
        try {
            String prId = prNode.path("number").asText();
            return Contribution.builder()
                    .id(prId)
                    .type("pull_request")
                    .username(prNode.path("user").path("login").asText())
                    .summary(prNode.path("title").asText())
                    .createdAt(Instant.parse(prNode.path("created_at").asText()))
                    .details(prNode)
                    .isSelected(true)
                    .build();
        } catch (Exception e) {
            log.warn("Failed to create contribution from pull request", e);
            return null;
        }
    }

    private Contribution createContributionFromIssue(JsonNode issueNode) {
        try {
            String issueId = issueNode.path("number").asText();
            return Contribution.builder()
                    .id(issueId)
                    .type("issue")
                    .username(issueNode.path("user").path("login").asText())
                    .summary(issueNode.path("title").asText())
                    .createdAt(Instant.parse(issueNode.path("created_at").asText()))
                    .details(issueNode)
                    .isSelected(true)
                    .build();
        } catch (Exception e) {
            log.warn("Failed to create contribution from issue", e);
            return null;
        }
    }

    private Contribution createContributionFromRelease(JsonNode releaseNode) {
        try {
            String releaseId = releaseNode.path("id").asText();
            return Contribution.builder()
                    .id(releaseId)
                    .type("release")
                    .username(releaseNode.path("author").path("login").asText())
                    .summary(releaseNode.path("name").asText())
                    .createdAt(Instant.parse(releaseNode.path("published_at").asText()))
                    .details(releaseNode)
                    .isSelected(true)
                    .build();
        } catch (Exception e) {
            log.warn("Failed to create contribution from release", e);
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

    private String getPersonalAccessToken(Long repositoryId) {
        // This would query the junction table to get the PAT for this repository
        // Implementation depends on your existing PAT entity structure
        return patRepository.findTokenByRepositoryId(repositoryId);
    }

    private boolean isAfterSince(String dateString, Instant since) {
        if (since == null || dateString == null || dateString.isEmpty()) {
            return true;
        }
        try {
            Instant date = Instant.parse(dateString);
            return date.isAfter(since);
        } catch (Exception e) {
            log.warn("Failed to parse date: {}", dateString);
            return true;
        }
    }
}
