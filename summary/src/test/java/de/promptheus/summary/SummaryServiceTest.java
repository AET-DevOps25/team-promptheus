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

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class SummaryServiceTest {

    @Mock
    private GenAiClient genAiClient;

    @Mock
    private ContributionClient contributionClient;

    @Mock
    private SummaryRepository summaryRepository;

    @Mock
    private GitRepositoryRepository gitRepositoryRepository;

    @InjectMocks
    private SummaryService summaryService;

    @BeforeEach
    void setUp() {
        MockitoAnnotations.openMocks(this);
    }

    @Test
    void testGetSummaries() {
        Summary summary = new Summary();
        summary.setId(1L);
        summary.setUsername("testuser");
        summary.setWeek("2024-W01");
        summary.setSummary("Test Summary");
        when(summaryRepository.findAll()).thenReturn(Collections.singletonList(summary));

        List<Summary> summaries = summaryService.getSummaries(java.util.Optional.empty());

        assertEquals(1, summaries.size());
        assertEquals("Test Summary", summaries.get(0).getSummary());
    }

    @Test
    void testGenerateWeeklySummaries() {
        // Create a mock GitRepository
        GitRepository repository = new GitRepository();
        repository.setId(1L);
        repository.setRepositoryLink("https://github.com/test/repo");
        repository.setCreatedAt(Instant.now());

        // Setup mocks for new repository-based logic
        when(gitRepositoryRepository.findAll()).thenReturn(Collections.singletonList(repository));
        when(gitRepositoryRepository.findTokenByRepositoryId(1L)).thenReturn("test-token");
        when(gitRepositoryRepository.findDistinctUsersByRepositoryId(1L)).thenReturn(Collections.singletonList("testuser"));
        when(summaryRepository.findByUsernameAndWeek(any(), any())).thenReturn(Collections.emptyList());

        // Mock contribution with isSelected = true
        ContributionDto contribution = new ContributionDto();
        contribution.setId("1");
        contribution.setIsSelected(true);
        contribution.setType("commit");
        when(contributionClient.getContributionsForUserAndWeek(any(), any()))
                .thenReturn(Mono.just(Collections.singletonList(contribution)));

        when(genAiClient.generateSummaryAsync(any(), any(), any(), any())).thenReturn(Mono.just("Test summary"));

        summaryService.generateWeeklySummaries();

        verify(summaryRepository).save(any(Summary.class));
    }
}
