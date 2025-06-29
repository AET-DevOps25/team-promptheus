package de.promptheus.summary.client;

import de.promptheus.summary.contribution.api.ContributionControllerApi;
import de.promptheus.summary.contribution.model.ContributionDto;
import de.promptheus.summary.contribution.model.Page;
import de.promptheus.summary.contribution.model.Pageable;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import reactor.core.publisher.Mono;

import java.time.Instant;
import java.time.LocalDate;
import java.time.ZoneOffset;
import java.time.temporal.WeekFields;
import java.time.temporal.IsoFields;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.stream.Collectors;

@Component
@Slf4j
public class ContributionClient {

    private final ContributionControllerApi contributionApi;
    private final ObjectMapper objectMapper;

    public ContributionClient(@Value("${app.contributionServiceUrl}") String contributionServiceUrl) {
        this.contributionApi = new ContributionControllerApi();
        this.contributionApi.getApiClient().setBasePath(contributionServiceUrl);
        this.objectMapper = new ObjectMapper();
        this.objectMapper.registerModule(new JavaTimeModule());
        log.info("ContributionClient configured with URL: {}", contributionServiceUrl);
    }

    public Mono<List<ContributionDto>> getAllContributions() {
        log.warn("Fetching ALL contributions without filtering - this should be used sparingly!");

        Pageable pageable = new Pageable();
        pageable.setPage(0);
        pageable.setSize(1000);

        return contributionApi.getContributions(pageable, null, null, null)
                .cast(Page.class)
                .map(page -> {
                    List<Object> content = page.getContent();
                    if (content == null) {
                        return new ArrayList<ContributionDto>();
                    }

                    return content.stream()
                            .map(obj -> {
                                if (obj instanceof ContributionDto) {
                                    return (ContributionDto) obj;
                                } else {
                                    // Convert LinkedHashMap to ContributionDto using ObjectMapper
                                    return objectMapper.convertValue(obj, ContributionDto.class);
                                }
                            })
                            .collect(Collectors.toList());
                })
                .doOnSuccess(contributions -> log.info("Found {} total contributions", contributions.size()))
                .doOnError(error -> log.error("Failed to fetch all contributions", error));
    }

    public Mono<List<ContributionDto>> getContributionsForUserAndWeek(String username, String week) {
        log.info("Fetching contributions for user: {}, week: {}", username, week);

        // Parse week to get start and end dates
        WeekDates weekDates = parseWeek(week);

        // Use server-side filtering with the fixed contribution service
        Pageable pageable = new Pageable();
        pageable.setPage(0);
        pageable.setSize(1000);

        String startDateStr = weekDates.getStartDate().toString();
        String endDateStr = weekDates.getEndDate().toString();

        return contributionApi.getContributions(pageable, username, startDateStr, endDateStr)
                .cast(Page.class)
                .map(page -> {
                    List<Object> content = page.getContent();
                    if (content == null) {
                        return new ArrayList<ContributionDto>();
                    }

                    List<ContributionDto> contributions = content.stream()
                            .map(obj -> {
                                if (obj instanceof ContributionDto) {
                                    return (ContributionDto) obj;
                                } else {
                                    // Convert LinkedHashMap to ContributionDto using ObjectMapper
                                    return objectMapper.convertValue(obj, ContributionDto.class);
                                }
                            })
                            .collect(Collectors.toList());

                    log.info("Found {} contributions for user: {}, week: {} using server-side filtering",
                            contributions.size(), username, week);
                    return contributions;
                })
                .doOnError(error -> log.error("Failed to fetch contributions for user: {}, week: {}",
                        username, week, error));
    }



    private WeekDates parseWeek(String week) {
        // Parse format like "2024-W26"
        String[] parts = week.split("-W");
        int year = Integer.parseInt(parts[0]);
        int weekNumber = Integer.parseInt(parts[1]);

        log.debug("Parsing week: {} -> year={}, weekNumber={}", week, year, weekNumber);

        // Use ISO week standards (Monday = 1, weeks start on Monday)
        LocalDate startOfWeek = LocalDate.of(year, 1, 1)
                .with(IsoFields.WEEK_OF_WEEK_BASED_YEAR, weekNumber)
                .with(WeekFields.ISO.dayOfWeek(), 1); // Monday = 1

        LocalDate endOfWeek = startOfWeek.plusDays(6);

        Instant startInstant = startOfWeek.atStartOfDay().toInstant(ZoneOffset.UTC);
        Instant endInstant = endOfWeek.atTime(23, 59, 59).toInstant(ZoneOffset.UTC);

        log.info("Week {} parsed to: {} to {} (LocalDate: {} to {})",
                week, startInstant, endInstant, startOfWeek, endOfWeek);

        return new WeekDates(startInstant, endInstant);
    }

    public static class WeekDates {
        private final Instant startDate;
        private final Instant endDate;

        public WeekDates(Instant startDate, Instant endDate) {
            this.startDate = startDate;
            this.endDate = endDate;
        }

        public Instant getStartDate() {
            return startDate;
        }

        public Instant getEndDate() {
            return endDate;
        }
    }
}
