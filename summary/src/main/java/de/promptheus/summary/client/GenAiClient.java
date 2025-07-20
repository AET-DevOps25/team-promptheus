package de.promptheus.summary.client;

import de.promptheus.summary.genai.api.DefaultApi;
import de.promptheus.summary.genai.model.ContributionsIngestRequest;
import de.promptheus.summary.genai.model.SummaryResponse;
import de.promptheus.summary.genai.model.TaskStatus;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClientException;
import org.springframework.web.reactive.function.client.WebClientRequestException;
import org.springframework.web.reactive.function.client.WebClientResponseException;
import reactor.core.publisher.Mono;
import reactor.util.retry.Retry;

import java.time.Duration;
import java.util.concurrent.ThreadLocalRandom;

@Component
@RequiredArgsConstructor
@Slf4j
public class GenAiClient {

    private final DefaultApi genAiApi;

    @Value("${app.retry.maxAttempts:5}")
    private int maxRetryAttempts;

    @Value("${app.retry.baseDelay:2000}")
    private long baseDelayMillis;

    @Value("${app.retry.maxDelay:120000}")
    private long maxDelayMillis;

    @Value("${app.polling.intervalNormal:2000}")
    private long normalPollingIntervalMillis;

    @Value("${app.polling.intervalBackfill:5000}")
    private long backfillPollingIntervalMillis;

    public Mono<SummaryResponse> generateSummaryAsync(ContributionsIngestRequest request) {
        return generateSummaryAsync(request, false);
    }

    public Mono<SummaryResponse> generateSummaryAsync(ContributionsIngestRequest request, boolean isBackfill) {
        log.info("Starting async summary generation for user: {}, week: {}, repository: {} (backfill: {})",
                request.getUser(), request.getWeek(), request.getRepository(), isBackfill);

        return genAiApi.startContributionsIngestionTaskContributionsPost(request)
                .retryWhen(createRetrySpec("task creation"))
                .flatMap(taskResponse -> {
                    log.info("Created task: {} for user: {}, week: {}", taskResponse.getTaskId(), request.getUser(), request.getWeek());
                    return pollTaskUntilComplete(taskResponse.getTaskId(), isBackfill);
                })
                .doOnSuccess(summary -> log.info("Successfully generated summary for user: {}, week: {}", request.getUser(), request.getWeek()))
                .doOnError(error -> log.error("Failed to generate summary for user: {}, week: {} - Error: {}",
                        request.getUser(), request.getWeek(), error.getMessage()));
    }

    private Mono<SummaryResponse> pollTaskUntilComplete(String taskId, boolean isBackfill) {
        Duration pollingInterval = Duration.ofMillis(isBackfill ? backfillPollingIntervalMillis : normalPollingIntervalMillis);

        return genAiApi.getIngestionTaskStatusIngestTaskIdGet(taskId)
                .retryWhen(createRetrySpec("status polling"))
                .flatMap(status -> {
                    log.debug("Task {} status: {}", taskId, status.getStatus());

                    if (status.getStatus() == TaskStatus.DONE) {
                        if (status.getSummary() != null) {
                            return Mono.just(status.getSummary());
                        } else {
                            return Mono.error(new RuntimeException("Task completed but no summary available"));
                        }
                    } else if (status.getStatus() == TaskStatus.FAILED) {
                        String errorMessage = status.getErrorMessage() != null ? status.getErrorMessage() : "Unknown error";
                        return Mono.error(new RuntimeException("Task failed: " + errorMessage));
                    } else if (status.getStatus() == TaskStatus.QUEUED ||
                               status.getStatus() == TaskStatus.INGESTING ||
                               status.getStatus() == TaskStatus.SUMMARIZING) {
                        // Still processing, wait and retry with jitter to avoid thundering herd
                        Duration delayWithJitter = addJitter(pollingInterval);
                        return Mono.delay(delayWithJitter)
                                .then(pollTaskUntilComplete(taskId, isBackfill));
                    } else {
                        return Mono.error(new RuntimeException("Unknown task status: " + status.getStatus()));
                    }
                })
                .onErrorResume(this::handlePollingError);
    }

    private Retry createRetrySpec(String operation) {
        return Retry.backoff(maxRetryAttempts, Duration.ofMillis(baseDelayMillis))
                .maxBackoff(Duration.ofMillis(maxDelayMillis))
                .jitter(0.5) // Add 50% jitter to prevent thundering herd
                .filter(this::isRetryableException)
                .doBeforeRetry(retrySignal -> {
                    Throwable failure = retrySignal.failure();
                    log.warn("Retrying {} operation (attempt {}/{}) due to: {} - {}",
                            operation,
                            retrySignal.totalRetries() + 1,
                            maxRetryAttempts,
                            failure.getClass().getSimpleName(),
                            failure.getMessage());
                })
                .onRetryExhaustedThrow((retryBackoffSpec, retrySignal) -> {
                    log.error("Retry exhausted for {} operation after {} attempts. Last error: {}",
                            operation, retrySignal.totalRetries(), retrySignal.failure().getMessage());
                    return new RuntimeException("Failed " + operation + " after " + retrySignal.totalRetries() + " retries",
                            retrySignal.failure());
                });
    }

    private boolean isRetryableException(Throwable throwable) {
        // Retry on connection errors, timeouts, and 5xx server errors
        if (throwable instanceof WebClientRequestException) {
            // Network connection issues, timeouts, connection resets
            return true;
        }
        if (throwable instanceof WebClientResponseException responseException) {
            int status = responseException.getRawStatusCode();
            // Retry on 5xx server errors and 429 (too many requests)
            return status >= 500 || status == 429;
        }
        if (throwable instanceof WebClientException) {
            // Other WebClient exceptions that might be retryable
            String message = throwable.getMessage();
            return message != null && (
                    message.contains("Connection reset") ||
                    message.contains("Connection refused") ||
                    message.contains("timeout") ||
                    message.contains("Connection pool shut down")
            );
        }
        return false;
    }

    private Mono<SummaryResponse> handlePollingError(Throwable error) {
        if (isRetryableException(error)) {
            log.warn("Recoverable error during polling, will retry: {}", error.getMessage());
            // For polling errors, we don't want to fail immediately but rather continue trying
            return Mono.delay(Duration.ofSeconds(10))
                    .then(Mono.error(error)); // This will trigger the retry mechanism
        } else {
            log.error("Non-recoverable error during polling: {}", error.getMessage());
            return Mono.error(error);
        }
    }

    private Duration addJitter(Duration baseDelay) {
        // Add random jitter between 0% and 20% to prevent thundering herd
        long baseMillis = baseDelay.toMillis();
        long jitterMillis = ThreadLocalRandom.current().nextLong(0, baseMillis / 5); // 0-20% jitter
        return Duration.ofMillis(baseMillis + jitterMillis);
    }
}
