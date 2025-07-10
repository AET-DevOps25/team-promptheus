package com.server.config;

import com.server.genai.api.DefaultApi;
import com.server.genai.ApiClient;
import com.server.summary.api.SummaryControllerApi;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.reactive.function.client.WebClient;

@Configuration
public class ApiClientConfig {

    @Value("${genai.service.url:http://localhost:8003}")
    private String genaiServiceUrl;

    @Value("${summary.service.url:http://localhost:8084}")
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
        return new SummaryControllerApi(summaryApiClient);
    }
}
