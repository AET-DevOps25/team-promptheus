package com.server.api;

import com.server.CommunicationObjects.*;
import com.fasterxml.jackson.databind.ObjectMapper;
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
    void createQuestion_ValidRequest_ReturnsSuccess() throws Exception {
        // Arrange
        UUID usercode = UUID.randomUUID();
        QuestionSubmission question = new QuestionSubmission("What are the recent changes?", "testuser", 123L, "2025-W04");

        QuestionAnswerConstruct mockResponse = QuestionAnswerConstruct.builder()
                .answer("This is a test answer")
                .confidence(0.9f)
                .createdAt(java.time.Instant.now())
                .build();

        when(gitRepoService.createQuestion(any(UUID.class), any(String.class), any(String.class), any(Long.class), any(String.class)))
                .thenReturn(mockResponse);

        Counter question_creation_total = mock(Counter.class);
        when(meterRegistry.counter("question_creation_total")).thenReturn(question_creation_total);
        // Act & Assert
        mockMvc.perform(post("/api/repositories/{usercode}/question", usercode)
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(question)))
                .andExpect(status().isOk());
        verify(meterRegistry).counter("question_creation_total");
        verify(question_creation_total).increment();
        verify(gitRepoService).createQuestion(any(UUID.class), any(String.class), any(String.class), any(Long.class), any(String.class));
    }

    @Test
    void createQuestion_InvalidUsercode_ReturnsForbidden() throws Exception {
        // Arrange
        UUID invalidUsercode = UUID.randomUUID();
        QuestionSubmission question = new QuestionSubmission("Test question", "testuser", 123L, "2025-W04");

        when(gitRepoService.createQuestion(any(UUID.class), any(String.class), any(String.class), any(Long.class), any(String.class)))
                .thenThrow(new ResponseStatusException(HttpStatus.FORBIDDEN, "link is not a valid access id"));

        // Act & Assert
        mockMvc.perform(post("/api/repositories/{usercode}/question", invalidUsercode)
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(question)))
                .andExpect(status().isForbidden());
        verify(gitRepoService).createQuestion(invalidUsercode, question.question(), question.username(), question.gitRepositoryId(), question.weekId());
    }
}
