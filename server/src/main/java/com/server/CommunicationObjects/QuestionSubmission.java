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
    String question
) {}
