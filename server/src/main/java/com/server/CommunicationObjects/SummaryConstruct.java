package com.server.CommunicationObjects;

import com.server.persistence.entity.Summary;
import io.swagger.v3.oas.annotations.media.Schema;
import java.time.Instant;
import lombok.Builder;

@Schema(description = "AI-generated summary of repository content")
@Builder
public record SummaryConstruct(
    @Schema(description = "Unique identifier for the summary", example = "42", requiredMode = Schema.RequiredMode.REQUIRED, nullable = false) Long id,

    @Schema(
        description = "Text content of the AI-generated summary",
        example = "This repository implements a RESTful API for user authentication using Spring Security",
        requiredMode = Schema.RequiredMode.REQUIRED,
        nullable = false
    )
    String summary,

    @Schema(
        description = "Timestamp when the summary was generated",
        example = "2023-01-18T10:15:30.123Z",
        requiredMode = Schema.RequiredMode.REQUIRED,
        nullable = false
    )
    Instant createdAt
) {
    public static SummaryConstruct from(Summary s) {
        return SummaryConstruct.builder().summary(s.getSummary()).id(s.getId()).createdAt(s.getCreatedAt()).build();
    }
}
