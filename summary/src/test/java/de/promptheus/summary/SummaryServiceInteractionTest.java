package de.promptheus.summary;

import de.promptheus.summary.client.ContributionClient;
import de.promptheus.summary.client.GenAiClient;
import de.promptheus.summary.contribution.model.ContributionDto;
import de.promptheus.summary.persistence.SummaryRepository;
import de.promptheus.summary.service.SummaryService;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import reactor.core.publisher.Mono;

import java.util.Collections;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
public class SummaryServiceInteractionTest {

    @Mock
    private GenAiClient genAiClient;

    @Mock
    private ContributionClient contributionClient;

    @Mock
    private SummaryRepository summaryRepository;

    @InjectMocks
    private SummaryService summaryService;

    @Test
    void testGenerateSummaryForUser() {
        // Given
        String username = "testuser";
        String week = "2025-W26";
        String summaryText = "Test summary";

        // Mock that no existing summary exists
        when(summaryRepository.findByUsernameAndWeek(eq(username), eq(week))).thenReturn(Collections.emptyList());

        // Mock contribution with isSelected = true
        ContributionDto contribution = new ContributionDto();
        contribution.setId("1");
        contribution.setIsSelected(true);
        contribution.setType("commit");
        when(contributionClient.getContributionsForUserAndWeek(eq(username), eq(week)))
                .thenReturn(Mono.just(Collections.singletonList(contribution)));

        when(genAiClient.generateSummaryAsync(eq(username), eq(week), any(), any())).thenReturn(Mono.just(summaryText));

        // When
        summaryService.generateSummaryForUser(username, week);

        // Then
        verify(genAiClient).generateSummaryAsync(eq(username), eq(week), any(), any());
        verify(summaryRepository).save(any());
    }
}
