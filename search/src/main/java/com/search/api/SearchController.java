package com.search.api;

import com.meilisearch.sdk.model.FacetSearchable;
import io.micrometer.core.instrument.MeterRegistry;
import io.swagger.v3.oas.annotations.Operation;
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

import com.search.api.SearchResult;
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

    @Operation(summary = "allows searching the repository's content")
    @ApiResponses(value = {
            @ApiResponse(responseCode = "200", description = "searched repository-content",
                    content = {@Content(mediaType = "application/json", schema = @Schema(implementation = SearchResult.class))}),
            @ApiResponse(responseCode = "403", description = "Forbidden - Requested code does not exist",
                    content = {@Content(mediaType = "text/plain", schema = @Schema(implementation = String.class))}),

    })
    @GetMapping("/{usercode}")
    public ResponseEntity<SearchResult> search(
            @PathVariable @NotNull UUID usercode,
            @RequestParam(name = "query") @NotNull @NotBlank String query) {
        meterRegistry.counter("searches_performed_total").increment();
        FacetSearchable results = searchService.search(usercode,query);
        return ResponseEntity.status(HttpStatus.OK)
                .body(SearchResult.builder()
                        .facetHits(results.getFacetHits())
                        .processingTimeMs(results.getProcessingTimeMs())
                        .facetQuery(results.getFacetQuery())
                        .build());
    }
}
