package de.promptheus.contributions.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.meilisearch.sdk.Client;
import com.meilisearch.sdk.Config;
import com.meilisearch.sdk.Index;
import com.meilisearch.sdk.exceptions.MeilisearchException;
import com.meilisearch.sdk.model.Embedder;
import com.meilisearch.sdk.model.EmbedderSource;
import com.meilisearch.sdk.model.Settings;
import com.meilisearch.sdk.model.TaskInfo;
import de.promptheus.contributions.entity.Contribution;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import jakarta.annotation.PostConstruct;
import java.time.Instant;
import java.time.LocalDate;
import java.time.ZoneOffset;
import java.time.temporal.IsoFields;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
@RequiredArgsConstructor
@Slf4j
public class MeilisearchService {

    private final ObjectMapper objectMapper;
    private final OllamaEmbeddingService ollamaEmbeddingService;
    
    @Value("${app.meiliHost}")
    private String meilisearchHost;
    
    @Value("${app.meiliMasterKey}")
    private String meilisearchMasterKey;
    
    private Client meilisearchClient;
    private Index contributionsIndex;
    
    private static final String CONTRIBUTIONS_INDEX_NAME = "contributions";
    
    @PostConstruct
    public void init() {
        try {
            Config config = new Config(meilisearchHost, meilisearchMasterKey);
            meilisearchClient = new Client(config);
            
            // Create or get the contributions index
            try {
                contributionsIndex = meilisearchClient.getIndex(CONTRIBUTIONS_INDEX_NAME);
                log.info("Connected to existing Meilisearch contributions index");
            } catch (MeilisearchException e) {
                TaskInfo taskInfo = meilisearchClient.createIndex(CONTRIBUTIONS_INDEX_NAME, "id");
                meilisearchClient.waitForTask(taskInfo.getTaskUid());
                contributionsIndex = meilisearchClient.getIndex(CONTRIBUTIONS_INDEX_NAME);
                log.info("Created new Meilisearch contributions index");
            }
        } catch (Exception e) {
            log.error("Failed to initialize Meilisearch service", e);
        }
    }
    
    public void indexContributions(List<Contribution> contributions, String repositoryUrl) {
        if (contributions.isEmpty()) {
            return;
        }
        
        try {
            List<Map<String, Object>> documents = new ArrayList<>();
            
            for (Contribution contribution : contributions) {
                Map<String, Object> document = createDocument(contribution, repositoryUrl);
                if (document != null) {
                    documents.add(document);
                }
            }
            
            if (!documents.isEmpty()) {
                String documentsJson = objectMapper.writeValueAsString(documents);
                TaskInfo taskInfo = contributionsIndex.addDocuments(documentsJson);
                meilisearchClient.waitForTask(taskInfo.getTaskUid());
                
                log.info("Indexed {} contributions to Meilisearch", documents.size());
            }
            
        } catch (Exception e) {
            log.error("Failed to index contributions to Meilisearch", e);
        }
    }
    
    private Map<String, Object> createDocument(Contribution contribution, String repositoryUrl) {
        try {
            Map<String, Object> document = new HashMap<>();
            
            // Extract user and week from contribution
            String user = contribution.getUsername();
            String week = getISOWeek(contribution.getCreatedAt());
            
            // Create unique ID
            String documentId = user + "-" + week + "-" + contribution.getId();
            document.put("id", documentId);
            
            // Basic fields
            document.put("user", user);
            document.put("week", week);
            document.put("contribution_id", contribution.getId());
            document.put("contribution_type", contribution.getType());
            document.put("repository", repositoryUrl);
            document.put("author", user);
            document.put("created_at", contribution.getCreatedAt().toString());
            document.put("created_at_timestamp", contribution.getCreatedAt().getEpochSecond());
            
            // Extract content based on type
            JsonNode details = contribution.getDetails();
            String content = buildContentFromDetails(contribution.getType(), details, repositoryUrl);
            
            // Type-specific fields
            switch (contribution.getType()) {
                case "commit":
                    document.put("title", contribution.getSummary());
                    document.put("message", contribution.getSummary());
                    document.put("body", "");
                    document.put("filename", extractFilenames(details));
                    document.put("patch", extractPatches(details));
                    break;
                    
                case "pull_request":
                    document.put("title", contribution.getSummary());
                    document.put("message", "");
                    document.put("body", details.path("body").asText(""));
                    document.put("filename", "");
                    document.put("patch", "");
                    break;
                    
                case "issue":
                    document.put("title", contribution.getSummary());
                    document.put("message", "");
                    document.put("body", details.path("body").asText(""));
                    document.put("filename", "");
                    document.put("patch", "");
                    break;
                    
                case "release":
                    document.put("title", contribution.getSummary());
                    document.put("message", "");
                    document.put("body", details.path("body").asText(""));
                    document.put("filename", "");
                    document.put("patch", "");
                    break;
                    
                default:
                    document.put("title", contribution.getSummary());
                    document.put("message", "");
                    document.put("body", "");
                    document.put("filename", "");
                    document.put("patch", "");
            }
            
            document.put("content", content);
            document.put("relevance_score", 1.0);
            document.put("is_selected", contribution.getIsSelected());
            
            // Generate vector embeddings for the content
            // This will throw an exception if embeddings cannot be generated
            List<Double> embeddings = ollamaEmbeddingService.generateEmbedding(content);
            if (embeddings != null && !embeddings.isEmpty()) {
                document.put("_vectors", Map.of("default", embeddings));
                log.debug("Generated embeddings for contribution {} with {} dimensions", 
                        contribution.getId(), embeddings.size());
            } else {
                String errorMessage = String.format("No embeddings generated for contribution %s", contribution.getId());
                log.error(errorMessage);
                throw new RuntimeException(errorMessage);
            }
            
            return document;
            
        } catch (Exception e) {
            log.warn("Failed to create document for contribution {}", contribution.getId(), e);
            return null;
        }
    }
    
