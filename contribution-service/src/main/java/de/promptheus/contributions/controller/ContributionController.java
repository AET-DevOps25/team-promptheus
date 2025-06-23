package de.promptheus.contributions.controller;

import de.promptheus.contributions.dto.TriggerRequest;
import de.promptheus.contributions.dto.TriggerResponse;
import de.promptheus.contributions.service.ContributionFetchService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import jakarta.validation.Valid;

@RestController
@RequestMapping("/api/contributions")
@RequiredArgsConstructor
@Slf4j
public class ContributionController {

    private final ContributionFetchService contributionFetchService;

    @Operation(summary = "Trigger contribution fetch for all repositories")
    @ApiResponses(value = {
            @ApiResponse(responseCode = "200", description = "Contribution fetch triggered successfully",
                    content = {@Content(mediaType = "application/json", 
                            schema = @Schema(implementation = TriggerResponse.class))}),
            @ApiResponse(responseCode = "400", description = "Bad request"),
            @ApiResponse(responseCode = "500", description = "Internal server error")
    })
    @PostMapping("/trigger")
    public ResponseEntity<TriggerResponse> triggerContributionFetch() {
        log.info("Manual trigger for contribution fetch initiated");
        
        TriggerResponse response = contributionFetchService.triggerFetchForAllRepositories();
        
        log.info("Manual trigger completed. Processed {} repositories", 
                response.getRepositoriesProcessed());
        
        return ResponseEntity.ok(response);
    }

    @Operation(summary = "Trigger contribution fetch for specific repository")
    @ApiResponses(value = {
            @ApiResponse(responseCode = "200", description = "Contribution fetch triggered successfully",
                    content = {@Content(mediaType = "application/json", 
                            schema = @Schema(implementation = TriggerResponse.class))}),
            @ApiResponse(responseCode = "400", description = "Bad request - Invalid repository"),
            @ApiResponse(responseCode = "404", description = "Repository not found"),
            @ApiResponse(responseCode = "500", description = "Internal server error")
    })
    @PostMapping("/trigger/repository")
    public ResponseEntity<TriggerResponse> triggerContributionFetchForRepository(
            @Valid @RequestBody TriggerRequest request) {
        log.info("Manual trigger for contribution fetch initiated for repository: {}", 
                request.getRepositoryUrl());
        
        TriggerResponse response = contributionFetchService.triggerFetchForRepository(
                request.getRepositoryUrl());
        
        log.info("Manual trigger completed for repository: {}. Fetched {} contributions", 
                request.getRepositoryUrl(), response.getContributionsFetched());
        
        return ResponseEntity.ok(response);
    }

    @Operation(summary = "Get health status of contribution service")
    @GetMapping("/health")
    public ResponseEntity<String> health() {
        return ResponseEntity.ok("Contribution Service is running");
    }
} 