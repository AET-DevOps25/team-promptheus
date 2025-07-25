package com.server.api;

import com.server.CommunicationObjects.*;
import io.micrometer.core.instrument.MeterRegistry;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.ExampleObject;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import jakarta.validation.constraints.NotNull;
import java.util.UUID;
import java.util.List;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/repositories")
public class GitRepoController {

    private final GitRepoService gitRepoService;
    private final MeterRegistry meterRegistry;

    @Autowired
    public GitRepoController(GitRepoService gitRepoService, MeterRegistry registry) {
        this.gitRepoService = gitRepoService;
        meterRegistry = registry;
    }

    @Operation(summary = "Provide the personal access token to retrieve the secure maintainer and developer links")
    @ApiResponses(
        value = {
            @ApiResponse(
                responseCode = "200",
                description = "Secure maintainer and developer access links successfully generated",
                content = {
                    @Content(
                        mediaType = "application/json",
                        schema = @Schema(
                            implementation = LinkConstruct.class,
                            description = "Contains developer and stakeholder access links",
                            requiredProperties = { "developerview", "stakeholderview" }
                        ),
                        examples = @ExampleObject(
                            value = """
                            {
                              "developerview": "https://example.com/app/123e4567-e89b-12d3-a456-426614174000",
                              "stakeholderview": "https://example.com/app/123e4567-e89b-12d3-a456-426614174001"
                            }
                            """
                        )
                    ),
                }
            ),
            @ApiResponse(
                responseCode = "403",
                description = "Forbidden - Invalid personal access token provided",
                content = {
                    @Content(
                        mediaType = "application/json",
                        schema = @Schema(description = "Error message", nullable = false),
                        examples = @ExampleObject(value = "\"Invalid personal access token\"")
                    ),
                }
            ),
        }
    )
    @PostMapping("/PAT")
    public ResponseEntity<LinkConstruct> createFromPAT(
        @io.swagger.v3.oas.annotations.parameters.RequestBody(
            description = "Personal Access Token for GitHub repository",
            required = true,
            content = @Content(
                mediaType = "application/json",
                schema = @Schema(implementation = PATConstruct.class),
                examples = @ExampleObject(
                    value = """
                    {
                      "pat": "ghp_1234567890abcdefghijklmnopqrstuvwxyz",
                      "repolink": "https://github.com/organization/repository"
                    }
                    """
                )
            )
        ) @RequestBody PATConstruct patRequest
    ) {
        LinkConstruct lc = gitRepoService.createAccessLinks(patRequest);
        meterRegistry.counter("pat_registration_total").increment();
        return ResponseEntity.ok(lc);
    }

    @Operation(summary = "Get the git repository information", description = "Auth is handled via the provided UUID")
    @ApiResponses(
        value = {
            @ApiResponse(
                responseCode = "200",
                description = "Repository information including questions, summaries, and contents",
                content = {
                    @Content(
                        mediaType = "application/json",
                        schema = @Schema(
                            implementation = GitRepoInformationConstruct.class,
                            description = "Complete repository information with related metadata",
                            requiredProperties = { "repoLink", "isMaintainer", "createdAt" }
                        ),
                        examples = @ExampleObject(
                            value = """
                            {
                              "repoLink": "https://github.com/organization/repository",
                              "isMaintainer": true,
                              "createdAt": "2023-01-15T14:30:45.123Z",
                              "questions": [
                                {
                                  "question": "How does the authentication system work?",
                                  "answers": [
                                    {
                                      "answer": "The system uses OAuth2 with JWT tokens",
                                      "createdAt": "2023-01-16T09:15:30.456Z"
                                    }
                                  ],
                                  "createdAt": "2023-01-15T16:45:22.789Z"
                                }
                              ],
                              "summaries": [],
                              "contents": []
                            }
                            """
                        )
                    ),
                }
            ),
            @ApiResponse(
                responseCode = "403",
                description = "Forbidden - Requested UUID access token does not exist",
                content = {
                    @Content(
                        mediaType = "application/json",
                        schema = @Schema(implementation = String.class, description = "Error message", nullable = false),
                        examples = @ExampleObject(
                            value = "\"Invalid access token\""
                        )
                    ),
                }
            ),
        }
    )
    @GetMapping("/{usercode}")
    public ResponseEntity<GitRepoInformationConstruct> getGitRepository(
        @PathVariable @NotNull @Schema(
            description = "UUID access token for repository authentication",
            example = "123e4567-e89b-12d3-a456-426614174000",
            nullable = false
        ) UUID usercode
    ) {
        GitRepoInformationConstruct gitRepository = gitRepoService.getRepositoryByAccessID(usercode);
        return ResponseEntity.ok(gitRepository);
    }

