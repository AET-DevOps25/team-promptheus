package de.promptheus.contributions.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import jakarta.annotation.PostConstruct;
import java.util.List;
import java.util.Map;

@Service
@RequiredArgsConstructor
@Slf4j
public class OllamaEmbeddingService {

    private final ObjectMapper objectMapper;
    private final RestTemplate restTemplate;
    
    @Value("${app.ollamaBaseUrl}")
    private String ollamaBaseUrl;
    
    @Value("${app.ollamaModel}")
    private String ollamaModel;
    
    @Value("${app.ollamaApiKey}")
    private String ollamaApiKey;
    
    @PostConstruct
    public void init() {
        log.info("Initialized Ollama embedding service with base URL: {} and model: {}", 
                ollamaBaseUrl, ollamaModel);
    }
    
    /**
     * Generate vector embeddings for the given text
     * @param text The text to generate embeddings for
     * @return List of doubles representing the embedding vector
     * @throws RuntimeException if embedding generation fails
     */
    public List<Double> generateEmbedding(String text) {
        if (text == null || text.trim().isEmpty()) {
            log.warn("Cannot generate embedding for empty text");
            return null;
        }
       
        try {
            
            Map<String, Object> requestBody = Map.of(
                "model", ollamaModel,
                "input", text
            );
            
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            if (ollamaApiKey != null && !ollamaApiKey.trim().isEmpty()) {
                headers.setBearerAuth(ollamaApiKey);
            }
            
            HttpEntity<Map<String, Object>> entity = new HttpEntity<>(requestBody, headers);
            ResponseEntity<String> responseEntity = restTemplate.exchange(
                    ollamaBaseUrl + "/api/embed", 
                    HttpMethod.POST, 
                    entity, 
                    String.class
            );
            
            String response = responseEntity.getBody();
            
            if (response != null) {
                try {
                    JsonNode responseNode = objectMapper.readTree(response);
                    JsonNode embeddingsNode = responseNode.path("embeddings");
                    
                    if (embeddingsNode.isArray() && embeddingsNode.size() > 0) {
                        JsonNode embeddingArray = embeddingsNode.get(0);
                        if (embeddingArray.isArray()) {
                            return objectMapper.convertValue(embeddingArray, 
                                    objectMapper.getTypeFactory().constructCollectionType(List.class, Double.class));
                        }
                    }
                } catch (Exception jsonException) {
                    String errorMessage = "Failed to parse embedding response from Ollama: " + jsonException.getMessage();
                    log.error(errorMessage, jsonException);
                    throw new RuntimeException(errorMessage, jsonException);
                }
            }
            
            String errorMessage = "Failed to extract embeddings from Ollama response. The model may not support embeddings or the response format is unexpected.";
            log.error(errorMessage);
            throw new RuntimeException(errorMessage);
            
        } catch (Exception e) {
            if (e instanceof IllegalStateException || e instanceof RuntimeException) {
                throw e; // Re-throw our custom exceptions
            }
            String errorMessage = String.format("Failed to generate embedding for text (length: %d): %s", text.length(), e.getMessage());
            log.error(errorMessage, e);
            throw new RuntimeException(errorMessage, e);
        }
    }
    
    /**
     * Generate embeddings for multiple texts in batch
     * @param texts List of texts to generate embeddings for
     * @return Map of text to embedding vector
     */
    public Map<String, List<Double>> generateEmbeddings(List<String> texts) {
        if (texts == null || texts.isEmpty()) {
            return Map.of();
        }
        
        // For now, process individually - could be optimized for batch processing
        return texts.stream()
                .filter(text -> text != null && !text.trim().isEmpty())
                .collect(java.util.stream.Collectors.toMap(
                        text -> text,
                        this::generateEmbedding,
                        (existing, replacement) -> existing
                ))
                .entrySet().stream()
                .filter(entry -> entry.getValue() != null)
                .collect(java.util.stream.Collectors.toMap(
                        Map.Entry::getKey,
                        Map.Entry::getValue
                ));
    }
    
    /**
     * Check if the Ollama service is available and the model is accessible
     * @return true if service is healthy, false otherwise
     */
    public boolean isHealthy() {
        try {
            HttpHeaders headers = new HttpHeaders();
            if (ollamaApiKey != null && !ollamaApiKey.trim().isEmpty()) {
                headers.setBearerAuth(ollamaApiKey);
            }
            
            HttpEntity<String> entity = new HttpEntity<>(headers);
            ResponseEntity<String> responseEntity = restTemplate.exchange(
                    ollamaBaseUrl + "/api/tags", 
                    HttpMethod.GET, 
                    entity, 
                    String.class
            );
            
            String response = responseEntity.getBody();
            
            if (response != null) {
                JsonNode responseNode = objectMapper.readTree(response);
                JsonNode modelsNode = responseNode.path("models");
                
                if (modelsNode.isArray()) {
                    for (JsonNode modelNode : modelsNode) {
                        String modelName = modelNode.path("name").asText();
                        if (modelName.startsWith(ollamaModel)) {
                            log.info("Ollama model {} is available", ollamaModel);
                            return true;
                        }
                    }
                }
            }
            
            log.warn("Ollama model {} not found in available models", ollamaModel);
            return false;
            
        } catch (Exception e) {
            log.error("Failed to check Ollama health", e);
            return false;
        }
    }
} 