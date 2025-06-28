package com.server.CommunicationObjects;

import io.swagger.v3.oas.annotations.media.Schema;

@Schema(description = "Request object containing GitHub Personal Access Token and repository information")
public record PATConstruct(
    @Schema(
        description = "URL to the GitHub repository",
        example = "https://github.com/organization/repository",
        requiredMode = Schema.RequiredMode.REQUIRED,
        nullable = false
    )
    String repolink,

    @Schema(
        description = "GitHub Personal Access Token with repo scope",
        example = "ghp_1234567890abcdefghijklmnopqrstuvwxyz",
        requiredMode = Schema.RequiredMode.REQUIRED,
        nullable = false
    )
    String pat
) {}
