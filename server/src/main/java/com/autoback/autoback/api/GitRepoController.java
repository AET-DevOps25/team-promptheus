package com.autoback.autoback.api;

import com.autoback.autoback.CommunicationObjects.*;
import com.meilisearch.sdk.model.SearchResult;
import io.micrometer.core.instrument.MeterRegistry;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.ExampleObject;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.UUID;

@RestController
@RequestMapping("/api/repositories")
public class GitRepoController {
    private final GitRepoService gitRepoService;
    private final SearchService searchService;
    private final MeterRegistry meterRegistry;

    @Autowired
    public GitRepoController(GitRepoService gitRepoService, SearchService searchService, MeterRegistry registry) {
        this.gitRepoService = gitRepoService;
        this.searchService = searchService;
        meterRegistry = registry;
    }

    @Operation(summary = "Provide the personal access token to retrieve the secure maintainer and developer links")
    @ApiResponses(value = {
            @ApiResponse(responseCode = "200", description = "secure maintainer and developer links",
                    content = {@Content(mediaType = "application/json", schema = @Schema(implementation = LinkConstruct.class))}),
            @ApiResponse(responseCode = "403", description = "Forbidden - Requested code does not exist"),

    })
    @PostMapping("/PAT")
    public ResponseEntity<LinkConstruct> createFromPAT(@RequestBody PATConstruct patRequest) {
        LinkConstruct lc = gitRepoService.createAccessLinks(patRequest);
        meterRegistry.counter("pat_registration_total").increment();
        return ResponseEntity.ok(lc);
    }

    @Operation(summary = "Get the git repository information", description = "Auth is handled via the provided UUID")
    @ApiResponses(value = {
            @ApiResponse(responseCode = "200", description = "get repository-content",
                    content = {@Content(mediaType = "application/json", schema = @Schema(implementation = GitRepoInformationConstruct.class))}),
            @ApiResponse(responseCode = "403", description = "Forbidden - Requested code does not exist",
                    content = {@Content(mediaType = "text/plain", schema = @Schema(implementation = String.class))}),
    })
    @GetMapping("/{usercode}")
    public ResponseEntity<GitRepoInformationConstruct> getGitRepository(@PathVariable @NotNull UUID usercode) {
        GitRepoInformationConstruct gitRepository = gitRepoService.getRepositoryByAccessID(usercode);
        return ResponseEntity.ok(gitRepository);
    }

    @Operation(summary = "allows searching the repository's content")
    @ApiResponses(value = {
            @ApiResponse(responseCode = "200", description = "searched repository-content",
                    content = {@Content(mediaType = "application/json", schema = @Schema(implementation = SearchResult.class))}),
            @ApiResponse(responseCode = "403", description = "Forbidden - Requested code does not exist",
                    content = {@Content(mediaType = "text/plain", schema = @Schema(implementation = String.class))}),

    })
    @GetMapping("/{usercode}/search")
    public ResponseEntity<SearchResult> search(
            @PathVariable @NotNull UUID usercode,
            @RequestParam(name = "query") @NotNull @NotBlank String query) {
        GitRepoInformationConstruct gitRepository = gitRepoService.getRepositoryByAccessID(usercode);
        if (gitRepository.contents().isEmpty())
            return ResponseEntity.noContent().build();
        SearchResult results = searchService.search(query);
        return ResponseEntity.status(HttpStatus.OK)
                .body(results);
    }

    @Operation(summary = "tell the AI service which items should be included into the summary")
    @ApiResponses(value = {
            @ApiResponse(responseCode = "200", description = "Items were included in the summary",
                    content = {@Content(mediaType = "text/plain", schema = @Schema(implementation = String.class))}),
            @ApiResponse(responseCode = "400", description = "Invalid input provided - please make sure that all selected content exists",
                    content = {@Content(mediaType = "text/plain", schema = @Schema(implementation = String.class))}),
            @ApiResponse(responseCode = "403", description = "Forbidden - Requested code does not exist",
                    content = {@Content(mediaType = "text/plain", schema = @Schema(implementation = String.class))}),

    })
    @PostMapping("/{usercode}/selection")
    public ResponseEntity<String> createCommitSelectionForSummary(@PathVariable @NotNull UUID usercode, @RequestBody SelectionSubmission selection) {
        gitRepoService.createCommitSelection(usercode, selection);

        return ResponseEntity.ok("Created Successfully");
    }


    @Operation(summary = "create a question to be answered asynchronously by the ai service")
    @ApiResponses(value = {
            @ApiResponse(responseCode = "200", description = "Items were included in the summary",
                    content = {@Content(mediaType = "text/plain", schema = @Schema(implementation = String.class))}),
            @ApiResponse(responseCode = "403", description = "Forbidden - Requested code does not exist"),

    })
    @PostMapping("/{usercode}/question")
    public ResponseEntity<String> createQuestion(
            @PathVariable @NotNull UUID usercode,
            @io.swagger.v3.oas.annotations.parameters.RequestBody(
                description = "Question to create",
                required = true,
                content = @Content(
                        mediaType = "application/json",
                        schema = @Schema(implementation = QuestionSubmission.class),
                        examples = @ExampleObject(value = "{ \"question\": \"Why are these developer raving about 42?\" }"))
                )
    @RequestBody
    QuestionSubmission question) {
        gitRepoService.createQuestion(usercode, question.question());
        meterRegistry.counter("question_creation_total").increment();

        return ResponseEntity.ok("Created Successfully");
    }
}
