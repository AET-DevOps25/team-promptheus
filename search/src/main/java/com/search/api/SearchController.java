package com.search.api;

import io.micrometer.core.instrument.MeterRegistry;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/api/search")
public class SearchController {
    private final SearchService searchService;
    private final MeterRegistry meterRegistry;

    @Autowired
    public SearchController(SearchService searchService, MeterRegistry registry) {
        this.searchService = searchService;
        meterRegistry = registry;
    }

    @Operation(summary = "Search repository content with filtering and sorting")
    @ApiResponses(value = {@ApiResponse(responseCode = "200", description = "Search results", content = {@Content(mediaType = "application/json", schema = @Schema(implementation = SearchResult.class))}), @ApiResponse(responseCode = "403", description = "Forbidden - Requested code does not exist", content = {@Content(mediaType = "text/plain", schema = @Schema(implementation = String.class))}),})
    @GetMapping("/{usercode}")
    public ResponseEntity<SearchResult> search(@PathVariable @NotNull UUID usercode, @RequestParam(name = "query") @NotNull @NotBlank String query, @Parameter(description = "Filter by user") @RequestParam(required = false) String user, @Parameter(description = "Filter by week") @RequestParam(required = false) String week, @Parameter(description = "Filter by contribution type") @RequestParam(required = false) String contribution_type, @Parameter(description = "Filter by repository") @RequestParam(required = false) String repository, @Parameter(description = "Filter by author") @RequestParam(required = false) String author, @Parameter(description = "Filter by timestamp (exact or range like '1640995200 TO 1672531200')") @RequestParam(required = false) String created_at_timestamp, @Parameter(description = "Filter by selection status") @RequestParam(required = false) Boolean is_selected, @Parameter(description = "Sort fields (comma-separated, prefix with - for descending, e.g., '-created_at_timestamp,relevance_score')") @RequestParam(required = false) String sort, @Parameter(description = "Maximum number of Search responses") @RequestParam(required = false) Integer limit, @Parameter(description = "Offset of Search responses") @RequestParam(required = false) Integer offset) {
        meterRegistry.counter("searches_performed_total").increment();
        Map<String, String> filters = SearchFilter.createFilterMap(user, week, contribution_type, repository, author, created_at_timestamp, is_selected);

        // Parse sort parameter
        List<String> sortFields = null;
        if (sort != null && !sort.trim().isEmpty()) {
            sortFields = Arrays.asList(sort.split(","));
            sortFields = sortFields.stream().map(String::trim).filter(s -> !s.isEmpty()).toList();
        }

        com.meilisearch.sdk.model.Searchable meilisearchResults = searchService.search(usercode, query, filters, sortFields, limit, offset);

        // Convert MeiliSearch Searchable to our custom SearchResult
        SearchResult results = SearchResult.builder().hits(meilisearchResults.getHits()).processingTimeMs(meilisearchResults.getProcessingTimeMs()).query(query).build();
        return ResponseEntity.status(HttpStatus.OK).body(results);
    }
}
