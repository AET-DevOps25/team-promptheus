package com.search.api;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.ArgumentMatchers.isNull;
import static org.mockito.Mockito.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.meilisearch.sdk.model.Searchable;
import io.micrometer.core.instrument.Counter;
import io.micrometer.core.instrument.MeterRegistry;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

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

        // Create mock search hits with test data
        ArrayList<HashMap<String, Object>> mockHits = new ArrayList<>();
        HashMap<String, Object> hit1 = new HashMap<>();
        hit1.put("id", "1");
        hit1.put("title", "Test Result 1");
        hit1.put("content", "This is a test result");
        mockHits.add(hit1);

        HashMap<String, Object> hit2 = new HashMap<>();
        hit2.put("id", "2");
        hit2.put("title", "Test Result 2");
        hit2.put("content", "Another test result");
        mockHits.add(hit2);

        HashMap<String, Object> hit3 = new HashMap<>();
        hit3.put("id", "3");
        hit3.put("title", "Test Result 3");
        hit3.put("content", "Yet another test result");
        mockHits.add(hit3);

        // Create expected result with actual hits
        SearchResult expectedResult = SearchResult.builder().hits(mockHits).processingTimeMs(42).query(query).facetHits(null).facetQuery(null).build();

        // Mock the Searchable interface that MeiliSearch returns
        Searchable mockSearchable = mock(Searchable.class);
        when(mockSearchable.getHits()).thenReturn(mockHits);
        when(mockSearchable.getProcessingTimeMs()).thenReturn(42);

        // Mock the service call with correct parameters (all 6 parameters)
        // The controller passes null for sortFields, limit, and offset when not provided
        when(searchService.search(eq(usercode), eq(query), any(Map.class), isNull(), isNull(), isNull())).thenReturn(mockSearchable);

        Counter searches_performed_total = mock(Counter.class);
        when(meterRegistry.counter("searches_performed_total")).thenReturn(searches_performed_total);

        // Act & Assert
        mockMvc
            .perform(get("/api/search/{usercode}", usercode).param("query", query))
            .andExpect(status().isOk())
            .andExpect(content().json(objectMapper.writeValueAsString(expectedResult)));

        // Verify the service was called with correct parameters
        verify(searchService, times(1)).search(eq(usercode), eq(query), any(Map.class), isNull(), isNull(), isNull());
    }

    @Test
    void search_WithAllFiltersAndSorting_ReturnsSearchResult() throws Exception {
        // Arrange
        UUID usercode = UUID.randomUUID();
        String query = "test query";
        String user = "testuser";
        String week = "2024-01";
        String contributionType = "commit";
        String repository = "test-repo";
        String author = "test-author";
        String createdAtTimestamp = "1640995200";
        Boolean isSelected = true;
        String sort = "-created_at_timestamp,relevance_score";
        Integer limit = 10;
        Integer offset = 0;

        // Create mock search hits
        ArrayList<HashMap<String, Object>> mockHits = new ArrayList<>();
        HashMap<String, Object> hit = new HashMap<>();
        hit.put("id", "1");
        hit.put("title", "Filtered Result");
        hit.put("content", "This is a filtered test result");
        mockHits.add(hit);

        // Create expected result
        SearchResult expectedResult = SearchResult.builder().hits(mockHits).processingTimeMs(25).query(query).facetHits(null).facetQuery(null).build();

        // Mock the Searchable interface
        Searchable mockSearchable = mock(Searchable.class);
        when(mockSearchable.getHits()).thenReturn(mockHits);
        when(mockSearchable.getProcessingTimeMs()).thenReturn(25);

        // Mock the service call with all parameters
        when(searchService.search(eq(usercode), eq(query), any(Map.class), any(List.class), eq(limit), eq(offset))).thenReturn(mockSearchable);

        Counter searches_performed_total = mock(Counter.class);
        when(meterRegistry.counter("searches_performed_total")).thenReturn(searches_performed_total);

        // Act & Assert
        mockMvc
            .perform(
                get("/api/search/{usercode}", usercode)
                    .param("query", query)
                    .param("user", user)
                    .param("week", week)
                    .param("contribution_type", contributionType)
                    .param("repository", repository)
                    .param("author", author)
                    .param("created_at_timestamp", createdAtTimestamp)
                    .param("is_selected", isSelected.toString())
                    .param("sort", sort)
                    .param("limit", limit.toString())
                    .param("offset", offset.toString())
            )
            .andExpect(status().isOk())
            .andExpect(content().json(objectMapper.writeValueAsString(expectedResult)));

        // Verify the service was called with correct parameters
        verify(searchService, times(1)).search(eq(usercode), eq(query), any(Map.class), any(List.class), eq(limit), eq(offset));
        verify(searches_performed_total, times(1)).increment();
    }

    @Test
    void search_WithEmptyQuery_ReturnsBadRequest() throws Exception {
        // Arrange
        UUID usercode = UUID.randomUUID();

        // Act & Assert
        mockMvc.perform(get("/api/search/{usercode}", usercode).param("query", "")).andExpect(status().isBadRequest());

        // Verify the service was never called
        verifyNoInteractions(searchService);
    }

    @Test
    void search_WithInvalidUsercode_ReturnsBadRequest() throws Exception {
        // Act & Assert
        mockMvc.perform(get("/api/search/{usercode}", "invalid-uuid").param("query", "test")).andExpect(status().isBadRequest());

        // Verify the service was never called
        verifyNoInteractions(searchService);
    }

    @Test
    void search_WithMissingQuery_ReturnsBadRequest() throws Exception {
        // Arrange
        UUID usercode = UUID.randomUUID();

        // Act & Assert
        mockMvc.perform(get("/api/search/{usercode}", usercode)).andExpect(status().isBadRequest());

        // Verify the service was never called
        verifyNoInteractions(searchService);
    }

    @Test
    void getFilterableAttributes_ReturnsListOfAttributes() throws Exception {
        // Arrange
        List<String> expectedAttributes = Arrays.asList("user", "week", "contribution_type", "repository", "author", "created_at_timestamp", "is_selected");

        when(searchService.getFilterableAttributes()).thenReturn(expectedAttributes);

        // Act & Assert
        mockMvc
            .perform(get("/api/search/filterable-attributes"))
            .andExpect(status().isOk())
            .andExpect(content().json(objectMapper.writeValueAsString(expectedAttributes)));

        verify(searchService, times(1)).getFilterableAttributes();
    }

    @Test
    void getSortableAttributes_ReturnsListOfAttributes() throws Exception {
        // Arrange
        List<String> expectedAttributes = Arrays.asList("created_at_timestamp", "relevance_score");

        when(searchService.getSortableAttributes()).thenReturn(expectedAttributes);

        // Act & Assert
        mockMvc
            .perform(get("/api/search/sortable-attributes"))
            .andExpect(status().isOk())
            .andExpect(content().json(objectMapper.writeValueAsString(expectedAttributes)));

        verify(searchService, times(1)).getSortableAttributes();
    }

    @Test
    void search_WithPartialFilters_ReturnsSearchResult() throws Exception {
        // Arrange
        UUID usercode = UUID.randomUUID();
        String query = "partial test";
        String repository = "specific-repo";
        Boolean isSelected = false;

        // Create mock search hits
        ArrayList<HashMap<String, Object>> mockHits = new ArrayList<>();
        HashMap<String, Object> hit = new HashMap<>();
        hit.put("id", "1");
        hit.put("title", "Partial Filter Result");
        hit.put("repository", repository);
        mockHits.add(hit);

        // Create expected result
        SearchResult expectedResult = SearchResult.builder().hits(mockHits).processingTimeMs(30).query(query).facetHits(null).facetQuery(null).build();

        // Mock the Searchable interface
        Searchable mockSearchable = mock(Searchable.class);
        when(mockSearchable.getHits()).thenReturn(mockHits);
        when(mockSearchable.getProcessingTimeMs()).thenReturn(30);

        // Mock the service call
        when(searchService.search(eq(usercode), eq(query), any(Map.class), isNull(), isNull(), isNull())).thenReturn(mockSearchable);

        Counter searches_performed_total = mock(Counter.class);
        when(meterRegistry.counter("searches_performed_total")).thenReturn(searches_performed_total);

        // Act & Assert
        mockMvc
            .perform(get("/api/search/{usercode}", usercode).param("query", query).param("repository", repository).param("is_selected", isSelected.toString()))
            .andExpect(status().isOk())
            .andExpect(content().json(objectMapper.writeValueAsString(expectedResult)));

        // Verify the service was called
        verify(searchService, times(1)).search(eq(usercode), eq(query), any(Map.class), isNull(), isNull(), isNull());
        verify(searches_performed_total, times(1)).increment();
    }

    @Test
    void search_WithSortingOnly_ReturnsSearchResult() throws Exception {
        // Arrange
        UUID usercode = UUID.randomUUID();
        String query = "sorted search";
        String sort = "-created_at_timestamp";

        // Create mock search hits
        ArrayList<HashMap<String, Object>> mockHits = new ArrayList<>();
        HashMap<String, Object> hit = new HashMap<>();
        hit.put("id", "1");
        hit.put("title", "Sorted Result");
        hit.put("created_at_timestamp", 1640995200);
        mockHits.add(hit);

        // Create expected result
        SearchResult expectedResult = SearchResult.builder().hits(mockHits).processingTimeMs(35).query(query).facetHits(null).facetQuery(null).build();

        // Mock the Searchable interface
        Searchable mockSearchable = mock(Searchable.class);
        when(mockSearchable.getHits()).thenReturn(mockHits);
        when(mockSearchable.getProcessingTimeMs()).thenReturn(35);

        // Mock the service call with sort fields
        when(searchService.search(eq(usercode), eq(query), any(Map.class), any(List.class), isNull(), isNull())).thenReturn(mockSearchable);

        Counter searches_performed_total = mock(Counter.class);
        when(meterRegistry.counter("searches_performed_total")).thenReturn(searches_performed_total);

        // Act & Assert
        mockMvc
            .perform(get("/api/search/{usercode}", usercode).param("query", query).param("sort", sort))
            .andExpect(status().isOk())
            .andExpect(content().json(objectMapper.writeValueAsString(expectedResult)));

        // Verify the service was called with sort fields
        verify(searchService, times(1)).search(eq(usercode), eq(query), any(Map.class), any(List.class), isNull(), isNull());
        verify(searches_performed_total, times(1)).increment();
    }

    @Test
    void search_WithLimitAndOffset_ReturnsSearchResult() throws Exception {
        // Arrange
        UUID usercode = UUID.randomUUID();
        String query = "paginated search";
        Integer limit = 5;
        Integer offset = 10;

        // Create mock search hits
        ArrayList<HashMap<String, Object>> mockHits = new ArrayList<>();
        for (int i = 1; i <= 5; i++) {
            HashMap<String, Object> hit = new HashMap<>();
            hit.put("id", String.valueOf(i + 10));
            hit.put("title", "Paginated Result " + (i + 10));
            mockHits.add(hit);
        }

        // Create expected result
        SearchResult expectedResult = SearchResult.builder().hits(mockHits).processingTimeMs(20).query(query).facetHits(null).facetQuery(null).build();

        // Mock the Searchable interface
        Searchable mockSearchable = mock(Searchable.class);
        when(mockSearchable.getHits()).thenReturn(mockHits);
        when(mockSearchable.getProcessingTimeMs()).thenReturn(20);

        // Mock the service call with pagination
        when(searchService.search(eq(usercode), eq(query), any(Map.class), isNull(), eq(limit), eq(offset))).thenReturn(mockSearchable);

        Counter searches_performed_total = mock(Counter.class);
        when(meterRegistry.counter("searches_performed_total")).thenReturn(searches_performed_total);

        // Act & Assert
        mockMvc
            .perform(get("/api/search/{usercode}", usercode).param("query", query).param("limit", limit.toString()).param("offset", offset.toString()))
            .andExpect(status().isOk())
            .andExpect(content().json(objectMapper.writeValueAsString(expectedResult)));

        // Verify the service was called with pagination parameters
        verify(searchService, times(1)).search(eq(usercode), eq(query), any(Map.class), isNull(), eq(limit), eq(offset));
        verify(searches_performed_total, times(1)).increment();
    }

    @Test
    void search_MetricsCounterIncrementation_VerifyCounterCalled() throws Exception {
        // Arrange
        UUID usercode = UUID.randomUUID();
        String query = "metrics test";

        // Create mock search hits
        ArrayList<HashMap<String, Object>> mockHits = new ArrayList<>();
        HashMap<String, Object> hit = new HashMap<>();
        hit.put("id", "1");
        hit.put("title", "Metrics Test Result");
        mockHits.add(hit);

        // Mock the Searchable interface
        Searchable mockSearchable = mock(Searchable.class);
        when(mockSearchable.getHits()).thenReturn(mockHits);
        when(mockSearchable.getProcessingTimeMs()).thenReturn(15);

        // Mock the service call
        when(searchService.search(eq(usercode), eq(query), any(Map.class), isNull(), isNull(), isNull())).thenReturn(mockSearchable);

        Counter searches_performed_total = mock(Counter.class);
        when(meterRegistry.counter("searches_performed_total")).thenReturn(searches_performed_total);

        // Act
        mockMvc.perform(get("/api/search/{usercode}", usercode).param("query", query)).andExpect(status().isOk());

        // Assert - Verify metrics counter is called correctly
        verify(meterRegistry, times(1)).counter("searches_performed_total");
        verify(searches_performed_total, times(1)).increment();
    }

    @Test
    void search_EmptyResults_ReturnsEmptySearchResult() throws Exception {
        // Arrange
        UUID usercode = UUID.randomUUID();
        String query = "no results query";

        // Create empty mock search hits
        ArrayList<HashMap<String, Object>> emptyHits = new ArrayList<>();

        // Create expected result with empty hits
        SearchResult expectedResult = SearchResult.builder().hits(emptyHits).processingTimeMs(5).query(query).facetHits(null).facetQuery(null).build();

        // Mock the Searchable interface
        Searchable mockSearchable = mock(Searchable.class);
        when(mockSearchable.getHits()).thenReturn(emptyHits);
        when(mockSearchable.getProcessingTimeMs()).thenReturn(5);

        // Mock the service call
        when(searchService.search(eq(usercode), eq(query), any(Map.class), isNull(), isNull(), isNull())).thenReturn(mockSearchable);

        Counter searches_performed_total = mock(Counter.class);
        when(meterRegistry.counter("searches_performed_total")).thenReturn(searches_performed_total);

        // Act & Assert
        mockMvc
            .perform(get("/api/search/{usercode}", usercode).param("query", query))
            .andExpect(status().isOk())
            .andExpect(content().json(objectMapper.writeValueAsString(expectedResult)));

        // Verify the service was called and counter incremented
        verify(searchService, times(1)).search(eq(usercode), eq(query), any(Map.class), isNull(), isNull(), isNull());
        verify(searches_performed_total, times(1)).increment();
    }
}
