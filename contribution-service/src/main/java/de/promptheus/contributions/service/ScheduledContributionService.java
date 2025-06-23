package de.promptheus.contributions.service;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
@Slf4j
public class ScheduledContributionService {

    private final ContributionFetchService contributionFetchService;

    /**
     * Automatically trigger contribution fetch every 2 minutes
     */
    @Scheduled(fixedRate = 120000) // 2 minutes in milliseconds
    public void scheduledContributionFetch() {
        log.info("Starting scheduled contribution fetch");
        
        try {
            var response = contributionFetchService.triggerFetchForAllRepositories();
            log.info("Scheduled fetch completed - Status: {}, Repositories: {}, Contributions: {}", 
                    response.getStatus(), 
                    response.getRepositoriesProcessed(), 
                    response.getContributionsFetched());
        } catch (Exception e) {
            log.error("Scheduled contribution fetch failed", e);
        }
    }
} 