package com.autoback.autoback.api;

import com.autoback.autoback.CommunicationObjects.*;
import com.autoback.autoback.ConfigProperties;
import com.meilisearch.sdk.Client;
import com.meilisearch.sdk.Config;
import com.meilisearch.sdk.model.SearchResult;
import io.micrometer.core.instrument.Counter;
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

import java.util.Set;
import java.util.UUID;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/repositories")
public class GitRepoController {
    private final GitRepoService gitRepoService;
    private final Counter patRegistrationCnt;
    private final Counter questionCreationCnt;
    private final Client meilisearchClient;

    @Autowired
    public GitRepoController(GitRepoService gitRepoService, MeterRegistry registry, ConfigProperties properties) {
        this.gitRepoService = gitRepoService;
        meilisearchClient = new Client(new Config(properties.getMeiliHost(), properties.getMeiliMasterKey()));
        patRegistrationCnt = Counter.builder("pat_registration_total").description("Total number of personal access tokens registered").register(registry);
        questionCreationCnt = Counter.builder("question_creation_total").description("Total number of asked questions").register(registry);
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
        patRegistrationCnt.increment();
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
    public ResponseEntity<GitRepoInformationConstruct> getGitRepository(@RequestParam(name = "usercode", required = true) @NotNull @NotBlank @PathVariable UUID usercode) {
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
            @RequestParam(name = "usercode", required = true) @NotNull @NotBlank @PathVariable UUID usercode,
            @RequestParam(name = "query", required = true) @NotNull @NotBlank String query) {
        GitRepoInformationConstruct gitRepository = gitRepoService.getRepositoryByAccessID(usercode);
        if (gitRepository.contents().isEmpty())
            return ResponseEntity.notFound().build();
        SearchResult results = meilisearchClient.getIndex("content").search(query);
        return ResponseEntity.status(HttpStatus.OK).body(results);
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
    public ResponseEntity<String> createCommitSelectionForSummary(@RequestParam(name = "usercode", required = true) @NotNull @NotBlank @PathVariable UUID usercode, @RequestBody SelectionSubmission selection) {
        GitRepoInformationConstruct gitRepository = gitRepoService.getRepositoryByAccessID(usercode);

        Set<Long> content = gitRepository.contents().stream().map(ContentConstruct::id).collect(Collectors.toSet());
        if (selection.selection().stream().anyMatch(s -> !content.contains(s)))
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body("please make sure that all content exists");

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
    public ResponseEntity<String> createQuestion(@RequestParam(name = "usercode", required = true) @NotNull @NotBlank @PathVariable UUID usercode, @io.swagger.v3.oas.annotations.parameters.RequestBody(
            description = "QUestion to create", required = true,
            content = @Content(mediaType = "text/plain", schema = @Schema(implementation = String.class),
                    examples = @ExampleObject(value = "{ \"question\": \"Why are these developer raving about 42?\" }")))
    @RequestBody
    QuestionSubmission question) {
        gitRepoService.createQuestion(usercode, question.question());
        questionCreationCnt.increment();

        return ResponseEntity.ok("Created Successfully");
    }
}
