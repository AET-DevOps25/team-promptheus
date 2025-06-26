package de.promptheus.contributions.dto;

import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import lombok.Builder;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.NotBlank;
import java.time.Instant;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ContributionDto {

    @NotBlank(message = "ID is required")
    private String id; // Required for PUT operations
    
    @NotNull
    private Long gitRepositoryId;
    
    @NotNull
    private String type;
    
    @NotNull
    private String username;
    
    @NotNull
    private String summary;
    
    @NotNull
    private Boolean isSelected;
    
    private Instant createdAt;
    
    // Helper method to create DTO from entity
    public static ContributionDto fromEntity(de.promptheus.contributions.entity.Contribution contribution) {
        return ContributionDto.builder()
                .id(contribution.getId())
                .gitRepositoryId(contribution.getGitRepositoryId())
                .type(contribution.getType())
                .username(contribution.getUsername())
                .summary(contribution.getSummary())
                .isSelected(contribution.getIsSelected())
                .createdAt(contribution.getCreatedAt())
                .build();
    }
} 