    @Operation(summary = "Create a question and get the AI-powered answer")
    @ApiResponses(
        value = {
            @ApiResponse(
                responseCode = "200",
                description = "Question processed successfully with AI-generated answer",
                content = {
                    @Content(
                        mediaType = "application/json",
                        schema = @Schema(implementation = QuestionAnswerConstruct.class),
                        examples = @ExampleObject(
                            value = """
                            {
                              "answer": "Based on the contributions, the main technical challenges included...",
                              "confidence": 0.95,
                              "createdAt": "2023-01-16T09:15:30.456Z",
                              "genaiQuestionId": "018d1234-5678-7abc-def0-123456789abc",
                              "userName": "john.doe",
                              "weekId": "2025-W29",
                              "questionText": "What were the main technical challenges this week?",
                              "askedAt": "2023-01-16T09:15:30.456Z",
                              "responseTimeMs": 1420,
                              "conversationId": "john.doe:2025-W29"
                            }
                            """
                        )
                    ),
                }
            ),
            @ApiResponse(
                responseCode = "403",
                description = "Forbidden - Requested UUID access token does not exist",
                content = {
                    @Content(
                        mediaType = "application/json",
                        schema = @Schema(implementation = String.class, description = "Error message", nullable = false),
                        examples = @ExampleObject(value = "\"Invalid access token\"")
                    ),
                }
            ),
        }
    )
    @PostMapping("/{usercode}/question")
    public ResponseEntity<QuestionAnswerConstruct> createQuestion(
        @PathVariable @NotNull @Schema(
            description = "UUID access token for repository authentication",
            example = "123e4567-e89b-12d3-a456-426614174000",
            nullable = false
        ) UUID usercode,
        @io.swagger.v3.oas.annotations.parameters.RequestBody(
            description = "Question to create",
            required = true,
            content = @Content(
                mediaType = "application/json",
                schema = @Schema(implementation = QuestionSubmission.class),
                examples = @ExampleObject(value = "{ \"question\": \"Why are these developer raving about 42?\", \"username\": \"john.doe\", \"gitRepositoryId\": 123 }")
            )
        ) @RequestBody @NotNull QuestionSubmission question
    ) {
        QuestionAnswerConstruct result = gitRepoService.createQuestion(usercode, question.question(), question.username(), question.gitRepositoryId(), question.weekId());
        meterRegistry.counter("question_creation_total").increment();

        return ResponseEntity.ok(result);
    }

    @Operation(summary = "Get questions and answers for a specific user and week")
    @ApiResponses(
        value = {
            @ApiResponse(
                responseCode = "200",
                description = "Questions and answers for the specified user and week",
                content = {
                    @Content(
                        mediaType = "application/json",
                        schema = @Schema(
                            implementation = QuestionAnswerConstruct.class,
                            type = "array",
                            description = "List of questions and answers with rich metadata"
                        ),
                        examples = @ExampleObject(
                            value = """
                            [
                              {
                                "answer": "You worked on implementing the Q/A API system...",
                                "confidence": 0.95,
                                "createdAt": "2023-01-16T09:15:30.456Z",
                                "genaiQuestionId": "018d1234-5678-7abc-def0-123456789abc",
                                "userName": "john.doe",
                                "weekId": "2025-W29",
                                "questionText": "What did I work on this week?",
                                "askedAt": "2023-01-16T09:15:30.456Z",
                                "responseTimeMs": 1420,
                                "conversationId": "john.doe:2025-W29"
                              }
                            ]
                            """
                        )
                    )
                }
            )
        }
    )
    @GetMapping("/questions/{username}/{weekId}")
    public ResponseEntity<List<QuestionAnswerConstruct>> getQuestionsForUserWeek(
        @PathVariable @NotNull @Schema(
            description = "GitHub username to get questions for",
            example = "john.doe",
            nullable = false
        ) String username,
        @PathVariable @NotNull @Schema(
            description = "ISO week format (YYYY-WXX) to get questions for",
            example = "2025-W29",
            nullable = false
        ) String weekId
    ) {
        List<QuestionAnswerConstruct> questionsAndAnswers = gitRepoService.getQuestionsAndAnswersForUserWeek(username, weekId);
        return ResponseEntity.ok(questionsAndAnswers);
    }
}
