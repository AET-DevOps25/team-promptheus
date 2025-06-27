package de.promptheus.contributions.dto;

import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class TriggerRequest {

    @NotBlank(message = "Repository URL is required")
    @Pattern(regexp = "^https://github\\.com/[a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+$",
             message = "Repository URL must be a valid GitHub repository URL")
    private String repositoryUrl;
}
