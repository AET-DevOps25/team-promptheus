package de.promptheus.summary;

import de.promptheus.summary.client.GenAiClient;
import de.promptheus.summary.genai.model.SummaryResponse;
import de.promptheus.summary.persistence.Summary;
import de.promptheus.summary.persistence.SummaryRepository;
import de.promptheus.summary.service.SummaryService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;
import reactor.core.publisher.Mono;

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
    private SummaryRepository summaryRepository;

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
        when(summaryRepository.findDistinctUsernames()).thenReturn(Collections.singletonList("testuser"));
        when(genAiClient.generateSummary(any(), any(), any())).thenReturn(Mono.just(new SummaryResponse()));

        summaryService.generateWeeklySummaries();

        verify(summaryRepository).save(any(Summary.class));
    }
}
