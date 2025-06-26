package com.search.api;

import lombok.Builder;

import java.util.ArrayList;
import java.util.HashMap;

@Builder
public record SearchResult(ArrayList<HashMap<String, Object>> facetHits,int processingTimeMs,String facetQuery) {
}
