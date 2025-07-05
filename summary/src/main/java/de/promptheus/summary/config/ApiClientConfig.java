package de.promptheus.summary.config;

import de.promptheus.summary.contribution.api.ContributionControllerApi;
import de.promptheus.summary.genai.api.DefaultApi;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.reactive.function.client.WebClient;

@Configuration
public class ApiClientConfig {

    @Bean
    public DefaultApi genAiApi(@Value("${app.genaiServiceUrl}") String genaiServiceUrl) {
        WebClient webClient = WebClient.builder().build();
        de.promptheus.summary.genai.ApiClient apiClient = new de.promptheus.summary.genai.ApiClient(webClient);
        apiClient.setBasePath(genaiServiceUrl);
        return new DefaultApi(apiClient);
    }

    @Bean
    public ContributionControllerApi contributionApi(@Value("${app.contributionServiceUrl}") String contributionServiceUrl) {
        WebClient webClient = WebClient.builder().build();
        de.promptheus.summary.contribution.ApiClient apiClient = new de.promptheus.summary.contribution.ApiClient(webClient);
        apiClient.setBasePath(contributionServiceUrl);
        return new ContributionControllerApi(apiClient);
    }
}
