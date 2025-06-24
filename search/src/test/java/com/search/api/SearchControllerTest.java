package com.search.api;

import com.fasterxml.jackson.databind.ObjectMapper;
import io.micrometer.core.instrument.Counter;
import io.micrometer.core.instrument.MeterRegistry;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

import java.util.ArrayList;
import java.util.UUID;

import static org.mockito.Mockito.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

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
        SearchResult expectedResult = SearchResult.builder().facetHits(new ArrayList<>()).facetQuery("abc=bde")
                .processingTimeMs(42).build();

        when(searchService.search(usercode, query)).thenReturn(new FacetSearchTestResult());
        Counter searches_performed_total = mock(Counter.class);
        when(meterRegistry.counter("searches_performed_total")).thenReturn(searches_performed_total);
        // Act & Assert

        mockMvc.perform(get("/api/search/{usercode}", usercode).param("query", query)).andExpect(content().json(objectMapper.writeValueAsString(expectedResult))).andExpect(status().isOk());
        verify(searchService, only()).search(usercode,query);
    }
}