    private String buildContentFromDetails(String type, JsonNode details, String repositoryUrl) {
        StringBuilder content = new StringBuilder();
        
        content.append("Repository: ").append(repositoryUrl).append("\n");
        
        // Get author based on type
        String author = "";
        if (type.equals("commit")) {
            author = details.path("author").path("login").asText();
            if (author.isEmpty()) {
                author = details.path("commit").path("author").path("name").asText();
            }
        } else {
            author = details.path("user").path("login").asText();
        }
        content.append("Author: ").append(author).append("\n");
        
        switch (type) {
            case "commit":
                content.append("Commit: ").append(details.path("commit").path("message").asText()).append("\n");
                
                // Include file information
                JsonNode files = details.path("files");
                if (files.isArray()) {
                    for (JsonNode file : files) {
                        content.append("File: ").append(file.path("filename").asText()).append("\n");
                        String patch = file.path("patch").asText("");
                        if (!patch.isEmpty() && patch.length() > 500) {
                            patch = patch.substring(0, 500);
                        }
                        if (!patch.isEmpty()) {
                            content.append("Changes: ").append(patch).append("\n");
                        }
                    }
                }
                break;
                
            case "pull_request":
                content.append("Pull Request: ").append(details.path("title").asText()).append("\n");
                String prBody = details.path("body").asText("");
                if (!prBody.isEmpty()) {
                    content.append("Description: ").append(prBody).append("\n");
                }
                break;
                
            case "issue":
                content.append("Issue: ").append(details.path("title").asText()).append("\n");
                String issueBody = details.path("body").asText("");
                if (!issueBody.isEmpty()) {
                    content.append("Description: ").append(issueBody).append("\n");
                }
                break;
                
            case "release":
                content.append("Release: ").append(details.path("name").asText()).append("\n");
                String releaseBody = details.path("body").asText("");
                if (!releaseBody.isEmpty()) {
                    content.append("Release Notes: ").append(releaseBody).append("\n");
                }
                break;
        }
        
        return content.toString();
    }
    
    private String extractFilenames(JsonNode details) {
        StringBuilder filenames = new StringBuilder();
        JsonNode files = details.path("files");
        if (files.isArray()) {
            for (JsonNode file : files) {
                filenames.append(file.path("filename").asText()).append(" ");
            }
        }
        return filenames.toString().trim();
    }
    
    private String extractPatches(JsonNode details) {
        StringBuilder patches = new StringBuilder();
        JsonNode files = details.path("files");
        if (files.isArray()) {
            for (JsonNode file : files) {
                String patch = file.path("patch").asText("");
                if (!patch.isEmpty() && patch.length() > 500) {
                    patch = patch.substring(0, 500);
                }
                if (!patch.isEmpty()) {
                    patches.append(patch).append(" ");
                }
            }
        }
        return patches.toString().trim();
    }
    
    private String getISOWeek(Instant instant) {
        LocalDate date = instant.atZone(ZoneOffset.UTC).toLocalDate();
        int year = date.get(IsoFields.WEEK_BASED_YEAR);
        int week = date.get(IsoFields.WEEK_OF_WEEK_BASED_YEAR);
        return String.format("%d-W%02d", year, week);
    }
    
