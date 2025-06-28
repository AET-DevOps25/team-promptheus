package com.server.CommunicationObjects;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Builder;

@Schema(description = "Contains secure access links for developers and stakeholders")
@Builder
public record LinkConstruct(
    @Schema(
        description = "URL for developer access to the repository",
        example = "https://example.com/app/123e4567-e89b-12d3-a456-426614174000",
        requiredMode = Schema.RequiredMode.REQUIRED,
        nullable = false
    )
    String developerview,

    @Schema(
        description = "URL for stakeholder access to the repository",
        example = "https://example.com/app/123e4567-e89b-12d3-a456-426614174001",
        requiredMode = Schema.RequiredMode.REQUIRED,
        nullable = false
    )
    String stakeholderview
) {}
