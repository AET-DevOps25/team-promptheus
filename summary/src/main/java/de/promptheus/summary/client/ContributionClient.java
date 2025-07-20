package de.promptheus.summary.client;

import de.promptheus.summary.contribution.api.ContributionControllerApi;
import de.promptheus.summary.contribution.model.ContributionDto;
import de.promptheus.summary.contribution.model.Pageable;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import reactor.core.publisher.Mono;

import java.time.DayOfWeek;
import java.time.Instant;
import java.time.LocalDate;
import java.time.OffsetDateTime;
import java.time.ZoneOffset;
import java.time.temporal.IsoFields;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Component
@RequiredArgsConstructor
@Slf4j
public class ContributionClient {

    private final ContributionControllerApi contributionApi;

    public Mono<List<ContributionDto>> getContributionsForUserAndWeek(String username, String week) {
        Pageable pageable = new Pageable();
        pageable.setPage(0);
        pageable.setSize(1000);

        // Convert week format (e.g., "2025-W25") to start and end dates
        String[] startEndDates = convertWeekToDateRange(week);
        String startDate = startEndDates[0];
        String endDate = startEndDates[1];

        return contributionApi.getContributions(pageable, username, startDate, endDate)
                .map(page -> {
                    List<?> content = page.getContent();

                    if (content == null || content.isEmpty()) {
                        return List.<ContributionDto>of();
                    }

                    // Handle OpenAPI client returning LinkedHashMap objects instead of ContributionDto
                    if (content.get(0) instanceof Map) {
                        return content.stream()
                                .map(obj -> convertMapToContributionDto((Map<String, Object>) obj))
                                .collect(Collectors.toList());
                    }

                    // If already ContributionDto objects, cast directly
                    @SuppressWarnings("unchecked")
                    List<ContributionDto> contributions = (List<ContributionDto>) content;
                    return contributions;
                });
    }

    /**
     * Get the oldest contribution date for a specific repository and user
     */
    public Mono<Instant> getOldestContributionDate(String username, Long repositoryId) {
        // For now, we'll need to fetch all contributions and find the oldest
        // This is not optimal but works with the current API structure
        Pageable pageable = new Pageable();
        pageable.setPage(0);
        pageable.setSize(10000); // Large size to get all contributions

        return contributionApi.getContributions(pageable, username, null, null)
                .map(page -> {
                    List<?> content = page.getContent();
                    if (content == null || content.isEmpty()) {
                        return null;
                    }

                    // Convert to ContributionDto objects
                    List<ContributionDto> contributions;
                    if (content.get(0) instanceof Map) {
                        contributions = content.stream()
                                .map(obj -> convertMapToContributionDto((Map<String, Object>) obj))
                                .collect(Collectors.toList());
                    } else {
                        @SuppressWarnings("unchecked")
                        List<ContributionDto> typedContributions = (List<ContributionDto>) content;
                        contributions = typedContributions;
                    }

                    // Filter by repository and find oldest
                    return contributions.stream()
                            .filter(contrib -> contrib.getGitRepositoryId() != null &&
                                             contrib.getGitRepositoryId().equals(repositoryId))
                            .map(ContributionDto::getCreatedAt)
                            .filter(offsetDateTime -> offsetDateTime != null)
                            .map(OffsetDateTime::toInstant)
                            .min(Instant::compareTo)
                            .orElse(null);
                });
    }

    /**
     * Convert week format (e.g., "2025-W25") to ISO 8601 date range.
     * Returns array with [startDate, endDate] in ISO format.
     */
    private String[] convertWeekToDateRange(String week) {
        // Parse week format: "YYYY-WNN"
        String[] parts = week.split("-W");
        int year = Integer.parseInt(parts[0]);
        int weekNumber = Integer.parseInt(parts[1]);

        // Calculate the start of the week (Monday)
        LocalDate startOfWeek = LocalDate.of(year, 1, 1)
                .with(IsoFields.WEEK_OF_WEEK_BASED_YEAR, weekNumber)
                .with(DayOfWeek.MONDAY);

        // Calculate the end of the week (Sunday)
        LocalDate endOfWeek = startOfWeek.plusDays(6);

        // Convert to ISO 8601 format with UTC timezone
        String startDate = startOfWeek.atStartOfDay(ZoneOffset.UTC).toInstant().toString();
        String endDate = endOfWeek.atTime(23, 59, 59, 999_999_999).atZone(ZoneOffset.UTC).toInstant().toString();

        return new String[]{startDate, endDate};
    }

    /**
     * Convert LinkedHashMap from OpenAPI client to ContributionDto
     */
    private ContributionDto convertMapToContributionDto(Map<String, Object> map) {
        ContributionDto dto = new ContributionDto();

        if (map.containsKey("id")) {
            dto.setId((String) map.get("id"));
        }
        if (map.containsKey("gitRepositoryId")) {
            Object gitRepoId = map.get("gitRepositoryId");
            if (gitRepoId instanceof Number) {
                dto.setGitRepositoryId(((Number) gitRepoId).longValue());
            }
        }
        if (map.containsKey("type")) {
            dto.setType((String) map.get("type"));
        }
        if (map.containsKey("username")) {
            dto.setUsername((String) map.get("username"));
        }
        if (map.containsKey("summary")) {
            dto.setSummary((String) map.get("summary"));
        }
        if (map.containsKey("isSelected")) {
            dto.setIsSelected((Boolean) map.get("isSelected"));
        }
        if (map.containsKey("createdAt")) {
            Object createdAt = map.get("createdAt");
            if (createdAt instanceof Number) {
                // Convert timestamp from seconds.nanoseconds format
                double timestampSeconds = ((Number) createdAt).doubleValue();
                long seconds = (long) timestampSeconds;
                long nanos = (long) ((timestampSeconds - seconds) * 1_000_000_000);
                dto.setCreatedAt(OffsetDateTime.ofInstant(Instant.ofEpochSecond(seconds, nanos), ZoneOffset.UTC));
            }
        }

        return dto;
    }
}
