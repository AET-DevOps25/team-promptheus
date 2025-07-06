package de.promptheus.summary;

import de.promptheus.summary.client.ContributionClient;
import de.promptheus.summary.client.GenAiClient;
import de.promptheus.summary.contribution.model.ContributionDto;
import de.promptheus.summary.persistence.Summary;
import de.promptheus.summary.persistence.SummaryRepository;
import de.promptheus.summary.persistence.GitRepository;
import de.promptheus.summary.persistence.GitRepositoryRepository;
import de.promptheus.summary.service.SummaryService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;
import reactor.core.publisher.Mono;

import java.time.Instant;
import java.util.Collections;
import java.util.List;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import de.promptheus.summary.genai.model.ContributionsIngestRequest;
import de.promptheus.summary.genai.model.SummaryResponse;
import org.springframework.test.util.ReflectionTestUtils;

class SummaryServiceTest {

    private GenAiClient genAiClient;

    private ContributionClient contributionClient;

    private SummaryRepository summaryRepository;

    private GitRepositoryRepository gitRepositoryRepository;

    private SummaryService summaryService;

    @BeforeEach
    void setUp() {
        summaryRepository = mock(SummaryRepository.class);
        gitRepositoryRepository = mock(GitRepositoryRepository.class);
        genAiClient = mock(GenAiClient.class);
        contributionClient = mock(ContributionClient.class);
        summaryService = new SummaryService(genAiClient, contributionClient, summaryRepository, gitRepositoryRepository);
        ReflectionTestUtils.setField(summaryService, "githubPat", "test-pat");
    }

    @Test
    void testGetSummariesWithWeek() {
        Summary summary = new Summary();
        summary.setId(1L);
        summary.setGitRepositoryId(1L);
        summary.setUsername("testuser");
        summary.setWeek("2024-W28");
        summary.setOverview("Test Summary");
        when(summaryRepository.findByWeek("2024-W28")).thenReturn(Collections.singletonList(summary));

        List<Summary> summaries = summaryService.getSummaries(Optional.of("2024-W28"));

        assertEquals(1, summaries.size());
        assertEquals("Test Summary", summaries.get(0).getOverview());
    }

    @Test
    void testGetSummariesWithoutWeek() {
        Summary summary = new Summary();
        summary.setId(1L);
        summary.setGitRepositoryId(1L);
        summary.setUsername("testuser");
        summary.setWeek("2024-W28");
        summary.setOverview("Test Summary");
        when(summaryRepository.findAll()).thenReturn(Collections.singletonList(summary));

        List<Summary> summaries = summaryService.getSummaries(java.util.Optional.empty());

        assertEquals(1, summaries.size());
        assertEquals("Test Summary", summaries.get(0).getOverview());
    }

    @Test
    void testGenerateSummary() {
        // Given
        String username = "testuser";
        String week = "2024-W28";
        GitRepository repository = new GitRepository();
        repository.setId(1L);
        repository.setRepositoryLink("https://github.com/test/repo");

        ContributionDto contribution = new ContributionDto();
        contribution.setIsSelected(true);
        contribution.setType("commit");

        when(contributionClient.getContributionsForUserAndWeek(any(), any())).thenReturn(Mono.just(Collections.singletonList(contribution)));
        when(genAiClient.generateSummaryAsync(any(ContributionsIngestRequest.class))).thenReturn(Mono.just(new SummaryResponse()));
        when(summaryRepository.findByUsernameAndWeek(username, week)).thenReturn(Collections.emptyList());

        // When
        summaryService.generateSummary(username, week, repository, "test-token");

        // Then
        try {
            Thread.sleep(1000); // Wait for async processing
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
        verify(summaryRepository, times(1)).save(any(Summary.class));
    }
}
