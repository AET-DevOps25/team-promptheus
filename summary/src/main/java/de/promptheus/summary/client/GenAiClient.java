package de.promptheus.summary.client;

import de.promptheus.summary.genai.api.DefaultApi;
import de.promptheus.summary.genai.model.ContributionsIngestRequest;
import de.promptheus.summary.genai.model.IngestTaskStatus;
import de.promptheus.summary.genai.model.SummaryResponse;
import de.promptheus.summary.genai.model.TaskStatus;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import reactor.core.publisher.Mono;

import java.time.Duration;

@Component
@RequiredArgsConstructor
@Slf4j
public class GenAiClient {

    private final DefaultApi genAiApi;

    public Mono<SummaryResponse> generateSummaryAsync(ContributionsIngestRequest request) {
        log.info("Starting async summary generation for user: {}, week: {}, repository: {}",
                request.getUser(), request.getWeek(), request.getRepository());

        return genAiApi.startContributionsIngestionTaskContributionsPost(request)
                .flatMap(taskResponse -> {
                    log.info("Created task: {} for user: {}, week: {}", taskResponse.getTaskId(), request.getUser(), request.getWeek());
                    return pollTaskUntilComplete(taskResponse.getTaskId());
                })
                .doOnSuccess(summary -> log.info("Successfully generated summary for user: {}, week: {}", request.getUser(), request.getWeek()))
                .doOnError(error -> log.error("Failed to generate summary for user: {}, week: {}", request.getUser(), request.getWeek(), error));
    }

    private Mono<SummaryResponse> pollTaskUntilComplete(String taskId) {
        return genAiApi.getIngestionTaskStatusIngestTaskIdGet(taskId)
                .flatMap(status -> {
                    log.debug("Task {} status: {}", taskId, status.getStatus());

                    if (status.getStatus() == TaskStatus.DONE) {
                        if (status.getSummary() != null) {
                            return Mono.just(status.getSummary());
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
