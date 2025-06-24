package de.promptheus.contributions.dto;

import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import lombok.Builder;

import java.time.Instant;
import java.util.List;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class TriggerResponse {
    
    private String status;
    private String message;
    private Instant triggeredAt;
    private Integer repositoriesProcessed;
    private Integer contributionsFetched;
    private Integer contributionsUpserted;
    private List<String> processedRepositories;
    private List<String> errors;
    private Long processingTimeMs;
} 