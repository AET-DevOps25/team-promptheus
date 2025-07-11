package de.promptheus.contributions.controller;

import de.promptheus.contributions.dto.TriggerRequest;
import de.promptheus.contributions.dto.TriggerResponse;
import de.promptheus.contributions.service.ContributionFetchService;
import de.promptheus.contributions.service.GitHubApiService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import jakarta.validation.Valid;
import de.promptheus.contributions.dto.ContributionDto;
import de.promptheus.contributions.service.ContributionService;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import java.util.List;
import java.time.Instant;
import java.util.Map;

@RestController
@RequestMapping("/api/contributions")
@RequiredArgsConstructor
@Slf4j
public class ContributionController {

    private final ContributionFetchService contributionFetchService;
    private final ContributionService contributionService;

    @Operation(summary = "Trigger contribution fetch for all repositories")
    @ApiResponses(value = {
            @ApiResponse(responseCode = "200", description = "Contribution fetch triggered successfully",
                    content = {@Content(mediaType = "application/json",
                            schema = @Schema(implementation = TriggerResponse.class))}),
            @ApiResponse(responseCode = "400", description = "Bad request"),
            @ApiResponse(responseCode = "429", description = "GitHub API rate limit exceeded"),
            @ApiResponse(responseCode = "500", description = "Internal server error")
    })
    @PostMapping("/trigger")
    public ResponseEntity<?> triggerContributionFetch() {
        log.info("Manual trigger for contribution fetch initiated");

        try {
            TriggerResponse response = contributionFetchService.triggerFetchForAllRepositories();

            log.info("Manual trigger completed. Processed {} repositories",
                    response.getRepositoriesProcessed());

            return ResponseEntity.ok(response);
        } catch (GitHubApiService.RateLimitExceededException e) {
            return handleRateLimitException(e);
        } catch (Exception e) {
            log.error("Failed to trigger contribution fetch", e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(Map.of("error", "Internal server error", "message", e.getMessage()));
        }
    }

    @Operation(summary = "Trigger contribution fetch for specific repository")
    @ApiResponses(value = {
            @ApiResponse(responseCode = "200", description = "Contribution fetch triggered successfully",
                    content = {@Content(mediaType = "application/json",
                            schema = @Schema(implementation = TriggerResponse.class))}),
            @ApiResponse(responseCode = "400", description = "Bad request - Invalid repository"),
            @ApiResponse(responseCode = "404", description = "Repository not found"),
            @ApiResponse(responseCode = "429", description = "GitHub API rate limit exceeded"),
            @ApiResponse(responseCode = "500", description = "Internal server error")
    })
    @PostMapping("/trigger/repository")
    public ResponseEntity<?> triggerContributionFetchForRepository(
            @Valid @RequestBody TriggerRequest request) {
        log.info("Manual trigger for contribution fetch initiated for repository: {}",
                request.getRepositoryUrl());

        try {
            TriggerResponse response = contributionFetchService.triggerFetchForRepository(
                    request.getRepositoryUrl());

            log.info("Manual trigger completed for repository: {}. Fetched {} contributions",
                    request.getRepositoryUrl(), response.getContributionsFetched());

            return ResponseEntity.ok(response);
        } catch (GitHubApiService.RateLimitExceededException e) {
            return handleRateLimitException(e);
        } catch (Exception e) {
            log.error("Failed to trigger contribution fetch for repository: {}",
                    request.getRepositoryUrl(), e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(Map.of("error", "Internal server error", "message", e.getMessage()));
        }
    }

    @Operation(summary = "Get all contributions")
    @ApiResponses(value = {
            @ApiResponse(responseCode = "200", description = "Contributions retrieved successfully",
                    content = {@Content(mediaType = "application/json",
                            schema = @Schema(implementation = Page.class))}),
            @ApiResponse(responseCode = "400", description = "Bad request"),
            @ApiResponse(responseCode = "500", description = "Internal server error")
    })
    @GetMapping
    public ResponseEntity<Page<ContributionDto>> getContributions(
            @RequestParam(required = false) String contributor,
            @RequestParam(required = false) String startDate,
            @RequestParam(required = false) String endDate,
            Pageable pageable) {

        log.info("Retrieving contributions with filters - contributor: {}, startDate: {}, endDate: {}, pagination: {}",
                contributor, startDate, endDate, pageable);

        Page<ContributionDto> contributions;

        // Parse date parameters if provided
        Instant startInstant = null;
        Instant endInstant = null;

        try {
            if (startDate != null && !startDate.trim().isEmpty()) {
                startInstant = Instant.parse(startDate);
            }
            if (endDate != null && !endDate.trim().isEmpty()) {
                endInstant = Instant.parse(endDate);
            }
        } catch (Exception e) {
            log.error("Invalid date format provided: startDate={}, endDate={}", startDate, endDate, e);
            return ResponseEntity.badRequest().build();
        }

        // Use filtering method if any filters are provided, otherwise use the basic method
        if (contributor != null || startInstant != null || endInstant != null) {
            contributions = contributionService.getContributionsWithFilters(contributor, startInstant, endInstant, pageable);
        } else {
            contributions = contributionService.getAllContributions(pageable);
        }

        log.info("Retrieved {} contributions", contributions.getTotalElements());

        return ResponseEntity.ok(contributions);
    }

    @Operation(summary = "Update contribution selection status")
    @ApiResponses(value = {
            @ApiResponse(responseCode = "200", description = "Contribution selections updated successfully"),
            @ApiResponse(responseCode = "400", description = "Bad request - Invalid input"),
            @ApiResponse(responseCode = "500", description = "Internal server error")
    })
    @PutMapping
    public ResponseEntity<String> updateContributions(@Valid @RequestBody List<ContributionDto> contributions) {
        log.info("Updating selection status for {} contributions", contributions.size());

        int updated = contributionService.updateContributionSelections(contributions);

        log.info("Updated selection status for {} contributions", updated);

        return ResponseEntity.ok(String.format("Updated %d contributions", updated));
    }

    /**
     * Handle GitHub API rate limit exceptions with appropriate HTTP response
     */
    private ResponseEntity<Map<String, Object>> handleRateLimitException(GitHubApiService.RateLimitExceededException e) {
        log.warn("GitHub API rate limit exceeded: {}", e.getMessage());

        HttpHeaders headers = new HttpHeaders();
        headers.add("Retry-After", String.valueOf(e.getResetTimeEpoch() - System.currentTimeMillis() / 1000));
        headers.add("X-RateLimit-Remaining", String.valueOf(e.getRemainingRequests()));
        headers.add("X-RateLimit-Reset", String.valueOf(e.getResetTimeEpoch()));

        Map<String, Object> errorResponse = Map.of(
                "error", "Rate limit exceeded",
                "message", e.getMessage(),
                "remainingRequests", e.getRemainingRequests(),
                "resetTime", e.getResetTimeEpoch(),
                "resetTimeReadable", Instant.ofEpochSecond(e.getResetTimeEpoch()).toString()
        );

        return ResponseEntity.status(HttpStatus.TOO_MANY_REQUESTS)
                .headers(headers)
                .body(errorResponse);
    }
}
