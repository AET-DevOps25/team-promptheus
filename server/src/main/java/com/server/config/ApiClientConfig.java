package com.server.config;

import com.server.genai.api.DefaultApi;
import com.server.genai.ApiClient;
import com.server.summary.api.SummaryControllerApi;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.module.SimpleModule;
import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.databind.DeserializationContext;
import com.fasterxml.jackson.databind.JsonDeserializer;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import java.io.IOException;
import java.time.LocalDateTime;
import java.time.OffsetDateTime;
import java.time.ZoneOffset;
import java.time.format.DateTimeFormatter;

@Configuration
public class ApiClientConfig {

    @Value("${genai.service.url:http://genai:3003}")
    private String genaiServiceUrl;

    @Value("${summary.service.url:http://summary:8084}")
    private String summaryServiceUrl;

    @Bean
    public DefaultApi genaiApi() {
        ApiClient genaiApiClient = new com.server.genai.ApiClient();
        genaiApiClient.setBasePath(genaiServiceUrl);
        return new DefaultApi(genaiApiClient);
    }

    @Bean
    public SummaryControllerApi summaryApi() {
        com.server.summary.ApiClient summaryApiClient = new com.server.summary.ApiClient();
        summaryApiClient.setBasePath(summaryServiceUrl);

        // Configure ObjectMapper to handle LocalDateTime strings as UTC OffsetDateTime
        ObjectMapper objectMapper = summaryApiClient.getObjectMapper();

        // Add custom deserializer for OffsetDateTime that handles LocalDateTime strings
        SimpleModule module = new SimpleModule();
        module.addDeserializer(OffsetDateTime.class, new JsonDeserializer<OffsetDateTime>() {
            @Override
            public OffsetDateTime deserialize(JsonParser p, DeserializationContext ctxt) throws IOException {
                String text = p.getText();
                try {
                    // First try to parse as OffsetDateTime (with timezone)
                    return OffsetDateTime.parse(text);
                } catch (Exception e1) {
                    try {
                        // If that fails, try to parse as LocalDateTime and assume UTC
                        LocalDateTime localDateTime = LocalDateTime.parse(text);
                        return localDateTime.atOffset(ZoneOffset.UTC);
                    } catch (Exception e2) {
                        throw new IOException("Unable to parse date-time: " + text, e2);
                    }
                }
            }
        });

        objectMapper.registerModule(module);
        objectMapper.registerModule(new JavaTimeModule());
        objectMapper.configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);

        return new SummaryControllerApi(summaryApiClient);
    }
}
