package de.promptheus.contributions.service;

import de.promptheus.contributions.dto.TriggerResponse;
import de.promptheus.contributions.entity.GitRepository;
import de.promptheus.contributions.entity.Contribution;
import de.promptheus.contributions.repository.GitRepositoryRepository;
import de.promptheus.contributions.repository.ContributionRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;
import java.util.List;
import java.util.ArrayList;

@Service
@RequiredArgsConstructor
@Slf4j
public class ContributionFetchService {

    private final GitRepositoryRepository gitRepositoryRepository;
    private final ContributionRepository contributionRepository;
    private final GitHubApiService gitHubApiService;
    private final MeilisearchService meilisearchService;

    @Transactional
    public TriggerResponse triggerFetchForAllRepositories() {
        Instant startTime = Instant.now();
        List<String> processedRepositories = new ArrayList<>();
        List<String> errors = new ArrayList<>();
        int totalContributionsFetched = 0;
        int totalContributionsUpserted = 0;

        try {
            // Get all repositories that need fetching
            List<GitRepository> repositories = gitRepositoryRepository.findRepositoriesForFetch();
            log.info("Found {} repositories to process", repositories.size());

            for (GitRepository repository : repositories) {
                try {
                    log.info("Processing repository: {}", repository.getRepositoryLink());

                    // Fetch contributions since last fetch time
                    List<Contribution> contributions = gitHubApiService.fetchContributionsSince(
                            repository, repository.getLastFetchedAt());

                    // Upsert contributions
                    int upserted = upsertContributions(contributions, repository.getId());

                    // Index contributions to Meilisearch
                    meilisearchService.indexContributions(contributions, repository.getRepositoryLink());

                    // Update last fetched time only if contributions were actually found
                    if (contributions.size() > 0) {
                        repository.setLastFetchedAt(Instant.now());
                        gitRepositoryRepository.save(repository);
                        log.info("Updated last_fetched_at for repository {} since {} contributions were found",
                                repository.getRepositoryLink(), contributions.size());
                    } else {
                        log.info("NOT updating last_fetched_at for repository {} since 0 contributions were found",
                                repository.getRepositoryLink());
                    }

                    processedRepositories.add(repository.getRepositoryLink());
                    totalContributionsFetched += contributions.size();
                    totalContributionsUpserted += upserted;

                    log.info("Processed repository {}: {} contributions fetched, {} upserted",
                            repository.getRepositoryLink(), contributions.size(), upserted);

                } catch (Exception e) {
                    String error = String.format("Failed to process repository %s: %s",
                            repository.getRepositoryLink(), e.getMessage());
                    log.error(error, e);
                    errors.add(error);
                }
            }

            long processingTime = Instant.now().toEpochMilli() - startTime.toEpochMilli();

            return TriggerResponse.builder()
                    .status("SUCCESS")
                    .message("Contribution fetch completed")
                    .triggeredAt(startTime)
                    .repositoriesProcessed(processedRepositories.size())
                    .contributionsFetched(totalContributionsFetched)
                    .contributionsUpserted(totalContributionsUpserted)
                    .processedRepositories(processedRepositories)
                    .errors(errors)
                    .processingTimeMs(processingTime)
                    .build();

        } catch (Exception e) {
            log.error("Failed to trigger contribution fetch for all repositories", e);
            long processingTime = Instant.now().toEpochMilli() - startTime.toEpochMilli();

            return TriggerResponse.builder()
                    .status("ERROR")
                    .message("Failed to complete contribution fetch: " + e.getMessage())
                    .triggeredAt(startTime)
                    .repositoriesProcessed(processedRepositories.size())
                    .contributionsFetched(totalContributionsFetched)
                    .contributionsUpserted(totalContributionsUpserted)
                    .processedRepositories(processedRepositories)
                    .errors(errors)
                    .processingTimeMs(processingTime)
                    .build();
        }
    }

