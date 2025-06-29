package de.promptheus.summary.service;

import de.promptheus.summary.client.ContributionClient;
import de.promptheus.summary.client.GenAiClient;
import de.promptheus.summary.contribution.model.ContributionDto;
import de.promptheus.summary.genai.model.ContributionMetadata;
import de.promptheus.summary.genai.model.ContributionType;
import de.promptheus.summary.persistence.Summary;
import de.promptheus.summary.persistence.SummaryRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Mono;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.time.temporal.IsoFields;
import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@Slf4j
public class SummaryService {

    private final GenAiClient genAiClient;
    private final ContributionClient contributionClient;
    private final SummaryRepository summaryRepository;

    @Value("${app.defaultRepository:owner/repo}")
    private String defaultRepository;

    public List<Summary> getSummaries(Optional<String> week) {
        if (week.isPresent()) {
            return summaryRepository.findByWeek(week.get());
        }
        return summaryRepository.findAll();
    }

    @Scheduled(cron = "0 0 0 * * MON")
    public void generateWeeklySummaries() {
        // Calculate the previous week (since this runs on Monday, we want last week's summary)
        LocalDate today = LocalDate.now();
        LocalDate previousWeek = today.minusWeeks(1);
        String week = String.format("%d-W%02d",
                previousWeek.get(IsoFields.WEEK_BASED_YEAR),
                previousWeek.get(IsoFields.WEEK_OF_WEEK_BASED_YEAR));

        log.info("Starting automatic weekly summary generation for week: {}", week);

        // Get distinct usernames from existing summaries to generate new weekly summaries
        List<String> users = summaryRepository.findDistinctUsernames();
        for (String username : users) {
            generateSummaryForUser(username, week);
        }
    }

    public void generateSummaryForUser(String username, String week) {
        log.info("Starting summary generation for user: {}, week: {}", username, week);

        // Check if summary already exists for this user and week
        List<Summary> existingSummaries = summaryRepository.findByUsernameAndWeek(username, week);
        if (!existingSummaries.isEmpty()) {
            log.info("Summary already exists for user: {}, week: {} - skipping generation", username, week);
            return;
        }

        // Step 1: Fetch contributions for the specific user and week
        contributionClient.getContributionsForUserAndWeek(username, week)
                .flatMap(contributions -> {
                    log.info("Found {} total contributions for user: {}, week: {}", contributions.size(), username, week);

                    // Step 2: Filter by isSelected = true
                    List<ContributionDto> selectedContributions = contributions.stream()
                            .filter(contrib -> contrib.getIsSelected() != null && contrib.getIsSelected())
                            .collect(Collectors.toList());

                    if (selectedContributions.isEmpty()) {
                        log.warn("No selected contributions found for user: {}, week: {} - skipping summary generation", username, week);
                        return Mono.empty();
                    }

                    log.info("Found {} selected contributions for user: {}, week: {}", selectedContributions.size(), username, week);

                    // Step 3: Convert selected contributions to metadata format for GenAI service
                    List<ContributionMetadata> metadata = selectedContributions.stream()
                            .map(contrib -> {
                                ContributionMetadata meta = new ContributionMetadata();
                                meta.setType(mapToContributionType(contrib.getType()));
                                meta.setId(contrib.getId());
                                meta.setSelected(true); // All passed contributions are selected
                                return meta;
                            })
                            .collect(Collectors.toList());

                    log.info("Sending {} selected contributions to GenAI service for user: {}, week: {}", metadata.size(), username, week);

                    // Step 4: Send to GenAI service and monitor task completion
                    return genAiClient.generateSummaryAsync(username, week, defaultRepository, metadata);
                })
                .subscribe(
                    summaryMarkdown -> {
                        // Step 5: Save the summary to database
                        try {
                            Summary summary = new Summary();
                            summary.setUsername(username);
                            summary.setWeek(week);
                            summary.setSummary(summaryMarkdown);
                            summary.setCreatedAt(LocalDateTime.now());

                            Summary savedSummary = summaryRepository.save(summary);
                            log.info("Successfully generated and saved summary with ID {} for user: {}, week: {}",
                                    savedSummary.getId(), username, week);
                        } catch (Exception e) {
                            log.error("Failed to save summary for user: {}, week: {}", username, week, e);
                        }
                    },
                    error -> {
                        log.error("Failed to generate summary for user: {}, week: {}", username, week, error);
                    },
                    () -> {
                        log.debug("Summary generation completed for user: {}, week: {}", username, week);
                    }
                );
    }

    private ContributionType mapToContributionType(String type) {
        switch (type.toLowerCase()) {
            case "commit":
                return ContributionType.COMMIT;
            case "pull_request":
                return ContributionType.PULL_REQUEST;
            case "issue":
                return ContributionType.ISSUE;
            case "release":
                return ContributionType.RELEASE;
            default:
                log.warn("Unknown contribution type: {}, defaulting to COMMIT", type);
                return ContributionType.COMMIT;
        }
    }
}
