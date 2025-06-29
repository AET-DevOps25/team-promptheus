package de.promptheus.summary;

import de.promptheus.summary.client.GenAiClient;
import de.promptheus.summary.genai.model.SummaryResponse;
import de.promptheus.summary.persistence.SummaryRepository;
import de.promptheus.summary.service.SummaryService;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import reactor.core.publisher.Mono;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
public class SummaryServiceInteractionTest {

    @Mock
    private GenAiClient genAiClient;

    @Mock
    private SummaryRepository summaryRepository;

    @InjectMocks
    private SummaryService summaryService;

    @Test
    void testGenerateSummaryForUser() {
        // Given
        String username = "testuser";
        String week = "2025-W26";
        SummaryResponse summaryResponse = new SummaryResponse();
        summaryResponse.setOverview("Test summary");

        when(genAiClient.generateSummary(eq(username), eq(week), any())).thenReturn(Mono.just(summaryResponse));

        // When
        summaryService.generateSummaryForUser(username, week);

        // Then
        verify(genAiClient).generateSummary(eq(username), eq(week), any());
        verify(summaryRepository).save(any());
    }
}
