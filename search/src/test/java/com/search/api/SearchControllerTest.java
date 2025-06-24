package com.search.api;

import com.search.api.SearchController;
import com.search.api.SearchService;
import com.meilisearch.sdk.model.SearchResult;
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

@WebMvcTest(SearchController.class)
class SearchControllerTest {
    @Autowired
    private MockMvc mockMvc;

    @MockitoBean
    private SearchService searchService;

    @MockitoBean
    private MeterRegistry meterRegistry;

    @Autowired
    private ObjectMapper objectMapper;

    @Test
    void search_ValidRequest_ReturnsSearchResult() throws Exception {
        // Arrange
        UUID usercode = UUID.randomUUID();
        String query = "test query";
        SearchResult expectedResult = new SearchResult();

        when(searchService.search(query)).thenReturn(expectedResult);
        // Act & Assert
        mockMvc.perform(get("/api/repositories/{usercode}/search", usercode)
                .param("query", query))
                .andExpect(content().json(objectMapper.writeValueAsString(expectedResult)))
                .andExpect(status().isOk());
        verify(searchService,only()).search(query);
    }
}
