package com.search.api;

import org.junit.jupiter.api.Test;

import java.util.*;

import static org.junit.jupiter.api.Assertions.*;

class SearchFilterTest {

    @Test
    void testBuildFilterString_singleFilter() {
        Map<String, String> filters = new HashMap<>();
        filters.put("user", "Commander");
        String result = SearchFilter.buildFilterString(filters);
        assertEquals("user = \"Commander\"", result);
    }

    @Test
    void testBuildFilterString_multipleFilters() {
        Map<String, String> filters = new LinkedHashMap<>();
        filters.put("user", "Commander");
        filters.put("repository", "promptheus");
        String result = SearchFilter.buildFilterString(filters);
        assertEquals("user = \"Commander\" AND repository = \"promptheus\"", result);
    }

    @Test
    void testBuildFilterString_ignoresNonFilterable() {
        Map<String, String> filters = new HashMap<>();
        filters.put("user", "Commander");
        filters.put("nonexistent", "value");
        String result = SearchFilter.buildFilterString(filters);
        assertEquals("user = \"Commander\"", result);
    }

    @Test
    void testBuildFilterString_emptyMap() {
        Map<String, String> filters = new HashMap<>();
        String result = SearchFilter.buildFilterString(filters);
        assertEquals("", result);
    }

    @Test
    void testBuildFilterString_nullMap() {
        String result = SearchFilter.buildFilterString(null);
        assertEquals("", result);
    }

    @Test
    void testBuildFilterString_booleanAndTimestamp() {
        Map<String, String> filters = new LinkedHashMap<>();
        filters.put("is_selected", "true");
        filters.put("created_at_timestamp", "1640995200 TO 1672531200");
        String result = SearchFilter.buildFilterString(filters);
        assertEquals("is_selected = true AND created_at_timestamp 1640995200 TO 1672531200", result);
    }

    @Test
    void testIsValidFilterValue_boolean() {
        assertTrue(SearchFilter.isValidFilterValue("is_selected", "true"));
        assertTrue(SearchFilter.isValidFilterValue("is_selected", "false"));
        assertFalse(SearchFilter.isValidFilterValue("is_selected", "maybe"));
    }

    @Test
    void testIsValidFilterValue_timestamp() {
        assertTrue(SearchFilter.isValidFilterValue("created_at_timestamp", "1640995200"));
        assertTrue(SearchFilter.isValidFilterValue("created_at_timestamp", "1640995200 TO 1672531200"));
        assertFalse(SearchFilter.isValidFilterValue("created_at_timestamp", "not_a_timestamp"));
    }

    @Test
    void testSanitizeFilterValue_removesQuotesAndBackslashes() {
        String input = "\"dangerous\\input\"";
        String sanitized = SearchFilter.sanitizeFilterValue(input);
        assertEquals("dangerousinput", sanitized);
    }
}
