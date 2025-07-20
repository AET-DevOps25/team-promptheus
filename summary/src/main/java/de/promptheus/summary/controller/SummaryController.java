package de.promptheus.summary.controller;

import de.promptheus.summary.dto.SummaryDto;
import de.promptheus.summary.persistence.GitRepository;
import de.promptheus.summary.persistence.GitRepositoryRepository;
import de.promptheus.summary.service.SummaryService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.data.web.PageableDefault;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Optional;

@RestController
@RequestMapping("/api/summaries")
@RequiredArgsConstructor
@Slf4j
@Tag(name = "summary-controller", description = "Summary management operations")
public class SummaryController {

    private final SummaryService summaryService;
    private final GitRepositoryRepository gitRepositoryRepository;

    @GetMapping
    @Operation(summary = "Get summaries with optional filters and pagination",
               description = "Retrieve summaries with filtering by week, username, and repository. " +
                           "Supports pagination and sorting. Returns enriched data with repository information.")
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "Successfully retrieved summaries"),
        @ApiResponse(responseCode = "400", description = "Invalid request parameters"),
        @ApiResponse(responseCode = "500", description = "Internal server error")
    })
    public Page<SummaryDto> getSummaries(
            @Parameter(description = "Optional week filter in format YYYY-WXX (e.g., 2024-W01)")
            @RequestParam Optional<String> week,
            @Parameter(description = "Optional username filter")
            @RequestParam Optional<String> username,
            @Parameter(description = "Optional repository filter (supports full URL, owner/repo format, or partial name)")
            @RequestParam Optional<String> repository,
            @Parameter(description = "Pagination parameters - default page=0, size=20, sort by createdAt desc")
            @PageableDefault(size = 20, sort = "createdAt", direction = Sort.Direction.DESC) Pageable pageable) {

        log.info("Getting summaries with filters - week: {}, username: {}, repository: {}, page: {}, size: {}",
                week.orElse("all"), username.orElse("all"), repository.orElse("all"),
                pageable.getPageNumber(), pageable.getPageSize());

        return summaryService.getSummariesPaginatedWithRepoInfo(week, username, repository, pageable);
    }

    @PostMapping("/backfill")
    @Operation(summary = "Generate backfill summaries for all repositories and users")
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "Backfill summary generation triggered successfully"),
        @ApiResponse(responseCode = "500", description = "Internal server error")
    })
    public void generateBackfillSummaries() {
        log.info("Manual backfill summary generation triggered for all repositories and users");
        summaryService.generateBackfillSummaries();
    }


    @PostMapping("/{owner}/{repo}/{username}/{week}")
    @Operation(summary = "Generate summary")
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "Summary generation triggered successfully"),
        @ApiResponse(responseCode = "404", description = "Repository or user not found"),
        @ApiResponse(responseCode = "500", description = "Internal server error")
    })
    public void generateSummary(
            @Parameter(description = "Repository owner/organization") @PathVariable String owner,
            @Parameter(description = "Repository name") @PathVariable String repo,
            @Parameter(description = "Username to generate summary for") @PathVariable String username,
            @Parameter(description = "Week in format YYYY-WXX") @PathVariable String week) {
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
