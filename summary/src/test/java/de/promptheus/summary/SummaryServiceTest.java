package de.promptheus.summary;

import de.promptheus.summary.client.ContributionClient;
import de.promptheus.summary.client.GenAiClient;
import de.promptheus.summary.contribution.model.ContributionDto;
import de.promptheus.summary.dto.SummaryDto;
import de.promptheus.summary.genai.model.SummaryResponse;
import de.promptheus.summary.persistence.*;
import de.promptheus.summary.service.SummaryService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.test.util.ReflectionTestUtils;
import reactor.core.publisher.Mono;

import java.time.LocalDateTime;
import java.util.Collections;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyBoolean;
import static org.mockito.ArgumentMatchers.anyList;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.*;

import de.promptheus.summary.genai.model.ContributionsIngestRequest;


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
    void testGetSummariesPaginatedWithWeek() {
        Summary summary = new Summary();
        summary.setId(1L);
        summary.setGitRepositoryId(1L);
        summary.setUsername("testuser");
        summary.setWeek("2024-W28");
        summary.setOverview("Test Summary");
        summary.setCreatedAt(LocalDateTime.now());

        Page<Summary> summaryPage = new PageImpl<>(Collections.singletonList(summary));
        when(summaryRepository.findSummariesWithFilters(eq("2024-W28"), any(), any(), any(Pageable.class)))
                .thenReturn(summaryPage);

        Page<Summary> summaries = summaryService.getSummariesPaginated(
                Optional.of("2024-W28"),
                Optional.empty(),
                Optional.empty(),
                PageRequest.of(0, 20));

        assertEquals(1, summaries.getContent().size());
        assertEquals("Test Summary", summaries.getContent().get(0).getOverview());
    }

    @Test
    void testGetSummariesPaginatedWithoutWeek() {
        Summary summary = new Summary();
        summary.setId(1L);
        summary.setGitRepositoryId(1L);
        summary.setUsername("testuser");
        summary.setWeek("2024-W28");
        summary.setOverview("Test Summary");
        summary.setCreatedAt(LocalDateTime.now());

        Page<Summary> summaryPage = new PageImpl<>(Collections.singletonList(summary));
        when(summaryRepository.findSummariesWithFilters(any(), any(), any(), any(Pageable.class)))
                .thenReturn(summaryPage);

        Page<Summary> summaries = summaryService.getSummariesPaginated(
                Optional.empty(),
                Optional.empty(),
                Optional.empty(),
                PageRequest.of(0, 20));

        assertEquals(1, summaries.getContent().size());
        assertEquals("Test Summary", summaries.getContent().get(0).getOverview());
    }

    @Test
    void testGenerateSummary() {
        // Given
        String username = "testuser";
        String week = "2024-W28";
        GitRepository repository = new GitRepository();
        repository.setId(1L);
        repository.setRepositoryLink("https://github.com/test/repo");

        // Create a properly configured ContributionDto
        ContributionDto contribution = new ContributionDto();
        contribution.setIsSelected(true);
        contribution.setType("commit");
        contribution.setId("test-id");

        SummaryResponse summaryResponse = new SummaryResponse();
        summaryResponse.setOverview("Test summary");

        when(contributionClient.getContributionsForUserAndWeek(any(), any())).thenReturn(Mono.just(Collections.singletonList(contribution)));
        when(genAiClient.generateSummaryAsync(any(ContributionsIngestRequest.class), anyBoolean())).thenReturn(Mono.just(summaryResponse));
        when(summaryRepository.findByUsernameAndWeek(username, week)).thenReturn(Collections.emptyList());

        // When
        summaryService.generateSummary(username, week, repository, "test-token");

        // Then - use timeout to wait for async processing
        verify(summaryRepository, timeout(2000).times(1)).save(any(Summary.class));
    }

    @Test
    void testGetSummariesPaginatedWithRepoInfo() {
        // Given
        String username = "testuser";
        String week = "2024-W28";
        GitRepository repository = new GitRepository();
        repository.setId(1L);
        repository.setRepositoryLink("https://github.com/test/repo");

        Summary summary = new Summary();
        summary.setId(1L);
        summary.setGitRepositoryId(1L);
        summary.setUsername(username);
        summary.setWeek(week);
        summary.setOverview("Test Summary");
        summary.setCreatedAt(LocalDateTime.now());

        Page<Summary> summaryPage = new PageImpl<>(Collections.singletonList(summary));

        when(summaryRepository.findSummariesWithFilters(eq(week), eq(username), any(), any(Pageable.class)))
                .thenReturn(summaryPage);
        when(gitRepositoryRepository.findAllById(anyList()))
                .thenReturn(Collections.singletonList(repository));

        // Act
        Page<SummaryDto> summaries = summaryService.getSummariesPaginatedWithRepoInfo(
                Optional.of(week),
                Optional.of(username),
                Optional.empty(),
                PageRequest.of(0, 20));

        // Assert
        assertNotNull(summaries);
        assertEquals(1, summaries.getContent().size());
        assertEquals(username, summaries.getContent().get(0).getUsername());
        assertEquals(week, summaries.getContent().get(0).getWeek());
    }
}
