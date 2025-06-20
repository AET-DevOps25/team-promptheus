package com.autoback.autoback.api;

import com.autoback.autoback.CommunicationObjects.*;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.meilisearch.sdk.model.SearchResult;
import io.micrometer.core.instrument.Counter;
import io.micrometer.core.instrument.MeterRegistry;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.web.server.ResponseStatusException;

import java.time.Instant;
import java.util.List;
import java.util.Set;
import java.util.UUID;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@WebMvcTest(GitRepoController.class)
class GitRepoControllerTest {
    @Autowired
    private MockMvc mockMvc;

    @MockitoBean
    private GitRepoService gitRepoService;
    @MockitoBean
    private SearchService searchService;

    @MockitoBean
    private MeterRegistry meterRegistry;

    @Autowired
    private ObjectMapper objectMapper;

    @Test
    void createFromPAT_ValidRequest_ReturnsLinks() throws Exception {
        // Arrange
        PATConstruct request = new PATConstruct("https://github.com/test/repo", "ghp_testtoken123");
        LinkConstruct expectedResponse = new LinkConstruct("dev-uuid", "stakeholder-uuid");

        when(gitRepoService.createAccessLinks(any(PATConstruct.class))).thenReturn(expectedResponse);
        Counter patRegistrationCnt = mock(Counter.class);
        when(meterRegistry.counter("pat_registration_total")).thenReturn(patRegistrationCnt);

        // Act & Assert
        mockMvc.perform(post("/api/repositories/PAT")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk())
                .andExpect(content().json(objectMapper.writeValueAsString(expectedResponse)));
        verify(meterRegistry,only()).counter("pat_registration_total");
        verify(patRegistrationCnt,only()).increment();
        verify(gitRepoService, only()).createAccessLinks(any(PATConstruct.class));
    }

    @Test
    void createFromPAT_InvalidRequest_ReturnsBadRequest() throws Exception {
        // Arrange
        PATConstruct invalidRequest = new PATConstruct("", "");

        when(gitRepoService.createAccessLinks(any(PATConstruct.class))).thenThrow(new ResponseStatusException(HttpStatus.BAD_REQUEST, "invalid PAT"));
        // Act & Assert
        mockMvc.perform(post("/api/repositories/PAT")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(invalidRequest)))
                .andExpect(status().isBadRequest());
        verifyNoInteractions(meterRegistry);
    }

    @Test
    void getGitRepository_ValidUsercode_ReturnsGitRepoInfo() throws Exception {
        // Arrange
        UUID usercode = UUID.randomUUID();
        GitRepoInformationConstruct expectedResponse = GitRepoInformationConstruct.builder()
                .repoLink("https://github.com/test/repo")
                .isMaintainer(true)
                .createdAt(Instant.now())
                .questions(List.of())
                .summaries(List.of())
                .contents(List.of())
                .build();

        when(gitRepoService.getRepositoryByAccessID(usercode)).thenReturn(expectedResponse);

        // Act & Assert
        mockMvc.perform(get("/api/repositories/{usercode}", usercode))
                .andExpect(status().isOk())
                .andExpect(content().json(objectMapper.writeValueAsString(expectedResponse)));
        verify(gitRepoService,only()).getRepositoryByAccessID(usercode);
    }

    @Test
    void search_ValidRequest_ReturnsSearchResult() throws Exception {
        // Arrange
        UUID usercode = UUID.randomUUID();
        String query = "test query";
        SearchResult expectedResult = new SearchResult();
        ContentConstruct content = ContentConstruct.builder().build();

        when(gitRepoService.getRepositoryByAccessID(usercode)).thenReturn(GitRepoInformationConstruct.builder().contents(List.of(content)).build());
        when(searchService.search(query)).thenReturn(expectedResult);
        // Act & Assert
        mockMvc.perform(get("/api/repositories/{usercode}/search", usercode)
                .param("query", query))
                .andExpect(content().json(objectMapper.writeValueAsString(expectedResult)))
                .andExpect(status().isOk());
        verify(gitRepoService,only()).getRepositoryByAccessID(usercode);
        verify(searchService,only()).search(query);
    }

    @Test
    void createCommitSelectionForSummary_ValidRequest_ReturnsSuccess() throws Exception {
        // Arrange
        UUID usercode = UUID.randomUUID();
        ContentConstruct c1 = ContentConstruct.builder().id("asdsda").build();
        ContentConstruct c2 = ContentConstruct.builder().id("ladsad").build();
        SelectionSubmission selection = new SelectionSubmission(Set.of(c1.id(), c2.id()));

        // Act & Assert
        mockMvc.perform(post("/api/repositories/{usercode}/selection", usercode)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(selection)))
                .andExpect(status().isOk());
        verify(gitRepoService,times(1)).createCommitSelection(usercode, selection);
        verifyNoMoreInteractions(gitRepoService);
    }

    @Test
    void createCommitSelectionForSummary_ValidRequest_AssertsValidContent() throws Exception {
        // Arrange
        UUID usercode = UUID.randomUUID();
        SelectionSubmission selection = new SelectionSubmission(Set.of("does_not_exist"));
        doThrow(new ResponseStatusException(HttpStatus.BAD_REQUEST, "please make sure that all selected content exists for the current week"))
                .when(gitRepoService)
                        .createCommitSelection(usercode, selection);
        // Act & Assert
        mockMvc.perform(post("/api/repositories/{usercode}/selection", usercode)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(selection)))
                .andExpect(status().isBadRequest());
        verify(gitRepoService, only()).createCommitSelection(usercode, selection);
        verifyNoMoreInteractions(gitRepoService);
    }

    @Test
    void createQuestion_ValidRequest_ReturnsSuccess() throws Exception {
        // Arrange
        UUID usercode = UUID.randomUUID();
        QuestionSubmission question = new QuestionSubmission("What are the recent changes?");

        Counter question_creation_total = mock(Counter.class);
        when(meterRegistry.counter("question_creation_total")).thenReturn(question_creation_total);
        // Act & Assert
        mockMvc.perform(post("/api/repositories/{usercode}/question", usercode)
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(question)))
                .andExpect(status().isOk());
        verify(meterRegistry,only()).counter("question_creation_total");
        verify(question_creation_total,only()).increment();
        verify(gitRepoService,only()).createQuestion(any(UUID.class), any(String.class));
    }

    @Test
    void createQuestion_InvalidUsercode_ReturnsForbidden() throws Exception {
        // Arrange
        UUID invalidUsercode = UUID.randomUUID();
        QuestionSubmission question = new QuestionSubmission("Test question");

        doThrow(new ResponseStatusException(HttpStatus.FORBIDDEN, "link is not a valid access id"))
                .when(gitRepoService)
                .createQuestion(any(UUID.class), any(String.class));

        // Act & Assert
        mockMvc.perform(post("/api/repositories/{usercode}/question", invalidUsercode)
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(question)))
                .andExpect(status().isForbidden());
        verify(gitRepoService,only()).createQuestion(invalidUsercode, question.question());
    }
}