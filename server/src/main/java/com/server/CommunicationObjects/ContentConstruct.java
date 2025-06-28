package com.server.CommunicationObjects;

import com.server.persistence.entity.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import java.time.Instant;
import lombok.Builder;

@Schema(description = "Metadata about repository content with AI-generated summary")
@Builder
public record ContentConstruct(
    @Schema(description = "Unique identifier for the content item", example = "commit-12a34bc5", requiredMode = Schema.RequiredMode.REQUIRED, nullable = false)
    String id,

    @Schema(
        description = "Type of content (e.g., commit, pull request, issue)",
        example = "commit",
        requiredMode = Schema.RequiredMode.REQUIRED,
        nullable = false
    )
    String type,

    @Schema(description = "GitHub username of the content author", example = "johndoe", requiredMode = Schema.RequiredMode.REQUIRED, nullable = false)
    String user,

    @Schema(
        description = "AI-generated summary of the content",
        example = "Fixed authentication bug in login controller",
        requiredMode = Schema.RequiredMode.REQUIRED,
        nullable = false
    )
    String summary,

    @Schema(
        description = "Timestamp when the content was created or processed",
        example = "2023-01-20T08:45:12.789Z",
        requiredMode = Schema.RequiredMode.REQUIRED,
        nullable = false
    )
    Instant createdAt
) {
    public static ContentConstruct from(Content c) {
        return ContentConstruct.builder().type(c.getType()).id(c.getId()).user(c.getUser()).summary(c.getSummary()).createdAt(c.getCreatedAt()).build();
    }
}
