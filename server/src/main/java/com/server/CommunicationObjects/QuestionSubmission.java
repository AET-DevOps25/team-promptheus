package com.server.CommunicationObjects;

import io.swagger.v3.oas.annotations.media.Schema;

@Schema(description = "Request object for submitting a new question to be answered by the AI")
public record QuestionSubmission(
    @Schema(
        description = "The question text to be processed by the AI",
        example = "How does the authentication system work?",
        requiredMode = Schema.RequiredMode.REQUIRED,
        nullable = false,
        minLength = 5,
        maxLength = 500
    )
    String question,

    @Schema(
        description = "The username of the person asking the question",
        example = "john.doe",
        requiredMode = Schema.RequiredMode.REQUIRED,
        nullable = false,
        minLength = 1,
        maxLength = 100
    )
    String username,

    @Schema(
        description = "Optional repository ID to specify which repository the question is about (overrides repository from usercode)",
        example = "123",
        requiredMode = Schema.RequiredMode.NOT_REQUIRED,
        nullable = true
    )
    Long gitRepositoryId,

    @Schema(
        description = "Optional week ID to associate the question with a specific week (if not provided, uses current week)",
        example = "2025-W25",
        requiredMode = Schema.RequiredMode.NOT_REQUIRED,
        nullable = true
    )
    String weekId
) {}
