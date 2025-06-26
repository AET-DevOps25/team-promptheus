package com.search.api;

import com.meilisearch.sdk.model.FacetSearchable;

import java.util.ArrayList;
import java.util.HashMap;

public class FacetSearchTestResult implements FacetSearchable {
    @Override
    public ArrayList<HashMap<String, Object>> getFacetHits() {
        return new ArrayList<>();
    }

    @Override
    public int getProcessingTimeMs() {
        return 42;
    }

    @Override
    public String getFacetQuery() {
        return "abc=bde";
    }
}
