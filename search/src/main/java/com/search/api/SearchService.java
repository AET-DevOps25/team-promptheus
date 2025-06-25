package com.search.api;

import com.meilisearch.sdk.FacetSearchRequest;
import com.meilisearch.sdk.model.FacetSearchResult;
import com.meilisearch.sdk.model.FacetSearchable;
import com.search.ConfigProperties;
import com.meilisearch.sdk.Client;
import com.meilisearch.sdk.Config;
import com.meilisearch.sdk.model.SearchResult;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.UUID;

@Service
public class SearchService {
    private final Client meilisearchClient;

    @Autowired
    public SearchService(ConfigProperties properties) {
        meilisearchClient = new Client(new Config(properties.getMeiliHost(), properties.getMeiliMasterKey()));
    }

    public FacetSearchable search(@NotNull UUID usercode, @NotNull @NotBlank String query) {
        FacetSearchRequest request = FacetSearchRequest.builder().facetName("repo_id").facetQuery(usercode.toString()).q(query).build();
        return meilisearchClient.getIndex("content").facetSearch(request);
    }
}
