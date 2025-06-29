package de.promptheus.summary.client;

import de.promptheus.summary.genai.model.*;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

import java.time.Duration;
import java.util.List;

@Component
@Slf4j
public class GenAiClient {

    private final WebClient webClient;
    private final String githubPat;

    public GenAiClient(WebClient.Builder webClientBuilder,
                      @Value("${app.genaiServiceUrl}") String genaiServiceUrl,
                      @Value("${app.githubPat:}") String githubPat) {
        this.webClient = webClientBuilder.baseUrl(genaiServiceUrl).build();
        this.githubPat = githubPat;
        log.info("GenAiClient configured with URL: {}", genaiServiceUrl);
    }

    public Mono<String> generateSummaryAsync(String username, String week, String repository, List<ContributionMetadata> contributions) {
        log.info("Starting async summary generation for user: {}, week: {}, repository: {}, contributions: {}",
                username, week, repository, contributions.size());

        // Step 1: Create the ingest request
        ContributionsIngestRequest request = new ContributionsIngestRequest();
        request.setUser(username);
        request.setWeek(week);
        request.setRepository(repository);
        request.setContributions(contributions);
        request.setGithubPat(githubPat);

        // Step 2: POST to /contributions to start the async task
        return webClient.post()
                .uri("/contributions")
                .bodyValue(request)
                .retrieve()
                .bodyToMono(IngestTaskResponse.class)
                .flatMap(taskResponse -> {
                    log.info("Created task: {} for user: {}, week: {}", taskResponse.getTaskId(), username, week);
                    // Step 3: Poll the task status until completion
                    return pollTaskUntilComplete(taskResponse.getTaskId());
                })
                .doOnSuccess(summary -> log.info("Successfully generated summary for user: {}, week: {}", username, week))
                .doOnError(error -> log.error("Failed to generate summary for user: {}, week: {}", username, week, error));
    }

    private Mono<String> pollTaskUntilComplete(String taskId) {
        return webClient.get()
                .uri("/ingest/{taskId}", taskId)
                .retrieve()
                .bodyToMono(IngestTaskStatus.class)
                .flatMap(status -> {
                    log.debug("Task {} status: {}", taskId, status.getStatus());

                    if (status.getStatus() == TaskStatus.DONE) {
                        if (status.getSummary() != null && status.getSummary().getOverview() != null) {
                            return Mono.just(status.getSummary().getOverview());
                        } else {
                            return Mono.error(new RuntimeException("Task completed but no summary available"));
                        }
                    } else if (status.getStatus() == TaskStatus.FAILED) {
                        return Mono.error(new RuntimeException("Task failed: " + status.getErrorMessage()));
                    } else if (status.getStatus() == TaskStatus.QUEUED ||
                               status.getStatus() == TaskStatus.INGESTING ||
                               status.getStatus() == TaskStatus.SUMMARIZING) {
                        // Still processing, wait and retry
                        return Mono.delay(Duration.ofSeconds(2))
                                .then(pollTaskUntilComplete(taskId));
                    } else {
                        return Mono.error(new RuntimeException("Unknown task status: " + status.getStatus()));
                    }
                });
    }
}
