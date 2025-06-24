package com.search.api;

import com.search.ConfigProperties;
import com.meilisearch.sdk.Client;
import com.meilisearch.sdk.Config;
import com.meilisearch.sdk.model.SearchResult;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

@Service
public class SearchService {
    private final Client meilisearchClient;

    @Autowired
    public SearchService(ConfigProperties properties) {
        meilisearchClient = new Client(new Config(properties.getMeiliHost(), properties.getMeiliMasterKey()));
    }

    public SearchResult search(@NotNull @NotBlank String query) {
        return meilisearchClient.getIndex("content")
                .search(query);
    }
}
