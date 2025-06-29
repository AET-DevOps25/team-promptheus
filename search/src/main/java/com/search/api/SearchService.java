package com.search.api;

import com.meilisearch.sdk.Client;
import com.meilisearch.sdk.Config;
import com.meilisearch.sdk.Index;
import com.meilisearch.sdk.SearchRequest;
import com.meilisearch.sdk.model.Searchable;
import com.search.ConfigProperties;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;
import java.util.UUID;


@Service
@Slf4j
public class SearchService {
    private final Index contributionsIndex;

    @Autowired
    public SearchService(ConfigProperties properties) {
        Client meilisearchClient = new Client(new Config(properties.getMeiliHost(), properties.getMeiliMasterKey()));
        contributionsIndex = meilisearchClient.index("contributions");
    }

    public Searchable search(@NotNull @NotBlank String query, Map<String, String> filters, List<String> sort, Integer limit, Integer offset) {
        SearchRequest requestBuilder = new SearchRequest(query);

        // Set limit and offset if provided
        if (limit != null && limit > 0) {
            requestBuilder.setLimit(limit);
        }
        if (offset != null && offset >= 0) {
            requestBuilder.setOffset(offset);
        }

        // Set facets
        //requestBuilder.setFacets(facets.toArray(new String[0]));

        // Highlight all attributes by default
        requestBuilder.setAttributesToHighlight(new String[]{"*"});

        requestBuilder.setCropLength(20);

        // Build filter string using utility
        String filterString = SearchFilter.buildFilterString(filters);
        requestBuilder.setFilter(new String[]{filterString});

        // Add sorting using utility
        String[] sortArray = SearchFilter.validateAndFilterSortFields(sort);
        if (sortArray.length > 0) {
            requestBuilder.setSort(sortArray);
        }

        return contributionsIndex.search(requestBuilder);
    }

    public List<String> getFilterableAttributes() {
        return SearchFilter.FILTERABLE_ATTRIBUTES;
    }

    public List<String> getSortableAttributes() {
        return SearchFilter.SORTABLE_ATTRIBUTES;
    }
}
