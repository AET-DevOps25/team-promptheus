package de.promptheus.summary.controller;

import de.promptheus.summary.persistence.Summary;
import de.promptheus.summary.persistence.GitRepository;
import de.promptheus.summary.persistence.GitRepositoryRepository;
import de.promptheus.summary.service.SummaryService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Optional;

@RestController
@RequestMapping("/api/summaries")
@RequiredArgsConstructor
@Slf4j
public class SummaryController {

    private final SummaryService summaryService;
    private final GitRepositoryRepository gitRepositoryRepository;

    @GetMapping
    public List<Summary> getSummaries(@RequestParam Optional<String> week) {
        return summaryService.getSummaries(week);
    }

    @GetMapping("/repositories/search")
    public List<GitRepository> searchRepositoriesByName(@RequestParam String name) {
        log.info("Searching for repositories with name: {}", name);
        List<GitRepository> repositories = gitRepositoryRepository.findRepoByName(name);
        log.info("Found {} repositories matching name: {}", repositories.size(), name);
        return repositories;
    }

    @PostMapping("/{owner}/{repo}/{username}/{week}")
    public void generateSummary(@PathVariable String owner, @PathVariable String repo, @PathVariable String username, @PathVariable String week) {
        log.info("Manual summary generation triggered for user: {}, week: {}, repository: {}/{}", username, week, owner, repo);

        // Construct repository URL format that matches what's stored in database
        String repositoryUrl = String.format("https://github.com/%s/%s", owner, repo);

        // Find the specific repository by URL or name
        List<GitRepository> repositories = gitRepositoryRepository.findByRepositoryLink(repositoryUrl);

        // If not found by repo name, try with full URL
        if (repositories.isEmpty()) {
            repositories = gitRepositoryRepository.findRepoByName(repositoryUrl);
        }

        if (repositories.isEmpty()) {
            log.warn("No repository found with name: {} or URL: {}", repo, repositoryUrl);
            throw new RuntimeException("Repository not found: " + owner + "/" + repo);
        }

        // Use the first matching repository
        GitRepository targetRepository = repositories.get(0);
        log.info("Found repository: {} (ID: {}) for {}/{}", targetRepository.getRepositoryLink(), targetRepository.getId(), owner, repo);

        // Get PAT for this repository
        String token = gitRepositoryRepository.findTokenByRepositoryId(targetRepository.getId());
        if (token == null) {
            log.warn("No PAT found for repository: {} (ID: {})", targetRepository.getRepositoryLink(), targetRepository.getId());
            throw new RuntimeException("No PAT found for repository: " + owner + "/" + repo);
        }

        // Check if this user has contributions in this repository
        summaryService.generateSummary(username, week, targetRepository, token);
    }
}
