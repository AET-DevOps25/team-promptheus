package com.server.CommunicationObjects;

import io.swagger.v3.oas.annotations.media.Schema;
import java.time.Instant;
import java.util.List;
import lombok.Builder;

@Schema(description = "Repository information including metadata, questions, summaries, and contents")
@Builder
public record GitRepoInformationConstruct(
    @Schema(
        description = "URL to the GitHub repository",
        example = "https://github.com/organization/repository",
        requiredMode = Schema.RequiredMode.REQUIRED,
        nullable = false
    )
    String repoLink,

    @Schema(
        description = "Whether the requesting user has maintainer privileges",
        example = "true",
        requiredMode = Schema.RequiredMode.REQUIRED,
        nullable = false
    )
    boolean isMaintainer,

    @Schema(
        description = "Timestamp when the repository was registered with the service",
        example = "2023-01-15T14:30:45.123Z",
        requiredMode = Schema.RequiredMode.REQUIRED,
        nullable = false
    )
    Instant createdAt,

    @Schema(description = "List of questions and their answers related to this repository", nullable = true) List<QuestionConstruct> questions,

    @Schema(description = "List of AI-generated summaries of the repository content", nullable = true) List<SummaryConstruct> summaries,

    @Schema(description = "List of repository content metadata", nullable = true) List<ContentConstruct> contents
) {}