    @Transactional
    public TriggerResponse triggerFetchForRepository(String repositoryUrl) {
        Instant startTime = Instant.now();
        List<String> errors = new ArrayList<>();

        try {
            GitRepository repository = gitRepositoryRepository.findByRepositoryLink(repositoryUrl);
            if (repository == null) {
                return TriggerResponse.builder()
                        .status("ERROR")
                        .message("Repository not found: " + repositoryUrl)
                        .triggeredAt(startTime)
                        .repositoriesProcessed(0)
                        .contributionsFetched(0)
                        .contributionsUpserted(0)
                        .processedRepositories(List.of())
                        .errors(List.of("Repository not found: " + repositoryUrl))
                        .processingTimeMs(Instant.now().toEpochMilli() - startTime.toEpochMilli())
                        .build();
            }

            log.info("Processing specific repository: {}", repositoryUrl);

            // Fetch contributions since last fetch time
            List<Contribution> contributions = gitHubApiService.fetchContributionsSince(
                    repository, repository.getLastFetchedAt());

            // Upsert contributions
            int upserted = upsertContributions(contributions, repository.getId());

            // Index contributions to Meilisearch
            meilisearchService.indexContributions(contributions, repositoryUrl);

            // Update last fetched time only if contributions were actually found
            if (contributions.size() > 0) {
                repository.setLastFetchedAt(Instant.now());
                gitRepositoryRepository.save(repository);
                log.info("Updated last_fetched_at for repository {} since {} contributions were found",
                        repositoryUrl, contributions.size());
            } else {
                log.info("NOT updating last_fetched_at for repository {} since 0 contributions were found",
                        repositoryUrl);
            }

            long processingTime = Instant.now().toEpochMilli() - startTime.toEpochMilli();

            log.info("Processed repository {}: {} contributions fetched, {} upserted",
                    repositoryUrl, contributions.size(), upserted);

            return TriggerResponse.builder()
                    .status("SUCCESS")
                    .message("Contribution fetch completed for repository")
                    .triggeredAt(startTime)
                    .repositoriesProcessed(1)
                    .contributionsFetched(contributions.size())
                    .contributionsUpserted(upserted)
                    .processedRepositories(List.of(repositoryUrl))
                    .errors(errors)
                    .processingTimeMs(processingTime)
                    .build();

        } catch (Exception e) {
            log.error("Failed to trigger contribution fetch for repository: {}", repositoryUrl, e);
            long processingTime = Instant.now().toEpochMilli() - startTime.toEpochMilli();

            return TriggerResponse.builder()
                    .status("ERROR")
                    .message("Failed to fetch contributions for repository: " + e.getMessage())
                    .triggeredAt(startTime)
                    .repositoriesProcessed(0)
                    .contributionsFetched(0)
                    .contributionsUpserted(0)
                    .processedRepositories(List.of())
                    .errors(List.of(e.getMessage()))
                    .processingTimeMs(processingTime)
                    .build();
        }
    }

    private int upsertContributions(List<Contribution> contributions, Long repositoryId) {
        log.info("Starting upsert of {} contributions for repository ID {}", contributions.size(), repositoryId);
        int upserted = 0;

        for (Contribution contribution : contributions) {
            try {
                log.debug("Upserting contribution: type={}, id={}, username={}, summary={}",
                         contribution.getType(), contribution.getId(), contribution.getUsername(),
                         contribution.getSummary());

                contribution.setGitRepositoryId(repositoryId);
                contribution.setIsSelected(true);

                Contribution saved = contributionRepository.save(contribution);
                upserted++;

                log.debug("Successfully upserted contribution: type={}, id={}, database_id={}",
                         saved.getType(), saved.getId(), saved.getGitRepositoryId());

            } catch (Exception e) {
                log.error("Failed to upsert contribution type={}, id={}, username={}: {}",
                         contribution.getType(), contribution.getId(), contribution.getUsername(), e.getMessage(), e);
            }
        }

        log.info("Completed upsert: {}/{} contributions successfully saved for repository ID {}",
                upserted, contributions.size(), repositoryId);
        return upserted;
    }
}
