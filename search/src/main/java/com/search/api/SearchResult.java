package com.search.api;

import java.util.ArrayList;
import java.util.HashMap;
import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class SearchResult {

    private ArrayList<HashMap<String, Object>> hits;
    private int processingTimeMs;
    private String query;

    // Legacy facet search fields for backward compatibility
    private ArrayList<HashMap<String, Object>> facetHits;
    private String facetQuery;
}
