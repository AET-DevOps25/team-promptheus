package de.promptheus.summary;

import de.promptheus.summary.client.ContributionClient;
import de.promptheus.summary.client.GenAiClient;
import de.promptheus.summary.contribution.model.ContributionDto;
import de.promptheus.summary.persistence.SummaryRepository;
import de.promptheus.summary.persistence.GitRepository;
import de.promptheus.summary.persistence.GitRepositoryRepository;
import de.promptheus.summary.service.SummaryService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;
import org.springframework.test.util.ReflectionTestUtils;
import org.mockito.junit.jupiter.MockitoExtension;
import reactor.core.publisher.Mono;

import java.time.Instant;
import java.util.Collections;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.timeout;

import de.promptheus.summary.genai.model.ContributionsIngestRequest;
import de.promptheus.summary.genai.model.SummaryResponse;
import de.promptheus.summary.persistence.Summary;

@ExtendWith(MockitoExtension.class)
class SummaryServiceInteractionTest {

    @Mock
    private GenAiClient genAiClient;

    @Mock
    private ContributionClient contributionClient;

    @Mock
    private SummaryRepository summaryRepository;

    @Mock
    private GitRepositoryRepository gitRepositoryRepository;

    private SummaryService summaryService;

    @BeforeEach
    void setUp() {
        MockitoAnnotations.openMocks(this);
        summaryService = new SummaryService(genAiClient, contributionClient, summaryRepository, gitRepositoryRepository);
        ReflectionTestUtils.setField(summaryService, "githubPat", "test-pat");
    }

    @Test
    void generateSummary_savesSummary_whenContributionsExist() {
        // Given
        String username = "testuser";
        String week = "2025-W26";
        SummaryResponse summaryResponse = new SummaryResponse();
        summaryResponse.setOverview("Test overview");

        // Create a mock GitRepository
        GitRepository repository = new GitRepository();
        repository.setId(1L);
        repository.setRepositoryLink("https://github.com/test/repo");
        repository.setCreatedAt(Instant.now());

        // Create a properly configured ContributionDto
        ContributionDto contributionDto = new ContributionDto();
        contributionDto.setIsSelected(true);
        contributionDto.setType("commit");
        contributionDto.setId("test-id");

        // Mocks
        when(summaryRepository.findByUsernameAndWeek(eq(username), eq(week))).thenReturn(Collections.emptyList());
        when(contributionClient.getContributionsForUserAndWeek(eq(username), eq(week)))
                .thenReturn(Mono.just(Collections.singletonList(contributionDto)));
        when(genAiClient.generateSummaryAsync(any(ContributionsIngestRequest.class))).thenReturn(Mono.just(summaryResponse));

        // Execution
        summaryService.generateSummary(username, week, repository, "test-token");

        // Verification with timeout to wait for async operations
        verify(genAiClient, timeout(2000)).generateSummaryAsync(any(ContributionsIngestRequest.class));
        verify(summaryRepository, timeout(2000)).save(any(Summary.class));
    }

    @Test
    void generateSummary_skipsSaving_whenNoContributions() {
        // Given
        String username = "testuser";
        String week = "2025-W26";
        GitRepository repository = new GitRepository();
        repository.setId(1L);
        repository.setRepositoryLink("https://github.com/test/repo");
        repository.setCreatedAt(Instant.now());

        // Mocks
        when(summaryRepository.findByUsernameAndWeek(eq(username), eq(week))).thenReturn(Collections.emptyList());
        when(contributionClient.getContributionsForUserAndWeek(eq(username), eq(week))).thenReturn(Mono.just(Collections.emptyList()));

        // Execution
        summaryService.generateSummary(username, week, repository, "test-token");

        // Verification
        verify(genAiClient, never()).generateSummaryAsync(any(ContributionsIngestRequest.class));
        verify(summaryRepository, never()).save(any(Summary.class));
    }
}
