package de.promptheus.summary.config;

import de.promptheus.summary.contribution.api.ContributionControllerApi;
import de.promptheus.summary.genai.api.DefaultApi;
import io.netty.channel.ChannelOption;
import io.netty.handler.timeout.ReadTimeoutHandler;
import io.netty.handler.timeout.WriteTimeoutHandler;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.reactive.ReactorClientHttpConnector;
import org.springframework.web.reactive.function.client.ExchangeStrategies;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.netty.http.client.HttpClient;
import reactor.netty.resources.ConnectionProvider;

import java.time.Duration;
import java.util.concurrent.TimeUnit;

@Configuration
public class ApiClientConfig {

    @Value("${app.http.connection.maxConnections:50}")
    private int maxConnections;

    @Value("${app.http.timeout.connect:30000}")
    private int connectTimeoutMillis;

    @Value("${app.http.timeout.read:60000}")
    private int readTimeoutMillis;

    @Value("${app.http.timeout.write:30000}")
    private int writeTimeoutMillis;

    @Value("${app.http.timeout.response:300000}")
    private int responseTimeoutMillis;

    @Value("${app.http.buffer.maxSize:10485760}")
    private int bufferMaxSize;

    @Bean
    public DefaultApi genAiApi(@Value("${app.genaiServiceUrl}") String genaiServiceUrl) {
        WebClient webClient = createWebClientWithTimeouts();
        de.promptheus.summary.genai.ApiClient apiClient = new de.promptheus.summary.genai.ApiClient(webClient);
        apiClient.setBasePath(genaiServiceUrl);
        return new DefaultApi(apiClient);
    }

    @Bean
    public ContributionControllerApi contributionApi(@Value("${app.contributionServiceUrl}") String contributionServiceUrl) {
        WebClient webClient = createWebClientWithTimeouts();
        de.promptheus.summary.contribution.ApiClient apiClient = new de.promptheus.summary.contribution.ApiClient(webClient);
        apiClient.setBasePath(contributionServiceUrl);
        return new ContributionControllerApi(apiClient);
    }

    private WebClient createWebClientWithTimeouts() {
        // Create connection pool with configurable limits
        ConnectionProvider connectionProvider = ConnectionProvider.builder("summary-service")
                .maxConnections(maxConnections)
                .maxIdleTime(Duration.ofSeconds(30))
                .maxLifeTime(Duration.ofMinutes(10))
                .pendingAcquireTimeout(Duration.ofSeconds(30))
                .evictInBackground(Duration.ofSeconds(60))
                .build();

        // Configure HttpClient with configurable timeouts and connection settings
        HttpClient httpClient = HttpClient.create(connectionProvider)
                .option(ChannelOption.CONNECT_TIMEOUT_MILLIS, connectTimeoutMillis)
                .doOnConnected(conn -> conn
                        .addHandlerLast(new ReadTimeoutHandler(readTimeoutMillis, TimeUnit.MILLISECONDS))
                        .addHandlerLast(new WriteTimeoutHandler(writeTimeoutMillis, TimeUnit.MILLISECONDS))
                )
                .responseTimeout(Duration.ofMillis(responseTimeoutMillis));

        // Configure WebClient with configurable buffer sizes
        ExchangeStrategies strategies = ExchangeStrategies.builder()
                .codecs(configurer -> configurer.defaultCodecs().maxInMemorySize(bufferMaxSize))
                .build();

        return WebClient.builder()
                .clientConnector(new ReactorClientHttpConnector(httpClient))
                .exchangeStrategies(strategies)
                .build();
    }
}