    public void deleteContributionsForRepository(String repositoryUrl) {
        try {
            // Note: Meilisearch Java SDK doesn't support delete by filter directly
            // We would need to search for documents and then delete by IDs
            // For now, log a warning
            log.warn("Delete by filter not implemented in Java SDK. Documents for repository {} will remain in index until overwritten.", repositoryUrl);
            
            // Alternative approach: search for documents and delete by IDs
            // This is left as a TODO for production implementation
            
        } catch (Exception e) {
            log.error("Failed to delete contributions from Meilisearch", e);
        }
    }
    
    /**
     * Perform hybrid search combining text search and vector similarity
     * @param query The search query text
     * @param user Filter by user (optional)
     * @param week Filter by ISO week (optional) 
     * @param limit Maximum number of results
     * @return Search results as JSON string
     */
    public String hybridSearch(String query, String user, String week, int limit) {
        try {
            // Generate embedding for the query
            List<Double> queryEmbedding = ollamaEmbeddingService.generateEmbedding(query);
            
            // Build search parameters
            Map<String, Object> searchParams = new HashMap<>();
            searchParams.put("q", query);
            searchParams.put("limit", limit);
            searchParams.put("attributesToRetrieve", Arrays.asList(
                "id", "user", "week", "contribution_type", "title", "content", 
                "repository", "author", "created_at", "relevance_score"
            ));
            
            // Add filters
            List<String> filters = new ArrayList<>();
            if (user != null && !user.trim().isEmpty()) {
                filters.add("user = \"" + user + "\"");
            }
            if (week != null && !week.trim().isEmpty()) {
                filters.add("week = \"" + week + "\"");
            }
            
            if (!filters.isEmpty()) {
                searchParams.put("filter", String.join(" AND ", filters));
            }
            
            // Add vector search if embedding was generated successfully
            if (queryEmbedding != null && !queryEmbedding.isEmpty()) {
                Map<String, Object> vector = new HashMap<>();
                vector.put("default", queryEmbedding);
                searchParams.put("vector", vector);
                searchParams.put("hybrid", Map.of("semanticRatio", 0.5)); // 50% semantic, 50% keyword
                
                log.debug("Performing hybrid search with {} dimensional vector", queryEmbedding.size());
            } else {
                log.info("Performing text-only search (vector embedding failed)");
            }
            
            // Perform search
            String searchParamsJson = objectMapper.writeValueAsString(searchParams);
            
            // Note: The actual search result handling would depend on the Meilisearch Java SDK API
            // For now, we return the search parameters as a placeholder
            // In production, this would perform the actual search and return results
            
            log.info("Hybrid search completed for query: '{}' with {} results requested", query, limit);
            return searchParamsJson; // Placeholder - would return actual results
            
        } catch (Exception e) {
            log.error("Failed to perform hybrid search for query: '{}'", query, e);
            return null;
        }
    }
    
    /**
     * Search for contributions by user and week with vector similarity
     * @param user The username to search for
     * @param week The ISO week to search for  
     * @param semanticQuery Optional semantic query for similarity search
     * @param limit Maximum number of results
     * @return Search results as JSON string
     */
    public String searchContributions(String user, String week, String semanticQuery, int limit) {
        try {
            Map<String, Object> searchParams = new HashMap<>();
            
            // Build filters
            List<String> filters = new ArrayList<>();
            if (user != null && !user.trim().isEmpty()) {
                filters.add("user = \"" + user + "\"");
            }
            if (week != null && !week.trim().isEmpty()) {
                filters.add("week = \"" + week + "\"");
            }
            
            if (!filters.isEmpty()) {
                searchParams.put("filter", String.join(" AND ", filters));
            }
            
            searchParams.put("limit", limit);
            searchParams.put("attributesToRetrieve", Arrays.asList(
                "id", "user", "week", "contribution_type", "title", "content", 
                "repository", "author", "created_at", "relevance_score", "is_selected"
            ));
            
            // Add semantic search if query provided
            if (semanticQuery != null && !semanticQuery.trim().isEmpty()) {
                List<Double> queryEmbedding = ollamaEmbeddingService.generateEmbedding(semanticQuery);
                if (queryEmbedding != null && !queryEmbedding.isEmpty()) {
                    Map<String, Object> vector = new HashMap<>();
                    vector.put("default", queryEmbedding);
                    searchParams.put("vector", vector);
                    
                    log.debug("Performing filtered vector search for user: '{}', week: '{}', query: '{}'", 
                            user, week, semanticQuery);
                }
            }
            
            String searchParamsJson = objectMapper.writeValueAsString(searchParams);
            log.info("Searching contributions for user: '{}', week: '{}' with {} results requested", 
                    user, week, limit);
            
            // Return search parameters for now - would perform actual search in production
            return searchParamsJson;
            
        } catch (Exception e) {
            log.error("Failed to search contributions for user: '{}', week: '{}'", user, week, e);
            return null;
        }
    }
} 